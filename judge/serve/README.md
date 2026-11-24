# Serve the judge

A trained judge is a regular Hugging Face checkpoint. Serve it with vLLM, then call it from any evaluation code that
can talk to an OpenAI compatible endpoint, including the evaluation code EvalKit writes for your agent.

## Start the server

```bash
vllm serve ./outputs/judge-qwen3.5-9b/checkpoint-3846 \
    --served-model-name judge --dtype bfloat16 \
    --tensor-parallel-size 1 --max-model-len 65536
```

Use `--tensor-parallel-size 2` or more for 27B models. Set `--max-model-len` to cover your longest traces plus about
1,000 tokens for the reply. The judges were trained with thinking off, so send
`chat_template_kwargs={"enable_thinking": false}` with every request. `score.py` does this for you.

## Score a trace

```bash
cd judge/datagen && uv venv && uv pip install -e . && cd ../serve
../datagen/.venv/bin/python score.py --base-url http://localhost:8000/v1 --model judge \
    --rubric-library ../examples/rubrics.sample.jsonl --rubric-id gen_01895 \
    --evidence example_evidence.json
```

The reply is one JSON object:

```json
{"ok": true, "na": false, "score": "Partial Compliance", "reasoning": "...", "rubric_id": "gen_01895", "output_tokens": 347}
```

`example_evidence.json` is a short flight search where the agent lists a 13:05 departure although the user asked for
flights after 3pm. Rubric `gen_01895` asks whether the final output meets each requirement of the task. A 4B judge trained
with this pipeline on MiMo data answers `Partial Compliance` and names the 13:05 flight as the violation.

## Use it from your own evaluation code

Render the prompt with the same code that built the training data. The judge then sees exactly the layout it learned,
and its reply parses with the same parser:

```python
from judge_data.annotate.render import load_rubric
from judge_data.clients import make_client
from score import score

client = make_client("vllm", model_id="judge", base_url="http://localhost:8000/v1", cache_path=None)
rubric = load_rubric("rubrics.jsonl", "my_rubric_id")
result = score(client, rubric, {"context": conversation_text, "available_tools": tools_json})
```

Any rubric built with `judge_data.rubric_build` works the same way, including rubrics you write for your own domain.

A judge can also be called with a prompt you write yourself, as long as it asks for a JSON object with `reasoning`
and `score`. Expect the best agreement with prompts in the layouts it was trained on.
