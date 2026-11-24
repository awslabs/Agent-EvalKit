"""Trainer callbacks."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from transformers import TrainerCallback

logger = logging.getLogger(__name__)


class CopyProcessorConfigsCallback(TrainerCallback):
    """Copy processor and base model configs into every saved checkpoint.

    vLLM loads Qwen3.5 checkpoints through the multimodal architecture and
    needs preprocessor_config.json and video_preprocessor_config.json. The
    trainer does not save them, so they are copied from the base model.

    config.json and generation_config.json are copied only if missing. Full
    fine-tuning already writes them, so this is a no-op there. A LoRA
    checkpoint only has adapter_config.json, so the copy makes it describe
    its base model.

    The base model can be a local directory or a Hub ID. For a Hub ID each
    file is fetched through the Hugging Face cache. Missing files are skipped.
    """

    FILES = (
        "preprocessor_config.json",
        "video_preprocessor_config.json",
        "config.json",
        "generation_config.json",
    )

    def __init__(self, base_model_path: str):
        self.base_model_path = base_model_path

    def on_save(self, args, state, control, **kwargs):
        # Only rank 0 writes the checkpoint dir. On other ranks it may not exist yet.
        if not state.is_world_process_zero:
            return
        self.copy_to(Path(args.output_dir) / f"checkpoint-{state.global_step}")

    def _resolve(self, fname: str) -> Path | None:
        local = Path(self.base_model_path)
        if local.is_dir():
            src = local / fname
            return src if src.exists() else None
        try:
            from huggingface_hub import hf_hub_download

            return Path(hf_hub_download(self.base_model_path, fname))
        except Exception:
            return None

    def copy_to(self, dest: Path) -> list[str]:
        """Copy the config files into dest. Returns the names that were copied."""
        dest = Path(dest)
        copied = []
        for fname in self.FILES:
            if (dest / fname).exists():
                continue
            src = self._resolve(fname)
            if src is not None:
                shutil.copy2(src, dest / fname)
                copied.append(fname)
        if copied:
            logger.info("Copied %s into %s", ", ".join(copied), dest)
        return copied
