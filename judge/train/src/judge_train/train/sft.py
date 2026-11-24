"""Full fine-tuning with TRL SFTTrainer.

Single process:
    python -m judge_train.train --config configs/examples/qwen3.5-0.8b.yaml

Multi-GPU with FSDP:
    accelerate launch --config_file configs/accelerate/fsdp.yaml \\
        -m judge_train.train --config configs/examples/qwen3.5-4b.yaml
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from transformers import AutoConfig, AutoTokenizer
from trl import SFTConfig, SFTTrainer

from judge_train.config import Config, load_config
from judge_train.data.build import build_train_eval_datasets
from judge_train.train.callbacks import CopyProcessorConfigsCallback
from judge_train.utils.logging_utils import setup_logging

logger = setup_logging()

# Model types with GatedDeltaNet linear attention (Qwen3.5 family).
QWEN35_MODEL_TYPES = {"qwen3_5", "qwen3_5_moe"}


def is_qwen35(model_name_or_path: str) -> bool:
    hf_config = AutoConfig.from_pretrained(model_name_or_path, trust_remote_code=True)
    return getattr(hf_config, "model_type", "") in QWEN35_MODEL_TYPES


def _warn_hub_id_multinode(config: Config) -> None:
    model_path = config.model_name_or_path
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    if world_size > 1 and "/" in model_path and not Path(model_path).exists():
        logger.warning(
            "Model path '%s' looks like a Hub ID in a multi-process job (WORLD_SIZE=%d). "
            "Download it to a local directory first to avoid cache races on shared filesystems.",
            model_path, world_size,
        )


def validate_qwen35(config: Config) -> None:
    """Reject settings known to break Qwen3.5 training."""
    if config.data.packing:
        raise ValueError(
            "Qwen3.5 does not support packing (GatedDeltaNet limitation). Set data.packing: false."
        )
    if config.training.deepspeed:
        raise ValueError(
            "Qwen3.5 with DeepSpeed ZeRO gives loss=0 or NaN (GatedDeltaNet kernels under "
            "parameter partitioning). Use FSDP (training.fsdp: full_shard) or plain DDP."
        )
    if not config.training.bf16:
        logger.warning("Qwen3.5 RMSNorm overflows in float16. bf16 is strongly recommended.")
    # GatedDeltaNet has parameters that are not used in every forward pass, which breaks
    # DDP gradient reduction. FSDP does not need this.
    if not config.training.fsdp and config.training.ddp_find_unused_parameters is None:
        config.training.ddp_find_unused_parameters = True
        logger.info("Qwen3.5: enabled ddp_find_unused_parameters=True")


def resolve_resume_checkpoint(config: Config) -> str | None:
    """None starts fresh, "auto" picks the latest checkpoint-*, anything else is a path."""
    resume = config.training.resume
    if resume != "auto":
        return resume
    run_dir = Path(config.training.output_dir) / config.training.exp_name

    def step(p: Path) -> int:
        tail = p.name.split("-")[-1]
        return int(tail) if tail.isdigit() else -1

    ckpts = sorted((p for p in run_dir.glob("checkpoint-*") if p.is_dir() and step(p) >= 0), key=step)
    if ckpts:
        logger.info("Auto-resume from %s", ckpts[-1])
        return str(ckpts[-1])
    logger.info("Auto-resume: no checkpoints in %s, starting fresh", run_dir)
    return None


def build_peft_config(config: Config):
    """peft.LoraConfig when lora.enabled, else None.

    SFTTrainer wraps the model with get_peft_model() before FSDP sharding.
    Checkpoints then hold only the adapter. Merge with judge_train.utils.merge_lora.
    """
    if not config.lora.enabled:
        return None
    from peft import LoraConfig as PeftLoraConfig

    return PeftLoraConfig(
        r=config.lora.r,
        lora_alpha=config.lora.alpha,
        lora_dropout=config.lora.dropout,
        target_modules=list(config.lora.target_modules),
        bias="none",
        task_type="CAUSAL_LM",
    )


def build_model_init_kwargs(config: Config) -> dict:
    """Kwargs for from_pretrained, passed to SFTTrainer through SFTConfig.model_init_kwargs."""
    kwargs = {
        "dtype": torch.bfloat16 if config.training.bf16 else torch.float32,
        "trust_remote_code": True,
    }
    if config.attn_implementation:
        kwargs["attn_implementation"] = config.attn_implementation
    if config.training.use_cpu:
        kwargs["device_map"] = "cpu"
    elif config.training.fsdp:
        # Load on CPU so FSDP can shard. TRL defaults to device_map="auto" and only
        # overrides it for DDP and DeepSpeed, so without this the full model lands on
        # one GPU before sharding and runs out of memory.
        kwargs["device_map"] = None
        kwargs["low_cpu_mem_usage"] = True
    return kwargs


def build_sft_config(config: Config) -> SFTConfig:
    tc = config.training
    return SFTConfig(
        model_init_kwargs=build_model_init_kwargs(config),
        output_dir=str(Path(tc.output_dir) / tc.exp_name),
        max_length=config.data.max_length,
        packing=config.data.packing,
        completion_only_loss=tc.completion_only_loss,
        num_train_epochs=tc.num_train_epochs,
        per_device_train_batch_size=tc.per_device_train_batch_size,
        per_device_eval_batch_size=tc.per_device_eval_batch_size,
        gradient_accumulation_steps=tc.gradient_accumulation_steps,
        learning_rate=tc.learning_rate,
        lr_scheduler_type=tc.lr_scheduler_type,
        # transformers 5 deprecates warmup_ratio. A float below 1 in warmup_steps is the same ratio.
        warmup_steps=tc.warmup_ratio,
        weight_decay=tc.weight_decay,
        max_grad_norm=tc.max_grad_norm,
        bf16=tc.bf16,
        gradient_checkpointing=tc.gradient_checkpointing,
        deepspeed=tc.deepspeed,
        save_strategy=tc.save_strategy,
        save_steps=tc.save_steps,
        save_total_limit=tc.save_total_limit,
        save_only_model=tc.save_only_model,
        logging_steps=tc.logging_steps,
        eval_strategy=tc.eval_strategy,
        eval_steps=tc.eval_steps,
        eval_on_start=tc.eval_on_start,
        max_steps=tc.max_steps,
        report_to=tc.report_to,
        run_name=tc.run_name or tc.exp_name,
        dataloader_num_workers=tc.dataloader_num_workers,
        dataset_num_proc=tc.dataset_num_proc,
        fsdp=tc.fsdp,
        fsdp_config=tc.fsdp_config,
        ddp_find_unused_parameters=tc.ddp_find_unused_parameters,
        ddp_timeout=tc.ddp_timeout,
        use_cpu=tc.use_cpu,
        seed=config.seed,
    )


def main(config_path: str):
    config = load_config(config_path)
    _warn_hub_id_multinode(config)
    qwen35 = is_qwen35(config.model_name_or_path)
    if qwen35:
        validate_qwen35(config)
    if config.data.format == "messages" and config.training.completion_only_loss:
        logger.info("data.format is 'messages', so completion_only_loss has no effect")
        config.training.completion_only_loss = False

    tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_dataset, eval_dataset = build_train_eval_datasets(config)
    sft_config = build_sft_config(config)

    callbacks = []
    if qwen35:
        callbacks.append(CopyProcessorConfigsCallback(config.model_name_or_path))

    peft_config = build_peft_config(config)
    if peft_config is not None:
        logger.info(
            "LoRA enabled: r=%d alpha=%d dropout=%s targets=%s",
            config.lora.r, config.lora.alpha, config.lora.dropout, config.lora.target_modules,
        )

    # The model is passed as a path so that, under FSDP, Accelerate can use
    # cpu_ram_efficient_loading (rank 0 loads weights, other ranks receive them).
    trainer = SFTTrainer(
        model=config.model_name_or_path,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        callbacks=callbacks or None,
        peft_config=peft_config,
    )

    logger.info("Starting training: %s", config.training.exp_name)
    trainer.train(resume_from_checkpoint=resolve_resume_checkpoint(config))
    # There is no final save_model(). Under multi-node FSDP one large consolidated
    # save at the end can stall long enough to trip the NCCL watchdog. Checkpoints
    # come from save_strategy. For bf16 vLLM-ready copies run afterwards:
    #     python -m judge_train.utils.bf16_save {output_dir}/{exp_name}
    logger.info("Training complete. Output dir: %s", sft_config.output_dir)
    return trainer


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="SFT training for the judge model")
    parser.add_argument("--config", required=True, help="Training YAML config")
    args = parser.parse_args(argv)
    main(args.config)


if __name__ == "__main__":
    cli()
