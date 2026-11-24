"""The normalised Trace schema, loading trace pools, and rendering evidence for each level.

A trace pool is any JSONL of traces. Each line is either already in the normalised schema

    {"trace_id": "t1", "agent_id": "org/repo", "framework": "langgraph", "user_goal": "...",
     "turns": [{"user": "...", "reasoning": "...", "assistant": "...",
                "tool_calls": [{"tool_name": "search", "arguments": {"q": "..."}}],
                "tool_results": [{"hits": 3}]}],
     "tool_catalogue": ["search", "fetch"], "tags": {"topic": "travel"},
     "target_labels": {"goal_reached": 1}, "primary_dim": "goal_reached"}

or uses the raw field names `scenario_id`, `user_input`, `agent_response`, which `normalise`
maps. Only `turns` is required. `tool_catalogue` may list names or `{"name", "description"}`
objects, and called tool names are always added. `tags` are free form strings used for
stratified sampling. `target_labels` and `primary_dim` are optional ground truth: a label per
dimension (1 = property present) and the one dimension the trace was built to exercise.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

# The numbered turn header `render_context` emits. Anchored, because trace content can quote the
# words "Turn 1:" mid sentence. The `: ` alternative covers prompts that put the slot after a
# label, as in "Context: {context}".
HEADER = re.compile(r"(?:^|\n|: )Turn \d+:\n", re.M)


@dataclass
class Trace:
    trace_id: str
    agent_id: str
    framework: str
    user_goal: str
    turns: list[dict] = field(default_factory=list)
    tool_catalogue: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)   # flattened, with turn index
    num_turns: int = 0
    target_labels: dict | None = None
    # Which dimension this trace was built to exercise. When a pool carries labels for several
    # dimensions, only this one is usually trustworthy as ground truth.
    primary_dim: str | None = None
    primary_class: str | None = None
    source: str = "trace_pool"
    tags: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


TRACE_FIELDS = set(Trace.__dataclass_fields__)


def _tool_name(t) -> str:
    return str(t.get("name") or t.get("tool_name") or "") if isinstance(t, dict) else str(t)


def normalise(raw: dict, idx: int = 0) -> Trace | None:
    """One pool line to a Trace, or None when it has no usable turns."""
    turns_in = raw.get("turns") or []
    if not isinstance(turns_in, list) or not turns_in:
        return None

    turns: list[dict] = []
    calls: list[dict] = []
    catalogue: set[str] = {n for n in map(_tool_name, raw.get("tool_catalogue") or raw.get("tools")
                                          or []) if n}
    for ti, t in enumerate(turns_in):
        if not isinstance(t, dict):
            continue
        tc = [c for c in (t.get("tool_calls") or []) if isinstance(c, dict)]
        tr = t.get("tool_results") or []
        tc = [{**c, "tool_name": c.get("tool_name") or c.get("name") or ""} for c in tc]
        for ci, c in enumerate(tc):
            if c["tool_name"]:
                catalogue.add(c["tool_name"])
            calls.append({
                "turn_index": len(turns),
                "call_index": ci,
                "tool_name": c["tool_name"],
                "arguments": c.get("arguments"),
                "tool_call_id": c.get("tool_call_id"),
                "result": tr[ci] if ci < len(tr) else None,
            })
        turns.append({
            "turn_index": len(turns),
            "user": str(t.get("user") or t.get("user_input") or ""),
            "reasoning": str(t.get("reasoning") or ""),
            "assistant": str(t.get("assistant") or t.get("agent_response") or ""),
            "tool_calls": tc,
            "tool_results": tr,
        })
    if not turns:
        return None

    tid = raw.get("trace_id") or raw.get("scenario_id") or f"t{idx:08d}"
    labels = raw.get("target_labels")

    return Trace(
        trace_id=str(tid),
        agent_id=str(raw.get("agent_id") or raw.get("source_repo") or "unknown"),
        framework=str(raw.get("framework") or "unknown"),
        user_goal=str(raw.get("user_goal") or turns[0]["user"])[:2000],
        turns=turns,
        tool_catalogue=sorted(catalogue),
        tool_calls=calls,
        num_turns=len(turns),
        target_labels=labels if isinstance(labels, dict) else None,
        primary_dim=raw.get("primary_dim"),
        primary_class=raw.get("primary_class"),
        source=str(raw.get("source") or "trace_pool"),
        tags={str(k): str(v) for k, v in (raw.get("tags") or {}).items()},
    )


def load_jsonl(path: str | Path) -> list[Trace]:
    """Load a trace pool. Unusable lines are skipped. `rubric_trace_match.sample` samples from it."""
    out: list[Trace] = []
    with Path(path).open(errors="replace") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = normalise(raw, i)
            if t is not None:
                out.append(t)
    return out


def from_dict(d: dict) -> Trace:
    """A Trace from its `as_dict()` form, ignoring extra keys."""
    return Trace(**{k: v for k, v in d.items() if k in TRACE_FIELDS})


# --------------------------------------------------------------------------------------------
# Evidence rendering. The corpus declares an evaluation level, and the level fixes which slots
# have to be filled. These build the text that goes into those slots.
# --------------------------------------------------------------------------------------------

def render_context(t: Trace, upto_turn: int | None = None,
                   upto_call: tuple[int, int] | None = None,
                   turn_labels: bool = True,
                   scrub: Callable[[str], str] | None = None) -> str:
    """Render the conversation. `upto_turn` and `upto_call` truncate for TRACE and TOOL_CALL.

    The surface form here is invented. A rubric prompt only gives a slot, `{context}` or
    `<<CONVERSATION_CONTEXT>>`, and your evaluation service's own serialiser fills it. So a model
    trained on one fixed layout can start keying on `Turn N:` as a structural anchor and break when
    the service emits something else. `turn_labels` switches the numbered headers off, and callers
    are expected to vary it across records so the model learns to read a conversation rather than to
    find a marker.

    `scrub` rewrites assistant text on the way out, which is where internal reasoning lives. It is a
    parameter rather than a fixed policy because whether reasoning is present is itself a coverage
    axis, see `annotate.scrub`.
    """
    def asst(s: str) -> str:
        return scrub(s).strip() if scrub else s

    # Without the numbered headers there is nothing for the speaker lines to be indented under, so
    # the indent goes too. The two layouts should differ in more than one character, otherwise a
    # model can learn one and treat the other as the same string with a header deleted.
    pad = "  " if turn_labels else ""
    lines = []
    for turn in t.turns:
        ti = turn["turn_index"]
        if upto_turn is not None and ti > upto_turn:
            break
        if upto_call is not None and ti > upto_call[0]:
            break
        if turn_labels:
            lines.append(f"Turn {ti + 1}:")
        elif lines:
            lines.append("")
        if turn["user"]:
            lines.append(f"{pad}User: {turn['user']}")
        stop_here = upto_call is not None and ti == upto_call[0]
        if stop_here:
            # A tool call judge must not see the call it is judging, nor what followed it.
            for ci, c in enumerate(turn["tool_calls"] or []):
                if ci >= upto_call[1]:
                    break
                lines.append(f"{pad}Tool call: {c.get('tool_name')}({json.dumps(c.get('arguments'), ensure_ascii=False)})")
                res = (turn["tool_results"] or [None] * len(turn["tool_calls"]))
                if ci < len(res) and res[ci] is not None:
                    lines.append(f"{pad}Tool result: {json.dumps(res[ci], ensure_ascii=False)[:1200]}")
            break
        for ci, c in enumerate(turn["tool_calls"] or []):
            lines.append(f"{pad}Tool call: {c.get('tool_name')}({json.dumps(c.get('arguments'), ensure_ascii=False)})")
            res = turn["tool_results"] or []
            if ci < len(res) and res[ci] is not None:
                lines.append(f"{pad}Tool result: {json.dumps(res[ci], ensure_ascii=False)[:1200]}")
        if turn["assistant"] and not (upto_turn is not None and ti == upto_turn):
            a = asst(turn["assistant"])
            # A turn whose response was entirely reasoning goes empty once reasoning is removed.
            # Inside the context that is harmless and honest, the turn really did produce only tool
            # calls, so the line is dropped rather than left blank.
            if a:
                lines.append(f"{pad}Agent: {a}")
    return "\n".join(lines)


def render_tools(t: Trace) -> str:
    if not t.tool_catalogue:
        return "No tools were available to this agent."
    return "\n".join(f"- {n}" for n in t.tool_catalogue)


def render_tool_call(t: Trace, turn_index: int, call_index: int) -> str:
    """The judged call and its result. A tool level judge receives the call and its result as one
    object, so the result is part of the evidence."""
    for c in t.tool_calls:
        if c["turn_index"] == turn_index and c["call_index"] == call_index:
            out = f"{c['tool_name']}({json.dumps(c['arguments'], ensure_ascii=False)})"
            if c.get("result") is not None:
                out += f"\nTool result: {json.dumps(c['result'], ensure_ascii=False)[:1200]}"
            return out
    return ""


# An evaluation service may fill the same slots differently: dump the normalised session objects and
# render the history one item per line, each line the Python repr of a message dict or of a list of
# tool executions, newlines inside a message escaped. The "repr" context format produces that
# serialisation, so the judge also learns to read it.

def _p_text(text: str) -> dict:
    return {"content_type": "text", "text": text}


def _p_call_id(t: Trace, ti: int, ci: int) -> str:
    import base64
    import hashlib
    h = hashlib.sha256(f"{t.trace_id}|{ti}|{ci}".encode()).digest()
    return "tooluse_" + base64.urlsafe_b64encode(h).decode()[:22]


def _p_execution(t: Trace, turn: dict, ci: int) -> dict:
    c = (turn["tool_calls"] or [])[ci]
    res = turn["tool_results"] or []
    r = res[ci] if ci < len(res) else None
    content = "" if r is None else (r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)[:1200])
    cid = _p_call_id(t, turn["turn_index"], ci)
    args = c.get("arguments")
    return {"tool_call": {"name": c.get("tool_name"), "parameters": args if isinstance(args, (dict, str)) else {},
                          "tool_call_id": cid},
            "tool_result": {"content": content, "error": None, "tool_call_id": cid}}


def _p_history(t: Trace, upto_turn: int | None = None,
               upto_call: tuple[int, int] | None = None) -> str:
    items: list = []
    for turn in t.turns:
        ti = turn["turn_index"]
        if upto_turn is not None and ti > upto_turn:
            break
        if upto_call is not None and ti > upto_call[0]:
            break
        if turn["user"]:
            items.append({"role": "user", "content": [_p_text(turn["user"])]})
        n_calls = len(turn["tool_calls"] or [])
        if upto_call is not None and ti == upto_call[0]:
            n_calls = min(n_calls, upto_call[1])
        execs = [_p_execution(t, turn, ci) for ci in range(n_calls)]
        if execs:
            items.append(execs)
        if upto_call is not None and ti == upto_call[0]:
            break
        if turn["assistant"] and not (upto_turn is not None and ti == upto_turn):
            items.append({"role": "assistant", "content": [_p_text(turn["assistant"])]})
    return "\n".join(str(x) for x in items)


def evidence_repr(t: Trace, level: str, target: dict | None = None,
                        tool_specs: dict[str, dict] | None = None) -> dict[str, str]:
    """`evidence_for` in the repr serialisation. `tool_specs` maps a tool name to its
    {"description", "parameters"} for the catalogue; names without one get None, as in the library."""
    specs = tool_specs or {}
    tools = str([{"name": n, "description": (specs.get(n) or {}).get("description"),
                  "parameters": (specs.get(n) or {}).get("parameters")} for n in t.tool_catalogue])
    if level == "SESSION":
        return {"context": _p_history(t), "available_tools": tools}
    if level == "TRACE":
        ti = (target or {}).get("turn_index", t.num_turns - 1)
        raw = t.turns[ti]["assistant"] if ti < len(t.turns) else ""
        return {"context": _p_history(t, upto_turn=ti), "assistant_turn": str(_p_text(raw))}
    if level == "TOOL_CALL":
        ti = (target or {}).get("turn_index", 0)
        ci = (target or {}).get("call_index", 0)
        turn = next(x for x in t.turns if x["turn_index"] == ti)
        return {"context": _p_history(t, upto_call=(ti, ci)), "available_tools": tools,
                "tool_turn": str(_p_execution(t, turn, ci))}
    raise ValueError(f"unknown level {level}")


def evidence_for(t: Trace, level: str, target: dict | None = None,
                 turn_labels: bool = True,
                 scrub: Callable[[str], str] | None = None) -> dict[str, str]:
    """Build the placeholder values for one level.

    SESSION sees everything. TRACE sees the conversation up to a chosen assistant turn plus that
    turn as the target. TOOL_CALL sees the conversation up to a chosen call plus that call.

    `scrub` has to reach the judged assistant turn as well as the context, not just the context.
    At TRACE level that turn is the object of judgement, so leaving reasoning in it while removing
    it from the context would be the worst of both, and it is also where a leak does the most damage.
    """
    kw = {"turn_labels": turn_labels, "scrub": scrub}
    if level == "SESSION":
        return {"context": render_context(t, **kw), "available_tools": render_tools(t)}
    if level == "TRACE":
        ti = (target or {}).get("turn_index", t.num_turns - 1)
        raw = t.turns[ti]["assistant"] if ti < len(t.turns) else ""
        return {"context": render_context(t, upto_turn=ti, **kw),
                "assistant_turn": (scrub(raw).strip() if scrub else raw)}
    if level == "TOOL_CALL":
        ti = (target or {}).get("turn_index", 0)
        ci = (target or {}).get("call_index", 0)
        return {"context": render_context(t, upto_call=(ti, ci), **kw),
                "available_tools": render_tools(t),
                "tool_turn": render_tool_call(t, ti, ci)}
    raise ValueError(f"unknown level {level}")
