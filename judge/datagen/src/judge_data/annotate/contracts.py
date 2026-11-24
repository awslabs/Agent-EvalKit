"""Output contracts: how a training prompt asks for the answer, and the target written to match.

The annotator always answers the rubric's own contract (reasoning then score, fenced JSON), which is
what a judge service asks for. A record can then be re-served under another contract: the prompt's
output block is rewritten and the same judgement is re-serialised to match, so a contract never
needs its own annotation pass.

Contracts:
  native          the rubric's own block; target ```json {"reasoning", "score"}```
  score_only      schema without the reasoning property (a verdict only judge); ```json {"score"}```
  verdict_fenced  the score key renamed "verdict"; fenced
  verdict_bare    the score key renamed "verdict"; bare JSON, the fence instruction dropped
  score_first     score before reasoning in schema and target; fenced
  keyvalue        "Reasoning: ...\\nScore: ..." lines instead of JSON
  xml             <reasoning>...</reasoning><score>...</score> instead of JSON
"""
from __future__ import annotations

import hashlib
import json
import re

CONTRACTS = ("native", "score_only", "verdict_fenced", "verdict_bare", "score_first", "keyvalue", "xml")
DEFAULT_WEIGHTS = "native:70,score_only:8,verdict_fenced:4,verdict_bare:4,score_first:6,keyvalue:4,xml:4"

ANCHOR = "The output should be a well-formatted JSON instance"
SCHEMA_HEAD = "Here is the output JSON schema:"
FENCE_TAIL = ("Do not return any preamble or explanations, return only a pure JSON string "
              "surrounded by triple backticks (```).")
BARE_TAIL = "Do not return any preamble or explanations, return only a pure JSON string."


def parse_weights(spec: str) -> dict[str, int]:
    w = {k: int(v) for k, v in (x.split(":") for x in spec.split(","))}
    bad = set(w) - set(CONTRACTS)
    if bad:
        raise ValueError(f"unknown output contracts {sorted(bad)}")
    return w


def pick(pair_id: str, weights: dict[str, int]) -> str:
    names = [n for n in CONTRACTS if weights.get(n)]
    x = int(hashlib.sha256(f"{pair_id}|contract".encode()).hexdigest()[:8], 16) % sum(weights[n] for n in names)
    for n in names:
        x -= weights[n]
        if x < 0:
            return n
    return names[-1]


def _schema_span(prompt: str) -> tuple[int, int, dict] | None:
    i = prompt.find(SCHEMA_HEAD)
    if i < 0:
        return None
    j = prompt.find("{", i)
    try:
        obj, end = json.JSONDecoder().raw_decode(prompt, j)
    except ValueError:
        return None
    return j, end, obj


def apply(prompt: str, contract: str, enum: list) -> str | None:
    """The prompt with its output block rewritten for `contract`; None if it cannot be done exactly."""
    if contract == "native":
        return prompt
    a = prompt.find(ANCHOR)
    if a < 0 or prompt.count(ANCHOR) != 1:
        return None
    options = " or ".join(str(e) if not isinstance(e, str) else f"'{e}'" for e in enum)
    if contract == "keyvalue":
        return (prompt[:a] + "Return your evaluation as two lines and nothing else:\n"
                "Reasoning: <step by step reasoning, using no more than 250 words>\n"
                f"Score: <one of {options}>")
    if contract == "xml":
        return (prompt[:a] + "Return your evaluation as XML and nothing else:\n"
                "<reasoning>step by step reasoning, using no more than 250 words</reasoning>\n"
                f"<score>one of {options}</score>")
    span = _schema_span(prompt)
    if span is None:
        return None
    j, end, schema = span
    props, req = dict(schema.get("properties", {})), list(schema.get("required", []))
    if "score" not in props or "reasoning" not in props:
        return None
    if contract == "score_only":
        props.pop("reasoning")
        req = [k for k in req if k != "reasoning"]
    elif contract in ("verdict_fenced", "verdict_bare"):
        sc = dict(props.pop("score"))
        sc["title"] = "Verdict"
        sc["description"] = sc.get("description", "").replace("score should", "verdict should")
        props["verdict"] = sc
        req = ["verdict" if k == "score" else k for k in req]
    elif contract == "score_first":
        props = {"score": props["score"], **{k: v for k, v in props.items() if k != "score"}}
        req = ["score"] + [k for k in req if k != "score"]
    new = {**schema, "properties": props, "required": req}
    ascii_only = "\\u" in prompt[j:end]
    out = prompt[:j] + json.dumps(new, ensure_ascii=ascii_only) + prompt[end:]
    if contract == "verdict_bare":
        if FENCE_TAIL not in out:
            return None
        # No fences anywhere: neither around the schema shown nor around the answer asked for.
        k = out.find(SCHEMA_HEAD)
        rest = out[k:].replace(FENCE_TAIL, "\0")
        rest = re.sub(r"(?m)^[ \t]*```[ \t]*\n", "", rest, count=2)  # whole fence lines, indent and all
        out = out[:k] + rest.replace("\0", BARE_TAIL)
    return out


def target(reasoning: str, score, contract: str) -> str:
    """The judgement serialised the way `contract` asks for it."""
    if contract == "keyvalue":
        return f"Reasoning: {reasoning}\nScore: {score}"
    if contract == "xml":
        return f"<reasoning>{reasoning}</reasoning>\n<score>{score}</score>"
    if contract == "score_only":
        obj = {"score": score}
    elif contract in ("verdict_fenced", "verdict_bare"):
        obj = {"reasoning": reasoning, "verdict": score}
    elif contract == "score_first":
        obj = {"score": score, "reasoning": reasoning}
    else:
        obj = {"reasoning": reasoning, "score": score}
    body = json.dumps(obj, ensure_ascii=False)
    return body if contract == "verdict_bare" else f"```json\n{body}\n```"
