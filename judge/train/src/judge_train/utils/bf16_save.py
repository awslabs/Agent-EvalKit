"""Write bf16-sharded copies of saved fp32 checkpoints.

FSDP FULL_STATE_DICT saves fp32 safetensors, about twice the bytes bf16
needs. This module writes a separate bf16 copy in a new directory and leaves
the fp32 checkpoint untouched. The copy is self-contained and vLLM-loadable:

  - weights are cast fp32 to bf16 and written in 5 GB shards with an index
  - config, tokenizer, chat template, and processor files are copied over
  - training state (optimizer, scheduler, RNG) is left out
  - dtype fields in config.json are set to bfloat16

Run after training:

    # every checkpoint-{step}/ under a run dir -> checkpoint-{step}-bf16/
    python -m judge_train.utils.bf16_save ./outputs/my-run

    # one checkpoint to an explicit destination
    python -m judge_train.utils.bf16_save ./outputs/my-run/checkpoint-1000 --dst ./outputs/my-run-bf16

Idempotent. A destination that already has model.safetensors.index.json is skipped.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Iterable
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

SHARD_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB shards
INDEX_FILE = "model.safetensors.index.json"
TRAINING_STATE_FILES = {
    INDEX_FILE, "optimizer.bin", "optimizer.pt", "pytorch_model_fsdp.bin",
    "scheduler.pt", "trainer_state.json",
}
TRAINING_STATE_PREFIXES = ("rng_state",)


def _step(p: Path) -> int:
    parts = p.name.split("-")
    return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1


def is_aux_file(f: Path) -> bool:
    """True for files that belong next to the weights (config, tokenizer, processor)."""
    return (
        f.is_file()
        and f.suffix != ".safetensors"
        and f.name not in TRAINING_STATE_FILES
        and not f.name.startswith(TRAINING_STATE_PREFIXES)
    )


def convert_to_bf16(src_dir: Path | str, dst_dir: Path | str) -> None:
    """Write a bf16-sharded copy of the checkpoint at src_dir into dst_dir."""
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)
    if (dst_dir / INDEX_FILE).exists():
        return

    src_files = sorted(src_dir.glob("*.safetensors"))
    if not src_files:
        raise FileNotFoundError(f"No safetensors files in {src_dir}")

    def tensors():
        for sf_path in src_files:
            with safe_open(str(sf_path), framework="pt", device="cpu") as f:
                for key in f.keys():
                    yield key, f.get_tensor(key)

    shard_and_write(tensors(), dst_dir, src_dir)


def shard_and_write(
    tensors: Iterable[tuple[str, torch.Tensor]],
    dst_dir: Path,
    aux_src_dir: Path,
    shard_bytes: int = SHARD_BYTES,
) -> None:
    """Stream (name, tensor) pairs into bf16 shards plus an index.

    fp32 tensors are cast to bf16. Other dtypes are kept. Aux files are then
    copied from aux_src_dir and config.json dtype fields are patched.
    """
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    weight_map: dict[str, str] = {}
    total_bytes = 0
    current: dict[str, torch.Tensor] = {}
    current_bytes = 0
    shard_names: list[str] = []
    template = "model-{idx:05d}-of-XXXXX.safetensors"

    def flush() -> None:
        nonlocal current, current_bytes
        if not current:
            return
        fname = template.format(idx=len(shard_names) + 1)
        save_file(current, str(dst_dir / fname), metadata={"format": "pt"})
        for name in current:
            weight_map[name] = fname
        shard_names.append(fname)
        current = {}
        current_bytes = 0

    for key, t in tensors:
        if t.dtype == torch.float32:
            t = t.to(torch.bfloat16)
        current[key] = t
        nbytes = t.numel() * t.element_size()
        current_bytes += nbytes
        total_bytes += nbytes
        if current_bytes >= shard_bytes:
            flush()
    flush()

    final = {old: old.replace("XXXXX", f"{len(shard_names):05d}") for old in shard_names}
    for old, new in final.items():
        (dst_dir / old).rename(dst_dir / new)
    weight_map = {k: final[v] for k, v in weight_map.items()}

    with (dst_dir / INDEX_FILE).open("w") as f:
        json.dump({"metadata": {"total_size": total_bytes}, "weight_map": weight_map}, f, indent=2)

    copy_aux_files(aux_src_dir, dst_dir)
    _patch_config_dtype(dst_dir)


def copy_aux_files(src_dir: Path, dst_dir: Path) -> None:
    """Copy aux files from src_dir without overwriting files already in dst_dir."""
    for f in Path(src_dir).iterdir():
        if is_aux_file(f) and not (dst_dir / f.name).exists():
            shutil.copy2(f, dst_dir / f.name)


def _patch_config_dtype(dst_dir: Path) -> None:
    cfg_path = dst_dir / "config.json"
    if not cfg_path.exists():
        return
    cfg = json.loads(cfg_path.read_text())
    if "dtype" in cfg:
        cfg["dtype"] = "bfloat16"
    cfg["torch_dtype"] = "bfloat16"
    cfg_path.write_text(json.dumps(cfg, indent=2))


def convert_all_checkpoints(output_dir: Path | str) -> list[str]:
    """Convert every checkpoint-{step}/ under output_dir to a sibling checkpoint-{step}-bf16/."""
    ckpts = sorted(
        (p for p in Path(output_dir).glob("checkpoint-*")
         if p.is_dir() and _step(p) >= 0 and not p.name.endswith("-bf16")),
        key=_step,
    )
    for ckpt in ckpts:
        convert_to_bf16(ckpt, f"{ckpt}-bf16")
    return [str(p) for p in ckpts]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write bf16-sharded, vLLM-loadable checkpoint copies")
    parser.add_argument(
        "path",
        help="A run dir (converts every checkpoint-*/ inside it) or a single checkpoint dir with --dst",
    )
    parser.add_argument("--dst", default=None, help="Destination for single-checkpoint mode")
    args = parser.parse_args(argv)

    if args.dst:
        convert_to_bf16(args.path, args.dst)
        print(f"Wrote bf16 checkpoint: {args.dst}")
        return
    done = convert_all_checkpoints(args.path)
    if not done:
        print(f"No checkpoint-*/ dirs found under {args.path}")
        return
    print(f"Converted {len(done)} checkpoint(s):")
    for d in done:
        print(f"  {d} -> {d}-bf16")


if __name__ == "__main__":
    main()
