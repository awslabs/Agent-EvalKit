"""Parse judge responses into structured annotation results."""
from __future__ import annotations


def parse(text: str, score_enum: list[str], extract_json) -> dict:
    """Parse a judgement. Returns a dict with ``ok`` plus fields or a reason."""
    obj = extract_json(text)
    if not isinstance(obj, dict):
        return {"ok": False, "why": "reply did not parse as a JSON object"}
    if "score" not in obj or "reasoning" not in obj:
        return {"ok": False, "why": f"missing reasoning or score, got keys {sorted(obj)[:6]}"}
    score = str(obj["score"]).strip()
    reasoning = str(obj["reasoning"]).strip()
    # A reply that mentions a reasoning tag is quoting the agent, not wrapping its own answer, so it
    # is kept as is; the flag makes the one incoherent combination (stripped prompt, judgement still
    # citing reasoning) findable later.
    from judge_data.annotate import scrub
    tags = scrub.has_tag(reasoning)
    if score.upper() in ("N/A", "NA", "NOT APPLICABLE"):
        return {"ok": True, "na": True, "score": "N/A", "reasoning": reasoning,
                "reply_quotes_reasoning": tags}
    # Compare as text first, then numerically: a numerical scale declares JSON numbers and the judge
    # answers with a bare number.
    if not _in_enum(score, score_enum):
        return {"ok": False, "why": "score outside the declared scale",
                "returned": score[:80], "expected": score_enum}
    return {"ok": True, "na": False, "score": score, "reasoning": reasoning,
            "reply_quotes_reasoning": tags}


def _in_enum(score: str, score_enum: list) -> bool:
    if any(score == str(e).strip() for e in score_enum):
        return True
    try:
        v = float(score)
    except (TypeError, ValueError):
        return False
    for e in score_enum:
        try:
            if abs(float(e) - v) < 1e-9:
                return True
        except (TypeError, ValueError):
            continue
    return False


ANNOTATOR_SUFFIX = (
    "\n\nIf this rubric cannot be meaningfully applied to the evidence above, for example because "
    "the behaviour it measures is not present at all, answer with a score of \"N/A\" instead of "
    "guessing. Do not include internal or system XML tags in your response.")
