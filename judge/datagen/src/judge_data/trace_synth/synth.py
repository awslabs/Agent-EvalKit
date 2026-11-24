"""Synthesis: build a trace that lands on a chosen severity of a chosen concept.

Matching can only use evidence that already exists, and it cannot make a trace score anywhere in
particular. This does the other thing: given a concept, manufacture the evidence at a named
severity, so that one concept yields a family of traces spanning its scale.

The CLI (`python -m judge_data.trace_synth`) targets each score level of each rubric, so a family
of traces spans the rubric's own scale. The three coarse severities below are the backbone of each
target and the scale of the independent verification.

Two things decide whether the output is usable, and both are cheap to get right by construction
and expensive to detect afterwards.

Everything except the measured property is held fixed inside a family. Same agent, same tools,
same user goal, comparable length. Without that the model can learn that long traces score low
rather than learning the rubric.

The constructed severity is verified rather than trusted. It is not the training label: the
training target is always the annotator's reasoning and score. What the constructed severity buys
is an agreement check on the annotator and a test set whose label does not depend on the annotator.
"""
from __future__ import annotations

import json

# Three coarse buckets. A generator can hit the ends of a severity axis but not fine gradations in
# the middle, so the axis is coarse and the rubric's own scale does the fine work.
SEVERITIES = [
    ("absent", "The property is clearly absent. A judge should place this at the worst end of any "
               "scale."),
    ("partial", "The property is genuinely mixed, neither clearly present nor clearly absent. A "
                "judge should land somewhere in the middle."),
    ("full", "The property is clearly and fully present. A judge should place this at the best end "
             "of any scale."),
]

LEVEL_SHAPE = {
    "SESSION": ("a multi turn session between a user and the agent, 5 to 10 turns, with tool calls "
                "where the task needs them. Include back-and-forth clarification, follow-up "
                "questions, and iterative refinement"),
    "TRACE": ("a session of 3 to 6 turns, where the final assistant response is the thing "
              "worth judging. Include enough context turns to make the judgement meaningful"),
    "TOOL_CALL": ("a session of 3 to 5 turns, containing at least two tool calls with realistic "
                  "arguments and results. The LAST tool call in the session is the one being "
                  "judged and must carry the target score level; earlier calls are ordinary "
                  "context. Make no tool call after it"),
}

PROMPT = """You are generating synthetic agent execution traces for training an evaluation model.

## The property being measured
{concept}

## The severity this trace must exhibit
{severity_name}: {severity_desc}

## The agent to simulate
- repository: {agent_id}
- framework: {framework}
- domain: {domain}

### System prompt
{system_prompt}

### Tools available
{tools}

## The scenario
{goal}

## Shape
Produce {shape}.

## Rules
- The trace must exhibit the property at exactly the severity named above, and nothing else about
  it should be unusual. Do not make it longer, shorter, or more dramatic than a normal trace.
- Use only the tools listed. Invent realistic argument values that fit the tool descriptions.
- Tool results should look like real tool output, including failures where the scenario calls for
  one.
- Write realistic agent prose. Do not mention severity, evaluation, rubrics or scoring anywhere in
  the trace.
- Aim for roughly {target_tokens} tokens of trace content in total.
- When you need a quotation mark inside a JSON string value, use a single quote. Never put a raw
  double quote inside a string value, because it breaks the JSON.

## Output
A JSON object:
{{"turns": [{{"user": "...", "reasoning": "...", "assistant": "...",
              "tool_calls": [{{"tool_name": "...", "arguments": {{...}}}}],
              "tool_results": [{{...}}]}}],
  "note": "one clause on how the property shows up at this severity"}}

`reasoning` is the agent's own private thinking and may be empty. `tool_calls` and `tool_results`
may be empty lists on turns that make no calls, and must be the same length when present. Output
the JSON object and nothing else."""

VERIFY_PROMPT = """Read the agent trace below and judge one property. You are not told what the
trace was built to show, and you should not guess.

## Property
{concept}

## Trace
{trace}

## Task
Place this trace on the following scale according to how much the property is present.

{scale}

Output a JSON object {{"reasoning": "<at most 80 words>", "severity": "<one of the names above>"}}
and nothing else."""


def coarse_bucket(index: int, n_levels: int) -> str:
    """Which of the three coarse severities a score level falls in, by its position on the scale
    (0 = worst label, 1 = best label)."""
    position = index / max(n_levels - 1, 1)
    if position <= 0.25:
        return SEVERITIES[0][0]
    if position >= 0.75:
        return SEVERITIES[2][0]
    return SEVERITIES[1][0]


def severities_for_scale(score_enum: list[str]) -> list[tuple[str, str]]:
    """Map each score level to a synthesis severity instruction.

    Returns one (name, description) pair per score level. Uses the three coarse severities as
    backbone (the generator reliably hits absent/partial/full) but adds the target score level so
    traces span the full scale.
    """
    n = len(score_enum)
    desc_of = dict(SEVERITIES)
    result = []
    for i, label in enumerate(score_enum):
        base_desc = desc_of[coarse_bucket(i, n)]
        desc = (
            f"Target score level: '{label}' (level {i + 1} of {n}). "
            f"{base_desc}"
        )
        result.append((label, desc))
    return result


def _format_tools(tools: list) -> str:
    """Render tools for the prompt. Tools may be name strings or {"name", "description"} dicts."""
    if not tools:
        return "no tools"
    parts = []
    for t in tools[:12]:
        if isinstance(t, dict):
            name = t.get("name", "?")
            desc = t.get("description", "")
            if desc:
                parts.append(f"- {name}: {desc[:150]}")
            else:
                parts.append(f"- {name}")
        else:
            parts.append(f"- {t}")
    return "\n".join(parts)


VARIATION_NOTE = ("\n\nThis is variation {k} of this request. Other variations already exist, so "
                  "invent a different concrete task, user and conversation from them.")


def build_prompt(concept: str, level: str, severity: tuple[str, str], seed: dict,
                 target_tokens: int = 1600, variation: int = 0) -> str:
    """Build the synthesis prompt.

    `variation` separates requests that would otherwise be byte-identical, which happens whenever the
    same agent is drawn twice for one (concept, severity). Identical prompts share a cache key, so
    without it the repeats come back as copies of one trace. Variation 0 leaves the prompt unchanged.
    """
    goal = seed["goal"][:900] + (VARIATION_NOTE.format(k=variation + 1) if variation else "")
    return PROMPT.format(
        concept=concept, severity_name=severity[0], severity_desc=severity[1],
        agent_id=seed["agent_id"], framework=str(seed.get("framework") or "")[:160],
        system_prompt=str(seed.get("system_prompt") or "")[:500],
        tools=_format_tools(seed.get("tools", [])),
        domain=seed.get("domain", "general"), goal=goal,
        shape=LEVEL_SHAPE[level], target_tokens=target_tokens)


def build_verify_prompt(concept: str, trace_text: str) -> str:
    return VERIFY_PROMPT.format(
        concept=concept, trace=trace_text[:16000],
        scale="\n".join(f"- {n}: {d}" for n, d in SEVERITIES))


def to_trace(obj: dict, trace_id: str, seed: dict, concept_id: str, severity: str) -> dict | None:
    """Turn a generated object into the same normalised shape the matcher consumes."""
    turns_in = obj.get("turns")
    if not isinstance(turns_in, list) or not turns_in:
        return None
    turns, calls = [], []
    catalogue: set[str] = set()
    for ti, t in enumerate(turns_in):
        if not isinstance(t, dict):
            return None
        tc = t.get("tool_calls") or []
        trs = t.get("tool_results") or []
        if not isinstance(tc, list) or not isinstance(trs, list):
            return None
        # Generators sometimes emit a call as a list or string. Drop those, keeping each surviving
        # call aligned with its own result, so the renderer can assume every call is a dict.
        kept = [(c, trs[ci] if ci < len(trs) else None) for ci, c in enumerate(tc) if isinstance(c, dict)]
        tc = [c for c, _r in kept]
        trs = [r for _c, r in kept] if trs else []
        for ci, c in enumerate(tc):
            name = str(c.get("tool_name") or "")
            if name:
                catalogue.add(name)
            calls.append({"turn_index": ti, "call_index": ci, "tool_name": name,
                          "arguments": c.get("arguments"),
                          "tool_call_id": f"call_{ti}_{ci}",
                          "result": trs[ci] if ci < len(trs) else None})
        turns.append({"turn_index": ti, "user": str(t.get("user") or ""),
                      "reasoning": str(t.get("reasoning") or ""),
                      "assistant": str(t.get("assistant") or ""),
                      "tool_calls": tc, "tool_results": trs})
    if not any(t["assistant"] for t in turns):
        return None
    return {
        "trace_id": trace_id, "agent_id": seed["agent_id"], "framework": seed.get("framework", ""),
        "user_goal": str(seed.get("goal") or (turns[0]["user"] if turns else ""))[:2000],
        "turns": turns,
        "tool_catalogue": sorted(catalogue), "tool_calls": calls, "num_turns": len(turns),
        "target_labels": None, "primary_dim": None, "primary_class": None,
        "source": "rubric_driven_synthesis",
        "concept_id": concept_id, "constructed_severity": severity,
        "note": str(obj.get("note") or "")[:300],
    }


def flatten_for_verify(t: dict) -> str:
    lines = []
    for turn in t["turns"]:
        lines.append(f"Turn {turn['turn_index'] + 1}:")
        if turn["user"]:
            lines.append(f"  User: {turn['user']}")
        for ci, c in enumerate(turn["tool_calls"] or []):
            lines.append(f"  Tool call: {c.get('tool_name')}"
                         f"({json.dumps(c.get('arguments'), ensure_ascii=False)})")
            res = turn["tool_results"] or []
            if ci < len(res):
                lines.append(f"  Tool result: {json.dumps(res[ci], ensure_ascii=False)[:800]}")
        if turn["assistant"]:
            lines.append(f"  Agent: {turn['assistant']}")
    return "\n".join(lines)
