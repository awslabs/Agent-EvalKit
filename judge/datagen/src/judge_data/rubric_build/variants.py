"""Output format variants of library rubrics. Pure logic, no LLM.

Given a base rubric, produce variants that differ in output contract (JSON shape, fencing, key
names, non JSON formats) while keeping the evaluation criteria identical.

These are library level variants: each one is a separate rubric record with its own id
(`<rubric_id>#<variant_id>`, the base keeps its id) in the library record schema.
`annotate.contracts` does the same job at annotation time without multiplying the library, and is
what the recipe uses. Note that `annotate` expects a reply with `reasoning` and `score`, so
annotate only the `base`, `schema_unfenced` and `numeric` variants directly.

    python -m judge_data.rubric_build.variants --library rubric_library.jsonl \
        --out rubric_library.variants.jsonl [--variants base,schema_unfenced,nonjson_xml]
"""
from __future__ import annotations

# Variant contracts: how the model is asked to format its answer.
CONTRACTS = {
    "base": {
        "desc": "fenced JSON, reasoning before score",
        "transform": lambda p: p,
    },
    "contract_bare_verdict": {
        "desc": "bare verdict only, no reasoning, no fence",
        "transform": lambda p: _swap_schema(p, verdict_only=True),
    },
    "contract_fenced_verdict": {
        "desc": "fenced JSON with verdict only",
        "transform": lambda p: _swap_schema(p, verdict_only=True, fenced=True),
    },
    "nonjson_keyvalue": {
        "desc": "key: value text format instead of JSON",
        "transform": lambda p: _to_keyvalue(p),
    },
    "nonjson_xml": {
        "desc": "XML tags instead of JSON",
        "transform": lambda p: _to_xml(p),
    },
    "schema_unfenced": {
        "desc": "JSON schema shown without code fence",
        "transform": lambda p: _unfence_schema(p),
    },
    "numeric": {
        "desc": "numeric form: bare float, no label",
        "transform": lambda p: _numeric_form(p),
    },
}


def format_variants(rubric: dict, variant_ids: list[str] | None = None) -> list[dict]:
    """Generate output-format variants of a base rubric.

    Args:
        rubric: dict with at least 'rendered_prompt', 'rubric_id', 'score_enum'
        variant_ids: which variants to produce (default: all of CONTRACTS).
            Each must be a key in CONTRACTS.

    Returns:
        list of rubric dicts. A variant's id is `<rubric_id>#<variant_id>`, the base keeps its id.
    """
    if variant_ids is None:
        variant_ids = list(CONTRACTS.keys())

    base_prompt = rubric.get("rendered_prompt", "")
    results = []
    for vid in variant_ids:
        if vid not in CONTRACTS:
            continue
        contract = CONTRACTS[vid]
        new = dict(rubric)
        new["rendered_prompt"] = contract["transform"](base_prompt)
        if vid != "base":
            new["rubric_id"] = f"{rubric.get('rubric_id', '')}#{vid}"
        results.append(new)
    return results


# ── Internal transform helpers ──────────────────────────────────────────────

def _swap_schema(prompt: str, verdict_only: bool = False, fenced: bool = False) -> str:
    """Replace the JSON schema section with a simpler one."""
    schema_start = prompt.find("The output should be a well-formatted JSON")
    if schema_start < 0:
        schema_start = prompt.find("Here is the output JSON schema")
    if schema_start < 0:
        return prompt
    suffix_start = prompt.find("Do not return any preamble", schema_start)
    if suffix_start < 0:
        return prompt

    if verdict_only:
        replacement = ('Output only the score as a single word, nothing else.'
                       if not fenced
                       else 'Output the score in a JSON object: ```json\n{"score": "<your score>"}\n```')
    else:
        replacement = prompt[schema_start:suffix_start]
    return prompt[:schema_start] + replacement + "\n\n" + prompt[suffix_start:]


def _to_keyvalue(prompt: str) -> str:
    """Replace JSON output instruction with key: value format."""
    marker = "The output should be a well-formatted JSON"
    i = prompt.find(marker)
    if i < 0:
        return prompt
    end = prompt.find("Do not return any preamble", i)
    if end < 0:
        return prompt
    replacement = ("Output your answer as:\nreasoning: <your reasoning>\n"
                   "score: <your score>\n\nUse exactly these keys.")
    return prompt[:i] + replacement + "\n\n" + prompt[end:]


def _to_xml(prompt: str) -> str:
    """Replace JSON output instruction with XML format."""
    marker = "The output should be a well-formatted JSON"
    i = prompt.find(marker)
    if i < 0:
        return prompt
    end = prompt.find("Do not return any preamble", i)
    if end < 0:
        return prompt
    replacement = ("Output your answer as:\n<evaluation>\n  <reasoning>...</reasoning>\n"
                   "  <score>...</score>\n</evaluation>")
    return prompt[:i] + replacement + "\n\n" + prompt[end:]


def _unfence_schema(prompt: str) -> str:
    """Remove code fences around the JSON schema shown in the prompt."""
    schema_head = "Here is the output JSON schema:"
    i = prompt.find(schema_head)
    if i < 0:
        return prompt
    rest = prompt[i + len(schema_head):]
    body = rest.lstrip("\n")
    if body.startswith("```"):
        lines = body.split("\n")
        inner = []
        in_fence = False
        for line in lines:
            if line.strip().startswith("```") and not in_fence:
                in_fence = True
                continue
            if line.strip() == "```" and in_fence:
                in_fence = False
                continue
            if in_fence:
                inner.append(line)
        return prompt[:i + len(schema_head)] + "\n" + "\n".join(inner) + rest[len(body):]
    return prompt


def _numeric_form(prompt: str) -> str:
    """Transform to the numeric form: score is a bare float."""
    return prompt.replace('"score"', '"score" (a number between 0.0 and 1.0)')


def main() -> None:
    import argparse

    from judge_data.rubric_build.assemble import write_corpus
    from judge_data.utils.io import read_jsonl

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", required=True, help="Rubric library JSONL")
    ap.add_argument("--out", required=True, help="Output JSONL with every variant of every rubric")
    ap.add_argument("--variants", default=None,
                    help=f"Comma separated subset of: {','.join(CONTRACTS)} (default: all)")
    ap.add_argument("--skip-no-task", action="store_true",
                    help="Copy rubrics without task prose as they are")
    a = ap.parse_args()
    vids = a.variants.split(",") if a.variants else None
    bad = set(vids or []) - set(CONTRACTS)
    if bad:
        raise SystemExit(f"unknown variants {sorted(bad)}")
    out = []
    for r in read_jsonl(a.library):
        if a.skip_no_task and not r.get("task"):
            out.append(r)
            continue
        out.extend(format_variants(r, vids))
    write_corpus(out, a.out)
    print(f"{len(out)} rubric records -> {a.out}")


if __name__ == "__main__":
    main()
