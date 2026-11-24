"""JSONL loading and record schemas."""

from __future__ import annotations

import pytest

from conftest import MESSAGES_FIXTURE, PC_FIXTURE
from judge_train.data.loader import build_stream, iter_examples, load_examples, resolve_paths
from judge_train.data.schema import (
    MessagesExample,
    PromptCompletionExample,
    parse_example,
)


def test_iter_examples_skips_blank_lines():
    rows = list(iter_examples(str(MESSAGES_FIXTURE)))
    assert len(rows) == 4
    assert all("messages" in r for r in rows)


def test_glob_reads_all_files_sorted(tmp_path):
    (tmp_path / "b.jsonl").write_text('{"id": "b"}\n')
    (tmp_path / "a.jsonl").write_text('{"id": "a1"}\n{"id": "a2"}\n')
    assert resolve_paths(str(tmp_path / "*.jsonl")) == [
        str(tmp_path / "a.jsonl"), str(tmp_path / "b.jsonl"),
    ]
    assert [r["id"] for r in iter_examples(str(tmp_path / "*.jsonl"))] == ["a1", "a2", "b"]


def test_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        list(iter_examples("/nonexistent/dir/*.jsonl"))


def test_build_stream_max_samples():
    assert len(list(build_stream(str(PC_FIXTURE)))) == 6
    assert len(list(build_stream(str(PC_FIXTURE), max_samples=2))) == 2


def test_load_examples_prompt_completion():
    records = load_examples(str(PC_FIXTURE))
    assert len(records) == 6
    assert all(isinstance(r, PromptCompletionExample) for r in records)
    assert records[0].id == "pc_001"
    assert records[3].prompt[-1].role == "tool"
    assert [m.role for m in records[1].prompt] == ["system", "user", "assistant", "user"]


def test_load_examples_messages():
    records = load_examples(str(MESSAGES_FIXTURE))
    assert all(isinstance(r, MessagesExample) for r in records)
    assert records[3].model_extra["meta"] == {"source": "synthetic"}


def test_load_examples_reports_bad_record(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text(
        '{"prompt": [{"role": "user", "content": "q"}], "completion": [{"role": "assistant", "content": "a"}]}\n'
        '{"prompt": [{"role": "user", "content": "q"}], "completion": []}\n'
    )
    with pytest.raises(ValueError, match="#1"):
        load_examples(str(p))


@pytest.mark.parametrize("record, match", [
    ({"prompt": [{"role": "assistant", "content": "x"}],
      "completion": [{"role": "assistant", "content": "y"}]}, "must end with"),
    ({"prompt": [{"role": "user", "content": "x"}],
      "completion": [{"role": "user", "content": "y"}]}, "only assistant"),
    ({"prompt": [], "completion": [{"role": "assistant", "content": "y"}]}, "at least 1"),
    ({"text": "plain"}, "neither"),
])
def test_schema_rejects(record, match):
    with pytest.raises(ValueError, match=match):
        parse_example(record)


def test_message_extra_fields_are_kept():
    ex = parse_example({
        "prompt": [{"role": "user", "content": "q"}],
        "completion": [{"role": "assistant", "content": "", "tool_calls": [{"name": "f"}]}],
    })
    assert ex.completion[0].model_extra["tool_calls"] == [{"name": "f"}]
