"""Check which tokens receive loss before launching a full run.

Builds the dataset exactly as the trainer would (inline or pre-tokenized),
runs a few samples through SFTTrainer's collator, and prints how many tokens
are masked and the decoded text that is trained on.

Loads the model weights once, because SFTTrainer needs a model. Run it on a
machine that can hold the model in memory.

Usage:
    python -m judge_train.data.verify_labels --config configs/examples/qwen3.5-0.8b.yaml --num-samples 5
"""

from __future__ import annotations

import argparse
import logging
import tempfile

from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer

from judge_train.config import load_config
from judge_train.data.build import build_train_eval_datasets

logger = logging.getLogger(__name__)


def verify(config_path: str, num_samples: int = 3) -> list[dict]:
    config = load_config(config_path)
    tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataset, _ = build_train_eval_datasets(config)

    with tempfile.TemporaryDirectory() as tmp:
        sft_config = SFTConfig(
            output_dir=tmp,
            max_length=config.data.max_length,
            packing=False,
            completion_only_loss=config.training.completion_only_loss,
            max_steps=0,
            report_to="none",
            bf16=False,
        )
        trainer = SFTTrainer(
            model=config.model_name_or_path,
            args=sft_config,
            train_dataset=dataset,
            processing_class=tokenizer,
        )

    num_samples = min(num_samples, len(trainer.train_dataset))
    samples = [trainer.train_dataset[i] for i in range(num_samples)]
    batch = trainer.data_collator(samples)

    print(f"\n{'=' * 60}\nConfig: {config_path}\nFormat: {config.data.format}\nSamples: {num_samples}\n{'=' * 60}\n")
    stats = []
    for i in range(num_samples):
        labels = batch["labels"][i]
        input_ids = batch["input_ids"][i]
        non_pad = int(batch["attention_mask"][i].sum().item()) if "attention_mask" in batch else len(input_ids)
        masked = int((labels == -100).sum().item())
        trained = int((labels != -100).sum().item())
        trained_text = tokenizer.decode(input_ids[labels != -100]) if trained else ""
        stats.append({"non_pad": non_pad, "masked": masked, "trained": trained, "trained_text": trained_text})

        print(f"Sample {i}:")
        print(f"  Tokens: {len(input_ids)}, non-pad: {non_pad}, masked: {masked}, "
              f"trained: {trained} ({trained / max(non_pad, 1) * 100:.1f}%)")
        shown = trained_text[:200] + ("..." if len(trained_text) > 200 else "")
        print(f"  Trained text: {shown or '(none)'}\n")
    return stats


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Inspect loss masking for an SFT config")
    parser.add_argument("--config", required=True, help="Training YAML config")
    parser.add_argument("--num-samples", type=int, default=3, help="Samples to inspect")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    verify(args.config, num_samples=args.num_samples)


if __name__ == "__main__":
    main()
