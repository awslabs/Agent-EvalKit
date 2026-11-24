"""Chat-template tokenization and completion masks, using the local tiny tokenizer."""

from __future__ import annotations

import pytest

from conftest import EMPTY_THINK
from judge_train.data.tokenization import tokenize_messages, tokenize_prompt_completion

NO_THINK = {"enable_thinking": False}
PROMPT = [{"role": "user", "content": "Rate this."}]
COMPLETION = [{"role": "assistant", "content": '{"score": 4}'}]


def _split(tok, out):
    boundary = out["completion_mask"].index(1)
    return tok.decode(out["input_ids"][:boundary]), tok.decode(out["input_ids"][boundary:])


# -- messages ------------------------------------------------------------------

def test_messages_round_trip(tiny_tokenizer):
    out = tokenize_messages(PROMPT + COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    assert set(out) == {"input_ids"}
    assert all(isinstance(t, int) for t in out["input_ids"])
    assert tiny_tokenizer.decode(out["input_ids"]) == (
        "<|im_start|>user\nRate this.<|im_end|>\n"
        f"<|im_start|>assistant\n{EMPTY_THINK}" '{"score": 4}<|im_end|>\n'
    )


def test_messages_truncation(tiny_tokenizer):
    msgs = [{"role": "user", "content": "word " * 200}, {"role": "assistant", "content": "ok"}]
    out = tokenize_messages(msgs, tiny_tokenizer, max_length=32)
    assert len(out["input_ids"]) == 32


def test_messages_template_failure_returns_none(tiny_tokenizer):
    tok = tiny_tokenizer.__class__.from_pretrained(tiny_tokenizer.name_or_path)
    tok.chat_template = "{{ raise_exception('boom') }}"
    assert tokenize_messages(PROMPT + COMPLETION, tok) is None


# -- prompt-completion ---------------------------------------------------------

def test_prompt_completion_mask_boundary(tiny_tokenizer):
    out = tokenize_prompt_completion(PROMPT, COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    ids, mask = out["input_ids"], out["completion_mask"]
    assert len(ids) == len(mask)
    assert set(mask) == {0, 1}
    # All prompt tokens first, then all completion tokens. No interleaving.
    boundary = mask.index(1)
    assert mask == [0] * boundary + [1] * (len(mask) - boundary)

    prompt_text, completion_text = _split(tiny_tokenizer, out)
    assert prompt_text == f"<|im_start|>user\nRate this.<|im_end|>\n<|im_start|>assistant\n{EMPTY_THINK}"
    assert completion_text == '{"score": 4}<|im_end|>\n'


def test_prompt_completion_matches_messages_tokens(tiny_tokenizer):
    pc = tokenize_prompt_completion(PROMPT, COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    msgs = tokenize_messages(PROMPT + COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    assert pc["input_ids"] == msgs["input_ids"]


def test_fixture_records_all_tokenize(tiny_tokenizer, pc_rows):
    for row in pc_rows:
        out = tokenize_prompt_completion(
            row["prompt"], row["completion"], tiny_tokenizer, chat_template_kwargs=NO_THINK,
        )
        assert out is not None, row["id"]
        _, completion_text = _split(tiny_tokenizer, out)
        assert completion_text == row["completion"][0]["content"] + "<|im_end|>\n", row["id"]


def test_missing_enable_thinking_false_is_skipped(tiny_tokenizer):
    """Without enable_thinking=false the prompt is not a prefix of the full conversation."""
    assert tokenize_prompt_completion(PROMPT, COMPLETION, tiny_tokenizer) is None


@pytest.mark.parametrize("prompt, completion", [
    ([], COMPLETION),
    (PROMPT, []),
    (PROMPT + COMPLETION, COMPLETION),  # prompt ends with assistant
])
def test_invalid_records_are_skipped(tiny_tokenizer, prompt, completion):
    assert tokenize_prompt_completion(prompt, completion, tiny_tokenizer, chat_template_kwargs=NO_THINK) is None


def test_prompt_may_end_with_tool(tiny_tokenizer):
    prompt = [
        {"role": "user", "content": "Cancel order 1."},
        {"role": "assistant", "content": "<tool_call>lookup</tool_call>"},
        {"role": "tool", "content": "shipped"},
    ]
    out = tokenize_prompt_completion(prompt, COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    assert out is not None


def test_truncation_keeps_mask_aligned(tiny_tokenizer):
    long_completion = [{"role": "assistant", "content": "reason " * 100}]
    full = tokenize_prompt_completion(PROMPT, long_completion, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    prompt_len = full["completion_mask"].index(1)

    max_length = prompt_len + 5
    out = tokenize_prompt_completion(
        PROMPT, long_completion, tiny_tokenizer, max_length=max_length, chat_template_kwargs=NO_THINK,
    )
    assert len(out["input_ids"]) == len(out["completion_mask"]) == max_length
    assert out["input_ids"] == full["input_ids"][:max_length]
    assert sum(out["completion_mask"]) == 5


def test_truncation_that_drops_completion_is_skipped(tiny_tokenizer):
    full = tokenize_prompt_completion(PROMPT, COMPLETION, tiny_tokenizer, chat_template_kwargs=NO_THINK)
    prompt_len = full["completion_mask"].index(1)
    assert tokenize_prompt_completion(
        PROMPT, COMPLETION, tiny_tokenizer, max_length=prompt_len, chat_template_kwargs=NO_THINK,
    ) is None
