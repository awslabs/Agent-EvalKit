# Examples

Small samples of the data the judge pipelines produce. The full training corpus is not released. These files show
the exact formats, so you can check your own runs against them.

## Licenses

| Content | Where it comes from | License |
|---|---|---|
| Traces, judge reasoning and scores in `training_records.sample.jsonl` | Written by MiMo-V2.6-Pro-MOPD | Model under MIT ([XiaomiMiMo/MiMo-V2.6-Pro-MOPD](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-MOPD)) |
| Agent system prompts and tool definitions inside those traces | 76 open-source agent repositories | MIT (47) or Apache-2.0 (29), each listed with its copyright notice in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |
| Rubrics in `rubrics.sample.jsonl` and concepts in `concepts.sample.jsonl` | Written by MiMo-V2.6-Pro-MOPD | Model under MIT |
| Agent profiles in `agents.sample.jsonl` | 8 of the open-source repositories above | MIT or Apache-2.0, listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |
| Prompt layout around each rubric | This repository's renderer | Apache-2.0 |

The sample files are released under this repository's Apache-2.0 license. Third-party material inside the traces
stays under its original license, as listed in `THIRD_PARTY_NOTICES.md`.

Only agents from repositories under permissive licenses were used. We checked every repository's license file
through the GitHub API and dropped any repository with no license, a copyleft license, a non-commercial or
source-available license, or modified terms. The `agent_id` field of each record names its repository.

Concept labels that came from public seed rubrics were reduced to a short statement of what is measured, and every
rubric was written fresh from its label, so no seed rubric is reproduced here. We checked every file for runs of eight
or more words shared with the seed rubrics. The only matches are short stock phrases, such as "the information in the
response is supported by", in 2 of the 104 rubrics and 5 of the 118 record concepts. None of the 100 sample concepts
matches.

| File | Records | What it is |
|---|---:|---|
| `training_records.sample.jsonl` | 118 | Training records, spread across evaluation level and output contract |
| `rubrics.sample.jsonl` | 104 | Rubrics from the library, spread across level and scale shape |
| `concepts.sample.jsonl` | 100 | Rubric concepts, the input the rubric generator starts from |
| `agents.sample.jsonl` | 8 | Agent profiles for trace synthesis, the `--agents` input |

## Training records

One JSON object per line.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Record id |
| `prompt` | list of messages | The complete judge prompt: rubric, evidence, and the reply format to use |
| `completion` | list of messages | The target reply, in the reply format the prompt asks for |
| `meta` | object | Not used for training. Drop it before tokenizing |

`meta` fields:

| Field | Meaning |
|---|---|
| `rubric_id`, `concept` | The rubric and the concept it was written from |
| `level` | `SESSION` (a whole conversation), `TRACE` (one turn), or `TOOL_CALL` (one tool call) |
| `n_levels` | How many levels the rubric's scale has |
| `output_contract` | The reply format: `native` (the rubric's own JSON), `keyvalue`, `xml`, `score_only`, `score_first`, `verdict_bare`, or `verdict_fenced` |
| `agent_id` | The open-source agent profile the trace was conditioned on |
| `verdict` | The teacher's score, which is the training target |

## Rubrics

One rubric per line.

| Field | Meaning |
|---|---|
| `rubric_id`, `concept_id`, `concept` | The rubric and the concept it was written from |
| `level`, `domain` | Evaluation level and application domain |
| `task` | What the judge should check |
| `scale_type`, `n_levels`, `score_enum`, `scale` | The scale: its type, size, labels, and a definition for each level. Numeric scales also carry `output_enum`, the values a judge answers with |
| `placeholders` | The evidence the rubric reads: `context`, `assistant_turn`, `available_tools`, or `tool_turn` |
| `rendered_prompt` | The full judge prompt with the evidence left as placeholders |

The placeholders in `rendered_prompt`, written `<<CONVERSATION_CONTEXT>>` or `{context}`, are where the evidence goes.
`judge/serve/score.py` and the annotation step fill them in. Every training record already has them filled.

A rubric's `rendered_prompt` always asks for its own JSON reply format. Annotation then rewrites that format into one
of the seven output contracts for each training record, so the records show all seven while the rubrics show one.

## Concepts

One concept per line: `concept_id`, `concept` (a short statement of what is measured), `level`, and `domain`.
Pass a concept file to the rubric generator with `--concepts` to build rubrics from concepts directly.

## Agents

One agent profile per line: `agent_id`, `source_repo`, `system_prompt`, `tools` (each with `name` and `description`),
`framework`, and `domain`. Pass the file to `trace_synth` or the recipe with `--agents`. The profiles come from 8 of
the open-source repositories in `THIRD_PARTY_NOTICES.md`, under MIT or Apache-2.0. Each `system_prompt` is the first
500 characters of the agent's prompt, the same length the training traces were synthesized from.

With the sample concepts and agents you can run the whole recipe without any data of your own:

```bash
cd ../datagen && source .venv/bin/activate
bash recipes/build_training_data.sh --concepts ../examples/concepts.sample.jsonl \
    --agents ../examples/agents.sample.jsonl --out /tmp/judge-dry-run --backend mock --cache none
```
