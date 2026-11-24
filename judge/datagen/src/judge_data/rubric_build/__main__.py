"""CLI: build a rubric library from a concept list, or from seed rubrics.

From a concept list (the open release ships concepts, not seed rubrics):

    python -m judge_data.rubric_build --concepts concepts.jsonl --out out/rubric_library.jsonl \\
        --presentations 3 --backend vllm --base-url http://localhost:8000/v1 \\
        --model-id MiMo-V2.6-Pro-MOPD

From seed rubrics (clean room: only a short concept label crosses over, never seed prose):

    python -m judge_data.rubric_build --seeds seed_rubrics.jsonl --out out/rubric_library.jsonl \\
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

Stages: [seeds -> concept labels -> clean room relabel -> cluster into a registry ->
optional judgeability filter] -> rubrics per concept, rendered -> schema and placeholder checks ->
clean room n-gram check versus the seeds -> optional functional test -> repairs and held out
splits cut by concept, scale family and language -> library JSONL.

Writes next to --out: concepts.jsonl (the concept list actually used, reusable with --concepts)
and rubric_build_report.json.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from judge_data.clients import add_backend_args, client_from_args
from judge_data.rubric_build import assemble, embed, extract, library, validate
from judge_data.utils.io import log, read_jsonl, write_jsonl


def concepts_from_seeds(seeds: list[dict], client, a) -> tuple[list[dict], dict]:
    for i, s in enumerate(seeds):
        s.setdefault("rubric_idx", i)
    extracted = extract.batch_extract_concepts(seeds, client)
    log(f"{len(extracted)} concept labels from {len(seeds)} seed rubrics")

    # Clean room: a label that shares a long phrase with its own seed is restated.
    by_idx = {str(s["rubric_idx"]): s for s in seeds}
    relabelled = 0
    for c in extracted:
        src = validate.seed_text(by_idx.get(str(c["rubric_idx"]), {}))
        new = validate.relabel_if_copied(c["concept"], src, client)
        if new != c["concept"]:
            c["concept"] = new
            relabelled += 1
    log(f"{relabelled} labels restated because they copied seed wording")

    if a.no_cluster:
        registry = list({c["concept"]: c for c in extracted}.values())
        for i, c in enumerate(registry):
            c["concept_id"] = f"cn{i:05d}"
    else:
        vecs = embed.embed_texts([c["concept"] for c in extracted], embed.embedder_from_args(a))
        registry = extract.cluster_concepts(extracted, vecs, threshold=a.cluster_threshold)
    log(f"{len(registry)} concepts in the registry")

    rejected: list[dict] = []
    if a.filter_unjudgeable:
        registry, rejected = extract.filter_unjudgeable(registry, client)
        log(f"{len(registry)} judgeable concepts, {len(rejected)} dropped")

    concepts = library.normalise_concepts([{
        "concept_id": c["concept_id"], "concept": c["concept"], "level": c.get("level", "TRACE")}
        for c in registry])
    return concepts, {"extracted": len(extracted), "relabelled": relabelled,
                      "registry": len(registry), "rejected_unjudgeable": len(rejected)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--concepts", help="Concept list JSONL (concept_id, concept, level, domain)")
    src.add_argument("--seeds", help="Seed rubrics JSONL (rubric_idx, metric_name, definition, ...)")
    ap.add_argument("--out", required=True, help="Output rubric library JSONL")
    ap.add_argument("--presentations", type=int, default=1,
                    help="Rubrics generated per concept, each a different scale and presentation")
    ap.add_argument("--no-cluster", action="store_true",
                    help="--seeds: dedupe labels by exact text instead of embedding clustering")
    ap.add_argument("--cluster-threshold", type=float, default=0.30,
                    help="--seeds: cosine distance threshold for clustering (default 0.30)")
    ap.add_argument("--filter-unjudgeable", action="store_true",
                    help="--seeds: drop concepts a judge cannot settle from trace evidence alone")
    ap.add_argument("--cleanroom-ngram", type=int, default=8,
                    help="--seeds: drop generated rubrics sharing a word n-gram of this length "
                         "with any seed rubric (0 disables the check)")
    ap.add_argument("--functional-test", type=int, default=0,
                    help="Run this many sampled rubrics once on canned evidence and report how "
                         "many return a parseable in-scale verdict")
    assemble.add_split_args(ap)
    ap.add_argument("--seed", type=int, default=2026)
    add_backend_args(ap)
    embed.add_embed_args(ap)
    a = ap.parse_args()

    client = client_from_args(a)
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    report: dict = {"inputs": {"concepts": a.concepts, "seeds": a.seeds}}

    seeds: list[dict] = []
    if a.seeds:
        seeds = read_jsonl(a.seeds)
        log(f"{len(seeds)} seed rubrics")
        concepts, report["concepts"] = concepts_from_seeds(seeds, client, a)
    else:
        concepts = library.load_concepts(a.concepts)
        log(f"{len(concepts)} concepts, levels {dict(Counter(c['level'] for c in concepts))}")
    write_jsonl(out.parent / "concepts.jsonl", library.concept_rows(concepts))

    rubrics, report["generation"] = library.rubrics_from_concepts(
        concepts, client, rng, presentations=a.presentations)
    log(f"{len(rubrics)} rubrics rendered: {report['generation']}")

    if seeds and a.cleanroom_ngram:
        cr = validate.cleanroom_check(rubrics, [validate.seed_text(s) for s in seeds],
                                      n=a.cleanroom_ngram)
        bad = set(cr["failed_ids"])
        rubrics = [r for r in rubrics if r["rubric_id"] not in bad]
        report["cleanroom"] = cr
        log(f"clean room: {len(bad)} of {cr['checked']} rubrics shared a {a.cleanroom_ngram}-gram "
            f"with the seeds and were dropped")

    if a.functional_test:
        sample = rng.sample(rubrics, min(a.functional_test, len(rubrics)))
        res = [validate.functional_test(r, client) for r in sample]
        report["functional_test"] = {"run": len(res), "parsed": sum(x["parsed"] for x in res),
                                     "in_enum": sum(x["in_enum"] for x in res)}
        log(f"functional test: {report['functional_test']}")

    rubrics, repairs = assemble.repair(rubrics)
    rubrics = assemble.split_from_args(rubrics, a)
    summary = validate.check_corpus(rubrics)
    report["corpus"] = {**assemble.corpus_stats(rubrics), "repairs": dict(repairs),
                        "schema_errors": summary["schema_errors"],
                        "duplicate_ids": summary["duplicate_ids"]}
    assemble.write_corpus(rubrics, str(out))
    (out.parent / "rubric_build_report.json").write_text(json.dumps(report, indent=2,
                                                                    ensure_ascii=False))
    log(f"wrote {len(rubrics)} rubrics -> {out}: {report['corpus']}")


if __name__ == "__main__":
    main()
