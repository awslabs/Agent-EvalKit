"""Shared fixtures. Everything is built locally, so tests need no network and no GPU.

`tiny_model_dir` holds a byte-level BPE tokenizer trained on the fixtures plus
a randomly initialized 2-layer Llama model. The chat template imitates the
Qwen3.5 behaviour that matters for masking: with enable_thinking=false the
generation prompt and the final assistant turn both carry an empty think block.
Without it the generation prompt opens a think block that the full
conversation does not have, so the prompt is not a token prefix of it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# Keep everything offline and on CPU.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PC_FIXTURE = FIXTURES_DIR / "sample_prompt_completion.jsonl"
MESSAGES_FIXTURE = FIXTURES_DIR / "sample_messages.jsonl"
REPO_ROOT = Path(__file__).resolve().parents[1]

SPECIAL_TOKENS = ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<think>", "</think>"]
EMPTY_THINK = "<think>\n\n</think>\n\n"

CHAT_TEMPLATE = (
    "{%- set no_think = enable_thinking is defined and enable_thinking is false -%}"
    "{%- for message in messages -%}"
    "{{ '<|im_start|>' + message['role'] + '\n' }}"
    "{%- if message['role'] == 'assistant' and loop.last and no_think -%}{{ '<think>\n\n</think>\n\n' }}{%- endif -%}"
    "{{ message['content'] + '<|im_end|>\n' }}"
    "{%- endfor -%}"
    "{%- if add_generation_prompt -%}"
    "{{ '<|im_start|>assistant\n' }}"
    "{%- if no_think -%}{{ '<think>\n\n</think>\n\n' }}{%- else -%}{{ '<think>\n' }}{%- endif -%}"
    "{%- endif -%}"
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _fixture_texts() -> list[str]:
    texts = []
    for row in read_jsonl(PC_FIXTURE):
        texts += [m["content"] for m in row["prompt"] + row["completion"]]
    for row in read_jsonl(MESSAGES_FIXTURE):
        texts += [m["content"] for m in row["messages"]]
    return texts + ["user assistant system tool"]


def build_tiny_tokenizer():
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast

    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=512,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=False,
    )
    tok.train_from_iterator(_fixture_texts(), trainer=trainer)

    hf_tok = PreTrainedTokenizerFast(
        tokenizer_object=tok,
        eos_token="<|im_end|>",
        pad_token="<|endoftext|>",
        additional_special_tokens=["<|im_start|>", "<think>", "</think>"],
        clean_up_tokenization_spaces=False,
    )
    hf_tok.chat_template = CHAT_TEMPLATE
    return hf_tok


@pytest.fixture(scope="session")
def tiny_model_dir(tmp_path_factory) -> Path:
    """Directory with a tiny tokenizer and model, usable as model_name_or_path."""
    import torch
    from transformers import LlamaConfig, LlamaForCausalLM

    out = tmp_path_factory.mktemp("tiny-model")
    tok = build_tiny_tokenizer()
    tok.save_pretrained(out)

    torch.manual_seed(0)
    cfg = LlamaConfig(
        vocab_size=len(tok),
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=1024,
        pad_token_id=tok.pad_token_id,
        eos_token_id=tok.eos_token_id,
        bos_token_id=None,
        tie_word_embeddings=True,
    )
    LlamaForCausalLM(cfg).save_pretrained(out)
    return out


@pytest.fixture(scope="session")
def tiny_tokenizer(tiny_model_dir):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(tiny_model_dir))
    assert tok.chat_template, "chat template did not round-trip through save_pretrained"
    return tok


@pytest.fixture
def pc_rows() -> list[dict]:
    return read_jsonl(PC_FIXTURE)


@pytest.fixture
def write_config(tmp_path):
    """Write a YAML config from a dict and return its path."""
    import yaml

    def _write(cfg: dict, name: str = "config.yaml") -> str:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        return str(path)

    return _write
