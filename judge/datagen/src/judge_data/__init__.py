"""Training data pipeline for an LLM judge that scores agent traces with arbitrary rubrics.

Four parts:

- ``rubric_build``: concepts to a rubric library with held out splits.
- ``trace_synth``: synthesize agent traces that land at a chosen score level of a rubric.
- ``rubric_trace_match``: pair an existing trace pool with a rubric library.
- ``annotate``: a teacher model judges each (rubric, trace) pair and yields SFT records.

Every stage that calls a model takes a ``judge_data.clients.ModelClient``.
"""

__version__ = "0.1.0"
