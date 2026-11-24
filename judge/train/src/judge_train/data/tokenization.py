"""Chat-template tokenization that matches TRL SFTTrainer.

These functions replicate what TRL's SFTTrainer does when it tokenizes a
conversational dataset, so a dataset can be tokenized once offline (Stage A)
and then loaded by the trainer without re-tokenization (Stage B).

Output rows carry `input_ids`, plus `completion_mask` for prompt-completion
data. TRL's collator turns `completion_mask == 0` into `labels == -100`, which
gives completion-only loss.
"""

from __future__ import annotations

import logging
from typing import Any

from transformers import PreTrainedTokenizerBase

from judge_train.data.schema import PROMPT_END_ROLES

logger = logging.getLogger(__name__)


def _flatten(ids):
    # apply_chat_template returns a list of lists for some tokenizers.
    if ids and isinstance(ids[0], list):
        return ids[0]
    return ids


def tokenize_messages(
    messages: list[dict[str, Any]],
    tokenizer: PreTrainedTokenizerBase,
    max_length: int | None = None,
    chat_template_kwargs: dict[str, Any] | None = None,
) -> dict[str, list[int]] | None:
    """Tokenize one conversation with the chat template, then truncate.

    Returns {"input_ids": [...]} or None if the chat template fails.
    """
    kwargs = dict(chat_template_kwargs or {})
    try:
        result = tokenizer.apply_chat_template(
            messages, tokenize=True, return_dict=True, **kwargs,
        )
    except Exception as e:
        logger.warning("Skipping record: apply_chat_template failed: %s", e)
        return None

    input_ids = _flatten(result["input_ids"])
    if max_length is not None and len(input_ids) > max_length:
        input_ids = input_ids[:max_length]
    return {"input_ids": input_ids}


def tokenize_prompt_completion(
    prompt: list[dict[str, Any]],
    completion: list[dict[str, Any]],
    tokenizer: PreTrainedTokenizerBase,
    max_length: int | None = None,
    chat_template_kwargs: dict[str, Any] | None = None,
) -> dict[str, list[int]] | None:
    """Tokenize a prompt-completion pair and build its completion mask.

    The prompt is rendered with add_generation_prompt=True and the full
    conversation without it. Tokens past the prompt length are completion
    tokens (mask 1). Everything before is prompt (mask 0).

    Returns {"input_ids", "completion_mask"} or None when the record should be
    skipped:
      - prompt or completion is empty
      - prompt does not end with a user or tool message
      - the chat template fails
      - the rendered prompt is not a token prefix of the full conversation
      - truncation to max_length removes every completion token
    """
    if not prompt or not completion:
        return None

    if prompt[-1]["role"] not in PROMPT_END_ROLES:
        logger.warning(
            "Skipping record: prompt ends with role '%s', expected 'user' or 'tool'.",
            prompt[-1]["role"],
        )
        return None

    kwargs = dict(chat_template_kwargs or {})
    try:
        prompt_ids = tokenizer.apply_chat_template(
            prompt, add_generation_prompt=True, tokenize=True, return_dict=False, **kwargs,
        )
        full_ids = tokenizer.apply_chat_template(
            prompt + completion, add_generation_prompt=False, tokenize=True,
            return_dict=False, **kwargs,
        )
    except Exception as e:
        logger.warning("Skipping record: apply_chat_template failed: %s", e)
        return None

    prompt_ids = list(_flatten(prompt_ids))
    full_ids = list(_flatten(full_ids))
    prompt_len = len(prompt_ids)

    if full_ids[:prompt_len] != prompt_ids:
        logger.warning(
            "Skipping record: prompt tokens are not a prefix of the full conversation. "
            "Check the chat template and chat_template_kwargs."
        )
        return None

    if max_length is not None and len(full_ids) > max_length:
        full_ids = full_ids[:max_length]

    prompt_len = min(prompt_len, len(full_ids))
    completion_len = len(full_ids) - prompt_len
    if completion_len <= 0:
        logger.warning(
            "Skipping record: truncation removed all completion tokens "
            "(prompt_len=%d, max_length=%s).", prompt_len, max_length,
        )
        return None

    return {
        "input_ids": full_ids,
        "completion_mask": [0] * prompt_len + [1] * completion_len,
    }
