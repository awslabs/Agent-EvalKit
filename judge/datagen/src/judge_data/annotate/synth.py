"""Annotation of synthesized pairs: one pairs JSONL from `trace_synth`.

    python -m judge_data.annotate \
        --pairs out/pairs.jsonl --out out/output.jsonl \
        [--rubric-library out/rubric_library.jsonl] [--agent-registry agent_registry.jsonl] \
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

Each synthesized trace is parsed into turns (`trace_synth.synth.to_trace`) and rendered into the
evidence its rubric's level declares (`judge_data.traces.evidence_for`): the conversation, plus the
judged final turn at TRACE, the tool catalogue at SESSION, the catalogue and the judged call at
TOOL_CALL. The teacher sees exactly the prompt stored in the training record, the prompt a judge
receives. `--allow-na` appends an N/A option for the teacher only.

Rubrics are looked up by id in the library (default: rubric_library.jsonl next to the pairs), so a
re-rendered library takes effect without re-synthesizing. The copy embedded in a pair is a fallback.

Each record is re-served under an output contract (`annotate.contracts`), chosen per pair id, so
the trained judge follows varied output instructions. A prompt whose output block cannot be
rewritten exactly stays native.

Writes `--out` (SFT records `{id, prompt, completion, meta}`, scored only, `meta` holding
`rubric_id, concept, level, n_levels, output_contract, agent_id, verdict, split, teacher`) and
`<out stem>.judgments.jsonl` (one row per pair: ok, why, score, N/A), which is what a quality
report reads.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from judge_data.clients import client_from_args
from judge_data.utils.io import log
from judge_data.utils.jsonx import extract_json


CONTEXT_FORMATS = ("repr", "turns", "flat")

# Agent reasoning shown as <thinking> blocks inside the agent's text on a share of records, because
# real agent traffic sometimes carries it. A synthesized turn's reasoning sometimes narrates the
# construction ("at this severity level I should..."), so a trace is only eligible when no turn's
# reasoning reads like that.
THINKING_SHARE = 0.3
LEAKY = re.compile(r"severit|rubric|evaluat|\bscor|judg|deliberate|intentional|planted|as instructed|"
                   r"target (?:level|label)|the property|exhibit|worst.case|best.case", re.I)


def wants_thinking(pair_id: str) -> bool:
    import hashlib
    return int(hashlib.sha256(f"{pair_id}|thinking".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF < THINKING_SHARE


def pick_format(pair_id: str, weights: dict[str, int]) -> str:
    """Deterministic per pair, so a rerun renders (and caches) the same prompt."""
    import hashlib
    names = [n for n in CONTEXT_FORMATS if weights.get(n)]
    x = int(hashlib.sha256(pair_id.encode()).hexdigest()[:8], 16) % sum(weights[n] for n in names)
    for n in names:
        x -= weights[n]
        if x < 0:
            return n
    return names[-1]


def build_evidence(pair: dict, rubric: dict, tools_by_agent: dict[str, dict[str, dict]],
                   fmt: str = "turns") -> tuple[dict | None, str]:
    """Parse the pair's trace and render the evidence slots for the rubric's level.

    `fmt`: "repr" (one Python repr of a message per line), "turns" (numbered `Turn N:` blocks) or
    "flat" (no headers). See traces.render_context and traces.evidence_repr."""
    from judge_data import traces
    from judge_data.trace_synth import synth

    obj = extract_json(pair["trace"])
    if not isinstance(obj, dict) or not isinstance(obj.get("turns"), list):
        return None, "trace did not parse into turns (malformed JSON or cut at max_tokens)"
    seed = {"agent_id": pair.get("agent_id", "unknown"), "framework": "", "goal": ""}
    t = synth.to_trace(obj, pair["id"], seed, pair.get("rubric", {}).get("rubric_id", ""),
                       pair.get("severity", ""))
    if t is None:
        return None, "trace has no usable turns"
    tr = traces.from_dict(t)
    thinking = False
    if wants_thinking(pair["id"]) and not any(LEAKY.search(x.get("reasoning") or "") for x in tr.turns) \
            and any((x.get("reasoning") or "").strip() for x in tr.turns):
        thinking = True
        for x in tr.turns:
            r = (x.get("reasoning") or "").strip()
            if r and x["assistant"].strip():
                x["assistant"] = f"<thinking>{r}</thinking>\n{x['assistant']}"
    # The judge should see what the agent could have called, not only what it did call.
    agent_tools = tools_by_agent.get(tr.agent_id)
    if agent_tools:
        tr.tool_catalogue = sorted(set(agent_tools) | set(tr.tool_catalogue))

    level = rubric["level"]
    target = None
    if level == "TOOL_CALL":
        if not tr.tool_calls:
            return None, "TOOL_CALL rubric but the trace makes no tool call"
        last = tr.tool_calls[-1]
        target = {"turn_index": last["turn_index"], "call_index": last["call_index"]}
    elif level == "TRACE":
        judged = [x["turn_index"] for x in tr.turns if x["assistant"].strip()]
        target = {"turn_index": judged[-1]}
    if fmt == "repr":
        ev = traces.evidence_repr(tr, level, target, agent_tools or {})
    else:
        ev = traces.evidence_for(tr, level, target, turn_labels=fmt == "turns")
    for slot in rubric.get("placeholders") or []:
        if not str(ev.get(slot, "")).strip():
            return None, f"no evidence for slot {slot}"
    ev["_thinking"] = thinking
    return ev, ""


def run(a: argparse.Namespace) -> None:
    """Annotate one pairs JSONL from trace_synth. `a` comes from `annotate.__main__`, with this
    source's defaults filled in and `a.pairs` holding the one input file."""
    pairs_file = a.pairs[0]

    client = client_from_args(a)
    teacher = client.model_id

    from judge_data.annotate import contracts
    from judge_data.annotate.parse import parse
    from judge_data.annotate.prompt import annotator_prompt, final_meta, judge_prompt

    lib_path = Path(a.rubric_library) if a.rubric_library else Path(pairs_file).with_name("rubric_library.jsonl")
    library = {}
    if lib_path.exists():
        library = {r["rubric_id"]: r for r in map(json.loads, open(lib_path))}
    log(f"rubric library: {len(library)} rubrics from {lib_path if library else '(none, using embedded)'}")
    tools_by_agent = {}
    if a.agent_registry:
        for ag in map(json.loads, open(a.agent_registry)):
            tools_by_agent[ag["agent_id"]] = {
                (t.get("name") if isinstance(t, dict) else t):
                    ({"description": t.get("description"), "parameters": t.get("parameters")}
                     if isinstance(t, dict) else {})
                for t in ag.get("tools", [])}
    weights = {k: int(v) for k, v in (x.split(":") for x in a.context_formats.split(","))}
    bad_fmt = set(weights) - set(CONTEXT_FORMATS)
    if bad_fmt:
        raise SystemExit(f"unknown --context-formats {sorted(bad_fmt)}")
    cweights = contracts.parse_weights(a.output_contracts or contracts.DEFAULT_WEIGHTS)
    splits = set((a.splits or "train,test").split(","))

    pairs = [json.loads(l) for l in open(pairs_file)]
    if a.limit:
        pairs = pairs[:a.limit]
    log(f"{len(pairs)} pairs")

    prompts, meta, skipped = [], [], []
    for pair in pairs:
        emb = pair.get("rubric", {})
        rubric = library.get(emb.get("rubric_id")) if library else emb
        why = None
        if rubric is None:  # an embedded copy would carry a stale rendering
            why = "rubric not in the library"
        elif rubric.get("exclude_reason"):
            why = f"rubric excluded: {rubric['exclude_reason']}"
        elif rubric.get("split", "train") not in splits:
            why = f"rubric split {rubric.get('split')} not selected"
        elif len(rubric.get("score_enum") or []) > 20:
            why = "scale has more than 20 levels"
        if why:
            skipped.append({"id": pair["id"], "ok": False, "stage": "rubric", "why": why})
            continue
        try:
            fmt = pick_format(pair["id"], weights)
            ev, why = build_evidence(pair, rubric, tools_by_agent, fmt)
        except Exception as e:  # one malformed trace must not take down the run
            ev, why = None, f"evidence rendering failed: {type(e).__name__}"
        if ev is None:
            skipped.append({"id": pair["id"], "ok": False, "stage": "evidence", "why": why})
            continue
        ev.pop("_thinking", None)
        judge_p = judge_prompt(rubric, ev)
        prompts.append(annotator_prompt(rubric, ev) if a.allow_na else judge_p)
        meta.append({"pair": pair, "rubric": rubric, "judge_prompt": judge_p})
    reasons = Counter(s["why"] for s in skipped)
    log(f"{len(prompts)} prompts built, {len(skipped)} pairs skipped: {dict(reasons.most_common(5))}")

    log(f"Annotating {len(prompts)} pairs with {teacher}...")
    results = client.map(prompts, max_tokens=a.max_tokens, desc="annotate")

    out = Path(a.out)
    jpath = out.with_name(out.stem + ".judgments.jsonl")
    n_ok = n_na = n_bad = 0
    with open(out, "w") as f, open(jpath, "w") as jf:
        for s in skipped:
            jf.write(json.dumps(s, ensure_ascii=False) + "\n")
        for r, m in zip(results, meta):
            pair, rubric = m["pair"], m["rubric"]
            row = {"id": pair["id"], "rubric_id": rubric.get("rubric_id"), "level": rubric.get("level"),
                   "severity": pair.get("severity"), "score_enum": rubric.get("score_enum"),
                   "teacher": teacher}
            if not r.ok or not r.text:
                n_bad += 1
                jf.write(json.dumps({**row, "ok": False, "stage": "call",
                                     "why": r.error or "empty reply"}) + "\n")
                continue
            enum_out = rubric.get("output_enum") or rubric.get("score_enum", [])
            j = parse(r.text, enum_out, extract_json)
            if not j.get("ok"):
                n_bad += 1
                jf.write(json.dumps({**row, "ok": False, "stage": "parse", "why": j.get("why"),
                                     "reply_head": r.text[:200]}, ensure_ascii=False) + "\n")
                continue
            value, label = j["score"], j["score"]
            numeric_out = enum_out and not isinstance(enum_out[0], str)
            if numeric_out and not j["na"]:  # the compact layout answers a numerical scale by value
                value = float(j["score"])
                label = next((s["label"] for s in rubric.get("scale", [])
                              if abs(float(s.get("value", 1e9)) - value) < 1e-9), j["score"])
            jf.write(json.dumps({**row, "ok": True, "na": j["na"], "score": label,
                                 "reasoning": j["reasoning"]}, ensure_ascii=False) + "\n")
            if j["na"]:
                n_na += 1
                continue
            contract = contracts.pick(pair["id"], cweights)
            train_prompt = contracts.apply(m["judge_prompt"], contract, enum_out)
            if train_prompt is None:
                contract, train_prompt = "native", m["judge_prompt"]
            n_ok += 1
            f.write(json.dumps({
                "id": pair["id"],
                "prompt": [{"role": "user", "content": train_prompt}],
                "completion": [{"role": "assistant",
                                "content": contracts.target(j["reasoning"], value, contract)}],
                "meta": final_meta({**rubric, "agent_id": pair.get("agent_id"), "verdict": label,
                                    "output_contract": contract, "teacher": teacher}),
            }, ensure_ascii=False) + "\n")
    log(f"{n_ok} training records -> {out}; N/A {n_na}, failed {n_bad}, skipped {len(skipped)}; "
        f"judgments -> {jpath}")

