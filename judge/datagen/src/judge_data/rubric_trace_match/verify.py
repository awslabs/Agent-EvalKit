"""CLI: per record invariant checks over a matched-pair annotation output or an assembled file, streaming.

    python -m judge_data.rubric_trace_match.verify --annotated out/annotated \
        --rubric-library out/rubric_library.jsonl [--limit N]
    python -m judge_data.rubric_trace_match.verify --file out/training/training.jsonl \
        --rubric-library out/rubric_library.jsonl

This exists because the failures that matter in this pipeline are silent. A prompt that still
contains an unfilled placeholder, a record labelled as having its reasoning removed that still has
it, a score outside the scale it declares: none of these raise, none look wrong in a progress line,
and every one is a training defect. So the contracts are written down as checks a machine runs, and
the check can run while annotation is still in flight.

Every check states a contract the record claims about itself, so a violation is always either a bug
here or a bug in the stage, never a judgement call.

Memory stays flat. The file is larger than is comfortable to hold and holding it is not needed to
check a record on its own.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from judge_data.annotate import render, scrub
from judge_data.annotate.parse import _in_enum
from judge_data.traces import HEADER
from judge_data.utils.io import read_jsonl


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annotated", default=None, help="An annotation output directory (annotate on matched pairs)")
    ap.add_argument("--file", default=None,
                    help="A JSONL file directly, for checking an assembled training file")
    ap.add_argument("--rubric-library", required=True, help="Rubric library JSONL")
    ap.add_argument("--teacher", default=None,
                    help="Flag records whose meta.teacher is not this model id")
    ap.add_argument("--limit", type=int, default=0, help="check only the first N lines")
    ap.add_argument("--examples", type=int, default=2, help="violations to print per check")
    a = ap.parse_args()

    recs = {r["rubric_id"]: r for r in read_jsonl(a.rubric_library)}
    # Rubrics whose own instructions contain a phrase the leak detector matches. Their records are
    # exempt from the leak check, which is the same exemption the stage makes by scoping detection to
    # the evidence rather than the whole prompt.
    leaky_rubrics = {rid for rid, r in recs.items() if scrub.leaks(r["rendered_prompt"])}
    print(f"library {len(recs)} rubrics, {len(leaky_rubrics)} whose own text matches the leak "
          f"detector and are therefore exempt: {sorted(leaky_rubrics)}")

    fail: Counter = Counter()
    ex: dict[str, list] = defaultdict(list)
    seen_ids: set[str] = set()
    n = ok = bad = torn = dup = 0
    verdicts: Counter = Counter()
    axes: dict[str, Counter] = defaultdict(Counter)

    def flag(name: str, rid: str, detail: str = "") -> None:
        fail[name] += 1
        if len(ex[name]) < a.examples:
            ex[name].append((rid, detail[:220]))

    if not (a.annotated or a.file):
        ap.error("pass --annotated or --file")
    path = Path(a.file) if a.file else Path(a.annotated) / "annotated.jsonl"
    print(f"checking {path}")
    with path.open(errors="replace") as f:
        for line in f:
            n += 1
            if a.limit and n > a.limit:
                break
            try:
                r = json.loads(line)
            except Exception:
                torn += 1
                continue
            rid = str(r.get("id", "?"))
            # `ok is False` is a recorded failure. `ok` absent is not: the assembled training file
            # carries only id, prompt, completion and meta, because every record in it succeeded by
            # construction. Testing truthiness would count every assembled record as a failure and
            # report zero violations over zero records, a gate that cannot fail.
            if r.get("ok") is False:
                bad += 1
                continue
            ok += 1
            if rid in seen_ids:
                dup += 1
            seen_ids.add(rid)

            m = r.get("meta") or {}
            rec = recs.get(m.get("rubric_id"))

            # Shape.
            try:
                prompt = r["prompt"][0]["content"]
                comp = r["completion"][0]["content"]
            except Exception:
                flag("record shape is not prompt and completion", rid)
                continue
            if not prompt.strip():
                flag("prompt is empty", rid)

            # The id is the join key between a rubric and a trace, so it has to agree with the
            # metadata that names them, otherwise a slice built from ids selects other records.
            if "|" in rid:
                r_id, t_id = rid.split("|", 1)
                if r_id != m.get("rubric_id"):
                    flag("id disagrees with meta.rubric_id", rid, str(m.get("rubric_id")))
                if "trace_id" in m and t_id != str(m.get("trace_id")):
                    flag("id disagrees with meta.trace_id", rid, str(m.get("trace_id")))
            else:
                flag("id is not rubric_id|trace_id", rid)

            # Output contract. The assembled target is fenced, an annotation stage record is bare.
            # Both shapes have to parse here.
            fenced = comp.strip().startswith("```")
            body = scrub.unfence(comp)
            try:
                c = json.loads(body)
            except Exception:
                flag("completion is not JSON", rid, comp[:200])
                c = {}
            axes["target_format"]["fenced" if fenced else "bare"] += 1
            if set(c) != {"reasoning", "score"}:
                flag("completion keys are not exactly reasoning and score", rid, str(sorted(c)))
            reasoning = str(c.get("reasoning") or "")
            score = "" if c.get("score") is None else str(c.get("score"))
            if not reasoning.strip():
                flag("reasoning is empty", rid)

            # Score versus the scale its rubric declares. An assembled record carries no is_na, and
            # N/A records are held back in their own file unless --keep-na.
            is_na = m["is_na"] if "is_na" in m else score.upper() == "N/A"
            if is_na:
                if score.upper() != "N/A":
                    flag("is_na set but score is not N/A", rid, score)
            else:
                enum = (rec or {}).get("output_enum") or (rec or {}).get("score_enum") or []
                if not _in_enum(score, enum):
                    flag("score outside declared scale", rid, f"{score!r} not in {enum}")
                if score.upper() == "N/A":
                    flag("score is N/A but is_na is not set", rid)
            if str(m.get("verdict")) != score:
                flag("meta.verdict disagrees with the completion score", rid,
                     f"{m.get('verdict')!r} vs {score!r}")

            # Evidence format contracts, the two axes added by the scrub policy.
            ts = m.get("thinking_stripped")
            if ts == "all" and scrub.has_tag(prompt):
                flag("labelled fully stripped but reasoning tags remain", rid)
            # A judgement that cites the agent's reasoning is fine when the reasoning is there, and
            # is the one real incoherence when it is not: the target would assert evidence the input
            # does not contain. A tag in the reply is otherwise a quotation and is left alone.
            if ts == "all" and scrub.has_tag(reasoning):
                flag("judgement cites reasoning that was removed from the prompt", rid,
                     reasoning[:200])
            if m.get("context_layout") == "no_turn_labels" and HEADER.search(prompt):
                flag("labelled no turn headers but a numbered header is present", rid)
            if m.get("context_layout") == "turn_labels" and not HEADER.search(prompt):
                # Not a defect on its own. A single turn trace truncated at turn one can legitimately
                # have no header line, so this is counted and shown rather than treated as a failure.
                flag("labelled turn headers but none found, informational", rid)

            # Leakage.
            if m.get("rubric_id") not in leaky_rubrics and scrub.leaks(prompt):
                flag("target label leak present in prompt", rid)

            # Placeholders, checked on the template the record came from, since trace content can
            # quote a placeholder string verbatim.
            if rec is not None:
                miss = render.unfillable(rec)
                if miss:
                    flag("template has an unfillable placeholder", rid, str(sorted(miss)))
                if "<<" in rec.get("rendered_prompt", ""):
                    for slot, marker in render.MARKERS.items():
                        if marker in prompt:
                            flag("marker left unfilled", rid, marker)
            else:
                flag("meta.rubric_id is not in the corpus", rid, str(m.get("rubric_id")))

            if a.teacher and m.get("teacher") != a.teacher:
                flag("teacher is not the expected model", rid, str(m.get("teacher")))

            verdicts[score] += 1
            for k in ("source", "level", "thinking_stripped", "context_layout", "split"):
                axes[k][m.get(k)] += 1

    print(f"\nlines {n:,}   usable {ok:,}   recorded failures {bad:,}   unparseable {torn}")
    print(f"duplicate ids among usable records: {dup:,}")
    print("\n=== invariant violations ===")
    if not fail:
        print("  none")
    for name, cnt in fail.most_common():
        share = 100 * cnt / max(ok, 1)
        print(f"  {cnt:8,d}  ({share:6.3f}%)  {name}")
        for rid, detail in ex[name]:
            print(f"              {rid[:70]}  {detail}")
    print("\n=== composition of the usable records ===")
    for k, c in axes.items():
        t = sum(c.values())
        print(f"  {k:18s}", {str(kk): f"{100*v/t:.1f}%" for kk, v in c.most_common(8)})
    hard = sum(v for k, v in fail.items() if "informational" not in k)
    print(f"\nhard violations {hard:,} of {ok:,} usable records")


if __name__ == "__main__":
    main()
