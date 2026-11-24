"""bf16 conversion, LoRA merge, and the processor-config callback."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from safetensors import safe_open
from safetensors.torch import save_file

from judge_train.train.callbacks import CopyProcessorConfigsCallback
from judge_train.utils.bf16_save import (
    INDEX_FILE,
    convert_all_checkpoints,
    convert_to_bf16,
    shard_and_write,
)
from judge_train.utils.merge_lora import merge_all_checkpoints, merge_lora_to_bf16


def _load_all(d: Path) -> dict[str, torch.Tensor]:
    index = json.loads((d / INDEX_FILE).read_text())
    out = {}
    for fname in sorted(set(index["weight_map"].values())):
        with safe_open(str(d / fname), framework="pt") as f:
            for k in f.keys():
                out[k] = f.get_tensor(k)
    assert set(out) == set(index["weight_map"])
    return out


def _fake_checkpoint(d: Path, tensors: dict[str, torch.Tensor]) -> Path:
    d.mkdir(parents=True)
    save_file(tensors, str(d / "model.safetensors"))
    (d / "config.json").write_text(json.dumps({"model_type": "llama", "dtype": "float32"}))
    (d / "tokenizer.json").write_text("{}")
    for name in ["optimizer.bin", "scheduler.pt", "trainer_state.json", "rng_state_0.pth"]:
        (d / name).write_text("x")
    return d


@pytest.fixture
def weights():
    g = torch.Generator().manual_seed(0)
    return {
        "a.weight": torch.randn(8, 4, generator=g),
        "b.weight": torch.randn(4, 4, generator=g),
        "steps": torch.arange(3),  # non-float tensors keep their dtype
    }


def test_convert_to_bf16(tmp_path, weights):
    src = _fake_checkpoint(tmp_path / "checkpoint-10", weights)
    dst = tmp_path / "out"
    convert_to_bf16(src, dst)

    got = _load_all(dst)
    assert got["a.weight"].dtype == torch.bfloat16
    assert torch.equal(got["a.weight"], weights["a.weight"].to(torch.bfloat16))
    assert got["steps"].dtype == torch.int64

    cfg = json.loads((dst / "config.json").read_text())
    assert cfg["dtype"] == cfg["torch_dtype"] == "bfloat16"
    assert (dst / "tokenizer.json").exists()
    for name in ["optimizer.bin", "scheduler.pt", "trainer_state.json", "rng_state_0.pth"]:
        assert not (dst / name).exists()
    # The source checkpoint is untouched.
    assert json.loads((src / "config.json").read_text())["dtype"] == "float32"

    # Idempotent: a second run does not rewrite the destination.
    mtime = (dst / INDEX_FILE).stat().st_mtime_ns
    convert_to_bf16(src, dst)
    assert (dst / INDEX_FILE).stat().st_mtime_ns == mtime


def test_sharding(tmp_path, weights):
    src = _fake_checkpoint(tmp_path / "src", weights)
    shard_and_write(iter(weights.items()), tmp_path / "dst", src, shard_bytes=1)
    shards = sorted(p.name for p in (tmp_path / "dst").glob("*.safetensors"))
    assert shards == [f"model-0000{i}-of-00003.safetensors" for i in (1, 2, 3)]
    assert set(_load_all(tmp_path / "dst")) == set(weights)


def test_convert_all_checkpoints(tmp_path, weights):
    run = tmp_path / "run"
    for step in (100, 20):
        _fake_checkpoint(run / f"checkpoint-{step}", weights)
    done = convert_all_checkpoints(run)
    assert done == [str(run / "checkpoint-20"), str(run / "checkpoint-100")]
    assert (run / "checkpoint-100-bf16" / INDEX_FILE).exists()
    # Re-running does not pick up the -bf16 dirs.
    assert convert_all_checkpoints(run) == done


def _fake_adapter(d: Path, base_dir: Path, r: int, alpha: int, a: torch.Tensor, b: torch.Tensor):
    d.mkdir(parents=True)
    save_file(
        {"base_model.model.a.lora_A.weight": a, "base_model.model.a.lora_B.weight": b},
        str(d / "adapter_model.safetensors"),
    )
    (d / "adapter_config.json").write_text(json.dumps({
        "peft_type": "LORA", "r": r, "lora_alpha": alpha, "base_model_name_or_path": str(base_dir),
    }))
    (d / "tokenizer_config.json").write_text('{"from": "adapter"}')
    (d / "config.json").write_text('{"from": "adapter"}')


def test_merge_lora(tmp_path, weights):
    base = _fake_checkpoint(tmp_path / "base", weights)
    g = torch.Generator().manual_seed(1)
    a, b = torch.randn(2, 4, generator=g), torch.randn(8, 2, generator=g)
    _fake_adapter(tmp_path / "run" / "checkpoint-5", base, r=2, alpha=4, a=a, b=b)

    done = merge_all_checkpoints(tmp_path / "run")
    assert done == [str(tmp_path / "run" / "checkpoint-5")]
    dst = tmp_path / "run" / "checkpoint-5-merged-bf16"

    got = _load_all(dst)
    expected = (weights["a.weight"] + (4 / 2) * (b @ a)).to(torch.bfloat16)
    assert torch.equal(got["a.weight"], expected)
    assert torch.equal(got["b.weight"], weights["b.weight"].to(torch.bfloat16))
    # Base config is kept. Adapter tokenizer files overlay the base.
    assert json.loads((dst / "config.json").read_text())["model_type"] == "llama"
    assert json.loads((dst / "tokenizer_config.json").read_text()) == {"from": "adapter"}
    assert not (dst / "adapter_config.json").exists()


def test_merge_lora_key_mismatch(tmp_path, weights):
    base = _fake_checkpoint(tmp_path / "base", {"other.weight": torch.zeros(8, 4)})
    _fake_adapter(tmp_path / "adapter", base, 2, 4, torch.zeros(2, 4), torch.zeros(8, 2))
    with pytest.raises(RuntimeError, match="do not match"):
        merge_lora_to_bf16(tmp_path / "adapter", tmp_path / "out")


def test_processor_config_callback(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    for name in ["preprocessor_config.json", "video_preprocessor_config.json", "config.json"]:
        (base / name).write_text(json.dumps({"src": "base"}))

    out = tmp_path / "out"
    ckpt = out / "checkpoint-7"
    ckpt.mkdir(parents=True)
    (ckpt / "config.json").write_text(json.dumps({"src": "trained"}))

    cb = CopyProcessorConfigsCallback(str(base))
    args = SimpleNamespace(output_dir=str(out))

    # Non-zero ranks do nothing.
    cb.on_save(args, SimpleNamespace(is_world_process_zero=False, global_step=7), None)
    assert not (ckpt / "preprocessor_config.json").exists()

    cb.on_save(args, SimpleNamespace(is_world_process_zero=True, global_step=7), None)
    assert (ckpt / "preprocessor_config.json").exists()
    assert (ckpt / "video_preprocessor_config.json").exists()
    # Existing files are not overwritten. Missing source files are skipped.
    assert json.loads((ckpt / "config.json").read_text()) == {"src": "trained"}
    assert not (ckpt / "generation_config.json").exists()


def test_processor_config_callback_unknown_hub_id(tmp_path):
    cb = CopyProcessorConfigsCallback("no-such-org/no-such-model")
    assert cb.copy_to(tmp_path) == []
