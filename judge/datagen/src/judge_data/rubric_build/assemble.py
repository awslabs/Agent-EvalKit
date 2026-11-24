"""Corpus assembly and splitting. Pure logic, no LLM.

Takes a collection of rubric records, applies repairs, cuts train and test splits, and writes the
library with a fixed record schema.
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path

from judge_data.rubric_build.render import scale_family

# The fields of a library record, in order. `output_enum` is present only when it differs from
# `score_enum`. `language` and `holdout_axes` are read by `rubric_trace_match.resplit`.
# `exclude_reason` is present only on rubrics a later stage should skip.
LIBRARY_FIELDS = ("rubric_id", "concept_id", "concept", "level", "domain", "language",
                  "scale_type", "n_levels", "score_enum", "output_enum", "scale", "task",
                  "placeholders", "rendered_prompt", "split", "holdout_axes", "exclude_reason")

# Legal placeholders in rubric instructions.
LEGAL_PLACEHOLDERS = {"context", "assistant_turn", "available_tools", "tool_turn", "retrieved_passages"}

# Pattern for invented placeholders that no filler knows.
PLACEHOLDER_RE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]{1,40})\}(?!\})")


def build_corpus(
    rubrics: list[dict],
    concept_holdout_fraction: float = 0.20,
    holdout_scale_families: set[str] | None = None,
    holdout_languages: set[str] | None = None,
    seed: int = 20260903,
) -> list[dict]:
    """Assemble rubrics into a corpus with train/test splits.

    Splits are cut along axes (concept, scale family, language) rather than at random, so
    different presentations of the same concept don't leak across splits.

    Args:
        rubrics: library records (rubric_id, concept_id, level, scale_type, n_levels, language)
        concept_holdout_fraction: fraction of concepts to hold out
        holdout_scale_families: scale families to hold out (default: ordinal_6, numerical_4, wide_14)
        holdout_languages: languages to hold out (default: ja)
        seed: random seed for reproducibility

    Returns:
        list of rubrics with 'split' and 'holdout_axes' fields added.
    """
    if holdout_scale_families is None:
        holdout_scale_families = {"ordinal_6", "numerical_4", "wide_14"}
    if holdout_languages is None:
        holdout_languages = {"ja"}
    rng = random.Random(seed)
    concepts = sorted({r["concept_id"] for r in rubrics})
    n_hold = int(len(concepts) * concept_holdout_fraction)
    holdout_concepts = set(rng.sample(concepts, n_hold)) if n_hold > 0 else set()

    for r in rubrics:
        axes = []
        if r.get("concept_id") in holdout_concepts:
            axes.append("concept")
        if scale_family(r.get("scale_type", ""), r.get("n_levels", 0)) in holdout_scale_families:
            axes.append("scale_family")
        if (r.get("language") or "en") in holdout_languages:
            axes.append("language")
        r["split"] = "test" if axes else "train"
        r["holdout_axes"] = axes

    rubrics.sort(key=lambda r: (r.get("level", ""), r.get("rubric_id", "")))
    return rubrics


def repair(rubrics: list[dict]) -> tuple[list[dict], Counter]:
    """Remove invented placeholders (`{made_up}`) from the task prose, the scale definitions and
    the rendered prompt.

    Returns the repaired list (modified in place) and a count of repairs by kind.
    """
    counts: Counter = Counter()
    for r in rubrics:
        text = (r.get("task") or "") + " ".join(s.get("definition", "") for s in r.get("scale") or [])
        invented = sorted(set(PLACEHOLDER_RE.findall(text)) - LEGAL_PLACEHOLDERS)
        if invented:
            for tok in invented:
                ph = "{" + tok + "}"
                r["task"] = (r.get("task") or "").replace(ph, tok)
                for s in r.get("scale") or []:
                    s["definition"] = s.get("definition", "").replace(ph, tok)
                r["rendered_prompt"] = r.get("rendered_prompt", "").replace(ph, tok)
            counts["removed_invented_placeholders"] += 1
    return rubrics, counts


def library_record(r: dict) -> dict:
    """A rubric in the library record schema, nothing else."""
    out = {k: r[k] for k in LIBRARY_FIELDS if k in r}
    if out.get("output_enum") == out.get("score_enum"):
        out.pop("output_enum", None)
    if not out.get("exclude_reason"):
        out.pop("exclude_reason", None)
    return out


def write_corpus(rubrics: list[dict], path: str) -> None:
    """Write the library JSONL, one record per rubric in the library record schema."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        for r in rubrics:
            f.write(json.dumps(library_record(r), ensure_ascii=False) + "\n")


def corpus_stats(rubrics: list[dict]) -> dict:
    """Compute summary statistics for a corpus."""
    train = [r for r in rubrics if r.get("split") == "train"]
    test = [r for r in rubrics if r.get("split") == "test"]
    return {
        "total": len(rubrics),
        "train": len(train),
        "test": len(test),
        "holdout_pct": round(100 * len(test) / max(len(rubrics), 1), 1),
        "by_level": dict(Counter(r.get("level", "?") for r in rubrics)),
        "by_holdout_axis": dict(Counter(a for r in test for a in r.get("holdout_axes", []))),
        "unique_concepts": len({r.get("concept_id", r.get("concept", "")) for r in rubrics}),
    }


def add_split_args(ap) -> None:
    """The held out split flags shared by the library building CLIs."""
    ap.add_argument("--holdout-fraction", type=float, default=0.20,
                    help="Share of generated concepts held out as test (default 0.20)")
    ap.add_argument("--holdout-scale-families", default="ordinal_6,numerical_4,wide_14",
                    help="Scale families held out as test, comma separated")
    ap.add_argument("--holdout-languages", default="ja",
                    help="Rubric languages held out as test, comma separated")


def split_from_args(rubrics: list[dict], a) -> list[dict]:
    return build_corpus(
        rubrics, concept_holdout_fraction=a.holdout_fraction,
        holdout_scale_families={x for x in a.holdout_scale_families.split(",") if x},
        holdout_languages={x for x in a.holdout_languages.split(",") if x}, seed=a.seed)
