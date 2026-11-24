"""Rubric library construction.

Modules, each usable on its own:

- extract: concept labels from seed rubrics, clustering into a registry, authoring missing
  concepts, judgeability filtering
- library: concept lists, and concepts to rendered rubric records
- generate: rubric prose and scales from a concept plus a presentation spec
- render: the prompt layouts a judge receives (pure logic)
- variants: output format variants of a rubric (pure logic)
- validate: schema and placeholder checks, clean room n-gram check, functional test, relabelling
- assemble: repairs, held out splits cut by concept, scale family and language, and the library
  record schema (pure logic)
- embed: pluggable sentence embeddings for deduplication

CLIs: `python -m judge_data.rubric_build` (concepts or seeds to a library), `.gapfill`,
`.variants`, `.rerender`.

Example::

    import random

    from judge_data.clients import make_client
    from judge_data.rubric_build import library

    client = make_client("vllm", base_url="http://localhost:8000/v1", model_id="MiMo-V2.6-Pro-MOPD")
    concepts = library.normalise_concepts([{"concept": "the response avoids unnecessary words"}])
    rubrics, stats = library.rubrics_from_concepts(concepts, client, random.Random(0),
                                                   presentations=3)
"""
