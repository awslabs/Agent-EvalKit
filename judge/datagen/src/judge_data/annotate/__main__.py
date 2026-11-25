"""CLI: annotate (rubric, trace) pairs. A teacher judges each pair with the prompt a judge receives.

    # synthesized pairs, one JSONL from trace_synth
    python -m judge_data.annotate --pairs out/pairs.jsonl --out out/output.jsonl \\
        --rubric-library out/rubric_library.jsonl --agent-registry agent_registry.jsonl $B

    # matched pairs, one or more directories from rubric_trace_match
    python -m judge_data.annotate --pairs out/match --out out/annotated \\
        --rubric-library out/rubric_library.jsonl --strip-pct 30 $B

The source is read from --pairs. A file means synthesized pairs. One or more directories mean
matched pairs. `--source` overrides the detection.

Synthesized pairs write the SFT records to --out and `<out stem>.judgments.jsonl` beside it.
Matched pairs write annotated.jsonl into the --out directory. Run `rubric_trace_match.assemble`
on it next.

Options marked [synth] or [matched] apply to that source only and are rejected for the other.
Defaults that differ per source are shown for each. See `annotate.synth` and `annotate.matched`
for the evidence and reasoning policy of each source.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from judge_data.clients import add_backend_args

SOURCES = ("synth", "matched")

# Options owned by one source. Each defaults to None in the parser, so a value the user passed is
# told apart from a default, and the source's default is filled in after detection.
ONLY = {
    "synth": ("agent_registry", "splits", "context_formats", "output_contracts"),
    "matched": ("workers", "exclude_rubrics", "strip_list", "strip_pct", "no_label_pct"),
}
DEFAULTS = {
    "synth": {"max_tokens": 2048, "allow_na": False, "context_formats": "repr:2,turns:1,flat:1"},
    "matched": {"max_tokens": 2000, "allow_na": True, "workers": 64, "strip_pct": 0,
                "no_label_pct": 50},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m judge_data.annotate", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pairs", action="append", required=True,
                    help="A pairs JSONL from trace_synth, or a directory with pairs.jsonl and "
                         "traces.jsonl from rubric_trace_match (repeatable for directories)")
    ap.add_argument("--out", required=True,
                    help="synth: output records JSONL. matched: output directory")
    ap.add_argument("--source", choices=SOURCES, default=None,
                    help="Force the source instead of reading it from --pairs")
    ap.add_argument("--rubric-library", default=None,
                    help="Rubric library JSONL, rubrics are looked up by id. Required for matched. "
                         "synth default: rubric_library.jsonl next to --pairs")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="Max tokens of a teacher reply (default: synth 2048, matched 2000)")
    na = ap.add_mutually_exclusive_group()
    na.add_argument("--allow-na", dest="allow_na", action="store_const", const=True, default=None,
                    help="Offer the teacher an N/A option (default: synth off, matched on)")
    na.add_argument("--no-na", dest="allow_na", action="store_const", const=False,
                    help="Do not offer the teacher an N/A option")
    ap.add_argument("--limit", type=int, default=0, help="Annotate only the first N pairs, 0 for all")

    s = ap.add_argument_group("synthesized pairs only [synth]")
    s.add_argument("--agent-registry", default=None,
                   help="Agent registry, to show each agent's full tool catalogue to the judge")
    s.add_argument("--splits", default=None,
                   help="Only rubrics in these library splits, comma separated (default: all)")
    s.add_argument("--context-formats", default=None,
                   help="Weights of the conversation serialisations, assigned per pair id "
                        "(repr: one Python repr of a message per line, turns: numbered Turn N: "
                        "blocks, flat: no headers). Default: repr:2,turns:1,flat:1")
    s.add_argument("--output-contracts", default=None,
                   help="Weights of the training-record output contracts (see annotate.contracts). "
                        "The teacher always answers the rubric's own. 'native:1' disables "
                        "re-serving")

    m = ap.add_argument_group("matched pairs only [matched]")
    m.add_argument("--workers", type=int, default=None, help="Pairs annotated in parallel (default 64)")
    m.add_argument("--exclude-rubrics", default=None,
                   help="File of rubric ids to leave out of training data")
    m.add_argument("--strip-list", default=None,
                   help="File of pair ids whose internal reasoning is removed entirely")
    m.add_argument("--strip-pct", type=int, default=None,
                   help="Also remove all reasoning on this hash chosen percent of pairs (default 0)")
    m.add_argument("--no-label-pct", type=int, default=None,
                   help="Percent of records rendered without numbered turn headers (default 50)")
    add_backend_args(ap)
    return ap


def detect_source(ap: argparse.ArgumentParser, paths: list[str]) -> str:
    kinds = []
    for p in paths:
        q = Path(p)
        if q.is_dir():
            kinds.append("matched")
        elif q.is_file():
            kinds.append("synth")
        else:
            ap.error(f"--pairs {p} does not exist (pass --source to say what it will be)")
    if set(kinds) == {"matched"}:
        return "matched"
    if kinds == ["synth"]:
        return "synth"
    ap.error("--pairs takes one pairs JSONL file, or one or more directories, not a mix "
             "or several files")


def main() -> None:
    ap = build_parser()
    a = ap.parse_args()
    a.source = a.source or detect_source(ap, a.pairs)

    other = SOURCES[1 - SOURCES.index(a.source)]
    given = ["--" + k.replace("_", "-") for k in ONLY[other] if getattr(a, k) is not None]
    if given:
        name = {"synth": "synthesized", "matched": "matched"}
        ap.error(f"{', '.join(given)} {'applies' if len(given) == 1 else 'apply'} only to "
                 f"{name[other]} pairs, but --pairs holds {name[a.source]} pairs")
    for k, v in DEFAULTS[a.source].items():
        if getattr(a, k) is None:
            setattr(a, k, v)

    if a.source == "synth":
        if len(a.pairs) != 1:
            ap.error("synthesized pairs take one --pairs file")
        from judge_data.annotate import synth
        synth.run(a)
    else:
        if not a.rubric_library:
            ap.error("--rubric-library is required for matched pairs")
        from judge_data.annotate import matched
        matched.run(a)


if __name__ == "__main__":
    main()
