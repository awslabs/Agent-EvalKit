"""CLI: match a rubric library to a trace pool. Produces pairs and stops there.

    python -m judge_data.rubric_trace_match.run \\
        --rubric-library out/rubric_library.jsonl --traces trace_pool.jsonl \\
        --traces-limit 2000 --cap 6 --out out/match \\
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

The trace pool is any JSONL of traces in the normalised Trace schema (see
`judge_data.traces`). Stages, each resumable:

1. Rubric features: which behaviours a trace must show for the rubric to apply (one call each).
2. Trace features: which behaviours each trace shows, its domains, and the turns and tool calls
   most worth judging (one call each).
3. Selection (pure): score every trace for every rubric, gate by level, pick the target turn or
   call, take the top `--cap` under a per agent cap. When a rubric has a labelled ground truth
   dimension in the pool, positives and negatives are mixed.

Outputs in --out: pairs.jsonl and traces.jsonl. Pass the directory to `python -m judge_data.annotate --pairs`.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from judge_data.clients import add_backend_args, client_from_args
from judge_data.rubric_trace_match import match, sample
from judge_data import traces as tr
from judge_data.utils import stage
from judge_data.utils.io import read_jsonl
from judge_data.utils.jsonx import extract_json


def pick_rubrics(recs: list[dict], n: int | None, seed: int) -> list[dict]:
    """All rubrics, or `n` of them spread over level and placeholder style."""
    if not n:
        return recs
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for r in recs:
        buckets[(r.get("level"), "<<" in r.get("rendered_prompt", ""))].append(r)
    keys = sorted(buckets, key=str)
    out, i = [], 0
    while len(out) < n and any(buckets[k] for k in keys):
        k = keys[i % len(keys)]
        if buckets[k]:
            out.append(buckets[k].pop(rng.randrange(len(buckets[k]))))
        i += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubric-library", required=True, help="Rubric library JSONL")
    ap.add_argument("--traces", required=True, help="Trace pool JSONL (normalised Trace schema)")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--rubrics", type=int, default=0, help="Use only this many rubrics (0 = all)")
    ap.add_argument("--splits", default=None,
                    help="Only rubrics in these library splits, comma separated (default: all)")
    ap.add_argument("--traces-limit", type=int, default=0,
                    help="Sample this many traces from the pool (0 = all)")
    ap.add_argument("--strata", default="topic,flow_type",
                    help="Trace tags to stratify on, comma separated")
    ap.add_argument("--cap", type=int, default=6, help="Traces per rubric")
    ap.add_argument("--max-per-agent", type=int, default=6, help="Per rubric, traces per agent")
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--seed", type=int, default=2026)
    add_backend_args(ap)
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    client = client_from_args(a)

    splits = set(a.splits.split(",")) if a.splits else None
    recs = [r for r in pick_rubrics(read_jsonl(a.rubric_library), a.rubrics or None, a.seed)
            if splits is None or r.get("split", "train") in splits]
    print(f"rubrics: {len(recs)}  by level {dict(Counter(r.get('level') for r in recs))}")

    pool = tr.load_jsonl(a.traces)
    keys = tuple(k for k in a.strata.split(",") if k)
    if a.traces_limit and a.traces_limit < len(pool):
        chosen = sample.stratified(pool, a.traces_limit, seed=a.seed, keys=keys)
        sample.report(chosen, pool, keys)
    else:
        chosen = pool
    tdicts = [t.as_dict() for t in chosen]
    label_dims = {k for t in tdicts for k in (t.get("target_labels") or {})}
    for r in recs:
        r["ground_truth_dim"] = match.ground_truth_dim(r, label_dims)
    print(f"traces: {len(tdicts)}  with tool calls {sum(1 for t in tdicts if t['tool_calls'])}  "
          f"with ground truth labels {sum(1 for t in tdicts if t['target_labels'])}")

    # Stage 1: rubric features.
    def rubric_work(item):
        r = client.invoke(match.build_rubric_prompt(item["rec"]), max_tokens=3000)
        obj = extract_json(r.text) if r.ok else None
        if not isinstance(obj, dict):
            return {"id": item["id"], "error": r.error or "unparseable"}
        return {"id": item["id"], "features": obj}

    stage.run_stage([{"id": r["rubric_id"], "rec": r} for r in recs],
                    out / "rubric_features.jsonl", rubric_work, workers=a.workers,
                    desc="rubric-features")
    rfeat = {k: v["features"] for k, v in stage.load_by_id(out / "rubric_features.jsonl").items()
             if v.get("features")}

    # Stage 2: trace features.
    def trace_work(item):
        t = item["t"]
        r = client.invoke(match.build_trace_prompt(t, tr.render_context(tr.from_dict(t))),
                          max_tokens=4000)
        obj = extract_json(r.text) if r.ok else None
        if not isinstance(obj, dict):
            return {"id": item["id"], "error": r.error or "unparseable"}
        return {"id": item["id"], "features": obj}

    stage.run_stage([{"id": t["trace_id"], "t": t} for t in tdicts],
                    out / "trace_features.jsonl", trace_work, workers=a.workers,
                    desc="trace-features")
    tfeat = {k: v["features"] for k, v in stage.load_by_id(out / "trace_features.jsonl").items()
             if v.get("features")}
    print(f"features: {len(rfeat)} rubrics, {len(tfeat)} traces")

    # Stage 3: selection. Pure, so it is cheap to redo and is not cached.
    tby = {t["trace_id"]: t for t in tdicts}
    pairs, per_rubric = [], Counter()
    for r in recs:
        rf = rfeat.get(r["rubric_id"])
        if not rf:
            continue
        sel = match.select_for_rubric(r, rf, tdicts, tfeat, a.cap, a.max_per_agent)
        per_rubric[r["rubric_id"]] = len(sel)
        dim = r["ground_truth_dim"]
        for s in sel:
            t = tby.get(s["trace_id"])
            gt = (t.get("target_labels") or {}).get(dim) if dim and t and match.is_primary(t, dim) \
                else None
            pairs.append({**s, "id": f"{r['rubric_id']}|{s['trace_id']}", "source": "matching",
                          "rubric_id": r["rubric_id"], "ground_truth_dim": dim,
                          "ground_truth_label": gt})
    (out / "pairs.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs))
    zero = [rid for rid, k in per_rubric.items() if k == 0]
    print(f"pairs: {len(pairs)}  rubrics with no trace: {len(zero)} of {len(recs)}")

    with (out / "traces.jsonl").open("w") as f:
        for t in tdicts:
            f.write(json.dumps({"id": t["trace_id"], "trace": t}, ensure_ascii=False) + "\n")
    print(f"wrote {out / 'traces.jsonl'} with {len(tdicts)} traces")
    print(f"tokens in={client.total_in} out={client.total_out}")
    print(f"\nnext: python -m judge_data.annotate --pairs {out} "
          f"--rubric-library {a.rubric_library} --out <annotated_dir>")


if __name__ == "__main__":
    main()
