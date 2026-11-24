"""Matching: pick traces for each rubric, and pick the target inside the trace.

1. Scope is the three evaluation levels, `SESSION`, `TRACE` and `TOOL_CALL`.
2. Target selection covers tool calls, not just turns. A tool call rubric needs a specific call.
3. Matching scores on overlap of a behaviour vocabulary. A model call annotates each rubric with
   the behaviours it requires and each trace with the behaviours it exhibits.
4. Rubric features come from library metadata where the library already knows them. Level, domain
   and concept are given, so only the required behaviours need a model call.
"""
from __future__ import annotations

LEVELS = ("SESSION", "TRACE", "TOOL_CALL")

# Matching scores on behaviour overlap, so a behaviour that is not in this vocabulary can never be
# matched.
BEHAVIOURS = [
    "tool_usage", "tool_error_recovery", "retrieval_and_grounding", "code_and_reasoning",
    "multi_turn_interaction", "planning_and_decomposition", "instruction_constraint_adherence",
    "safety_and_refusal", "factual_claims_made", "summarization_or_synthesis",
    "empathy_and_tone", "delegation_to_subagents", "self_correction", "creative_generation",
    "clarification_seeking", "hallucination_or_extrapolation", "ambiguity_interpretation",
    "termination_decision", "plan_vs_execution_fidelity", "resource_efficiency",
    "permission_boundary_adherence", "context_memory_management", "cross_step_consistency",
]

RUBRIC_FEATURE_PROMPT = """You are annotating an evaluation rubric so it can be matched to agent
traces that it can actually be applied to.

The rubric measures this property:
{concept}

It is applied at the {level} level, which means the judge sees {level_note}

For each behaviour below, give a number from 0.0 to 1.0 saying how necessary it is that a trace
exhibits that behaviour for this rubric to be applicable at all. 0.0 means irrelevant, 1.0 means
the rubric cannot be applied without it.

{behaviours}

Also give:
- "min_turns": the fewest conversation turns a trace needs for this rubric to apply.
- "needs_tool_call": true if the rubric cannot be applied unless the trace contains a tool call.
- "explanation": one sentence on what kind of trace this rubric needs.

Output one JSON object with a "behaviors_required" object plus those three fields. Nothing else."""

LEVEL_NOTE = {
    "SESSION": "every turn of the whole session and the catalogue of tools that were available.",
    "TRACE": "the conversation so far and one assistant response singled out as the target.",
    "TOOL_CALL": ("the conversation up to a tool call, the tool catalogue, and that one call "
                  "singled out as the target."),
}

TRACE_FEATURE_PROMPT = """You are annotating an agent trace so that evaluation rubrics can be
matched to it.

Trace summary:
- agent: {agent_id}
- framework: {framework}
- user goal: {user_goal}
- turns: {num_turns}
- tools called: {tools}

Conversation:
{context}

For each behaviour below, give a number from 0.0 to 1.0 saying how clearly this trace exhibits it.

{behaviours}

Also give:
- "domains": an object mapping any of these to 0.0-1.0 relevance: healthcare_medical, legal,
  finance, software_engineering, scientific_research, education, customer_service, security,
  creative_writing, data_analysis, ecommerce, devops, travel_booking, hr_recruiting, insurance,
  general
- "trace_quality": 0.0 to 1.0, how much evaluable signal this trace carries. Low means trivial or
  degenerate, high means substantive multi step behaviour with real decisions.
- "evaluable_turns": up to 3 objects {{"turn_index": int, "behaviors": [...], "reason": "..."}}
  naming the assistant turns most worth judging.
- "evaluable_tool_calls": up to 3 objects {{"turn_index": int, "call_index": int,
  "behaviors": [...], "reason": "..."}} naming the tool calls most worth judging. Prefer calls
  whose arguments came from the conversation, calls that errored or were retried, and calls that
  do something irreversible, over routine or filler calls.

Output one JSON object with "behaviors_present" plus those four fields. Nothing else."""


def build_rubric_prompt(rec: dict) -> str:
    return RUBRIC_FEATURE_PROMPT.format(
        concept=rec["concept"], level=rec["level"], level_note=LEVEL_NOTE[rec["level"]],
        behaviours="\n".join(f"- {b}" for b in BEHAVIOURS))


def build_trace_prompt(t: dict, context: str) -> str:
    return TRACE_FEATURE_PROMPT.format(
        agent_id=t["agent_id"], framework=t["framework"][:120],
        user_goal=t["user_goal"][:600], num_turns=t["num_turns"],
        tools=", ".join(t["tool_catalogue"][:20]) or "none",
        context=context[:14000], behaviours="\n".join(f"- {b}" for b in BEHAVIOURS))


# --------------------------------------------------------------------------------------------
# Scoring: weighted behaviour overlap plus a small trace quality term, times domain overlap.
# --------------------------------------------------------------------------------------------

def weighted_overlap(required: dict, present: dict) -> float:
    num = den = 0.0
    for b in BEHAVIOURS:
        req = float(required.get(b, 0.0) or 0.0)
        if req > 0:
            num += min(req, float(present.get(b, 0.0) or 0.0))
            den += req
    return num / den if den else 1.0


def domain_overlap(rubric_domain: str, trace_domains: dict) -> float:
    if rubric_domain == "general":
        return 1.0
    d = float(trace_domains.get(rubric_domain, 0.0) or 0.0)
    # A domain flavoured rubric still applies to a general trace, just less well.
    return max(d, float(trace_domains.get("general", 0.0) or 0.0) * 0.5)


def level_gate(level: str, t: dict, tf: dict, needs_tool_call: bool, min_turns: int) -> bool:
    if t["num_turns"] < max(1, min_turns):
        return False
    if level == "TOOL_CALL":
        return bool(tf.get("evaluable_tool_calls")) or bool(t["tool_calls"])
    if level == "SESSION" and t["num_turns"] < 2:
        return False
    if needs_tool_call and not t["tool_calls"]:
        return False
    return True


def match_score(rf: dict, tf: dict, quality_weight: float = 0.1) -> float:
    b = weighted_overlap(rf.get("behaviors_required", {}), tf.get("behaviors_present", {}))
    return b + quality_weight * float(tf.get("trace_quality", 0.5) or 0.5)


def pick_target(level: str, t: dict, tf: dict, rf: dict) -> dict | None:
    """Choose the turn or the tool call the rubric will be applied to."""
    if level == "SESSION":
        return {}
    req = rf.get("behaviors_required", {})

    if level == "TRACE":
        cands = tf.get("evaluable_turns") or []
        best, best_s = None, -1.0
        for c in cands:
            ti = c.get("turn_index")
            if not isinstance(ti, int) or ti >= t["num_turns"]:
                continue
            s = sum(float(req.get(b, 0.0) or 0.0) for b in (c.get("behaviors") or []))
            if s > best_s:
                best, best_s = {"turn_index": ti, "reason": c.get("reason", "")}, s
        if best is None:
            # fall back to the last turn that actually has an assistant response
            for turn in reversed(t["turns"]):
                if turn["assistant"]:
                    return {"turn_index": turn["turn_index"], "reason": "last assistant turn"}
            return None
        return best

    cands = tf.get("evaluable_tool_calls") or []
    valid = {(c["turn_index"], c["call_index"]) for c in t["tool_calls"]}
    best, best_s = None, -1.0
    for c in cands:
        key = (c.get("turn_index"), c.get("call_index"))
        if key not in valid:
            continue
        s = sum(float(req.get(b, 0.0) or 0.0) for b in (c.get("behaviors") or []))
        if s > best_s:
            best, best_s = {"turn_index": key[0], "call_index": key[1],
                            "reason": c.get("reason", "")}, s
    if best is None and t["tool_calls"]:
        c = t["tool_calls"][0]
        return {"turn_index": c["turn_index"], "call_index": c["call_index"],
                "reason": "first tool call"}
    return best


def select_for_rubric(rec: dict, rf: dict, traces: list[dict], tfeat: dict[str, dict],
                      cap: int, max_per_agent: int) -> list[dict]:
    """Score every trace, then take the top ones under an agent diversity cap.

    When the rubric has a `ground_truth_dim` that the pool carries labels for, the selection
    deliberately mixes traces where the property is present (label 1) with traces where it is
    absent (label 0). A rubric whose traces all score the same teaches the model to emit that score
    rather than to read the rubric, and this is where an existing pool can supply real contrast.
    """
    dim = rec.get("ground_truth_dim")
    scored: list[tuple[float, dict, dict]] = []
    for t in traces:
        tf = tfeat.get(t["trace_id"])
        if not tf:
            continue
        if not level_gate(rec["level"], t, tf, bool(rf.get("needs_tool_call")),
                          int(rf.get("min_turns", 1) or 1)):
            continue
        s = match_score(rf, tf) * domain_overlap(rec.get("domain") or "general", tf.get("domains", {}))
        if s <= 0.0:
            continue
        tgt = pick_target(rec["level"], t, tf, rf)
        if tgt is None:
            continue
        scored.append((s, t, tgt))
    scored.sort(key=lambda x: -x[0])

    def take(pool: list[tuple], limit: int) -> list[dict]:
        per_agent: dict[str, int] = {}
        out = []
        for s, t, tgt in pool:
            if len(out) >= limit:
                break
            a = t["agent_id"]
            if per_agent.get(a, 0) >= max_per_agent:
                continue
            per_agent[a] = per_agent.get(a, 0) + 1
            out.append({"trace_id": t["trace_id"], "agent_id": a, "match_score": round(s, 4),
                        "target": tgt})
        return out

    if dim:
        # Spread only over traces whose label for this dimension is the trustworthy one.
        pos = [x for x in scored if is_primary(x[1], dim)
               and (x[1].get("target_labels") or {}).get(dim) == 1]
        neg = [x for x in scored if is_primary(x[1], dim)
               and (x[1].get("target_labels") or {}).get(dim) == 0]
        rest = [x for x in scored if not is_primary(x[1], dim)]
        half = cap // 2
        out = take(pos, half) + take(neg, cap - half)
        if len(out) < cap:
            got = {o["trace_id"] for o in out}
            out += take([x for x in rest if x[1]["trace_id"] not in got], cap - len(out))
        return out[:cap]
    return take(scored, cap)


def is_primary(trace: dict, dim: str | None) -> bool:
    """True when this trace was built to exercise `dim`, so its label for `dim` is trustworthy.

    A pool trace can carry labels for several dimensions while having been built to exercise only
    one of them. The side labels are often unreliable, so only the primary one counts as ground
    truth. A trace with labels but no `primary_dim` counts as primary for every labelled dimension.
    """
    if not dim:
        return False
    labels = trace.get("target_labels") or {}
    if dim not in labels:
        return False
    return trace.get("primary_dim") in (None, dim)


def ground_truth_dim(rec: dict, label_dims: set[str]) -> str | None:
    """The labelled dimension a rubric can be checked with: its own `ground_truth_dim`, or its
    `rubric_id` when the pool carries labels under that name."""
    if rec.get("ground_truth_dim"):
        return rec["ground_truth_dim"]
    rid = rec.get("rubric_id")
    if rid in label_dims:
        return rid
    return None
