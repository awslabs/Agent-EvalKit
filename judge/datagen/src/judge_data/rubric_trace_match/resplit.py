"""Decide which annotated records are held out, and from what.

The library's per rubric `split` field cannot express everything on its own. It cannot express "a
seen rubric on an unseen trace", which is a property of the trace, not of the rubric. So holdout is
decided here, on three keys, and a record belongs to exactly one of them.

  test_trace   Chosen by a hash of the trace id, over every trace in the records. Every record on a
               chosen trace is held out whatever its rubric, because a trace that appears in
               training is not an unseen trace.

  test_lang    Every rubric whose language the library held out. Indivisible: a single rubric of
               that language in training destroys the probe for all the others. Written as its own
               file, and `--fold-lang-into-train` gives it up on purpose.

  test_axis    Held out on concept or scale family. Sized to a budget by keeping whole concept
               groups chosen by hash, never individual rubrics, because moving one rubric of a held
               out concept into training contaminates every other rubric of that concept.

Precedence when a record qualifies for more than one: trace, then language, then axis.

A library rubric in the train split never moves to test_lang or test_axis. A language or scale
family that a train rubric carries is therefore not held out, and the plan says so.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from judge_data.rubric_build.render import scale_family

# Traces are picked out of 10,000 buckets, so the cut is in hundredths of a percent.
TRACE_CUT = 500                     # 5.0 percent of the traces
KEEP_SCALE_FAMILIES = {"wide_14"}   # held out scale families kept as test_axis
N_CONCEPTS = 30                     # held out concepts kept as test_axis, chosen by hash


def bucket(s: str, salt: str) -> int:
    return int(hashlib.md5(f"{s}:{salt}".encode()).hexdigest()[:8], 16) % 10000


def rubric_info(r: dict) -> dict:
    """The split relevant attributes of one library rubric."""
    return {
        "concept": r.get("concept_id"),
        "scale_family": scale_family(r.get("scale_type", ""), r.get("n_levels", 0)),
        "language": r.get("language") or "en", "domain": r.get("domain") or "general",
        "split": r.get("split", "train"), "holdout": set(r.get("holdout_axes") or []),
    }


def load_info(library_path: Path) -> dict[str, dict]:
    info = {}
    for line in Path(library_path).open():
        if line.strip():
            r = json.loads(line)
            info[r["rubric_id"]] = rubric_info(r)
    return info


def plan(library_path: Path, trace_ids: set[str], trace_cut: int = TRACE_CUT,
         scale_families: set[str] | None = None, n_concepts: int = N_CONCEPTS) -> dict:
    """Return the rubric and trace sets that define each held out group."""
    info = load_info(library_path)
    flagged = [k for k, v in info.items() if v["split"] == "test"]
    train_langs = {v["language"] for v in info.values() if v["split"] != "test"}
    train_families = {v["scale_family"] for v in info.values() if v["split"] != "test"}

    # Membership is decided by held out attribute VALUES, not by which axis a rubric was flagged on.
    # A rubric carries a concept, a scale family and a language whether or not it was flagged on
    # each, so choosing rubrics by their flag lets a value escape on an unflagged axis. Deciding by
    # value makes the guarantee structural: if a value is held out, every rubric carrying it is held
    # out, so the value cannot appear in training by any route. A value a train rubric carries
    # cannot be held out, so it is dropped from the plan rather than pulling that rubric out of train.
    want_langs = {info[k]["language"] for k in flagged if "language" in info[k]["holdout"]}
    want_families = set(KEEP_SCALE_FAMILIES if scale_families is None else scale_families)
    held_langs = want_langs - train_langs
    held_families = want_families - train_families
    concepts = sorted({info[k]["concept"] for k in flagged
                       if "concept" in info[k]["holdout"]})
    kept_concepts = set(sorted(concepts, key=lambda c: (bucket(c, "cpick"), c))[:n_concepts])

    lang_rubrics, axis_rubrics = set(), set()
    for k, v in info.items():
        if v["language"] in held_langs:
            lang_rubrics.add(k)
        elif v["scale_family"] in held_families or v["concept"] in kept_concepts:
            axis_rubrics.add(k)

    test_traces = {t for t in trace_ids if bucket(t, "tracesplit") < trace_cut}
    return {"info": info, "test_lang_rubrics": lang_rubrics, "test_axis_rubrics": axis_rubrics,
            "test_traces": test_traces, "kept_concepts": kept_concepts,
            "held_families": held_families, "held_langs": held_langs,
            "not_held": {"languages": sorted(want_langs - held_langs),
                         "scale_families": sorted(want_families - held_families)}}


def assign(meta: dict, p: dict, fold_lang_into_train: bool = False) -> str:
    """Which split one record belongs to. Precedence: trace, language, axis, train."""
    if meta.get("trace_id") in p["test_traces"]:
        return "test_trace"
    rid = meta["rubric_id"]
    if rid in p["test_lang_rubrics"] and not fold_lang_into_train:
        return "test_lang"
    if rid in p["test_axis_rubrics"]:
        return "test_axis"
    return "train"


def check(records: list[dict], p: dict, fold_lang_into_train: bool = False) -> list[str]:
    """Contamination checks. Each states a guarantee the split claims to provide.

    These are assertions rather than diagnostics. A split whose guarantee silently fails is worse
    than no split, because every number measured on it reads as generalisation when it is
    memorisation. Concept, language and scale family come from the library via `p["info"]`, so a
    record needs only `rubric_id`, `trace_id` and `split` in its meta.
    """
    problems = []
    info = p["info"]
    train_traces, train_rubrics, train_langs, train_concepts, train_families = (
        set(), set(), set(), set(), set())
    for r in records:
        m = r["meta"]
        if m["split"] != "train":
            continue
        v = info.get(m.get("rubric_id")) or {}
        train_traces.add(m.get("trace_id"))
        train_rubrics.add(m.get("rubric_id"))
        train_langs.add(v.get("language") or "en")
        train_concepts.add(v.get("concept"))
        train_families.add(v.get("scale_family"))

    bad = train_traces & p["test_traces"]
    if bad:
        problems.append(f"{len(bad)} held out traces also appear in train")
    held_rubrics = p["test_axis_rubrics"] | (set() if fold_lang_into_train else p["test_lang_rubrics"])
    bad = train_rubrics & held_rubrics
    if bad:
        problems.append(f"{len(bad)} held out rubrics also appear in train")

    # A held out language must not be in train at all, otherwise the probe measures nothing. Folding the
    # language back into train (--fold-lang-into-train) gives that probe up on purpose.
    bad = set() if fold_lang_into_train else p["held_langs"] & train_langs
    if bad:
        problems.append(f"held out language(s) {sorted(bad)} appear in train")

    # The chosen values must be wholly absent from train. Checked on what was chosen, not
    # on what the kept rubrics happen to carry, because the latter is the mistake this guards.
    bad = p["kept_concepts"] & train_concepts
    if bad:
        problems.append(f"{len(bad)} held out concepts also appear in train, "
                        f"for example {sorted(bad)[:3]}")
    bad = p["held_families"] & train_families
    if bad:
        problems.append(f"held out scale families {sorted(bad)} also appear in train")
    return problems


def report(records: list[dict]) -> None:
    levels = ("SESSION", "TRACE", "TOOL_CALL")
    per = defaultdict(Counter)
    for r in records:
        per[r["meta"]["split"]][r["meta"]["level"]] += 1
    tot_by = Counter()
    for c in per.values():
        tot_by.update(c)
    print(f"\n  {'split':12s} {'total':>9s} " + " ".join(f"{lv:>14s}" for lv in levels))
    for sp in ("train", "test_trace", "test_axis", "test_lang"):
        c = per.get(sp)
        if not c:
            continue
        cells = " ".join(f"{c[lv]:8,d} {100*c[lv]/max(tot_by[lv],1):4.1f}%" for lv in levels)
        print(f"  {sp:12s} {sum(c.values()):9,d} {cells}")
    held = sum(sum(c.values()) for sp, c in per.items() if sp != "train")
    tot = sum(tot_by.values())
    print(f"  held out in total: {held:,} of {tot:,} ({100 * held / max(tot, 1):.1f}%)")
