"""Stage A round trip: JSONL -> prepare -> Arrow -> trainer loader."""

from __future__ import annotations

import json
import shutil

import pytest
from datasets import load_from_disk

from conftest import MESSAGES_FIXTURE, PC_FIXTURE
from judge_train.config import load_config
from judge_train.data.build import build_inline_dataset, build_train_eval_datasets, load_pretokenized_dataset
from judge_train.data.prepare import main as prepare_main
from judge_train.data.prepare import prepare
from judge_train.data.tokenization import tokenize_prompt_completion


def _cfg(tiny_model_dir, train_path, out, fmt="prompt_completion", **data):
    return {
        "model_name_or_path": str(tiny_model_dir),
        "data": {
            "train_path": str(train_path),
            "tokenized_data_path": str(out),
            "max_length": 512,
            "format": fmt,
            "chat_template_kwargs": {"enable_thinking": False},
            **data,
        },
    }


def test_prompt_completion_round_trip(tiny_model_dir, tiny_tokenizer, write_config, tmp_path, pc_rows):
    # Append one record that must be skipped (prompt ends with assistant).
    train = tmp_path / "train.jsonl"
    shutil.copy(PC_FIXTURE, train)
    with train.open("a") as f:
        f.write(json.dumps({
            "id": "bad",
            "prompt": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}],
            "completion": [{"role": "assistant", "content": "b"}],
        }) + "\n")

    out = tmp_path / "prepared"
    meta = prepare(write_config(_cfg(tiny_model_dir, train, out)))
    assert meta["total_records"] == 7
    assert meta["tokenized_records"] == 6
    assert meta["skipped_records"] == 1
    assert meta["format"] == "prompt_completion"
    assert json.loads((out / "metadata.json").read_text()) == meta

    ds = load_from_disk(str(out / "dataset"))
    assert set(ds.column_names) == {"input_ids", "completion_mask"}
    assert len(ds) == 6
    for row, src in zip(ds, pc_rows):
        expected = tokenize_prompt_completion(
            src["prompt"], src["completion"], tiny_tokenizer,
            max_length=512, chat_template_kwargs={"enable_thinking": False},
        )
        assert row["input_ids"] == expected["input_ids"]
        assert row["completion_mask"] == expected["completion_mask"]


def test_messages_round_trip(tiny_model_dir, write_config, tmp_path):
    out = tmp_path / "prepared"
    meta = prepare(write_config(_cfg(tiny_model_dir, MESSAGES_FIXTURE, out, fmt="messages", max_length=16)))
    assert meta["tokenized_records"] == 4
    ds = load_from_disk(str(out / "dataset"))
    assert ds.column_names == ["input_ids"]
    assert all(0 < len(r["input_ids"]) <= 16 for r in ds)


def test_cli_output_override_and_num_proc(tiny_model_dir, write_config, tmp_path):
    cfg_path = write_config(_cfg(tiny_model_dir, PC_FIXTURE, tmp_path / "unused"))
    out = tmp_path / "override"
    prepare_main(["--config", cfg_path, "--output", str(out), "--num-proc", "2"])
    assert (out / "dataset").exists()
    assert not (tmp_path / "unused").exists()


def test_max_train_samples(tiny_model_dir, write_config, tmp_path):
    out = tmp_path / "prepared"
    meta = prepare(write_config(_cfg(tiny_model_dir, PC_FIXTURE, out, max_train_samples=2)))
    assert meta["tokenized_records"] == 2


def test_missing_output_raises(tiny_model_dir, write_config):
    cfg = _cfg(tiny_model_dir, PC_FIXTURE, "x")
    del cfg["data"]["tokenized_data_path"]
    with pytest.raises(ValueError, match="tokenized_data_path"):
        prepare(write_config(cfg))


def test_trainer_loader_reads_stage_a_output(tiny_model_dir, write_config, tmp_path):
    out = tmp_path / "prepared"
    cfg_path = write_config(_cfg(tiny_model_dir, PC_FIXTURE, out, val_path=str(PC_FIXTURE)))
    prepare(cfg_path)
    cfg = load_config(cfg_path)

    train, evalset = build_train_eval_datasets(cfg)
    assert len(train) == 6 and "completion_mask" in train.column_names
    # Eval stays inline and keeps the prompt-completion columns.
    assert {"prompt", "completion", "chat_template_kwargs"} <= set(evalset.column_names)

    # Pointing straight at the Arrow dir also works.
    cfg.data.tokenized_data_path = str(out / "dataset")
    assert len(load_pretokenized_dataset(cfg)) == 6


def test_pretokenized_messages_rejected_for_prompt_completion(tiny_model_dir, write_config, tmp_path):
    out = tmp_path / "prepared"
    cfg_path = write_config(_cfg(tiny_model_dir, MESSAGES_FIXTURE, out, fmt="messages"))
    prepare(cfg_path)
    cfg = load_config(cfg_path)
    cfg.data.format = "prompt_completion"
    with pytest.raises(ValueError, match="completion_mask"):
        load_pretokenized_dataset(cfg)


def test_inline_dataset_carries_chat_template_kwargs(tiny_model_dir, write_config, tmp_path):
    cfg = load_config(write_config(_cfg(tiny_model_dir, PC_FIXTURE, tmp_path / "x")))
    ds = build_inline_dataset(cfg, "train")
    assert ds[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert build_inline_dataset(cfg, "eval") is None

    cfg.data.chat_template_kwargs = None
    assert "chat_template_kwargs" not in build_inline_dataset(cfg, "train").column_names
