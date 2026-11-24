# Judge model

Build training data for a small judge model and fine-tune it. The judge scores agent traces against rubrics that you
or your customers write, at three levels: one response (`TRACE`), a whole conversation (`SESSION`), or one tool call
(`TOOL_CALL`).

| Directory | What it does |
|---|---|
| [`datagen/`](datagen/) | Build a rubric library, pair rubrics with traces or synthesize traces for them, and annotate the pairs with a teacher model |
| [`train/`](train/) | Fine-tune a model on the annotated records with Hugging Face TRL and FSDP |
| [`serve/`](serve/) | Serve a trained judge with vLLM and score traces from your own evaluation code |
| [`examples/`](examples/) | Sample training records, rubrics, and concepts, so you can see the exact formats |

The two packages have separate environments, because training needs CUDA kernels that data generation does not.

## Quick start

```bash
# 1. Generate training data with any teacher model you can call
cd datagen
uv venv && uv pip install -e .
B="--backend vllm --base-url http://localhost:8000/v1 --model-id <teacher-model>"
bash recipes/build_training_data.sh --concepts ../examples/concepts.sample.jsonl \
    --agents ../examples/agents.sample.jsonl --out out --presentations 3 --traces-per-level 2 --verify $B

# 2. Fine-tune
cd ../train
bash scripts/setup.sh
python -m judge_train.data.prepare --config configs/examples/qwen3.5-9b.yaml --num-proc 32
bash scripts/launch.sh configs/examples/qwen3.5-9b.yaml
```

Point `data.train_path` in the training config at the `output.jsonl` that step 1 writes.

Then serve the checkpoint and score traces with it. See [`serve/`](serve/).

## What is released

- The code in `datagen/`, `train/`, and `serve/`.
- Samples of the training records, rubrics, and rubric concepts in `examples/`, with their licenses and third-party
  notices in [`examples/README.md`](examples/README.md#licenses) and [`examples/THIRD_PARTY_NOTICES.md`](examples/THIRD_PARTY_NOTICES.md).

The full training corpus is not released. The evaluation benchmark will be released later.
