"""YAML config -> dataclasses.

A config file has four top-level sections plus a few scalars:

    model_name_or_path: ./models/Qwen3.5-4B
    attn_implementation: flash_attention_2
    data: {...}       # DataConfig
    training: {...}   # TrainingConfig
    lora: {...}       # LoraConfig (optional)
    seed: 42

Unknown keys raise ValueError so typos fail fast. Defaults match the recipe
used for the released judge checkpoints, so a minimal config only needs the
model and data paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

DATA_FORMATS = ("messages", "prompt_completion")


@dataclass
class DataConfig:
    train_path: str = ""  # JSONL file or glob
    val_path: str | None = None
    max_length: int = 8192
    packing: bool = False
    chat_template_kwargs: dict | None = None  # e.g. {enable_thinking: false} for Qwen3.5
    max_train_samples: int | None = None
    max_eval_samples: int | None = None
    tokenized_data_path: str | None = None  # Stage A output dir. If set, training reads Arrow from here.
    format: str = "prompt_completion"  # "prompt_completion" | "messages"


@dataclass
class LoraConfig:
    enabled: bool = False
    r: int = 16
    alpha: int = 32
    dropout: float = 0.05
    target_modules: list[str] = field(
        default_factory=lambda: [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ]
    )


@dataclass
class TrainingConfig:
    exp_name: str = "default"
    output_dir: str = "outputs/"  # checkpoints go to {output_dir}/{exp_name}/checkpoint-{step}
    run_name: str | None = None  # name shown in the tracker. Defaults to exp_name.
    num_train_epochs: float = 1
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 5.0e-6
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    bf16: bool = True
    # Must stay false under FSDP. Activation checkpointing is set in the accelerate config instead.
    gradient_checkpointing: bool = False
    deepspeed: str | None = None
    save_strategy: str = "steps"
    save_steps: int = 1000
    save_total_limit: int | None = 2  # keep only the N most recent checkpoints
    save_only_model: bool = True  # weights only, no optimizer state. Smaller, but cannot resume.
    logging_steps: int = 10
    eval_strategy: str = "no"
    eval_steps: int | None = None
    eval_on_start: bool = False
    max_steps: int = -1
    report_to: str | list[str] = "none"  # any HF integration, e.g. "mlflow", "wandb", "tensorboard"
    dataloader_num_workers: int = 4
    dataset_num_proc: int | None = None
    fsdp: str | None = None  # "full_shard" for multi-GPU runs launched with accelerate
    fsdp_config: dict | None = None
    ddp_find_unused_parameters: bool | None = None
    ddp_timeout: int = 7200
    resume: str | None = None  # None (fresh) | "auto" (latest checkpoint in output dir) | explicit path
    completion_only_loss: bool = True  # loss on completion tokens only (prompt_completion format)
    use_cpu: bool = False  # force CPU, for debugging on a machine without CUDA


@dataclass
class Config:
    model_name_or_path: str = "Qwen/Qwen3.5-4B"
    attn_implementation: str | None = None  # e.g. "flash_attention_2". None lets transformers pick.
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    lora: LoraConfig = field(default_factory=LoraConfig)
    seed: int = 42


def _merge_into_dataclass(dc, overrides: dict, prefix: str = "") -> None:
    """Recursively merge a dict into a dataclass instance."""
    for k, v in overrides.items():
        if not hasattr(dc, k):
            raise ValueError(f"Unknown config key: {prefix}{k}")
        current = getattr(dc, k)
        if hasattr(current, "__dataclass_fields__"):
            if not isinstance(v, dict):
                raise ValueError(f"Config section '{prefix}{k}' must be a mapping")
            _merge_into_dataclass(current, v, prefix=f"{prefix}{k}.")
        else:
            setattr(dc, k, v)


def validate_config(config: Config) -> None:
    """Static checks that do not need the model or the data."""
    if config.data.format not in DATA_FORMATS:
        raise ValueError(
            f"Unknown data.format: '{config.data.format}'. Must be one of {DATA_FORMATS}."
        )
    if config.training.fsdp and config.training.gradient_checkpointing:
        raise ValueError(
            "training.gradient_checkpointing must be false when using FSDP. "
            "Activation checkpointing is set by fsdp_activation_checkpointing in the "
            "accelerate config instead. Setting both can hang NCCL."
        )


def load_config(path: str) -> Config:
    """Load a YAML config file into a validated Config."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    config = Config()
    if raw:
        if not isinstance(raw, dict):
            raise ValueError(f"Config file {path} must contain a mapping at the top level")
        _merge_into_dataclass(config, raw)
    validate_config(config)
    return config


def global_batch_size(config: Config, num_processes: int) -> int:
    """Sequences per optimizer step: processes x per-device batch x grad accumulation."""
    tc = config.training
    return num_processes * tc.per_device_train_batch_size * tc.gradient_accumulation_steps
