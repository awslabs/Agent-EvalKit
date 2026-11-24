"""CLI: fill the SESSION and TOOL_CALL gap of a rubric library.

A library extracted from public seed rubrics is mostly TRACE level, because most seed rubrics judge
a single response. This authors concepts per category (`extract.AUTHOR_PLAN`), drops concepts that
near duplicate a concept already in the library or another authored concept, drops concepts trace
evidence cannot settle, and writes several presentations per concept. Only the new rubrics are
written, so the existing library and its traces stay untouched. It also audits the existing
library's concepts with the judgeability check so records built on them can be filtered.

    python -m judge_data.rubric_build.gapfill \\
        --library out/rubric_library.jsonl --out out/gapfill_library.jsonl \\
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

Writes next to --out: gapfill_concepts.json (kept and rejected concepts), gapfill_concepts.jsonl
(the kept concepts as a concept list) and library_audit.jsonl.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from judge_data.clients import add_backend_args, client_from_args
from judge_data.rubric_build import assemble, embed, extract, library
from judge_data.utils.io import log, read_jsonl, write_jsonl


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", required=True, help="Existing rubric library JSONL")
    ap.add_argument("--out", required=True, help="Output JSONL of the new rubrics only")
    ap.add_argument("--presentations", type=int, default=5, help="Rubrics per authored concept")
    ap.add_argument("--plan-scale", type=float, default=1.0,
                    help="Multiply the per category authoring targets of extract.AUTHOR_PLAN")
    ap.add_argument("--near-dup", type=float, default=0.90,
                    help="Cosine similarity above which an authored concept counts as a duplicate")
    ap.add_argument("--no-audit", action="store_true", help="Skip auditing the existing library")
    assemble.add_split_args(ap)
    ap.add_argument("--seed", type=int, default=11)
    add_backend_args(ap)
    embed.add_embed_args(ap)
    a = ap.parse_args()

    client = client_from_args(a)
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lib = read_jsonl(a.library)
    existing = list(dict.fromkeys(r["concept"] for r in lib if r.get("concept")))
    log(f"{len(lib)} rubrics, {len(existing)} concepts, levels "
        f"{dict(Counter(r.get('level') for r in lib))}")

    # 1. Author per category, categories in parallel.
    def author(item):
        cat, level, target, guidance = item
        return extract.author_missing(cat, level, guidance, max(1, round(target * a.plan_scale)),
                                      client)
    with ThreadPoolExecutor(max_workers=len(extract.AUTHOR_PLAN)) as pool:
        authored = [c for got in pool.map(author, extract.AUTHOR_PLAN) for c in got]
    log(f"authored {len(authored)}: {dict(Counter(c['category'] for c in authored))}")

    rejected: list[dict] = []

    # 2. Near duplicates of the existing library or of each other.
    vecs = embed.embed_texts(existing + [c["concept"] for c in authored], embed.embedder_from_args(a))
    old, new = vecs[:len(existing)], vecs[len(existing):]
    sim_old = (new @ old.T).max(axis=1) if len(existing) and len(new) else np.zeros(len(new))
    kept, kept_vecs = [], []
    for c, v, s in zip(authored, new, sim_old):
        if s > a.near_dup:
            rejected.append({**c, "reject_reason": f"near duplicate of the library ({s:.2f})"})
        elif kept_vecs and float(np.max(np.stack(kept_vecs) @ v)) > a.near_dup:
            rejected.append({**c, "reject_reason": "near duplicate of another authored concept"})
        else:
            kept.append(c)
            kept_vecs.append(v)
    log(f"{len(kept)} after near duplicate removal")

    # 3. Concepts trace evidence cannot settle.
    kept, dropped = extract.filter_unjudgeable(kept, client)
    rejected += dropped
    log(f"{len(kept)} after the judgeability filter: {dict(Counter(c['level'] for c in kept))}")

    # 4. Audit the existing library's concepts with the judgeability check.
    if not a.no_audit and existing:
        _ok, bad = extract.filter_unjudgeable([{"concept": c} for c in existing], client)
        why = {d["concept"]: d["reject_reason"] for d in bad}
        write_jsonl(out.parent / "library_audit.jsonl",
                    [{"concept": c, "ok": c not in why, "reject_reason": why.get(c)}
                     for c in existing])
        log(f"library audit: {len(why)} concepts not judgeable from trace evidence")

    # 5. Several presentations per concept, one generation call per concept.
    concepts = library.normalise_concepts([
        {"concept_id": f"gap_{i:04d}", "concept": c["concept"], "level": c["level"],
         "polarity": "defect" if c["category"].startswith("defect_presence") else None}
        for i, c in enumerate(kept)])
    write_jsonl(out.parent / "gapfill_concepts.jsonl", library.concept_rows(concepts))
    rubrics, stats = library.rubrics_from_concepts(concepts, client, rng,
                                                   presentations=a.presentations)
    log(f"{len(rubrics)} rubrics rendered: {stats}")

    rubrics, _repairs = assemble.repair(rubrics)
    rubrics = assemble.split_from_args(rubrics, a)

    assemble.write_corpus(rubrics, str(out))
    (out.parent / "gapfill_concepts.json").write_text(json.dumps(
        {"kept": kept, "rejected": rejected}, indent=1, ensure_ascii=False))
    log(f"wrote {len(rubrics)} rubrics -> {out}; levels {dict(Counter(r['level'] for r in rubrics))}")


if __name__ == "__main__":
    main()
