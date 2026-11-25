# Recipes

A recipe is pure orchestration. It chains the module CLIs and passes paths and backend flags.
All logic lives in the modules (`rubric_build`, `trace_synth`, `annotate`).
Here `$B` stands for the backend flags, for example `--backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD`.

## build_training_data.sh

Concepts (or seed rubrics) plus an agent registry go in. SFT records come out.

| Stage | CLI | Output in `--out` |
|---|---|---|
| 1. Rubric library | `python -m judge_data.rubric_build` | `rubric_library.jsonl`, `concepts.jsonl`, `rubric_build_report.json` |
| 2. Trace synthesis | `python -m judge_data.trace_synth` | `pairs.jsonl` |
| 3. Annotation | `python -m judge_data.annotate` | `output.jsonl`, `output.judgments.jsonl` |

Stage 1 is skipped when you pass `--rubric-library`.

Stage 1 cuts held out splits by concept, scale family and language. A share of the concepts is
held out whole. Stages 2 and 3 cover every split unless you run them yourself with
`--splits train`. Each record in `output.jsonl` is `{id, prompt, completion, meta}`, and `meta`
holds `rubric_id, concept, level, n_levels, output_contract, agent_id, verdict, split, teacher`.
See the main README for every schema.

### Flags

| Flag | Meaning |
|---|---|
| `--concepts FILE` | Concept list JSONL. Stage 1 generates rubrics from it. |
| `--seeds FILE` | Seed rubrics JSONL. Stage 1 extracts concepts first. |
| `--rubric-library FILE` | Reuse a library and skip stage 1. |
| `--agents FILE` | Agent registry JSONL. Required. |
| `--out DIR` | Output directory. Required. |
| `--presentations N` | Rubrics per concept (default 1). |
| `--traces-per-level N` | Traces per score level of each rubric (default 1). |
| `--verify` | Place each trace on absent, partial or full with an independent call. |
| `--seed N` | Random seed (default 2026). |
| `--synth-max-tokens N` | Max tokens for one synthesized trace (default 8192). |
| `--backend`, `--model-id`, `--base-url`, `--api-key`, `--cache`, `--concurrency`, `--chat-template-kwargs` | Model backend, passed to every stage. |
| `--region`, `--aws-profile`, `--role-arn`, `--no-temperature`, `--additional-model-request-fields` | Bedrock backend options. |
| `--embed-backend`, `--embed-model`, `--embed-base-url`, `--embed-api-key` | Embeddings for concept dedup (seeds only). |

Set `PYTHON` to pick the interpreter, for example `PYTHON="uv run python"`.

### Examples

Self-hosted model behind vLLM. Several replicas can be comma separated.

```bash
bash recipes/build_training_data.sh \
    --concepts concepts.jsonl --agents agent_registry.jsonl --out out \
    --backend vllm --base-url http://localhost:8000/v1,http://localhost:8001/v1 \
    --model-id MiMo-V2.6-Pro-MOPD --concurrency 256 \
    --presentations 3 --traces-per-level 2 --verify
```

Amazon Bedrock with any model id the Converse API serves.

```bash
bash recipes/build_training_data.sh \
    --concepts concepts.jsonl --agents agent_registry.jsonl --out out \
    --backend bedrock --model-id <bedrock-model-id> --region us-west-2
```

Dry run with canned replies. No model, no network.

```bash
bash recipes/build_training_data.sh \
    --concepts ../examples/concepts.sample.jsonl --agents ../examples/agents.sample.jsonl --out /tmp/judge-dry-run \
    --backend mock --cache none
```

Re-annotating existing pairs with another teacher is stage 3 on its own.

```bash
python -m judge_data.annotate --pairs out/pairs.jsonl --out out/output_teacher2.jsonl \
    --rubric-library out/rubric_library.jsonl --agent-registry agent_registry.jsonl \
    --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD \
    --cache out/teacher2_cache.sqlite
```

## One annotation step for both kinds of pairs

Stage 3 is `python -m judge_data.annotate`. It also annotates matched pairs, the output of
`rubric_trace_match` on an existing trace pool. A file passed to `--pairs` means synthesized
pairs. One or more directories mean matched pairs. `--source synth|matched` overrides this.

| Option | Synthesized pairs (this recipe) | Matched pairs |
|---|---|---|
| `--pairs` | One pairs JSONL file | One or more directories |
| `--out` | Records JSONL | Output directory |
| `--rubric-library` | Default next to `--pairs` | Required |
| N/A option for the teacher | Off, `--allow-na` turns it on | On, `--no-na` turns it off |
| `--max-tokens` | 2048 | 2000 |
| `--agent-registry`, `--splits`, `--context-formats`, `--output-contracts` | Accepted | Rejected |
| `--strip-pct` (0), `--strip-list`, `--no-label-pct` (50), `--exclude-rubrics`, `--workers` (64) | Rejected | Accepted |

Matched pairs write `annotated.jsonl` into `--out`. Assemble and verify follow.

```bash
python -m judge_data.rubric_trace_match --rubric-library out/rubric_library.jsonl \
    --traces trace_pool.jsonl --cap 6 --out out/match $B
python -m judge_data.annotate --pairs out/match \
    --rubric-library out/rubric_library.jsonl --out out/annotated --strip-pct 30 $B
python -m judge_data.rubric_trace_match.assemble --annotated out/annotated \
    --rubric-library out/rubric_library.jsonl --out out/training
python -m judge_data.rubric_trace_match.verify --file out/training/training.jsonl \
    --rubric-library out/rubric_library.jsonl
```

`verify` checks matched pair output only. Its id and output contract checks do not fit the
synthesized `output.jsonl`. The main README lists every option.
