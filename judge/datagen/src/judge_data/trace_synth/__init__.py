"""Rubric conditioned trace synthesis.

Given a rubric and a target level on its scale, generate an agent trace that exhibits the rubric's
concept at that level, simulating a real agent profile (system prompt and tools). Optionally verify
where each trace actually landed with an independent call.

- synth: prompts, severity mapping, parsing a generated trace into the normalised shape

The normalised Trace schema and evidence rendering live in `judge_data.traces`, shared with
`rubric_trace_match` and `annotate`.

CLI: `python -m judge_data.trace_synth`.
"""
