"""Annotation: a teacher model judges each (rubric, trace) pair with the exact prompt a judge
receives, and the reply becomes an SFT record `{id, prompt, completion}`.

- render: fill evidence into a rubric's placeholders, in either placeholder spelling
- prompt: the stored training prompt and the annotator's prompt
- parse: parse and check a judgement with the rubric's declared scale
- contracts: re-serve a judgement under other output contracts
- scrub: reasoning tag removal and target label leak detection
- synth: annotation of synthesized pairs (a pairs JSONL from trace_synth)
- matched: annotation of matched pairs (directories from rubric_trace_match)

CLI: `python -m judge_data.annotate`. It reads the source from `--pairs` and runs synth or matched.
"""
