"""Render a generated rubric into the prompt a judge receives. Pure logic, no LLM.

`generate.batch_generate` returns a rubric as prose (`task`) plus a `scale`. What a judge actually
sees takes one of two layouts:

  sectioned  evidence first in sections under `<<CONVERSATION_CONTEXT>>` style markers, then the
             task, the scale as a bullet list, and a JSON schema output block
  compact    the task with `{context}` style slots under headings, the scale as one
             `label: definition` line, and an indented output block

The evidence slots depend on the evaluation level (SESSION sees the tool catalogue, TOOL_CALL also
sees the judged call). Rendering both layouts from one table keeps a filler able to find every
slot.

`render_record` emits the rubric library record schema. Output contract variants come from
`variants.py` and `annotate.contracts`.
"""
from __future__ import annotations

import json
import random
import re

IMPORTANT_NOTE = ("**IMPORTANT**: The agent prompt and tools ALWAYS takes priority over "
                  "your own knowledge.")

SECTIONED_PREAMBLE = ("You are an expert evaluator. Evaluate the AI response according to the "
                      "evaluator-specific task, rubric, and instructions that follow.")

# Evidence sections per level, in render order:
# (section heading, slot name, open tag, close tag, marker)
EVIDENCE = {
    "SESSION": [
        ("### Context", "context", "<context>", "</context>", "<<CONVERSATION_CONTEXT>>"),
        ("### Available Tools", "available_tools", "<available_tools>", "</available_tools>",
         "<<AVAILABLE_TOOLS_CATALOG>>"),
    ],
    "TRACE": [
        ("### Context", "context", "<context>", "</context>", "<<CONVERSATION_CONTEXT>>"),
        ("### Assistant Turn", "assistant_turn", "<assistant_response>", "</assistant_response>",
         "<<ASSISTANT_FINAL_TURN>>"),
    ],
    "TOOL_CALL": [
        ("### Context", "context", "<context>", "</context>", "<<CONVERSATION_CONTEXT>>"),
        ("### Available Tools", "available_tools", "<available_tools>", "</available_tools>",
         "<<AVAILABLE_TOOLS_CATALOG>>"),
        ("### Target Tool Call", "tool_turn", "<tool_call>", "</tool_call>",
         "<<JUDGED_TOOL_CALL>>"),
    ],
}

# Headings that frame {context} in the compact layout.
CONTEXT_HEADINGS = [
    "## Conversation record", "## Conversation History", "## Previous turns:",
    "## Conversation history ##", "## Context",
]
# A session judge sees every turn, so "previous" turns would mislabel them.
SESSION_HEADINGS = [h for h in CONTEXT_HEADINGS if "Previous" not in h]
SCORING_HEADINGS = ["## Scoring", "## Evaluation Rubric", "## Score Definitions", "## Rubric"]

REASONING_DESC = [
    "step by step reasoning to derive the final score, using no more than 250 words",
    "step by step reasoning to derive the final answer, using no more than 250 words",
]

# The output block of the sectioned layout. Only the schema in the middle is rewritten per rubric.
_OUTPUT_HEAD = (
    "The output should be a well-formatted JSON instance that conforms to the JSON schema below.\n\n"
    "As an example, for the schema {\"properties\": {\"foo\": {\"title\": \"Foo\", \"description\": "
    "\"a list of strings\", \"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": "
    "[\"foo\"]}\nthe object {\"foo\": [\"bar\", \"baz\"]} is a well-formatted instance of the schema. "
    "The object {\"properties\": {\"foo\": [\"bar\", \"baz\"]}} is not well-formatted.\n\n"
    "Here is the output JSON schema:")
_OUTPUT_TAIL = ("Do not return any preamble or explanations, return only a pure JSON string "
                "surrounded by triple backticks (```).")

PLACEHOLDER_RE = re.compile(r"<<[A-Z_]+>>|\{(?:context|assistant_turn|available_tools|tool_turn)\}")


# Ways of spelling the enum in the schema description, varied per rubric.
ENUM_QUOTES = {
    "single_or": lambda e: " or ".join(f"'{x}'" for x in e),
    "single_comma": lambda e: ", ".join(f"'{x}'" for x in e),
    "backtick_or": lambda e: " or ".join(f"`{x}`" for x in e),
    "backtick_comma": lambda e: ",".join(f"`{x}`" for x in e),
}


def output_block(enum: list[str], reasoning_desc: str | None = None,
                 style: dict | None = None) -> str:
    """The sectioned layout's output format block for a given score enum.

    `style` varies the spelling: whether the schema is fenced or follows a blank line, how the enum
    is quoted, and "score" versus "answer should be one of". The default is unfenced."""
    st = style or {}
    desc = reasoning_desc or REASONING_DESC[0]
    quoted = ENUM_QUOTES[st.get("quote", "single_or")](enum)
    schema = {
        "properties": {
            "reasoning": {"description": desc, "title": "Reasoning", "type": "string"},
            "score": {"description": f"{st.get('word', 'score')} should be one of {quoted}",
                      "enum": list(enum), "title": "Score", "type": "string"},
        },
        "required": ["reasoning", "score"],
    }
    body = json.dumps(schema, ensure_ascii=False)
    if st.get("fence"):
        body = f"```\n{body}\n```"
    sep = "\n\n" if st.get("blank", True) else "\n"
    return f"{_OUTPUT_HEAD}{sep}{body}\n\n{_OUTPUT_TAIL}"


# The output block of the compact layout. The eight space indents are part of the block.
COMPACT_OUTPUT = """The output should be a well-formatted JSON instance that conforms to the JSON schema below.
        As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
        the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.
        Here is the output JSON schema:

        ```
        <<SCHEMA>>
        ```

        Do not return any preamble or explanations, return only a pure JSON string surrounded by triple backticks (```)."""


def output_enum(scale: list[dict], layout: str) -> list:
    """What the judge must answer with. The compact layout keys a numerical scale by its values, so
    there the answer is the number, not the label."""
    if layout == "compact" and all("value" in s for s in scale):
        return [s["value"] for s in scale]
    return [s["label"] for s in scale]


def render_compact(instructions: str, scale: list[dict]) -> str:
    """`{instructions}\n\n{score mapping}\n\n{output block}`."""
    numeric = all("value" in s for s in scale)
    mapping = {(s["value"] if numeric else s["label"]): s["definition"] for s in scale}
    values = list(mapping)
    options = ", ".join(str(v) if numeric else f"'{v}'" for v in values)
    schema = {
        "properties": {
            "reasoning": {"description": "step by step reasoning to derive the final score, using "
                                         "no more than 250 words", "title": "Reasoning", "type": "string"},
            "score": {"description": f"score should be one of {options}", "enum": values,
                      "title": "Score", "type": "float" if numeric else "string"},
        },
        "required": ["reasoning", "score"],
    }
    line = ", ".join(f"{k}: {v}" for k, v in mapping.items())
    return f"{instructions}\n\n{line}\n\n{COMPACT_OUTPUT.replace('<<SCHEMA>>', json.dumps(schema))}"


def presentation(rubric_id: str, level: str) -> dict:
    """Presentation axes beyond the generation spec, drawn from the rubric id so re-renders reproduce.

    Half the rubrics use the compact layout and half the sectioned layout."""
    rng = random.Random(f"{rubric_id}|presentation-v2")
    return {
        "layout": "compact" if rng.random() < 0.5 else "sectioned",
        "evidence_first": rng.random() < 0.35,
        "tools_first": level != "TRACE" and rng.random() < 0.5,
        "include_important": rng.random() < 0.15,
        "suffix_style": {"fence": rng.random() < 0.65, "blank": rng.random() < 0.5,
                         "quote": rng.choice(list(ENUM_QUOTES)),
                         "word": "answer" if rng.random() < 0.3 else "score"},
    }


def scoring_block(scale: list[dict], heading: str = "## Scoring") -> str:
    """Render the score levels, one bullet per level."""
    lines = [heading]
    for s in scale:
        if "value" in s:
            lines.append(f"- {s['label']} ({s['value']}): {s['definition']}")
        else:
            lines.append(f"- {s['label']}: {s['definition']}")
    return "\n".join(lines)


def evidence_sections(level: str, tools_first: bool = False) -> list[tuple]:
    """EVIDENCE[level], optionally with the tool catalogue ahead of the conversation. The judged call
    or turn always comes last."""
    secs = list(EVIDENCE[level])
    names = [x[1] for x in secs]
    if tools_first and "available_tools" in names:
        ci, ti = names.index("context"), names.index("available_tools")
        secs[ci], secs[ti] = secs[ti], secs[ci]
    return secs


def build_instructions(task: str, level: str, context_heading: str | None = None,
                       include_important: bool = True, evidence_first: bool = False,
                       tools_first: bool = False) -> str:
    """The compact layout's instruction prose with `{context}` style slots under headings. The
    scale is not included: `render_compact` appends it as one line."""
    body = [task.strip()]
    if include_important:
        body += ["", IMPORTANT_NOTE]
    ch = context_heading or CONTEXT_HEADINGS[0]
    ev = []
    for heading, name, _o, _c, _m in evidence_sections(level, tools_first):
        label = ch if name == "context" else f"## {heading.removeprefix('### ')}"
        ev += [label, f"{{{name}}}", ""]
    ev = ev[:-1]
    parts = ev + ["", *body] if evidence_first else body + ["", *ev]
    return "\n".join(parts)


def render_sectioned(task: str, scale: list[dict], level: str, enum: list[str],
                     include_important: bool = True,
                     scoring_heading: str = "## Scoring",
                     reasoning_desc: str | None = None,
                     tools_first: bool = False, style: dict | None = None,
                     evidence_first: bool = False) -> str:
    """The sectioned layout. The conversation (and the judged assistant turn) come first under
    "## Evaluation Context". The tool catalogue and the judged call sit under "## Evaluation Task".
    `evidence_first` puts those sections before the task prose instead of after it."""
    prefix = [s for s in EVIDENCE[level] if s[1] in ("context", "assistant_turn")]
    task_sections = [s for s in EVIDENCE[level] if s[1] not in ("context", "assistant_turn")]
    parts = [SECTIONED_PREAMBLE, "", "## Evaluation Context", ""]
    for heading, _name, open_tag, close_tag, marker in prefix:
        parts += [heading, open_tag, marker, close_tag, ""]
    ev = []
    for heading, _name, open_tag, close_tag, marker in task_sections:
        ev += [heading, open_tag, marker, close_tag, ""]
    body = [task.strip(), ""]
    parts += ["## Evaluation Task"] + ([""] + ev + body if evidence_first and ev else body + ev)
    parts += [scoring_block(scale, scoring_heading)]
    if include_important:
        parts += ["", IMPORTANT_NOTE]
    parts += ["", output_block(enum, reasoning_desc, style)]
    return "\n".join(parts)


def normalize_scale(scale_raw: list, numeric: bool) -> list[dict] | None:
    """Clean a generated scale: label + definition (+ value for numeric), worst to best."""
    if not isinstance(scale_raw, list) or len(scale_raw) < 2:
        return None
    out = []
    for s in scale_raw:
        if not isinstance(s, dict) or not str(s.get("label", "")).strip():
            return None
        item = {"label": str(s["label"]).strip(), "definition": str(s.get("definition", "")).strip()}
        if numeric:
            try:
                item["value"] = round(float(s["value"]), 4)
            except (KeyError, TypeError, ValueError):
                return None
        out.append(item)
    if numeric and [x["value"] for x in out] == sorted((x["value"] for x in out), reverse=True):
        out.reverse()
    if len({x["label"] for x in out}) != len(out):
        return None
    return out


def scale_family(scale_type: str, n_levels: int) -> str:
    """The scale family a rubric belongs to, from its shape. Used by the scale family holdout."""
    if scale_type == "numerical":
        return f"numerical_{n_levels}"
    if n_levels == 2:
        return "binary"
    return f"wide_{n_levels}" if n_levels >= 10 else f"ordinal_{n_levels}"


def record(rubric_id: str, concept_id: str, concept: str, level: str, scale: list[dict],
           rendered_prompt: str, placeholders: list[str], task: str = "", domain: str = "general",
           language: str = "en", out_enum: list | None = None) -> dict:
    """One rubric library record. `output_enum` is written only when it differs from `score_enum`."""
    enum = [s["label"] for s in scale]
    r = {
        "rubric_id": rubric_id,
        "concept_id": concept_id,
        "concept": concept,
        "level": level,
        "domain": domain or "general",
        "language": language or "en",
        "scale_type": "numerical" if all("value" in s for s in scale) else "categorical",
        "n_levels": len(enum),
        "score_enum": enum,
    }
    if out_enum is not None and list(out_enum) != enum:
        r["output_enum"] = list(out_enum)
    r.update({"scale": scale, "task": task, "placeholders": placeholders,
              "rendered_prompt": rendered_prompt})
    return r


def render_record(rubric_id: str, concept: str, level: str, task: str, scale: list[dict],
                  spec: dict, concept_id: str | None = None) -> dict:
    """Turn one generated (task, scale) plus its presentation spec into a library record.

    `spec` is `generate.Spec.as_dict()`. It supplies the domain, language, headings and reasoning
    wording. Headings and reasoning wording it lacks (`rerender` passes only domain and language)
    are drawn from the rubric id, so re-renders reproduce. The layout and the other presentation
    axes come from `presentation`.
    """
    rng = random.Random(rubric_id)
    # The draw sequence is part of the output, so every rubric renders the same way on every run.
    # The first and the fourth draw are not used.
    if not spec.get("layout"):
        rng.randrange(2)
    context_heading = spec.get("context_heading") or rng.choice(
        SESSION_HEADINGS if level == "SESSION" else CONTEXT_HEADINGS)
    scoring_heading = spec.get("scoring_heading") or rng.choice(SCORING_HEADINGS)
    rng.random()
    rd = REASONING_DESC[int(spec.get("reasoning_desc", rng.randint(0, 1)))]
    task = PLACEHOLDER_RE.sub("", task).strip()
    enum = [s["label"] for s in scale]
    pres = presentation(rubric_id, level)
    if pres["layout"] == "compact" and re.search(r"[{}]", task + "".join(x["definition"] for x in scale)):
        # A prompt with `{context}` style slots may be filled with str.format(), so a literal brace
        # would break it. Such a rubric is rendered in the sectioned layout instead.
        pres["layout"] = "sectioned"
    if pres["layout"] == "compact":
        instructions = build_instructions(task, level, context_heading=context_heading,
                                          include_important=pres["include_important"],
                                          evidence_first=pres["evidence_first"],
                                          tools_first=pres["tools_first"])
        rendered = render_compact(instructions, scale)
    else:
        rendered = render_sectioned(
            task, scale, level, enum, include_important=pres["include_important"],
            scoring_heading=scoring_heading, reasoning_desc=rd,
            tools_first=pres["tools_first"], style=pres["suffix_style"],
            evidence_first=pres["evidence_first"])
    return record(rubric_id, concept_id or rubric_id, concept, level, scale, rendered,
                  [n for _h, n, *_ in EVIDENCE[level]], task=task,
                  domain=spec.get("domain") or "general", language=spec.get("language") or "en",
                  out_enum=output_enum(scale, pres["layout"]))
