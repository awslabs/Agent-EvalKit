"""Rubric-trace matching: pair a rubric library with an existing trace pool, annotate, assemble.

The trace pool is any JSONL of traces in the normalised Trace schema
(`judge_data.traces`).

- match: rubric and trace feature prompts, scoring, level gating, target selection
- sample: stratified trace sampling
- resplit: held out splits by trace, language and concept, with contamination checks

CLIs, in order::

    python -m judge_data.rubric_trace_match.run           # match rubrics to traces -> pairs
    python -m judge_data.annotate --pairs <run out dir>   # teacher judges every pair
    python -m judge_data.rubric_trace_match.assemble      # training files, splits, slices
    python -m judge_data.rubric_trace_match.verify        # invariant checks on the output
"""
