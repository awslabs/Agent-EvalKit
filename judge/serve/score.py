"""Score one agent trace against one rubric with a judge served behind an OpenAI compatible endpoint.

    python score.py --base-url http://localhost:8000/v1 --model judge \
        --rubric-library ../examples/rubrics.sample.jsonl --rubric-id gen_01895 \
        --evidence example_evidence.json

The evidence file maps slot names to text. A rubric lists the slots it reads in `placeholders`:
`context` (the conversation), `assistant_turn` (the response being judged), `available_tools`
(the tool catalogue), and `tool_turn` (the tool call being judged).

The prompt is rendered with the same code that built the training data, so the judge sees exactly
the layout it was trained on. Prints one JSON object with the score and the judge's reasoning.
"""
from __future__ import annotations

import argparse
import json
import sys

from judge_data.annotate.parse import parse
from judge_data.annotate.render import fill, load_rubric
from judge_data.clients import make_client
from judge_data.utils.jsonx import extract_json


def score(client, rubric: dict, evidence: dict[str, str], max_tokens: int = 1024) -> dict:
    missing = [s for s in rubric.get("placeholders") or [] if not str(evidence.get(s, "")).strip()]
    if missing:
        return {"ok": False, "why": f"no evidence for slot(s) {missing}"}
    res = client.invoke(fill(rubric, evidence), max_tokens=max_tokens, temperature=0.0)
    if not res.ok:
        return {"ok": False, "why": res.error}
    enum = rubric.get("output_enum") or rubric.get("score_enum") or []
    out = parse(res.text, enum, extract_json)
    out.update(rubric_id=rubric["rubric_id"], output_tokens=res.output_tokens)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base-url", required=True, help="OpenAI compatible endpoint, ending in /v1")
    ap.add_argument("--model", required=True, help="served model name")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--rubric-library", required=True)
    ap.add_argument("--rubric-id", required=True)
    ap.add_argument("--evidence", required=True, help="JSON file mapping slot names to text")
    ap.add_argument("--max-tokens", type=int, default=1024)
    a = ap.parse_args()

    client = make_client("vllm", model_id=a.model, base_url=a.base_url, api_key=a.api_key, cache_path=None)
    rubric = load_rubric(a.rubric_library, a.rubric_id)
    evidence = json.load(open(a.evidence))
    out = score(client, rubric, evidence, a.max_tokens)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
