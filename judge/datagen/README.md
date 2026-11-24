# evalkit-judge-data

Build SFT training data for an LLM judge that scores agent traces with arbitrary rubrics.

The judge reads one rubric and one piece of agent evidence (a session, a single reply, or a single
tool call) and returns a reasoning and a score from the rubric's own scale. To learn that, it needs
many different rubrics, many different traces, and a trusted judgement for each pair. This package
builds all three.

## The four parts

| Part | What it does | Main output |
|---|---|---|
| `rubric_build` | Concepts become a rubric library. Each concept gets several rubrics with different scales, layouts and wording. Held out splits are cut by concept, scale family and language. | `rubric_library.jsonl` |
| `trace_synth` | For each rubric and each level of its scale, synthesize an agent trace that should land on that level. The trace simulates a real agent profile (system prompt and tools). | `pairs.jsonl` |
| `rubric_trace_match` | When you already have a trace pool, pick traces for each rubric (stratified). After annotation, assemble the records with held out splits. | `pairs.jsonl`, then `training.jsonl` and split files |
| `annotate` | A teacher model judges each (rubric, trace) pair with the exact prompt a judge receives. The reply becomes the training target. Takes synthesized or matched pairs. | `output.jsonl` of `{id, prompt, completion, meta}`, or `annotated.jsonl` for matched pairs |

Two ways to get training data:

```
concepts.jsonl ──> rubric_build ──> rubric_library.jsonl ──> trace_synth ──> pairs.jsonl ──> annotate ──> output.jsonl
                                              │
trace_pool.jsonl ─────────────────────────────┴──> rubric_trace_match.run ──> match/ ──> annotate ──> annotated/ ──> rubric_trace_match.assemble ──> training.jsonl
```

Both paths use the same `annotate` step. It reads the kind of pairs from `--pairs`.

## Install

```bash
cd judge/datagen
uv venv && uv pip install -e .            # core: httpx, numpy
uv pip install -e '.[bedrock]'            # Amazon Bedrock backend (boto3)
uv pip install -e '.[embed,cluster]'      # sentence-transformers embeddings, scikit-learn clustering
```

Python 3.10 or newer.

## Model backends

Every stage that calls a model takes the same flags.

| Flag | Meaning |
|---|---|
| `--backend` | `vllm` or `openai` (any OpenAI compatible endpoint), `bedrock` (Converse API), `mock` (canned replies, for tests) |
| `--model-id` | The model name the endpoint knows. Required except for `mock`. There is no default model. |
| `--base-url` | HTTP backends. Ends in `/v1`. Several replicas can be comma separated. |
| `--api-key` | HTTP backends. Bearer token, if the endpoint needs one. |
| `--cache` | SQLite reply cache (default `llm_cache.sqlite`), or `none`. Reruns skip finished calls. |
| `--concurrency` | Requests in flight. Total for HTTP (default 256), per credential set for Bedrock (default 16). |
| `--chat-template-kwargs` | HTTP backends. JSON, for example `'{"enable_thinking": true}'`. With thinking on, text before `</think>` is dropped. |
| `--region`, `--aws-profile`, `--role-arn` | Bedrock. Region and profile accept comma separated lists, and requests are spread over them. |
| `--no-temperature` | Bedrock. Never send temperature, for models that reject it. |
| `--additional-model-request-fields` | Bedrock. JSON passed through as `additionalModelRequestFields`. |

The `vllm` backend sends `chat_template_kwargs={"enable_thinking": false}` unless you pass your own.
The `openai` backend sends nothing extra.

In code, use `judge_data.clients.make_client(...)`. Any object with `model_id`, `total_in`,
`total_out`, `invoke(prompt, max_tokens, temperature)` and `map(prompts, ...)` works. `invoke` never
raises. A failed call comes back as `Result(ok=False, error=...)`.

All examples below use a self-hosted model behind vLLM.

```bash
B="--backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD"
```

## Input schemas

All inputs are JSONL, one object per line.

### Concept list

The open release ships concepts, not seed rubrics.

```json
{"concept_id": "c0001", "concept": "the agent retried a failing tool call without changing its approach", "level": "SESSION", "domain": "general"}
```

| Field | Required | Meaning |
|---|---|---|
| `concept` | yes | A short statement of the observable property being measured. |
| `concept_id` | no | Unique id. Default `c<line number>`. |
| `level` | no | `SESSION`, `TRACE` or `TOOL_CALL`. Default `TRACE`. |
| `domain` | no | Pins the domain flavour, for example `finance`. Otherwise one is sampled per rubric. |
| `polarity` | no | `defect` frames every rubric as the presence of a fault. |

Other keys are accepted and ignored. The `concepts.jsonl` that `rubric_build` writes holds exactly
`concept_id`, `concept`, `level` and `domain`.

Levels decide what evidence the judge sees. `SESSION` sees every turn and the tool catalogue.
`TRACE` sees the conversation up to one assistant reply plus that reply. `TOOL_CALL` sees the
conversation up to one call, the tool catalogue, and that call with its result.

### Seed rubrics

Optional. Use these when you have your own rubric collection.

```json
{"rubric_idx": 0, "metric_name": "Politeness", "definition": "...", "scoring_scale": "1-5", "score_levels": {"1": "...", "5": "..."}, "grading_instructions": "...", "category": "tone"}
```

Only `metric_name` and `definition` matter much. The build is clean room: only a short concept
label crosses over from a seed. A label that shares a phrase of 8 or more words with its seed is
restated. Generated rubrics that share any 8 word n-gram with any seed are dropped.

### Agent registry

Not shipped. `trace_synth` reads it, and so does `annotate` on synthesized pairs.

```json
{"agent_id": "example/shop-assistant", "source_repo": "https://github.com/example/shop-assistant", "system_prompt": "You help customers with orders.", "tools": [{"name": "get_order", "description": "Look up an order", "parameters": {"type": "object"}}], "framework": "langgraph", "domain": "customer_support"}
```

| Field | Meaning |
|---|---|
| `agent_id` | Required. Unique id, often `org/repo`. |
| `source_repo` | Where the agent comes from. Informational. |
| `system_prompt` | The agent's system prompt. The first 500 characters go into the synthesis prompt. |
| `tools` | Tool names, or objects with `name`, `description` and optionally `parameters`. Up to 12 are used. |
| `framework` | Agent framework name. Informational. |
| `domain` | Used to match agents to rubric domains, for example `customer_support` plays `customer_service` rubrics. Unknown domains fall back to `general`. |
| `goal` | Optional scenario text. Default: "Complete a task in the `<domain>` domain". |

### Trace pool

For `rubric_trace_match`. Any JSONL of traces in the normalised Trace schema, defined in
`judge_data/traces.py` and shared by every stage that reads traces.

```json
{"trace_id": "t1", "agent_id": "org/repo", "framework": "strands", "user_goal": "refund order 12",
 "turns": [{"user": "Refund order 12", "reasoning": "", "assistant": "Done.",
            "tool_calls": [{"tool_name": "refund_order", "arguments": {"id": "12"}}],
            "tool_results": [{"status": "ok"}]}],
 "tool_catalogue": ["get_order", "refund_order"], "tags": {"topic": "shopping"},
 "target_labels": {"goal_reached": 1}, "primary_dim": "goal_reached"}
```

Only `turns` is required. The raw names `scenario_id`, `user_input` and `agent_response` are also
accepted. `tool_catalogue` may hold names or `{"name"}` objects, and called tools are always added.
`tags` are free strings used for stratified sampling. `target_labels` and `primary_dim` are optional
ground truth (1 means the property is present). When a rubric's id appears in `target_labels`,
matching mixes positive and negative traces for that rubric.

## Output schemas

### Rubric library record

Each line of `rubric_library.jsonl` is one rubric. `gapfill`, `rerender` and `variants` write the
same schema.

```json
{"rubric_id": "c0001_0", "concept_id": "c0001", "concept": "the agent retried a failing tool call without changing its approach",
 "level": "SESSION", "domain": "general", "language": "en", "scale_type": "categorical", "n_levels": 2,
 "score_enum": ["Repeats", "Adapts"], "scale": [{"label": "Repeats", "definition": "..."}, {"label": "Adapts", "definition": "..."}],
 "task": "...", "placeholders": ["context", "available_tools"], "rendered_prompt": "...",
 "split": "train", "holdout_axes": []}
```

| Field | Meaning |
|---|---|
| `rubric_id` | `<concept_id>_<n>`. |
| `concept_id`, `concept`, `level`, `domain` | As in the concept list. |
| `language` | The language the rubric is written in. Read by the language holdout. |
| `scale_type`, `n_levels` | `categorical` or `numerical`, and the number of levels. Together they name the scale family (`binary`, `ordinal_5`, `numerical_4`, `wide_14` and so on). |
| `score_enum`, `scale` | The score labels, and the scale itself (label, definition, and a value on numerical scales). |
| `output_enum` | Present only when the judge answers with something other than the labels. A numerical scale in the compact layout is answered by value. |
| `task` | The instruction prose. `rerender` rebuilds the prompt from it. |
| `placeholders` | The evidence slots the prompt needs: `context`, `assistant_turn`, `available_tools`, `tool_turn`. |
| `rendered_prompt` | The prompt template with evidence slots unfilled. |
| `split`, `holdout_axes` | `train` or `test`, and why (`concept`, `scale_family`, `language`). |
| `exclude_reason` | Optional. Later stages skip a rubric that has one. |

A rendered prompt uses one of two placeholder spellings, `<<CONVERSATION_CONTEXT>>` style markers
or `{context}` style slots. `annotate.render.fill` reads the spelling from the prompt itself.
The renderer (`rubric_build.render`) has two layouts:

| Layout | Shape |
|---|---|
| `sectioned` | Evidence first in sections under `<<CONVERSATION_CONTEXT>>` style markers, then the task, the scale as a bullet list, and a JSON schema output block. |
| `compact` | Task prose with `{context}` style slots under headings, the scale as one `label: definition` line, and an indented JSON schema output block. |

The library build renders half the rubrics as `sectioned` and half as `compact`, chosen by a hash
of the rubric id. A rubric whose prose holds a literal brace is always `sectioned`. The layout is
not stored in the record.

### Pairs from trace synthesis

```json
{"id": "synth-00000-1-0", "concept": "...", "severity": "Yes", "target_bucket": "full", "verified_severity": "full", "agent_id": "...", "rubric": {...}, "trace": "<generated JSON text>"}
```

`severity` is the target score label. `target_bucket` is its coarse position on the scale
(`absent`, `partial`, `full`). `verified_severity` is present with `--verify`.

### Training records

`annotate` writes `output.jsonl` for synthesized pairs. Matched pairs go through `rubric_trace_match.assemble`, which writes records of the same shape.

```json
{"id": "synth-00000-1-0",
 "prompt": [{"role": "user", "content": "<the filled judge prompt>"}],
 "completion": [{"role": "assistant", "content": "```json\n{\"reasoning\": \"...\", \"score\": \"Yes\"}\n```"}],
 "meta": {"rubric_id": "c0001_0", "concept": "...", "level": "TRACE", "n_levels": 2, "output_contract": "native",
          "agent_id": "example/shop-assistant", "verdict": "Yes", "split": "train", "teacher": "<model id>"}}
```

| `meta` field | Meaning |
|---|---|
| `rubric_id`, `concept`, `level`, `n_levels` | The rubric the record judges. |
| `output_contract` | The output contract of the prompt and the completion. |
| `agent_id` | The agent the trace simulates or comes from. |
| `verdict` | The score label the teacher chose. |
| `split` | The rubric's library split. `rubric_trace_match.assemble` writes its own splits here. |
| `teacher` | The model id that judged the pair. |

The completion follows the prompt's output contract. Most records use the rubric's own contract.
A share are re-served under others (score only, renamed key, score first, key value, XML) so the
judge learns to follow the output instruction it is given. The same judgement is re-serialised, so
no extra annotation is needed. A prompt whose output block cannot be rewritten exactly stays
native.

`output.judgments.jsonl` has one row per pair with `ok`, `why`, `score` and `na`, for quality reports.

## CLI reference

Every CLI prints `--help`. Each example below runs as written once the inputs exist.

### rubric_build

From a concept list:

```bash
python -m judge_data.rubric_build --concepts concepts.jsonl --out out/rubric_library.jsonl \
    --presentations 3 $B
```

From seed rubrics:

```bash
python -m judge_data.rubric_build --seeds seed_rubrics.jsonl --out out/rubric_library.jsonl \
    --filter-unjudgeable --functional-test 20 $B
```

Stages: seeds to concept labels, clean room relabel, clustering into a registry, optional
judgeability filter (seeds only), then rubrics per concept, schema and placeholder checks, clean
room n-gram check (seeds only), optional functional test, repairs, and splits.

Splits are cut on three axes. A share of the concepts (`--holdout-fraction`, default 0.2) is held
out whole, so every rubric of a held out concept is test. Every rubric in a held out scale family
or language is test as well.

Useful flags: `--presentations N` (rubrics per concept), `--holdout-fraction 0.2`,
`--holdout-scale-families ordinal_6,numerical_4,wide_14`, `--holdout-languages ja`,
`--cleanroom-ngram 8`, `--no-cluster`, `--cluster-threshold 0.30`.

Also writes `concepts.jsonl` (the concepts used, reusable with `--concepts`) and
`rubric_build_report.json` next to `--out`.

### rubric_build.gapfill

Author SESSION and TOOL_CALL concepts a library lacks, and write rubrics for them with splits. A
new concept is dropped when it near duplicates a concept already in the library or another new
concept (`--near-dup`, cosine similarity, default 0.90), or when a judge cannot settle it from
trace evidence. The existing library is not modified.

```bash
python -m judge_data.rubric_build.gapfill --library out/rubric_library.jsonl \
    --out out/gapfill_library.jsonl --presentations 5 $B
cat out/rubric_library.jsonl out/gapfill_library.jsonl > out/rubric_library_full.jsonl
```

Also writes `gapfill_concepts.json` (kept and rejected concepts), `gapfill_concepts.jsonl` and
`library_audit.jsonl` (each existing concept with `ok` and `reject_reason` from the judgeability
check).

### rubric_build.variants

Library level output format variants, one record per variant, with id `<rubric_id>#<variant>`.
`annotate` re-serves contracts on its own, so this is optional. Annotate only `base`,
`schema_unfenced` and `numeric` variants directly, since the others do not ask for `reasoning` and
`score`. `--skip-no-task` copies rubrics without task prose as they are.

```bash
python -m judge_data.rubric_build.variants --library out/rubric_library.jsonl \
    --out out/rubric_library.variants.jsonl --variants base,schema_unfenced,nonjson_xml
```

### rubric_build.rerender

Rebuild every prompt that has task prose with the current renderer. Ids, content and splits stay
the same, so existing pairs still resolve. Rubrics without task prose are copied as they are.
A backup is kept.

```bash
python -m judge_data.rubric_build.rerender --library out/rubric_library.jsonl
```

### trace_synth

```bash
python -m judge_data.trace_synth --rubric-library out/rubric_library.jsonl \
    --agent-registry agent_registry.jsonl --out out/pairs.jsonl \
    --traces-per-level 2 --verify $B
```

`--verify` places each trace on absent, partial or full with an independent call that is not told
the target. `--drop-mismatch` keeps only traces that landed in their target bucket. `--splits train`
synthesizes only for train rubrics. `--concepts N` samples N rubrics for a quick run.

### annotate

One step for both kinds of pairs. A file passed to `--pairs` is a pairs JSONL from `trace_synth`.
One or more directories are outputs of `rubric_trace_match.run`. `--source synth` or
`--source matched` overrides the detection.

Synthesized pairs:

```bash
python -m judge_data.annotate --pairs out/pairs.jsonl --out out/output.jsonl \
    --rubric-library out/rubric_library.jsonl --agent-registry agent_registry.jsonl $B
```

This writes `output.jsonl` and `output.judgments.jsonl`.

Matched pairs:

```bash
python -m judge_data.annotate --pairs out/match \
    --rubric-library out/rubric_library.jsonl --out out/annotated --strip-pct 30 $B
```

This writes `annotated.jsonl` into the `--out` directory. Run `rubric_trace_match.assemble` on it
next (see below).

Rubrics are looked up by id in the library, so a re-rendered library takes effect without new
traces. Some options apply to one source only. Passing one for the other source is an error.

| Option | Synthesized pairs | Matched pairs |
|---|---|---|
| `--pairs` | One pairs JSONL file | One or more directories, repeat the flag |
| `--out` | Records JSONL, judgments written beside it | Output directory |
| `--rubric-library` | Default `rubric_library.jsonl` next to `--pairs` | Required |
| `--allow-na`, `--no-na` | N/A off by default | N/A on by default |
| `--max-tokens` | Default 2048 | Default 2000 |
| `--limit N` | First N pairs, default all | First N pairs, default all |
| `--agent-registry` | Shows each agent's full tool catalogue | Not accepted |
| `--splits` | Library splits to annotate, default all | Not accepted |
| `--context-formats` | Default `repr:2,turns:1,flat:1` | Not accepted |
| `--output-contracts` | Default mix, `native:1` turns re-serving off | Not accepted |
| `--strip-pct`, `--strip-list` | Not accepted | Full reasoning removal on a share or list of pairs, default 0 |
| `--no-label-pct` | Not accepted | Percent of records without turn headers, default 50 |
| `--exclude-rubrics` | Not accepted | File of rubric ids to leave out |
| `--workers` | Not accepted | Pairs in parallel, default 64 |

`--context-formats` sets how the conversation is serialised: one Python repr of a message per
line, numbered `Turn N:` blocks, or no headers. `--output-contracts` weights the output contracts
records are re-served under.

On matched pairs, annotation removes reasoning blocks fully on `--strip-pct` percent of pairs (or
the ids in `--strip-list`), removes only leaky blocks elsewhere, and drops records whose evidence
still leaks a target label. It records each choice in `meta`. It appends as it goes, so a rerun
resumes.

### rubric_trace_match

Match, annotate, assemble, verify:

```bash
python -m judge_data.rubric_trace_match.run --rubric-library out/rubric_library.jsonl \
    --traces trace_pool.jsonl --traces-limit 5000 --cap 6 --out out/match $B

python -m judge_data.annotate --pairs out/match \
    --rubric-library out/rubric_library.jsonl --out out/annotated --strip-pct 30 $B

python -m judge_data.rubric_trace_match.assemble --annotated out/annotated \
    --rubric-library out/rubric_library.jsonl --out out/training

python -m judge_data.rubric_trace_match.verify --file out/training/training.jsonl \
    --rubric-library out/rubric_library.jsonl
```

`run` asks the model which behaviours each rubric needs and each trace shows, then scores every
pair, gates by level, picks the target turn or tool call, and keeps the top `--cap` per rubric
under a per agent cap. Sampling is stratified on the trace `tags` named by `--strata`
(default `topic,flow_type`) and over samples long traces and traces with failed tool calls.
`--splits train` matches only train rubrics.

The annotate step is the one described under `annotate` above, with matched pairs. Every stage
appends as it goes, so a rerun resumes.

`assemble` fences the targets, holds N/A judgements back in their own file, recomputes splits,
refuses to write a contaminated split, and writes `<name>.jsonl`, one file per split,
`slices/<axis>=<value>.txt` id lists and `manifest.json`. Records keep the training record `meta`
above. The splits are:

| Split | What is held out |
|---|---|
| `test_trace` | A hash chosen share of all traces (`--trace-cut`, per 10,000, default 500). Every record on a chosen trace is held out. |
| `test_lang` | Every rubric in a language the library held out. |
| `test_axis` | Up to `--axis-concepts` held out concepts, and every rubric in `--axis-scale-families` (default `wide_14`). |
| `train` | Everything else. |

A rubric in the library's train split never moves to `test_lang` or `test_axis`. If a train rubric
carries a requested language or scale family, that value is not held out and `assemble` says so.
The contamination checks assert that no held out trace, rubric, concept, language or scale family
appears in train.

`verify` checks every record for the contracts it claims: shape, id and meta agreement, score in
the rubric's scale, reasoning stripped when labelled so, no leftover placeholder, no label leak.
`--teacher MODEL` also flags records judged by another model. It checks matched pair output only
(`--annotated` or an assembled `--file`). Synthesized records use other ids and re-served output
contracts, so its checks do not fit them.

### Recipe

`recipes/build_training_data.sh` chains rubric_build, trace_synth and annotate. See
`recipes/README.md`.

```bash
bash recipes/build_training_data.sh --concepts concepts.jsonl --agents agent_registry.jsonl \
    --out out --presentations 3 --traces-per-level 2 --verify $B
```

## Embeddings

Concept deduplication (seeds and gapfill) needs sentence embeddings. Choose with
`--embed-backend`.

| Value | Source |
|---|---|
| `openai` | `/v1/embeddings` at `--embed-base-url` with `--embed-model` (vLLM can serve this) |
| `sentence-transformers` | A local model (`--embed-model`, default `sentence-transformers/all-MiniLM-L6-v2`). Needs the `[embed]` extra. |
| `hash` | Hashed word counts. No model and no network. Catches near verbatim duplicates only. |
| `auto` (default) | `openai` if a base URL is given, else `sentence-transformers` if installed, else `hash` |

If the chosen embedder fails, the run logs a warning and falls back to `hash`. Clustering uses
scikit-learn when the `[cluster]` extra is installed and a greedy leader clustering otherwise.

## Tests

No network and no GPU. The end to end tests run every CLI and the recipe with `--backend mock`.

```bash
uv run --with pytest pytest
```

## Scope

This package builds training data. No rubric, concept, agent or trace data ships here.
