"""Annotation of matched pairs: directories written by `rubric_trace_match`.

    python -m judge_data.annotate \
        --pairs out/match --rubric-library out/rubric_library.jsonl --out out/annotated \
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

`--pairs` is a directory holding pairs.jsonl and traces.jsonl (the output of `python -m judge_data.rubric_trace_match`), and may be
repeated. Pair ids are `rubric_id|trace_id`, so the union across input directories deduplicates
naturally and a pair produced twice is annotated once.

Evidence format policy, which this stage owns because it is the only place evidence is rendered:

  Target label leakage is removed where it can be removed and the record is dropped where it cannot.
  See `annotate.scrub` for what leaks and why the two cases differ.

  Agent reasoning blocks are removed entirely on a chosen subset (`--strip-list` names pair ids,
  `--strip-pct` picks a hash chosen share of traces that carry reasoning), and only leaky blocks
  are removed elsewhere. Reasoning presence and trace length tend to be confounded in a pool, and a
  subset breaks the confound. The axis is recorded per record as `meta.thinking_stripped`.

  Numbered turn headers are switched off on `--no-label-pct` percent of records, so a model cannot
  anchor on one invented layout.

Output: annotated.jsonl in --out, with `{id, ok, prompt, completion, meta}` per pair. Then run
`rubric_trace_match.assemble`.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from judge_data.annotate import parse as parse_mod
from judge_data.annotate import prompt as prompt_mod
from judge_data.annotate import render, scrub
from judge_data.clients import client_from_args
from judge_data import traces as tr
from judge_data.utils import stage
from judge_data.utils.io import read_jsonl
from judge_data.utils.jsonx import extract_json


def derive_target(rec: dict, t: dict, pair: dict) -> dict | None:
    """Which turn or tool call this rubric is applied to.

    Matching chose the target during selection and carries it on the pair. Synthesis did not,
    because a generated trace has no injected point of interest, so the obvious choice per level is
    made here. Returning None means the pair cannot be annotated at this level.
    """
    if pair.get("target") is not None:
        return pair["target"]
    if rec["level"] == "SESSION":
        return {}
    if rec["level"] == "TRACE":
        for turn in reversed(t["turns"]):
            if turn["assistant"]:
                return {"turn_index": turn["turn_index"]}
        return None
    if not t["tool_calls"]:
        return None
    c = t["tool_calls"][-1]
    return {"turn_index": c["turn_index"], "call_index": c["call_index"]}


def run(a: argparse.Namespace) -> None:
    """Annotate one or more `rubric_trace_match` output directories. `a` comes from
    `annotate.__main__`, with this source's defaults filled in."""

    strip_all_ids: set[str] = set()
    if a.strip_list:
        strip_all_ids = set(Path(a.strip_list).read_text().split())
        print(f"strip list: {len(strip_all_ids):,} records have all reasoning removed")

    drop_rubrics: set[str] = set()
    if a.exclude_rubrics:
        drop_rubrics = set(Path(a.exclude_rubrics).read_text().split())

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pool = client_from_args(a)

    recs = {r["rubric_id"]: r for r in read_jsonl(a.rubric_library)}
    print(f"library: {len(recs)} rubrics from {Path(a.rubric_library).name}")

    pairs: dict[str, dict] = {}
    tby: dict[str, dict] = {}
    for d in a.pairs:
        d = Path(d)
        pp, tt = d / "pairs.jsonl", d / "traces.jsonl"
        if not pp.exists():
            print(f"  {d}: no pairs.jsonl, skipped")
            continue
        n_new = 0
        for p in read_jsonl(pp):
            if p["id"] not in pairs:
                pairs[p["id"]] = p
                n_new += 1
        n_tr = 0
        for row in read_jsonl(tt):
            t = row.get("trace")
            if t and t["trace_id"] not in tby:
                tby[t["trace_id"]] = t
                n_tr += 1
        print(f"  {d.name}: +{n_new} new pairs, +{n_tr} new traces")
    print(f"\ntotal {len(pairs)} distinct pairs over {len(tby)} distinct traces")
    print("  by source:", dict(Counter(p.get("source", "?") for p in pairs.values())))

    missing_trace = [p for p in pairs.values() if p["trace_id"] not in tby]
    if missing_trace:
        print(f"  WARNING {len(missing_trace)} pairs reference a trace that no input directory "
              f"supplied, and are skipped")

    def work(item):
        p = item["pair"]
        rec = recs.get(p["rubric_id"])
        t = tby.get(p["trace_id"])
        if rec is None or t is None:
            return {"id": p["id"], "ok": False, "why": "rubric or trace not found",
                    "permanent": True}
        if p["rubric_id"] in drop_rubrics or rec.get("exclude_reason"):
            return {"id": p["id"], "ok": False, "why": "rubric excluded from training data",
                    "permanent": True}
        missing = render.unfillable(rec)
        if missing:
            return {"id": p["id"], "ok": False,
                    "why": f"template has unfillable placeholders {sorted(missing)}",
                    "permanent": True}
        target = derive_target(rec, t, p)
        if target is None:
            return {"id": p["id"], "ok": False, "why": "no target available at this level",
                    "permanent": True}

        # Reasoning removal. Full removal for the chosen subset, otherwise remove only the blocks
        # that leak, which keeps the agent's ordinary reasoning and takes out the cheat.
        if p["id"] in strip_all_ids or (a.strip_pct and scrub.bit(p["id"], "strip") < a.strip_pct):
            mode, fn = "all", scrub.strip_all
        else:
            mode, fn = "leaky", scrub.strip_leaky
        # A trace with no reasoning to begin with is recorded as untouched whatever the lists say,
        # so the axis separates "reasoning was removed" from "there was never any". The leaky
        # scrub stays in place, so a tag in an unexpected spot is still handled.
        if not any(scrub.has_tag(x["assistant"]) for x in t["turns"]):
            mode, fn = "none", scrub.strip_leaky
        labels = scrub.bit(p["id"], "layout") >= a.no_label_pct
        ev = tr.evidence_for(tr.from_dict(t), rec["level"], target, turn_labels=labels, scrub=fn)
        # Leakage is a property of the evidence, so only the evidence is checked. Checking the whole
        # prompt would also read the rubric, and a rubric can legitimately contain phrases like "the
        # scenario requires" as part of its instructions.
        evidence = ev["context"] + ev.get("assistant_turn", "") + ev.get("tool_turn", "")
        # Whether a leaky block was removed is asked of the text before removal, since the result
        # never leaks once the block is gone.
        if mode == "leaky" and not any(scrub.leaks(x["assistant"]) for x in t["turns"]):
            mode = "none"
        # An opener with no closer, or a closer of a different spelling, leaves the block in place.
        # Such a record would carry reasoning while labelled as stripped, so it is dropped.
        if mode == "all" and scrub.has_tag(evidence):
            return {"id": p["id"], "ok": False, "why": "reasoning markup unbalanced, cannot remove",
                    "permanent": True}
        # A leak that outlives block removal is in a tool result, in a call argument, or in the
        # agent's own prose. Patching those means rewriting trace content, which is a worse trade
        # than losing the record. Checked before the call, so a dropped record costs nothing.
        if scrub.leaks(evidence):
            return {"id": p["id"], "ok": False, "why": "target label leak survives removal",
                    "permanent": True}

        prompt = prompt_mod.judge_prompt(rec, ev)
        # At TRACE level the judged turn is the object of judgement. A turn that is entirely
        # reasoning leaves nothing to judge once reasoning is removed.
        if rec["level"] == "TRACE" and not ev.get("assistant_turn", "").strip():
            return {"id": p["id"], "ok": False, "why": "judged turn empty after reasoning removal",
                    "permanent": True}
        p = {**p, "thinking_stripped": mode,
             "context_layout": "turn_labels" if labels else "no_turn_labels"}

        ann_prompt = prompt_mod.annotator_prompt(rec, ev, allow_na=a.allow_na)
        r = pool.invoke(ann_prompt, max_tokens=a.max_tokens)
        if not r.ok:
            return {"id": p["id"], "ok": False, "why": r.error, "permanent": bool(r.filtered),
                    "trace_id": p["trace_id"]}
        j = parse_mod.parse(r.text, rec.get("output_enum") or rec["score_enum"], extract_json)
        if not j["ok"]:
            return {"id": p["id"], "ok": False, **{k: v for k, v in j.items() if k != "ok"},
                    "reply_head": r.text[:200]}
        rec_out = prompt_mod.sft_record(rec, {**p, "target": target, "teacher": pool.model_id},
                                        j, prompt)
        rec_out["ok"] = True
        return rec_out

    todo = [{"id": p["id"], "pair": p} for p in pairs.values() if p["trace_id"] in tby]
    if a.limit:
        todo = todo[:a.limit]
        print(f"limited to {len(todo)} pairs")
    stage.run_stage(todo, out / "annotated.jsonl", work, workers=a.workers, desc="annotate")

    rows = list(stage.load_by_id(out / "annotated.jsonl").values())
    ok = [x for x in rows if x.get("ok")]
    bad = [x for x in rows if not x.get("ok")]
    na = [x for x in ok if x["meta"]["is_na"]]
    print(f"\nannotated {len(rows)}: scored {len(ok) - len(na)}, N/A {len(na)}, failed {len(bad)}")
    if bad:
        print("  failures:", dict(Counter(str(x.get("why"))[:52] for x in bad)))
        filt = {x["trace_id"] for x in bad if x.get("permanent") and x.get("trace_id")}
        if filt:
            (out / "filtered_traces.txt").write_text("\n".join(sorted(filt)) + "\n")
            print(f"  {len(filt)} traces tripped a guardrail, listed in filtered_traces.txt")
    print("  by source:", dict(Counter(x["meta"]["source"] for x in ok)))
    print("  by level :", dict(Counter(x["meta"]["level"] for x in ok)))
    print("  reasoning removed:", dict(Counter(x["meta"].get("thinking_stripped")
                                               for x in ok)))
    print("  context layout   :", dict(Counter(x["meta"].get("context_layout") for x in ok)))
    print("  replies quoting the agent's reasoning:",
          sum(1 for x in ok if x["meta"].get("reply_quotes_reasoning")))
    print("  N/A rate by level:", {
        lv: round(sum(1 for x in ok if x["meta"]["level"] == lv and x["meta"]["is_na"])
                  / max(sum(1 for x in ok if x["meta"]["level"] == lv), 1), 3)
        for lv in ("SESSION", "TRACE", "TOOL_CALL")})
    print("  N/A rate by source:", {
        s: round(sum(1 for x in ok if x["meta"]["source"] == s and x["meta"]["is_na"])
                 / max(sum(1 for x in ok if x["meta"]["source"] == s), 1), 3)
        for s in ("matching", "synthesis")})
    print(f"tokens in={pool.total_in} out={pool.total_out}")
    print(f"\nnext: python -m judge_data.rubric_trace_match.assemble --annotated {out} "
          f"--rubric-library {a.rubric_library} --out <dir>")

