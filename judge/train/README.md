# Judge model training

Supervised fine-tuning (SFT) for the Agent-EvalKit judge model.
It does full fine-tuning of Qwen3.5 models with the Hugging Face TRL `SFTTrainer` and FSDP.
Training data is prompt-completion JSONL, and the loss covers the completion tokens only.

The example configs hold the exact recipe used for every released judge checkpoint.

## Contents

- [Install](#install)
- [Data format](#data-format)
- [Two data paths](#two-data-paths)
- [Launch training](#launch-training)
- [Default recipe](#default-recipe)
- [Checkpoints](#checkpoints)
- [Serve with vLLM](#serve-with-vllm)
- [Experiment tracking](#experiment-tracking)
- [Qwen3.5 constraints](#qwen35-constraints)
- [Tests](#tests)
- [Layout](#layout)

## Install

You need Linux, NVIDIA GPUs, a CUDA 12.8 toolkit (for compiling the kernels), and [uv](https://docs.astral.sh/uv/).

```bash
cd judge/train
bash scripts/setup.sh            # full install, including the CUDA kernels (up to an hour)
bash scripts/setup.sh --quick    # skip the kernel builds (fine for CPU tests)
source .venv/bin/activate
```

The script creates `.venv`, installs PyTorch 2.11.0 built for CUDA 12.8 from the PyTorch index, then installs this
package with the `qwen35` and `dev` extras. `constraints.txt` pins transformers, TRL, accelerate, and the other
libraries to the versions the released judges were trained with. A plain `uv pip install -e .` would pick up newer
releases, and newer releases of these libraries change behavior often enough to matter.

The full install also installs `causal-conv1d` and `flash-attn`, compiling them if no prebuilt wheel matches.
Compiling `flash-attn` took about 45 minutes with the default `MAX_JOBS=4` on an 8-GPU H100 node. Raise `MAX_JOBS` if
the machine has the memory for it, since each job can use several GB. The
compiler has to be the same CUDA version as PyTorch. The script uses `/usr/local/cuda-12.8` when it exists and
otherwise `/usr/local/cuda`. Set `CUDA_HOME` to point somewhere else. Set `TORCH_VERSION` and `TORCH_CUDA` (for
example `cu130`) only if you know your kernels and GPUs need a different build.
Qwen3.5 uses GatedDeltaNet linear attention, and these kernels plus `flash-linear-attention` make it 3 to 5 times faster.
Without them you will see this warning and training falls back to a slow PyTorch path:

```
The fast path is not available because one of the required library is not installed.
```

Set `TORCH_CUDA_ARCH_LIST` to match your GPUs before a full install. The default is `9.0` for H100 and H200.
Set `EXTRAS=qwen35,dev,mlflow` to also install MLflow.

Download a base model to a local directory:

```bash
huggingface-cli download Qwen/Qwen3.5-4B --local-dir ./models/Qwen3.5-4B
```

A local path is safer than a Hub ID for multi-node runs because every process reads the same files.

## Data format

Each line of the training JSONL is one example.

```json
{"id": "ex-001",
 "prompt": [{"role": "system", "content": "You are an evaluator."},
            {"role": "user", "content": "Rate this agent response from 1 to 5. ..."}],
 "completion": [{"role": "assistant", "content": "{\"reasoning\": \"...\", \"score\": 4}"}]}
```

- `prompt` is a list of chat messages. It must end with a `user` or `tool` message.
- `completion` holds the assistant message the model should learn to produce.
- `id` is optional. Extra keys such as `meta` are ignored.
- Roles can be `system`, `user`, `assistant`, and `tool`.

The prompt is rendered with the chat template and `add_generation_prompt=True`.
The full conversation is rendered without it.
Tokens past the prompt get loss. Prompt tokens get label `-100`.

Plain chat data is also supported with `data.format: messages` and rows like `{"messages": [...]}`.
In that case the loss covers the whole sequence.

`data.train_path` accepts a file or a glob such as `./data/*.jsonl`.

## Two data paths

**Pre-tokenized (Stage A then Stage B).** Use this for real runs.
Stage A tokenizes once on CPU and writes an Arrow dataset.
Stage B trains from it, so GPU nodes do no tokenization work.

```bash
# Stage A: needs data.tokenized_data_path in the config
python -m judge_train.data.prepare --config configs/examples/qwen3.5-4b.yaml --num-proc 32

# Stage B: the same config now reads the Arrow dataset
bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
```

Stage A writes `dataset/` and `metadata.json` under `data.tokenized_data_path`.
`metadata.json` records the source, tokenizer, max length, and how many records were kept or skipped.

**Inline.** Use this for small runs and debugging.
Remove `data.tokenized_data_path` from the config and `SFTTrainer` tokenizes the JSONL at startup.

Both paths produce the same token ids and completion masks for valid records.
Stage A also drops bad records and counts them in `metadata.json`.
It drops a record when the prompt does not end with a `user` or `tool` message, when the prompt is not a token prefix of the full conversation, or when truncation to `max_length` removes the whole completion.
The inline path only logs a warning for a prefix mismatch and keeps the record.

To check which tokens get loss before a long run:

```bash
python -m judge_train.data.verify_labels --config configs/examples/qwen3.5-0.8b.yaml --num-samples 5
```

It prints, for a few samples, how many tokens are masked and the decoded text that is trained on.
It loads the model once, so run it where the model fits in memory.

## Launch training

`scripts/launch.sh` wraps `accelerate launch` with `configs/accelerate/fsdp.yaml`.

Single node, all local GPUs:

```bash
bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
```

Multi-node: run the same command on every node and set these variables.

| Variable | Meaning | Default |
|---|---|---|
| `NUM_NODES` | total number of nodes | `1` |
| `NODE_RANK` | rank of this node, from 0 to `NUM_NODES - 1` | `0` |
| `MASTER_ADDR` | address of node 0, reachable from all nodes | `127.0.0.1` |
| `MASTER_PORT` | rendezvous port on node 0 | `29500` |
| `GPUS_PER_NODE` | processes per node | GPUs found by `nvidia-smi` |

```bash
# node 0
NUM_NODES=4 NODE_RANK=0 MASTER_ADDR=10.0.0.1 bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
# nodes 1, 2, 3
NUM_NODES=4 NODE_RANK=1 MASTER_ADDR=10.0.0.1 bash scripts/launch.sh configs/examples/qwen3.5-4b.yaml
```

Any scheduler or launcher works. It only has to start the script once per node with these variables.
Set `RDZV_BACKEND=c10d` if nodes may start in any order.

You can also call accelerate directly:

```bash
accelerate launch --config_file configs/accelerate/fsdp.yaml \
    --num_processes 8 -m judge_train.train --config configs/examples/qwen3.5-4b.yaml
```

For a quick single-process debug run, set `training.fsdp: null` and run `python -m judge_train.train --config <config>`.
Set `training.use_cpu: true` to force CPU on a machine without CUDA.

Checkpoints go to `{training.output_dir}/{training.exp_name}/checkpoint-{step}/`.
Set `training.resume: auto` to continue from the latest checkpoint there.
Resuming needs optimizer state, so also set `training.save_only_model: false`.

## Default recipe

These values are the defaults in `src/judge_train/config.py` and in every example config.

| Setting | Value |
|---|---|
| `data.max_length` | 8192 |
| `data.packing` | false |
| `data.format` | prompt_completion |
| `data.chat_template_kwargs` | `{enable_thinking: false}` |
| `training.num_train_epochs` | 1 |
| `training.per_device_train_batch_size` | 1 |
| `training.gradient_accumulation_steps` | 4 |
| `training.learning_rate` | 5.0e-6 |
| `training.lr_scheduler_type` | cosine |
| `training.warmup_ratio` | 0.05 |
| `training.weight_decay` | 0.01 |
| `training.max_grad_norm` | 1.0 |
| `training.bf16` | true |
| `training.gradient_checkpointing` | false |
| `training.fsdp` | full_shard |
| `training.save_strategy` / `save_steps` | steps / 1000 |
| `training.save_only_model` | true |
| `training.save_total_limit` | 2 |
| `training.logging_steps` | 10 |
| `training.completion_only_loss` | true |
| `seed` | 42 |
| `attn_implementation` | flash_attention_2 |

The two exceptions in the code defaults are `chat_template_kwargs` and `fsdp`.
They are unset in code so a minimal config also works for other models and single-process runs.

The global batch is `nodes x GPUs per node x per_device_train_batch_size x gradient_accumulation_steps`.
The recipe ran on 4 nodes with 8 GPUs each, which gives 4 x 8 x 1 x 4 = 128.
To keep 128 sequences per step on fewer GPUs, raise `gradient_accumulation_steps`.

| GPUs | `gradient_accumulation_steps` |
|---|---|
| 8 (1 node) | 16 |
| 16 (2 nodes) | 8 |
| 32 (4 nodes) | 4 |

Activation checkpointing comes from `fsdp_activation_checkpointing: true` in the accelerate config.
Keep `training.gradient_checkpointing: false` when FSDP is on. Setting both can hang NCCL, and the config loader rejects it.

## Checkpoints

There is no final `save_model()` call at the end of training.
On large multi-node FSDP runs one big consolidated save can stall long enough to trip the NCCL watchdog.
Checkpoints come only from `save_strategy`, so `save_strategy: "no"` saves nothing.

FSDP saves fp32 weights. Convert them to bf16 shards after training:

```bash
# every checkpoint-{step}/ in the run dir -> checkpoint-{step}-bf16/
python -m judge_train.utils.bf16_save ./outputs/judge-qwen3.5-4b

# or one checkpoint to a chosen destination
python -m judge_train.utils.bf16_save ./outputs/judge-qwen3.5-4b/checkpoint-1000 --dst ./outputs/judge-4b-bf16
```

Each bf16 directory is self-contained. It has 5 GB weight shards, the tokenizer, the chat template, and the processor configs.
Optimizer and RNG files are left out. The fp32 checkpoint is not changed.

For Qwen3.5 the trainer copies `preprocessor_config.json` and `video_preprocessor_config.json` from the base model into each checkpoint.
vLLM needs them to load Qwen3.5 checkpoints.

### LoRA

Set `lora.enabled: true` to train a LoRA adapter instead of the full model.
The defaults are `r: 16`, `alpha: 32`, `dropout: 0.05`, on all attention and MLP projections.
LoRA usually needs a higher learning rate than full fine-tuning, for example `1.0e-4`.

Merge the adapter into the base before serving:

```bash
python -m judge_train.utils.merge_lora ./outputs/my-lora-run/checkpoint-1000 --dst ./outputs/my-lora-merged
```

The merge works on tensors and keeps the Qwen3.5 multimodal architecture.
The result is a plain bf16 model.
On Qwen3.5, serving the merged model gives better outputs than serving the adapter with `--enable-lora`.

## Serve with vLLM

Point vLLM at a bf16 checkpoint directory:

```bash
vllm serve ./outputs/judge-qwen3.5-4b/checkpoint-1000-bf16 \
    --served-model-name judge \
    --max-model-len 8192
```

The judge was trained with thinking disabled. Pass the same setting at inference:

```bash
curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
  "model": "judge",
  "messages": [{"role": "user", "content": "Rate this agent response from 1 to 5. ..."}],
  "temperature": 0,
  "chat_template_kwargs": {"enable_thinking": false}
}'
```

With the OpenAI Python client, pass `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`.

## Experiment tracking

Tracking uses the standard Hugging Face `report_to` setting. The default is `none`.
Set `training.report_to` to `mlflow`, `wandb`, `tensorboard`, or a list of them.
Configure each tool with its usual environment variables.
For MLflow that means `MLFLOW_TRACKING_URI` and `MLFLOW_EXPERIMENT_NAME`.
`training.run_name` sets the run name and defaults to `training.exp_name`.

## Qwen3.5 constraints

The trainer checks these when the model type is Qwen3.5.

- No packing. GatedDeltaNet keeps recurrent state per sequence.
- No DeepSpeed. GatedDeltaNet kernels under ZeRO give loss 0 or NaN. Use FSDP or DDP.
- Use bf16. Qwen3.5 RMSNorm overflows in float16.
- Set `chat_template_kwargs: {enable_thinking: false}`. Otherwise the generation prompt opens a think block that the training target does not have.
- Without FSDP, `ddp_find_unused_parameters` is turned on automatically.
- `flash-linear-attention` is pinned to 0.4.2 because 0.5.0 corrupts outputs.

## Tests

The tests run on CPU with no network and no downloads.
They build a tiny tokenizer and a 2-layer model in a temp directory.

```bash
uv run --extra dev pytest
```

They cover config parsing, the record schema, tokenization and completion masks, Stage A round trips, label masking through the TRL collator, parity between the inline and pre-tokenized paths, a short CPU training run, bf16 conversion, and LoRA merging.

## Layout

```
configs/
  accelerate/fsdp.yaml        FSDP settings for accelerate launch
  examples/qwen3.5-*.yaml     the released recipe for 0.8B, 4B, and 9B
scripts/
  setup.sh                    uv environment with CUDA kernels
  launch.sh                   accelerate launch wrapper, single or multi-node
src/judge_train/
  config.py                   YAML to dataclasses, defaults, validation
  data/
    schema.py                 record schemas
    loader.py                 JSONL and glob reading
    tokenization.py           chat template tokenization and completion masks
    build.py                  datasets for the inline and pre-tokenized paths
    prepare.py                Stage A CLI
    verify_labels.py          loss mask inspection CLI
  train/
    sft.py                    trainer entry point (python -m judge_train.train)
    callbacks.py              copies processor configs into checkpoints
  utils/
    bf16_save.py              bf16 shard conversion CLI
    merge_lora.py             LoRA merge CLI
tests/
```
