"""Rubric validation: schema and placeholder checks, the clean room check, functional testing,
and relabelling.

Schema, placeholder and clean room checks are pure logic. Functional testing and relabelling use a
ModelClient.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from judge_data.utils.jsonx import extract_json

if TYPE_CHECKING:
    from judge_data.clients import ModelClient


# ── Schema validation (pure logic) ──────────────────────────────────────────

REQUIRED_FIELDS = ["rubric_id", "concept", "level", "score_enum", "rendered_prompt"]
VALID_LEVELS = {"SESSION", "TRACE", "TOOL_CALL"}


def check_schema(rubric: dict) -> list[str]:
    """Validate a single rubric's schema. Returns list of errors (empty = valid)."""
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in rubric:
            errors.append(f"missing field: {f}")
    if rubric.get("level") not in VALID_LEVELS:
        errors.append(f"invalid level: {rubric.get('level')}")
    enum = rubric.get("score_enum", [])
    if not isinstance(enum, list) or len(enum) < 2:
        errors.append(f"score_enum must be a list of 2+ labels, got {len(enum) if isinstance(enum, list) else type(enum)}")
    if len(set(enum)) != len(enum):
        errors.append("duplicate labels in score_enum")
    # A rubric is a template: it must carry exactly the evidence slots it declares in
    # `placeholders` (by default the slots of its level), in one spelling, and nothing a filler
    # cannot fill. The spelling is read from the prompt itself, as `annotate.render.fill` does.
    from judge_data.annotate.render import MARKERS
    from judge_data.rubric_build.render import EVIDENCE
    prompt = rubric.get("rendered_prompt", "")
    level = rubric.get("level")
    if level in EVIDENCE:
        markers = set(re.findall(r"<<([A-Z_]+)>>", prompt))
        slots = set(re.findall(r"\{(context|assistant_turn|available_tools|tool_turn)\}", prompt))
        if markers and slots:
            errors.append("mixes <<MARKER>> and {slot} placeholders")
        slot_of = {m.strip("<>"): n for n, m in MARKERS.items()}
        unknown = {f"<<{m}>>" for m in markers if m not in slot_of}
        if unknown:
            errors.append(f"unexpected placeholders: {sorted(unknown)}")
        found = {slot_of[m] for m in markers if m in slot_of} | slots
        want = set(rubric.get("placeholders") or [n for _h, n, *_ in EVIDENCE[level]])
        judged = {"TRACE": "assistant_turn", "TOOL_CALL": "tool_turn"}.get(level)
        need = want | {"context"} | ({judged} if judged else set())
        if need - found:
            errors.append(f"missing evidence slots for {level}: {sorted(need - found)}")
        if found - want:
            errors.append(f"unexpected placeholders: {sorted(found - want)}")
    return errors


def check_corpus(rubrics: list[dict]) -> dict:
    """Validate a whole corpus. Returns a summary dict."""
    errors_by_id = {}
    for r in rubrics:
        errs = check_schema(r)
        if errs:
            errors_by_id[r.get("rubric_id", "?")] = errs

    ids = [r.get("rubric_id", "") for r in rubrics]
    dup_ids = [rid for rid, count in Counter(ids).items() if count > 1]
    concepts = [r.get("concept_id", r.get("concept", "")) for r in rubrics]

    return {
        "total": len(rubrics),
        "schema_errors": len(errors_by_id),
        "duplicate_ids": dup_ids,
        "unique_concepts": len(set(concepts)),
        "by_level": dict(Counter(r.get("level", "?") for r in rubrics)),
        "errors": errors_by_id,
    }


# ── Clean room check (pure logic) ───────────────────────────────────────────

_WORD = re.compile(r"[a-z0-9]+")


def _words(s: str) -> list[str]:
    return _WORD.findall(s.lower())


def seed_text(seed: dict) -> str:
    """The prose of one seed rubric that generated text must not reproduce."""
    parts = [str(seed.get("metric_name", "")), str(seed.get("definition", "")),
             str(seed.get("grading_instructions", "") or "")]
    parts += [str(v) for v in (seed.get("score_levels") or {}).values()]
    return " ".join(parts)


def generated_text(rubric: dict) -> str:
    """The generated prose of a library rubric: task and scale definitions."""
    return " ".join([str(rubric.get("task") or "")]
                    + [str(s.get("definition", "")) for s in rubric.get("scale") or []])


def cleanroom_check(rubrics: list[dict], seed_texts: list[str], n: int = 8,
                    min_run: int = 5, max_run: int = 25) -> dict:
    """Measure how much generated prose reproduces seed wording.

    A record fails when it shares any word `n`-gram with the seed corpus. The longest common run
    of words is reported as a histogram. Pass only generated rubrics.

    Returns {"checked", "failed_ids", "longest_run_histogram", "worst"}.
    """
    grams: set[tuple] = set()
    phrases: set[str] = set()
    for t in seed_texts:
        toks = _words(t)
        grams |= {tuple(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))}
        for k in range(min_run, max_run + 1):
            for i in range(max(0, len(toks) - k + 1)):
                phrases.add(" ".join(toks[i:i + k]))

    failed, worst, runs, checked = [], [], Counter(), 0
    for r in rubrics:
        checked += 1
        toks = _words(generated_text(r))
        shared = {tuple(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))} & grams
        best = 0
        for i in range(len(toks) - min_run + 1):
            if " ".join(toks[i:i + min_run]) not in phrases:
                continue
            k = min_run
            while i + k < len(toks) and k < max_run and " ".join(toks[i:i + k + 1]) in phrases:
                k += 1
            best = max(best, k)
        runs[best] += 1
        if shared:
            failed.append(r.get("rubric_id"))
            worst.append({"rubric_id": r.get("rubric_id"), "shared_ngrams": len(shared),
                          "longest_run": best, "example": " ".join(next(iter(shared)))})
    worst.sort(key=lambda x: -x["shared_ngrams"])
    return {"checked": checked, "failed_ids": failed,
            "longest_run_histogram": dict(sorted(runs.items())), "worst": worst[:15]}


# ── Functional testing (uses ModelClient) ───────────────────────────────────

SAMPLE_EVIDENCE = {
    "context": ("Turn 1:\n  User: Can you check whether order 4471 has shipped?\n"
                "  Tool call: get_order({\"order_id\": \"4471\"})\n"
                "  Tool result: {\"status\": \"shipped\", \"carrier\": \"UPS\"}\n"
                "  Agent: Order 4471 shipped with UPS."),
    "assistant_turn": "Order 4471 shipped with UPS. You should receive it within three days.",
    "available_tools": "- get_order\n- cancel_order",
    "tool_turn": 'get_order({"order_id": "4471"})\nTool result: {"status": "shipped"}',
}


def functional_test(
    rubric: dict,
    client: "ModelClient",
    evidence: dict[str, str] | None = None,
) -> dict:
    """Fill every evidence slot of a rubric, run it, and check the verdict parses into its scale.

    Args:
        rubric: a library record (rendered_prompt, level, output_enum or score_enum)
        evidence: slot name -> text (context, assistant_turn, available_tools, tool_turn).
            Defaults to a short canned tool using conversation.

    Returns:
        dict with 'parsed' (bool), 'score' (str or None), 'in_enum' (bool),
        'reasoning_words' (int), 'raw' (str).
    """
    from judge_data.annotate.parse import _in_enum
    from judge_data.annotate.render import fill

    prompt = fill(rubric, evidence or SAMPLE_EVIDENCE)
    result = client.invoke(prompt, max_tokens=1024, temperature=0.0)
    raw = result.text or ""

    parsed_json = extract_json(raw)
    score = None
    reasoning = ""
    parsed = False
    if isinstance(parsed_json, dict):
        score = str(parsed_json.get("score", ""))
        reasoning = str(parsed_json.get("reasoning", ""))
        parsed = True

    enum = rubric.get("output_enum") or rubric.get("score_enum", [])
    return {
        "parsed": parsed,
        "score": score,
        "in_enum": _in_enum(score, enum) if score else False,
        "reasoning_words": len(reasoning.split()),
        "raw": raw[:500],
    }


# ── Relabelling (uses ModelClient) ──────────────────────────────────────────

RELABEL_PROMPT = """Restate each measured property below in different words.

Rules:
- Keep the meaning exactly. It must describe the same observable property.
- Use different wording. No run of four or more consecutive words may be shared with the input.
- At most 20 words, lowercase, no trailing period.
- Stay a statement of the property, not an instruction to a judge.

Properties:
{items}

Output a JSON array of objects {{"i": <index>, "restated": "..."}} and nothing else."""


def relabel_if_copied(
    concept: str,
    source_text: str,
    client: "ModelClient",
    threshold: int = 8,
) -> str:
    """Restate a concept label if it shares a long phrase with its source rubric.

    Returns the original concept if no overlap detected, or the restated version.
    """
    word_re = re.compile(r"[a-z0-9]+")
    cw = word_re.findall(concept.lower())
    sw = word_re.findall(source_text.lower())
    source_phrases = set()
    for n in range(4, 26):
        for j in range(max(0, len(sw) - n + 1)):
            source_phrases.add(" ".join(sw[j:j + n]))

    overlap = 0
    for n in range(threshold, len(cw) + 1):
        for j in range(max(0, len(cw) - n + 1)):
            if " ".join(cw[j:j + n]) in source_phrases:
                overlap = max(overlap, n)

    if overlap < threshold:
        return concept

    prompt = RELABEL_PROMPT.format(items=f"0. {concept}")
    result = client.invoke(prompt, max_tokens=500, temperature=0.0)
    parsed = extract_json(result.text)
    if isinstance(parsed, list) and parsed:
        obj = parsed[0]
        if isinstance(obj, dict) and obj.get("restated"):
            return str(obj["restated"]).strip().rstrip(".").lower()
    return concept
