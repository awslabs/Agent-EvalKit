"""Build the HF Datasets the trainer consumes.

Two paths:
  - Pre-tokenized (Stage B): load the Arrow dataset written by
    `python -m judge_train.data.prepare`.
  - Inline: read JSONL and let SFTTrainer tokenize on the fly.
"""

from __future__ import annotations

import logging
from pathlib import Path

from datasets import Dataset, load_from_disk

from judge_train.config import Config
from judge_train.data.loader import build_stream

logger = logging.getLogger(__name__)


def build_inline_dataset(config: Config, split: str = "train") -> Dataset | None:
    """Read JSONL for `split` ("train" or "eval") into an untokenized Dataset.

    Returns None when the split has no path (eval is optional).

    TRL reads chat template kwargs per row from a `chat_template_kwargs`
    column, so data.chat_template_kwargs is copied onto every row. Without it,
    settings such as enable_thinking=false would be ignored on this path.
    """
    if split == "train":
        path, max_samples = config.data.train_path, config.data.max_train_samples
    else:
        path, max_samples = config.data.val_path, config.data.max_eval_samples
    if not path:
        return None

    logger.info("Loading %s examples from %s", split, path)
    rows = list(build_stream(path, max_samples=max_samples))
    logger.info("Loaded %d %s examples", len(rows), split)

    if config.data.format == "prompt_completion":
        columns = {
            "prompt": [r["prompt"] for r in rows],
            "completion": [r["completion"] for r in rows],
        }
    else:
        columns = {"messages": [r["messages"] for r in rows]}

    if config.data.chat_template_kwargs:
        columns["chat_template_kwargs"] = [dict(config.data.chat_template_kwargs) for _ in rows]
    return Dataset.from_dict(columns)


def load_pretokenized_dataset(config: Config) -> Dataset:
    """Load the Stage A Arrow dataset from data.tokenized_data_path."""
    root = Path(config.data.tokenized_data_path)
    dataset_dir = root / "dataset"
    if not dataset_dir.exists():
        # Also accept a path that points directly at the Arrow dataset dir.
        dataset_dir = root
    logger.info("Loading pre-tokenized dataset from %s", dataset_dir)
    dataset = load_from_disk(str(dataset_dir))
    logger.info("Loaded %d pre-tokenized examples", len(dataset))

    if config.data.format == "prompt_completion" and "completion_mask" not in dataset.column_names:
        raise ValueError(
            "Pre-tokenized dataset has no 'completion_mask' column. Re-run "
            "`python -m judge_train.data.prepare` with data.format: prompt_completion."
        )
    return dataset


def build_train_eval_datasets(config: Config) -> tuple[Dataset, Dataset | None]:
    """Train dataset from Stage A output if configured, else inline. Eval is always inline."""
    if config.data.tokenized_data_path:
        train = load_pretokenized_dataset(config)
    else:
        train = build_inline_dataset(config, "train")
        if train is None:
            raise ValueError("Set data.train_path or data.tokenized_data_path")
    return train, build_inline_dataset(config, "eval")
