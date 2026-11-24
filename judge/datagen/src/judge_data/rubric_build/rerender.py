"""CLI: re-render a rubric library's prompts with the current renderer, keeping ids and content.

    python -m judge_data.rubric_build.rerender --library out/rubric_library.jsonl

Rebuilds every rubric that has task prose from that prose and its scale through
`render.render_record`, so presentation changes (layout, evidence order, output block styles)
reach an existing library without regenerating rubrics or traces. rubric_id, concept, level, scale
and domain are unchanged, so pairs keep resolving. A rubric without task prose is copied as it is.
The original file is kept with a backup suffix.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter

from judge_data.rubric_build import assemble, render, validate

# Fields a re-render keeps from the existing record rather than recomputing.
KEPT = ("split", "holdout_axes", "exclude_reason")


def rerender(r: dict) -> dict:
    spec = {"domain": r.get("domain"), "language": r.get("language")}
    out = render.render_record(r["rubric_id"], r["concept"], r["level"], r["task"], r["scale"],
                               spec, concept_id=r.get("concept_id"))
    for k in KEPT:
        if k in r:
            out[k] = r[k]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", required=True)
    ap.add_argument("--backup-suffix", default=".pre_rerender")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.library) if l.strip()]
    out, why = [], Counter()
    for r in rows:
        if not r.get("task"):
            out.append(r)
            why["no task prose, kept as is"] += 1
            continue
        n = rerender(r)
        errs = validate.check_schema(n)
        if errs:
            out.append(r)
            why["kept, re-render failed schema: " + errs[0][:50]] += 1
            continue
        out.append(n)
        why["re-rendered"] += 1
    bak = a.library.replace(".jsonl", f"{a.backup_suffix}.jsonl")
    if not os.path.exists(bak):
        shutil.copy2(a.library, bak)
    tmp = a.library + ".tmp"
    assemble.write_corpus(out, tmp)
    os.replace(tmp, a.library)
    print(f"{len(out)} rubrics -> {a.library} (backup {bak}): {dict(why)}")


if __name__ == "__main__":
    main()
