"""CLI: assemble annotated records into training files laid out for data ablation.

    python -m judge_data.rubric_trace_match.assemble --annotated out/annotated \
        --rubric-library out/rubric_library.jsonl --out out/training

One file holds every record, because a single source of truth avoids copies drifting apart. Beside
it go materialised cuts for the splits (train, test_trace, test_axis, test_lang, see `resplit`),
id lists per axis value under slices/, and manifest.json.

Every written record is `{id, prompt, completion, meta}` with `meta` holding
`rubric_id, concept, level, n_levels, output_contract, agent_id, verdict, split, teacher`. The
other keys of an annotated record are used for splitting and slicing here and are not written.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from judge_data.annotate.prompt import final_meta
from judge_data.rubric_trace_match import resplit
from judge_data.utils import stage

# The axes worth pre-cutting. Everything else is reachable from the id lists.
# Every split gets its own file. The three held out sets measure different things and pooling them
# into one "test" number would average an unseen concept with an unseen trace.
MATERIALISE = ["train", "test_trace", "test_axis", "test_lang"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annotated", action="append", required=True,
                    help="An annotation output directory (annotate on matched pairs), repeatable")
    ap.add_argument("--rubric-library", required=True, help="Rubric library JSONL, for resplitting")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default=None, help="File stem, default is the output directory name")
    ap.add_argument("--keep-na", action="store_true",
                    help="Keep N/A judgements in the training file. Off by default: a prompt's "
                         "score enum never contains N/A, so a target of N/A is a value the "
                         "prompt's own schema forbids. They are written to a separate file.")
    ap.add_argument("--no-fence", action="store_true",
                    help="store the target as bare JSON instead of fenced")
    ap.add_argument("--keep-corpus-split", action="store_true",
                    help="Use the library's per rubric split field as is. Off by default because "
                         "it cannot express a held out trace set")
    ap.add_argument("--fold-lang-into-train", action="store_true",
                    help="Put the held out language back into training")
    ap.add_argument("--trace-cut", type=int, default=resplit.TRACE_CUT,
                    help="Per 10,000 traces, how many are held out as test_trace")
    ap.add_argument("--axis-scale-families", default=",".join(sorted(resplit.KEEP_SCALE_FAMILIES)),
                    help="Held out scale families kept in test_axis, comma separated")
    ap.add_argument("--axis-concepts", type=int, default=resplit.N_CONCEPTS,
                    help="Held out concepts kept in test_axis")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    # Clear the slice directory rather than writing over it. A rerun that no longer produces some
    # axis value leaves the previous run's file behind, and a stale slice names records that are
    # not in the main file at all.
    slices = out / "slices"
    if slices.exists():
        for old_slice in slices.glob("*.txt"):
            old_slice.unlink()
    slices.mkdir(exist_ok=True)
    stem = a.name or out.name

    rows: dict[str, dict] = {}
    provenance = []
    for d in a.annotated:
        p = Path(d) / "annotated.jsonl"
        found = 0
        for k, v in stage.load_by_id(p).items():
            if not v.get("ok"):
                continue
            v["meta"]["source"] = v["meta"].get("source") or "matching"
            rows[k] = v
            found += 1
        provenance.append({"dir": str(d), "usable_records": found})
        print(f"{d}: {found} usable")

    recs = list(rows.values())

    # Wrap the target in a fence, matching the instruction the rubric's output block carries:
    # "Do not return any preamble or explanations, return only a pure JSON string surrounded by
    # triple backticks". Bare JSON would train the model to ignore that instruction.
    if not a.no_fence:
        for r in recs:
            c = r["completion"][0]["content"]
            if not c.lstrip().startswith("```"):
                r["completion"][0]["content"] = f"```json\n{c}\n```"

    # N/A goes to its own file. Kept rather than deleted, because a judge that declines when a
    # rubric does not apply is a real behaviour and the records are expensive to reproduce.
    na = [r for r in recs if r["meta"]["is_na"]]
    if not a.keep_na:
        recs = [r for r in recs if not r["meta"]["is_na"]]
        na_path = out / f"{stem}.na.jsonl"
        with na_path.open("w") as f:
            for r in na:
                f.write(json.dumps({"id": r["id"], "prompt": r["prompt"],
                                    "completion": r["completion"], "meta": final_meta(r["meta"])},
                                   ensure_ascii=False) + "\n")
        print(f"held back {len(na)} N/A records in {na_path.name}, not part of training")

    # Recompute the split. See resplit.py for why the library field alone cannot do this.
    info = resplit.load_info(Path(a.rubric_library))
    if not a.keep_corpus_split:
        trace_ids = {r["meta"]["trace_id"] for r in recs}
        plan = resplit.plan(Path(a.rubric_library), trace_ids, trace_cut=a.trace_cut,
                            scale_families={x for x in a.axis_scale_families.split(",") if x},
                            n_concepts=a.axis_concepts)
        print(f"\nresplit: {len(plan['test_traces']):,} held out traces of "
              f"{len(trace_ids):,}, {len(plan['test_axis_rubrics'])} axis rubrics "
              f"over {len(plan['kept_concepts'])} concepts, "
              f"{len(plan['test_lang_rubrics'])} language rubrics")
        if any(plan["not_held"].values()):
            print(f"  not held out because a train rubric carries them: {plan['not_held']}")
        for r in recs:
            r["meta"]["split"] = resplit.assign(r["meta"], plan, a.fold_lang_into_train)
        problems = resplit.check(recs, plan, a.fold_lang_into_train)
        resplit.report(recs)
        if problems:
            # Refuse to write. A contaminated split turns every later measurement into a claim about
            # memorisation that reads as a claim about generalisation.
            for pr in problems:
                print(f"  CONTAMINATION: {pr}")
            raise SystemExit("split is contaminated, nothing written")
        print("  contamination checks passed")

    # Stable order so the file is reproducible: source, level, id.
    recs.sort(key=lambda r: (r["meta"]["source"], r["meta"]["level"], r["id"]))

    main_path = out / f"{stem}.jsonl"
    with main_path.open("w") as f:
        for r in recs:
            f.write(json.dumps({"id": r["id"], "prompt": r["prompt"],
                                "completion": r["completion"], "meta": final_meta(r["meta"])},
                               ensure_ascii=False) + "\n")
    print(f"\nwrote {main_path} with {len(recs)} records, "
          f"{main_path.stat().st_size / 1e6:.1f} MB")

    for split in MATERIALISE:
        sub = [r for r in recs if r["meta"]["split"] == split]
        p = out / f"{stem}.{split}.jsonl"
        with p.open("w") as f:
            for r in sub:
                f.write(json.dumps({"id": r["id"], "prompt": r["prompt"],
                                    "completion": r["completion"], "meta": final_meta(r["meta"])},
                                   ensure_ascii=False) + "\n")
        print(f"  {p.name}: {len(sub)} records")

    # Id lists for every axis an ablation is likely to cut on.
    def lib(m: dict, k: str) -> str:
        return (info.get(m["rubric_id"]) or {}).get(k) or "unknown"

    axes = {
        "source": lambda m: m["source"],
        "level": lambda m: m["level"],
        "scale_family": lambda m: lib(m, "scale_family"),
        "language": lambda m: lib(m, "language"),
        "domain": lambda m: lib(m, "domain"),
        "is_na": lambda m: "na" if m["is_na"] else "scored",
        # The evidence format axes. Without these the scrub policy is a hidden variable: the
        # data would contain both regimes and offer no way to cut on them.
        "thinking_stripped": lambda m: m.get("thinking_stripped") or "unknown",
        "context_layout": lambda m: m.get("context_layout") or "unknown",
    }
    manifest_axes: dict[str, dict[str, int]] = {}
    for axis, key in axes.items():
        groups: dict[str, list[str]] = defaultdict(list)
        for r in recs:
            groups[str(key(r["meta"]))].append(r["id"])
        manifest_axes[axis] = {k: len(v) for k, v in sorted(groups.items())}
        for val, ids in groups.items():
            safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in val)[:60]
            (out / "slices" / f"{axis}={safe}.txt").write_text("\n".join(ids) + "\n")

    # Cross tabulations that a reader actually wants at a glance.
    cross = {
        "source_x_level": Counter(f"{r['meta']['source']}|{r['meta']['level']}" for r in recs),
        "source_x_na": Counter(f"{r['meta']['source']}|"
                               f"{'na' if r['meta']['is_na'] else 'scored'}" for r in recs),
        # Length versus reasoning presence, which is the confound the strip policy exists to
        # break. A long and fully stripped cell that is empty here means the policy did not work.
        "reasoning_x_length": Counter(
            f"{r['meta'].get('thinking_stripped')}|"
            f"{'long' if len(r['prompt'][0]['content']) >= 20000 else 'short'}"
            for r in recs),
        "level_x_reasoning": Counter(
            f"{r['meta']['level']}|{r['meta'].get('thinking_stripped')}" for r in recs),
    }

    manifest = {
        "records": len(recs),
        "main_file": main_path.name,
        "target_format": "bare_json" if a.no_fence else "fenced_json",
        "na_records_held_back": 0 if a.keep_na else len(na),
        "na_file": None if a.keep_na else f"{stem}.na.jsonl",
        "materialised_splits": {s: sum(1 for r in recs if r["meta"]["split"] == s)
                                for s in MATERIALISE},
        "teacher": sorted({r["meta"].get("teacher") or "?" for r in recs}),
        "inputs": provenance,
        "axes": manifest_axes,
        "cross_tabs": {k: dict(sorted(v.items())) for k, v in cross.items()},
        "slice_files": "slices/<axis>=<value>.txt, one record id per line",
        "note": ("Every record is one rubric applied to one trace and judged by the teacher. The "
                 "completion is the training target. The slices say whether the trace was found "
                 "by matching or built by synthesis."),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nmanifest: {out / 'manifest.json'}")
    for k, v in cross.items():
        print(f"  {k}: {dict(sorted(v.items()))}")


if __name__ == "__main__":
    main()
