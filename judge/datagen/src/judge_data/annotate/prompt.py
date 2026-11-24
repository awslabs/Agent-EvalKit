"""Construct judge prompts and assemble training records."""
from __future__ import annotations

import json

from judge_data.annotate.parse import ANNOTATOR_SUFFIX
from judge_data.annotate.render import fill


def judge_prompt(record: dict, evidence: dict[str, str]) -> str:
    """Exactly what a judge receives. Goes into the training record."""
    return fill(record, evidence)


def annotator_prompt(record: dict, evidence: dict[str, str], allow_na: bool = True) -> str:
    """What the teacher sees. The judge prompt plus an N/A instruction."""
    p = fill(record, evidence)
    return p + ANNOTATOR_SUFFIX if allow_na else p


# The keys of a training record's `meta`, in order. `teacher` is the model that judged the pair.
META_KEYS = ("rubric_id", "concept", "level", "n_levels", "output_contract", "agent_id", "verdict",
             "split", "teacher")


def final_meta(meta: dict) -> dict:
    """A record's meta reduced to META_KEYS, for the files training reads."""
    return {k: meta.get(k) for k in META_KEYS}


def sft_record(record: dict, pair: dict, judged: dict, prompt: str) -> dict:
    """Assemble an annotated record for `rubric_trace_match`.

    `meta` holds META_KEYS plus the keys `rubric_trace_match.assemble` and `verify` read: concept_id
    and trace_id (splits and contamination checks), source, is_na, target, thinking_stripped,
    context_layout and reply_quotes_reasoning (slices and invariant checks). `assemble` writes only
    META_KEYS.

    A rubric whose output enum is numeric (the compact layout of a numerical scale) is answered
    with the number, so the target carries a JSON number."""
    out_enum = record.get("output_enum") or record.get("score_enum") or []
    score = judged["score"]
    if out_enum and not isinstance(out_enum[0], str) and not judged.get("na"):
        score = float(score)
    return {
        "id": pair["id"],
        "prompt": [{"role": "user", "content": prompt}],
        "completion": [{"role": "assistant", "content": json.dumps(
            {"reasoning": judged["reasoning"], "score": score}, ensure_ascii=False)}],
        "meta": {
            "rubric_id": record.get("rubric_id"),
            "concept": record.get("concept"),
            "level": record.get("level"),
            "n_levels": record.get("n_levels"),
            "output_contract": "native",
            "agent_id": pair.get("agent_id"),
            "verdict": score,
            "split": record.get("split"),
            "teacher": pair.get("teacher"),
            "concept_id": record.get("concept_id"),
            "trace_id": pair.get("trace_id"),
            "source": pair.get("source"),
            "is_na": judged.get("na", False),
            "target": pair.get("target"),
            "thinking_stripped": pair.get("thinking_stripped", "none"),
            "context_layout": pair.get("context_layout", "turn_labels"),
            "reply_quotes_reasoning": judged.get("reply_quotes_reasoning", False),
        },
    }
