"""End-to-end CPU smoke test of `python -m judge_train.train` on the tiny local model.

Runs a few optimizer steps on both data paths, then converts the checkpoint
to bf16 and loads it back.
"""

from __future__ import annotations

import json
import math

import pytest

from conftest import PC_FIXTURE
from judge_train.data.prepare import prepare
from judge_train.utils.bf16_save import convert_all_checkpoints


@pytest.fixture
def smoke_cfg(tiny_model_dir, tmp_path):
    return {
        "model_name_or_path": str(tiny_model_dir),
        "data": {
            "train_path": str(PC_FIXTURE),
            "max_length": 512,
            "format": "prompt_completion",
            "chat_template_kwargs": {"enable_thinking": False},
        },
        "training": {
            "exp_name": "smoke",
            "output_dir": str(tmp_path / "outputs"),
            "max_steps": 3,
            "per_device_train_batch_size": 2,
            "gradient_accumulation_steps": 1,
            "learning_rate": 1.0e-3,
            "warmup_ratio": 0.0,
            "bf16": False,
            "save_steps": 2,
            "logging_steps": 1,
            "dataloader_num_workers": 0,
            "use_cpu": True,
        },
    }


def _losses(trainer):
    return [e["loss"] for e in trainer.state.log_history if "loss" in e]


def test_train_inline(smoke_cfg, write_config, tmp_path):
    from judge_train.train.sft import main

    trainer = main(write_config(smoke_cfg))
    losses = _losses(trainer)
    assert len(losses) == 3 and all(math.isfinite(x) for x in losses)

    run_dir = tmp_path / "outputs" / "smoke"
    ckpts = sorted(p.name for p in run_dir.glob("checkpoint-*"))
    assert ckpts == ["checkpoint-2", "checkpoint-3"]
    # save_only_model: no optimizer state in the checkpoint.
    assert not list((run_dir / "checkpoint-3").glob("optimizer*"))

    done = convert_all_checkpoints(run_dir)
    assert len(done) == 2
    bf16_dir = run_dir / "checkpoint-3-bf16"
    assert json.loads((bf16_dir / "config.json").read_text())["torch_dtype"] == "bfloat16"

    import torch
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(str(bf16_dir))
    assert next(model.parameters()).dtype == torch.bfloat16


def test_train_pretokenized(smoke_cfg, write_config, tmp_path):
    smoke_cfg["data"]["tokenized_data_path"] = str(tmp_path / "prepared")
    smoke_cfg["training"]["save_strategy"] = "no"
    cfg_path = write_config(smoke_cfg)
    prepare(cfg_path)
    from judge_train.train.sft import main

    trainer = main(cfg_path)
    assert all(math.isfinite(x) for x in _losses(trainer))
    assert {"input_ids", "completion_mask"} <= set(trainer.train_dataset.column_names)


def test_train_messages_format(smoke_cfg, write_config):
    from conftest import MESSAGES_FIXTURE
    from judge_train.train.sft import main

    smoke_cfg["data"].update(train_path=str(MESSAGES_FIXTURE), format="messages")
    smoke_cfg["training"].update(save_strategy="no", max_steps=1)
    trainer = main(write_config(smoke_cfg))
    assert all(math.isfinite(x) for x in _losses(trainer))
    # completion_only_loss does not apply to plain chat data.
    assert trainer.args.completion_only_loss is False


def test_cli_requires_config():
    from judge_train.train.sft import cli

    with pytest.raises(SystemExit):
        cli([])
