"""Config parsing, validation, and the mapping to SFTConfig."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO_ROOT
from judge_train.config import Config, global_batch_size, load_config, validate_config

EXAMPLE_CONFIGS = sorted((REPO_ROOT / "configs" / "examples").glob("*.yaml"))

# The recipe used for the released checkpoints.
RECIPE_DATA = {
    "max_length": 8192,
    "packing": False,
    "format": "prompt_completion",
    "chat_template_kwargs": {"enable_thinking": False},
}
RECIPE_TRAINING = {
    "num_train_epochs": 1,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "learning_rate": 5.0e-6,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.05,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "bf16": True,
    "gradient_checkpointing": False,
    "fsdp": "full_shard",
    "save_strategy": "steps",
    "save_steps": 1000,
    "save_only_model": True,
    "logging_steps": 10,
    "completion_only_loss": True,
    "save_total_limit": 2,
    "report_to": "none",
}


def test_example_configs_exist():
    names = {p.name for p in EXAMPLE_CONFIGS}
    assert {"qwen3.5-0.8b.yaml", "qwen3.5-4b.yaml", "qwen3.5-9b.yaml"} <= names


@pytest.mark.parametrize("path", EXAMPLE_CONFIGS, ids=lambda p: p.name)
def test_example_config_matches_recipe(path: Path):
    cfg = load_config(str(path))
    for k, v in RECIPE_DATA.items():
        assert getattr(cfg.data, k) == v, f"data.{k}"
    for k, v in RECIPE_TRAINING.items():
        assert getattr(cfg.training, k) == v, f"training.{k}"
    assert cfg.seed == 42
    assert cfg.attn_implementation == "flash_attention_2"
    assert cfg.data.train_path.startswith("./")
    assert cfg.training.output_dir.startswith("./")
    # 4 nodes x 8 GPUs gives the recipe's global batch of 128.
    assert global_batch_size(cfg, num_processes=32) == 128


def test_defaults_match_recipe():
    cfg = Config()
    for k, v in RECIPE_DATA.items():
        if k != "chat_template_kwargs":
            assert getattr(cfg.data, k) == v, f"data.{k}"
    for k, v in RECIPE_TRAINING.items():
        if k != "fsdp":  # default is no FSDP so a single process run works
            assert getattr(cfg.training, k) == v, f"training.{k}"
    assert cfg.training.fsdp is None


def test_empty_file_gives_defaults(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    assert load_config(str(p)) == Config()


def test_nested_merge_keeps_other_defaults(write_config):
    cfg = load_config(write_config({
        "model_name_or_path": "./m",
        "data": {"train_path": "./d.jsonl", "max_length": 128},
        "training": {"learning_rate": 1e-4},
        "lora": {"enabled": True, "r": 8},
    }))
    assert cfg.model_name_or_path == "./m"
    assert cfg.data.max_length == 128
    assert cfg.data.format == "prompt_completion"
    assert cfg.training.learning_rate == 1e-4
    assert cfg.training.gradient_accumulation_steps == 4
    assert cfg.lora.enabled and cfg.lora.r == 8 and cfg.lora.alpha == 32


@pytest.mark.parametrize("raw, key", [
    ({"not_a_key": 1}, "not_a_key"),
    ({"data": {"trian_path": "x"}}, "data.trian_path"),
    ({"training": {"lr": 1e-5}}, "training.lr"),
    ({"mlflow": {"tracking_uri": "x"}}, "mlflow"),
    ({"checkpoint_sync": {"enabled": True}}, "checkpoint_sync"),
])
def test_unknown_keys_raise(write_config, raw, key):
    with pytest.raises(ValueError, match=f"Unknown config key: {key}"):
        load_config(write_config(raw))


def test_section_must_be_mapping(write_config):
    with pytest.raises(ValueError, match="must be a mapping"):
        load_config(write_config({"data": "oops"}))


def test_bad_format_raises(write_config):
    with pytest.raises(ValueError, match="data.format"):
        load_config(write_config({"data": {"format": "chatml"}}))


def test_fsdp_with_gradient_checkpointing_raises():
    cfg = Config()
    cfg.training.fsdp = "full_shard"
    cfg.training.gradient_checkpointing = True
    with pytest.raises(ValueError, match="gradient_checkpointing"):
        validate_config(cfg)


def test_global_batch_size_scaling():
    cfg = Config()
    cfg.training.gradient_accumulation_steps = 16
    assert global_batch_size(cfg, num_processes=8) == 128


# -- mapping to TRL --------------------------------------------------------------

def test_build_sft_config(tmp_path):
    from judge_train.train.sft import build_sft_config

    cfg = Config()
    cfg.training.bf16 = False
    cfg.training.use_cpu = True
    cfg.training.output_dir = str(tmp_path)
    cfg.training.exp_name = "exp"
    sft = build_sft_config(cfg)
    assert sft.output_dir == str(tmp_path / "exp")
    assert sft.run_name == "exp"
    assert sft.completion_only_loss is True
    assert sft.max_length == 8192
    assert sft.packing is False
    assert sft.learning_rate == 5.0e-6
    assert sft.gradient_accumulation_steps == 4
    assert sft.warmup_steps == 0.05
    assert sft.save_only_model is True
    assert sft.save_total_limit == 2
    assert sft.report_to == [] or sft.report_to in ("none", ["none"])
    assert sft.seed == 42

    cfg.training.completion_only_loss = False
    cfg.training.run_name = "named"
    sft = build_sft_config(cfg)
    assert sft.completion_only_loss is False
    assert sft.run_name == "named"


def test_model_init_kwargs_fsdp():
    import torch

    from judge_train.train.sft import build_model_init_kwargs

    cfg = Config()
    cfg.attn_implementation = "flash_attention_2"
    kw = build_model_init_kwargs(cfg)
    assert kw["dtype"] == torch.bfloat16
    assert kw["attn_implementation"] == "flash_attention_2"
    assert "device_map" not in kw

    cfg.training.fsdp = "full_shard"
    kw = build_model_init_kwargs(cfg)
    assert kw["device_map"] is None and kw["low_cpu_mem_usage"] is True


def test_resolve_resume_checkpoint(tmp_path):
    from judge_train.train.sft import resolve_resume_checkpoint

    cfg = Config()
    cfg.training.output_dir = str(tmp_path)
    cfg.training.exp_name = "run"
    assert resolve_resume_checkpoint(cfg) is None

    cfg.training.resume = "auto"
    assert resolve_resume_checkpoint(cfg) is None
    for name in ["checkpoint-500", "checkpoint-1000", "checkpoint-1000-bf16", "checkpoint-99"]:
        (tmp_path / "run" / name).mkdir(parents=True)
    assert resolve_resume_checkpoint(cfg) == str(tmp_path / "run" / "checkpoint-1000")

    cfg.training.resume = "/some/explicit/path"
    assert resolve_resume_checkpoint(cfg) == "/some/explicit/path"


def test_validate_qwen35():
    from judge_train.train.sft import validate_qwen35

    cfg = Config()
    cfg.data.packing = True
    with pytest.raises(ValueError, match="packing"):
        validate_qwen35(cfg)

    cfg = Config()
    cfg.training.deepspeed = "ds.json"
    with pytest.raises(ValueError, match="DeepSpeed"):
        validate_qwen35(cfg)

    cfg = Config()
    validate_qwen35(cfg)
    assert cfg.training.ddp_find_unused_parameters is True

    cfg = Config()
    cfg.training.fsdp = "full_shard"
    validate_qwen35(cfg)
    assert cfg.training.ddp_find_unused_parameters is None
