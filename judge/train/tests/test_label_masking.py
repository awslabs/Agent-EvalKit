"""Completion-only loss: labels are -100 everywhere except completion tokens.

Covers both data paths:
  - Stage A rows go through TRL's collator, which turns completion_mask into labels.
  - The inline path is tokenized by SFTTrainer itself. Its rows must equal Stage A rows.
"""

from __future__ import annotations

import pytest
import torch
from datasets import Dataset
from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

from conftest import PC_FIXTURE
from judge_train.config import Config
from judge_train.data.build import build_inline_dataset
from judge_train.data.tokenization import tokenize_prompt_completion

NO_THINK = {"enable_thinking": False}


@pytest.fixture
def stage_a_rows(tiny_tokenizer, pc_rows):
    return [
        tokenize_prompt_completion(r["prompt"], r["completion"], tiny_tokenizer, chat_template_kwargs=NO_THINK)
        for r in pc_rows
    ]


def _collate(tok, rows, completion_only_loss=True):
    collator = DataCollatorForLanguageModeling(
        pad_token_id=tok.pad_token_id, completion_only_loss=completion_only_loss,
    )
    return collator([dict(r) for r in rows])


def test_labels_masked_outside_completion(tiny_tokenizer, stage_a_rows, pc_rows):
    batch = _collate(tiny_tokenizer, stage_a_rows)
    for i, row in enumerate(stage_a_rows):
        n = len(row["input_ids"])
        labels = batch["labels"][i]
        mask = torch.tensor(row["completion_mask"])
        # Prompt tokens and right padding are ignored.
        assert torch.all(labels[:n][mask == 0] == -100)
        assert torch.all(labels[n:] == -100)
        # Completion tokens are trained on, with their own ids as targets.
        trained = labels[:n][mask == 1]
        assert torch.all(trained != -100)
        assert trained.tolist() == [t for t, m in zip(row["input_ids"], row["completion_mask"]) if m]
        decoded = tiny_tokenizer.decode(trained.tolist())
        assert decoded == pc_rows[i]["completion"][0]["content"] + "<|im_end|>\n"


def test_full_loss_when_disabled(tiny_tokenizer, stage_a_rows):
    batch = _collate(tiny_tokenizer, stage_a_rows, completion_only_loss=False)
    for i, row in enumerate(stage_a_rows):
        n = len(row["input_ids"])
        assert torch.all(batch["labels"][i][:n] != -100)


def _trl_prepared(tiny_model_dir, tiny_tokenizer, dataset, tmp_path):
    from trl import SFTConfig, SFTTrainer

    args = SFTConfig(
        output_dir=str(tmp_path / "trl"),
        max_length=512,
        packing=False,
        completion_only_loss=True,
        report_to="none",
        bf16=False,
        max_steps=1,
        dataloader_num_workers=0,
        use_cpu=True,
        model_init_kwargs={"device_map": "cpu"},
    )
    trainer = SFTTrainer(
        model=str(tiny_model_dir), args=args, train_dataset=dataset, processing_class=tiny_tokenizer,
    )
    return trainer.train_dataset


def test_inline_path_matches_stage_a(tiny_model_dir, tiny_tokenizer, stage_a_rows, tmp_path):
    cfg = Config()
    cfg.data.train_path = str(PC_FIXTURE)
    cfg.data.chat_template_kwargs = dict(NO_THINK)
    inline = build_inline_dataset(cfg, "train")

    prepared = _trl_prepared(tiny_model_dir, tiny_tokenizer, inline, tmp_path)
    assert len(prepared) == len(stage_a_rows)
    for got, want in zip(prepared, stage_a_rows):
        assert got["input_ids"] == want["input_ids"]
        assert got["completion_mask"] == want["completion_mask"]


def test_inline_path_needs_chat_template_kwargs_column(
    tiny_model_dir, tiny_tokenizer, stage_a_rows, pc_rows, tmp_path,
):
    """TRL ignores chat template kwargs unless they are a dataset column."""
    bare = Dataset.from_dict({
        "prompt": [r["prompt"] for r in pc_rows],
        "completion": [r["completion"] for r in pc_rows],
    })
    prepared = _trl_prepared(tiny_model_dir, tiny_tokenizer, bare, tmp_path)
    assert prepared[0]["completion_mask"] != stage_a_rows[0]["completion_mask"]


def test_verify_labels_cli(tiny_model_dir, write_config, pc_rows, capsys):
    from judge_train.data.verify_labels import verify

    cfg_path = write_config({
        "model_name_or_path": str(tiny_model_dir),
        "data": {"train_path": str(PC_FIXTURE), "max_length": 512, "chat_template_kwargs": NO_THINK},
        "training": {"bf16": False, "use_cpu": True},
    })
    stats = verify(cfg_path, num_samples=2)
    assert [s["trained_text"] for s in stats] == [
        r["completion"][0]["content"] + "<|im_end|>\n" for r in pc_rows[:2]
    ]
    assert all(s["masked"] > 0 and s["trained"] > 0 for s in stats)
    assert "Trained text" in capsys.readouterr().out
