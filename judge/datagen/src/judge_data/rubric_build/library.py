"""Concept lists, and the shared step that turns concepts into rendered library rubrics.

A concept list is JSONL, one concept per line:

    {"concept_id": "c0001", "concept": "the agent retried a failing tool call without changing
     its approach", "level": "SESSION", "domain": "general"}

Fields:
  concept     required. A short statement of the observable property being measured.
  concept_id  optional. Defaults to `c<line number>`. Must be unique.
  level       SESSION, TRACE or TOOL_CALL. Default TRACE.
  domain      optional. Pins the domain flavour. Otherwise one is sampled per rubric.
  polarity    optional input. "defect" frames every rubric as the presence of a fault.

Other keys are accepted and ignored. Normalised concepts carry exactly
`concept_id, concept, level, domain`, plus `polarity` in memory when it is "defect".
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace
from typing import TYPE_CHECKING

from judge_data.rubric_build import generate, render, validate
from judge_data.utils.io import read_jsonl

if TYPE_CHECKING:
    from judge_data.clients import ModelClient

LEVELS = ("SESSION", "TRACE", "TOOL_CALL")


def normalise_concepts(rows: list[dict]) -> list[dict]:
    """Validate and fill defaults. Raises ValueError on a bad row."""
    out, seen = [], set()
    for i, r in enumerate(rows):
        concept = str(r.get("concept") or "").strip().rstrip(".")
        if not concept:
            raise ValueError(f"concept list row {i + 1} has no 'concept'")
        cid = str(r.get("concept_id") or f"c{i:05d}")
        if cid in seen:
            raise ValueError(f"duplicate concept_id {cid!r}")
        seen.add(cid)
        level = str(r.get("level") or "TRACE").upper()
        if level not in LEVELS:
            raise ValueError(f"concept {cid}: level must be one of {LEVELS}, got {level!r}")
        c = {"concept_id": cid, "concept": concept, "level": level,
             "domain": r.get("domain") or None}
        if r.get("polarity") == "defect":
            c["polarity"] = "defect"
        out.append(c)
    return out


CONCEPT_FIELDS = ("concept_id", "concept", "level", "domain")


def concept_rows(concepts: list[dict]) -> list[dict]:
    """Concepts as written to concepts.jsonl: `concept_id, concept, level, domain`."""
    return [{k: c.get(k) for k in CONCEPT_FIELDS} for c in concepts]


def load_concepts(path: str) -> list[dict]:
    return normalise_concepts(read_jsonl(path))


def rubrics_from_concepts(concepts: list[dict], client: "ModelClient", rng: random.Random,
                          presentations: int = 1) -> tuple[list[dict], dict]:
    """Generate `presentations` rubrics per concept and render each into a library record.

    One generation call per concept asks for all its presentations at once, so they come out
    different from each other. Records failing the schema check are dropped and counted.
    Returns (rubrics, stats).
    """
    specs: dict[str, list] = {}
    for c in concepts:
        ss = generate.sample_specs_for_concept(rng, c["level"], k=presentations,
                                               domain=c.get("domain"))
        if c.get("polarity") == "defect":
            ss = [replace(s, polarity="defect") for s in ss]
        specs[c["concept_id"]] = ss
    gen, failures = generate.batch_generate(concepts, specs, client)

    rubrics, n_per, bad_scale, bad_schema = [], Counter(), 0, Counter()
    for rec in gen:
        spec = rec.get("spec", {})
        scale = render.normalize_scale(rec.get("scale"), bool(spec.get("numeric")))
        if not scale or not rec.get("task"):
            bad_scale += 1
            continue
        cid = rec["concept_id"]
        r = render.render_record(f"{cid}_{n_per[cid]}", rec["concept"], rec["level"], rec["task"],
                                 scale, spec, concept_id=cid)
        errs = validate.check_schema(r)
        if errs:
            bad_schema[errs[0][:60]] += 1
            continue
        n_per[cid] += 1
        rubrics.append(r)
    stats = {"concepts": len(concepts), "generated": len(gen), "generation_failures": len(failures),
             "dropped_bad_scale": bad_scale, "dropped_schema": dict(bad_schema),
             "rubrics": len(rubrics)}
    return rubrics, stats
