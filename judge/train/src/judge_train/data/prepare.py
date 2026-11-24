"""Stage A: pre-tokenize JSONL into an Arrow dataset for the trainer.

Reads data.train_path, applies the chat template, tokenizes, truncates to
data.max_length, and writes:

    {data.tokenized_data_path}/dataset/        Arrow files (datasets.load_from_disk)
    {data.tokenized_data_path}/metadata.json   config snapshot and record counts

Runs on CPU. Use --num-proc to parallelize across cores for large datasets.

Usage:
    python -m judge_train.data.prepare --config configs/examples/qwen3.5-4b.yaml --num-proc 32
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer

from judge_train.config import load_config
from judge_train.data.loader import resolve_paths
from judge_train.data.tokenization import tokenize_messages, tokenize_prompt_completion

logger = logging.getLogger(__name__)


def prepare(config_path: str, num_proc: int = 1, output: str | None = None) -> dict:
    """Run Stage A and return the metadata dict.

    Args:
        config_path: training YAML config. Uses model_name_or_path and data.*.
        num_proc: worker processes for tokenization.
        output: overrides data.tokenized_data_path.
    """
    config = load_config(config_path)
    train_path = config.data.train_path
    max_length = config.data.max_length
    output = output or config.data.tokenized_data_path

    if not train_path:
        raise ValueError("config.data.train_path is required")
    if not output:
        raise ValueError("Set data.tokenized_data_path in the config or pass --output")

    output_path = Path(output)
    dataset_path = output_path / "dataset"
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading tokenizer from %s", config.model_name_or_path)
    tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, trust_remote_code=True)

    # Arrow's JSON reader avoids materializing millions of Python dicts.
    logger.info("Loading JSONL from %s", train_path)
    raw = load_dataset("json", data_files=resolve_paths(train_path), split="train")
    total_records = len(raw)
    logger.info("Loaded %d records", total_records)

    if config.data.max_train_samples and config.data.max_train_samples < total_records:
        raw = raw.select(range(config.data.max_train_samples))
        logger.info("Truncated to %d samples", len(raw))

    chat_template_kwargs = config.data.chat_template_kwargs
    is_prompt_completion = config.data.format == "prompt_completion"

    def tokenize_fn(example):
        if is_prompt_completion:
            result = tokenize_prompt_completion(
                example["prompt"], example["completion"], tokenizer,
                max_length=max_length, chat_template_kwargs=chat_template_kwargs,
            )
            if result is None:
                return {"input_ids": [], "completion_mask": [], "_skip": True}
        else:
            result = tokenize_messages(
                example["messages"], tokenizer,
                max_length=max_length, chat_template_kwargs=chat_template_kwargs,
            )
            if result is None:
                return {"input_ids": [], "_skip": True}
        return {**result, "_skip": False}

    logger.info(
        "Tokenizing: format=%s max_length=%s num_proc=%d chat_template_kwargs=%s",
        config.data.format, max_length, num_proc, chat_template_kwargs,
    )
    start = time.time()
    nproc = num_proc if num_proc > 1 else None
    tokenized = raw.map(
        tokenize_fn, num_proc=nproc, remove_columns=raw.column_names, desc="Tokenizing",
    )
    pre_filter = len(tokenized)
    tokenized = tokenized.filter(lambda x: not x["_skip"], num_proc=nproc)
    tokenized = tokenized.remove_columns(["_skip"])

    elapsed = time.time() - start
    kept = len(tokenized)
    skipped = pre_filter - kept
    logger.info(
        "Tokenized %d records in %.1fs (%.0f records/s, %d skipped)",
        kept, elapsed, kept / max(elapsed, 0.1), skipped,
    )
    if kept == 0:
        raise RuntimeError("No records were tokenized successfully")

    logger.info("Saving %d examples to %s", kept, dataset_path)
    tokenized.save_to_disk(str(dataset_path))

    metadata = {
        "source": train_path,
        "model_name_or_path": config.model_name_or_path,
        "format": config.data.format,
        "max_length": max_length,
        "chat_template_kwargs": chat_template_kwargs,
        "total_records": total_records,
        "tokenized_records": kept,
        "skipped_records": skipped,
        "num_proc": num_proc,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(output_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Done. Set data.tokenized_data_path: %s to train from this dataset.", output_path)
    return metadata


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pre-tokenize JSONL into an Arrow dataset")
    parser.add_argument("--config", required=True, help="Training YAML config")
    parser.add_argument("--num-proc", type=int, default=1, help="Tokenization worker processes")
    parser.add_argument("--output", default=None, help="Override data.tokenized_data_path")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    prepare(args.config, num_proc=args.num_proc, output=args.output)


if __name__ == "__main__":
    main()
