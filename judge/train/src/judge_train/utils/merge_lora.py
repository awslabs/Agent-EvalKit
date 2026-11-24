"""Merge a LoRA adapter into its base model and write a bf16-sharded checkpoint.

The merge works on tensors directly: for each targeted base weight W,
W_merged = W + (alpha / r) * (B @ A). No model class is instantiated, so
multimodal architectures such as Qwen3_5ForConditionalGeneration are kept as
is and memory stays low. The output is a plain full model that vLLM serves
with no LoRA flags.

Usage:
    # one adapter checkpoint
    python -m judge_train.utils.merge_lora ./outputs/my-run/checkpoint-1000 --dst ./outputs/merged-bf16

    # base defaults to base_model_name_or_path in adapter_config.json. Override with --base.
    python -m judge_train.utils.merge_lora ./outputs/my-run/checkpoint-1000 --dst ./out --base ./models/Qwen3.5-4B

    # every adapter checkpoint-{step}/ under a run dir -> checkpoint-{step}-merged-bf16/
    python -m judge_train.utils.merge_lora ./outputs/my-run
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch
from safetensors import safe_open

from judge_train.utils.bf16_save import INDEX_FILE, _step, is_aux_file, shard_and_write

ADAPTER_FILES = {"adapter_model.safetensors", "adapter_config.json"}


def is_adapter_dir(p: Path) -> bool:
    return (Path(p) / "adapter_config.json").exists()


def merge_lora_to_bf16(
    adapter_dir: Path | str,
    dst_dir: Path | str,
    base_dir: Path | str | None = None,
) -> None:
    """Merge the adapter in adapter_dir into its base and write dst_dir. Idempotent."""
    adapter_dir = Path(adapter_dir)
    dst_dir = Path(dst_dir)
    if (dst_dir / INDEX_FILE).exists():
        return

    acfg = json.loads((adapter_dir / "adapter_config.json").read_text())
    if acfg.get("peft_type") != "LORA":
        raise ValueError(f"Unsupported peft_type {acfg.get('peft_type')!r} (only LORA)")
    base_dir = Path(base_dir if base_dir is not None else acfg["base_model_name_or_path"])

    r = acfg["r"]
    alpha = acfg["lora_alpha"]
    scale = alpha / (r ** 0.5) if acfg.get("use_rslora", False) else alpha / r

    # Adapter keys look like base_model.model.<module>.lora_{A,B}.weight.
    # Index them by the base weight name they modify: <module>.weight.
    lora_a: dict[str, torch.Tensor] = {}
    lora_b: dict[str, torch.Tensor] = {}
    prefix = "base_model.model."
    with safe_open(str(adapter_dir / "adapter_model.safetensors"), framework="pt", device="cpu") as f:
        for k in f.keys():
            body = k[len(prefix):] if k.startswith(prefix) else k
            if body.endswith(".lora_A.weight"):
                lora_a[body[: -len(".lora_A.weight")] + ".weight"] = f.get_tensor(k)
            elif body.endswith(".lora_B.weight"):
                lora_b[body[: -len(".lora_B.weight")] + ".weight"] = f.get_tensor(k)
    targets = set(lora_a) & set(lora_b)
    if not targets:
        raise ValueError(f"No LoRA A/B pairs found in {adapter_dir}")

    base_files = sorted(base_dir.glob("*.safetensors"))
    if not base_files:
        raise FileNotFoundError(f"No safetensors files in base {base_dir}")

    merged = 0

    def tensors():
        nonlocal merged
        for sf_path in base_files:
            with safe_open(str(sf_path), framework="pt", device="cpu") as f:
                for key in f.keys():
                    t = f.get_tensor(key)
                    if key in targets:
                        delta = (lora_b[key].float() @ lora_a[key].float()) * scale
                        t = (t.float() + delta).to(torch.bfloat16)
                        merged += 1
                    yield key, t

    # Aux files come from the base. Then overlay the adapter dir's tokenizer and
    # processor files, but keep the base config.json.
    shard_and_write(tensors(), dst_dir, base_dir)
    for f in adapter_dir.iterdir():
        if not is_aux_file(f) or f.name in ADAPTER_FILES or f.name == "config.json":
            continue
        if not (dst_dir / f.name).exists():
            shutil.copy2(f, dst_dir / f.name)

    if merged != len(targets):
        raise RuntimeError(
            f"Merged {merged} modules but the adapter has {len(targets)} targets. "
            "The base and adapter key names do not match."
        )


def merge_all_checkpoints(output_dir: Path | str, base: str | None = None) -> list[str]:
    """Merge every adapter checkpoint-{step}/ under output_dir into a -merged-bf16 sibling."""
    ckpts = sorted(
        (p for p in Path(output_dir).glob("checkpoint-*")
         if p.is_dir() and _step(p) >= 0 and is_adapter_dir(p) and not p.name.endswith("-bf16")),
        key=_step,
    )
    for ckpt in ckpts:
        merge_lora_to_bf16(ckpt, f"{ckpt}-merged-bf16", base_dir=base)
    return [str(p) for p in ckpts]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Merge LoRA adapters into the base model as bf16 shards")
    parser.add_argument("path", help="An adapter checkpoint dir, or a run dir with adapter checkpoints")
    parser.add_argument("--dst", default=None, help="Destination for single-adapter mode")
    parser.add_argument("--base", default=None, help="Base model dir. Defaults to the adapter's base_model_name_or_path")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if args.dst or is_adapter_dir(path):
        dst = args.dst or str(path).rstrip("/") + "-merged-bf16"
        merge_lora_to_bf16(path, dst, base_dir=args.base)
        print(f"Wrote merged bf16 checkpoint: {dst}")
        return
    done = merge_all_checkpoints(path, base=args.base)
    if not done:
        print(f"No adapter checkpoint-*/ dirs found under {path}")
        return
    print(f"Merged {len(done)} adapter checkpoint(s):")
    for d in done:
        print(f"  {d} -> {d}-merged-bf16")


if __name__ == "__main__":
    main()
