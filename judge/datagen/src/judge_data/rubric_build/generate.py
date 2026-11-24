"""Rubric generation from concepts plus presentation specs.

Given a concept (what to measure) and one spec per wanted rubric (scale, domain, length, framing),
one model call writes every rubric of the concept: a metric name, the task prose and a scale.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING

from judge_data.utils.jsonx import extract_json

if TYPE_CHECKING:
    from judge_data.clients import ModelClient

# ── Presentation spec ───────────────────────────────────────────────────────

SCALE_FAMILIES = [
    ("binary", 2, False),
    ("ordinal_3", 3, False), ("ordinal_4", 4, False), ("ordinal_5", 5, False),
    ("ordinal_6", 6, False), ("ordinal_7", 7, False),
    ("numerical_3", 3, True), ("numerical_4", 4, True), ("numerical_5", 5, True),
    ("wide_10", 10, False), ("wide_14", 14, False), ("wide_20", 20, False),
]

DOMAINS = [
    "healthcare_medical", "legal", "finance", "software_engineering", "scientific_research",
    "education", "customer_service", "security", "creative_writing", "data_analysis",
    "ecommerce", "general", "devops", "travel_booking", "hr_recruiting", "insurance",
]


@dataclass
class Spec:
    """Describes how a single concept is turned into one rubric record.

    `layout` and `include_important` are sampled but not rendered: `render.presentation` picks the
    prompt layout and the important note per rubric id. `layout` still keeps the specs of one
    concept apart in `sample_specs_for_concept`, and both draws keep the sampled stream stable.
    """
    scale_family: str
    n_levels: int
    numeric: bool
    layout: str
    domain: str
    verbosity: str       # terse | normal | detailed
    polarity: str        # quality | defect
    language: str
    examples: int
    tiebreak: bool
    underspecified: bool
    conflicting: bool
    role_preamble: bool
    checklist: bool
    specifies_output_format: bool
    include_important: bool
    context_heading: str
    scoring_heading: str
    reasoning_desc: int

    def as_dict(self) -> dict:
        return asdict(self)


def sample_spec(rng, level: str, domain: str | None = None) -> Spec:
    """Sample one presentation spec for a concept at the given level.

    `domain` pins the domain flavour (for concepts that carry one). Otherwise it is sampled."""
    fams = {f[0]: f for f in SCALE_FAMILIES}
    sw = {"binary":.35,"ordinal_3":.11,"ordinal_4":.05,"ordinal_5":.15,
          "ordinal_6":.03,"ordinal_7":.06,"numerical_3":.03,"numerical_4":.02,
          "numerical_5":.05,"wide_10":.03,"wide_14":.01,"wide_20":.01}
    name = rng.choices(list(sw), weights=list(sw.values()), k=1)[0]
    _, n, numeric = fams[name]
    if n >= 10 and level == "TOOL_CALL" and rng.random() < 0.7:
        name, n, numeric = fams["ordinal_5"]
    dw = [.06,.06,.08,.1,.04,.04,.12,.07,.02,.06,.08,.12,.05,.04,.03,.03]
    ch = ["## Conversation record","## Conversation History","## Previous turns:",
          "## User Prompt","## Conversation history ##","## Context"]
    sh = ["## Scoring","## Evaluation Rubric","## Score Definitions","## Rubric"]
    return Spec(
        scale_family=name, n_levels=n, numeric=numeric,
        layout=rng.choices(["inline","markers"],[.55,.45],k=1)[0],
        domain=domain or rng.choices(DOMAINS, dw, k=1)[0],
        verbosity=rng.choices(["terse","normal","detailed"],[.3,.45,.25],k=1)[0],
        polarity=rng.choices(["quality","defect"],[.72,.28],k=1)[0],
        language=rng.choice(["en"]*9+["zh","es","ja"]),
        examples=rng.choice([0,0,0,1,1,2,3]),
        tiebreak=rng.random()<.35,
        underspecified=rng.random()<.12,
        conflicting=rng.random()<.08,
        role_preamble=rng.random()<.7,
        checklist=rng.random()<(.22 if level!="TOOL_CALL" else .1),
        specifies_output_format=rng.random()<.05,
        include_important=rng.random()<.6,
        context_heading=rng.choice(ch), scoring_heading=rng.choice(sh),
        reasoning_desc=rng.choice([0,1]),
    )


def sample_specs_for_concept(rng, level: str, k: int, domain: str | None = None) -> list[Spec]:
    """Sample k diverse presentation specs for one concept."""
    specs: list[Spec] = []
    used_scales: set[str] = set()
    used_layouts: set[str] = set()
    for i in range(k):
        for _ in range(12):
            s = sample_spec(rng, level, domain=domain)
            if s.scale_family in used_scales and len(used_scales) < min(k, 5):
                continue
            if i == 1 and s.layout in used_layouts:
                continue
            break
        used_scales.add(s.scale_family)
        used_layouts.add(s.layout)
        specs.append(s)
    return specs


# ── Rubric generation prompt ────────────────────────────────────────────────

LEVEL_NOTE = {
    "SESSION": ("The judge sees every turn of the whole session and the catalogue of tools that "
                "were available. It is judging the session as a whole."),
    "TRACE": ("The judge sees the conversation so far and one assistant response singled out as "
              "the target. It is judging that one response."),
    "TOOL_CALL": ("The judge sees the conversation up to the call, the catalogue of available "
                  "tools, and one tool call singled out as the target. It cannot see what "
                  "happened after the call."),
}

GENERATE_PROMPT = """You are writing evaluator definitions for an agent evaluation service. Each one
becomes an LLM as a judge evaluator that scores live agent traffic.

## The property being measured
{concept}

## Evaluation level: {level}
{level_note}

The judge has no reference answer, no expected output and no gold trajectory. Everything it
decides must be decidable from the evidence above.

## Write {n} different evaluators for this property

Each one measures the same underlying property but presents it differently. They must not read
like copies of each other. Vary the angle you approach the property from, the wording, and how
much guidance you give.

{items}

## Output format for each evaluator
- "metric_name": 2 to 5 words, title case, names the property.
- "task": the instruction prose the judge reads. State the judge's job and the criteria. Do NOT
  include the score level list, do NOT include the conversation or tool call itself, do NOT
  include any placeholder such as {{context}}, and do NOT say anything about the output format
  or JSON. Those parts are added separately.
- "scale": a list of exactly {n_levels_note} objects, ordered from worst to best, each with
  "label" and "definition". {value_note}

Rules for the scale:
- Labels are short, distinct and meaningful for this property. Do not default to Yes and No
  unless the property really is a two way decision, and prefer labels that name the outcome.
- Every definition says what makes a case fall in that level, in one sentence.
- Labels must be unique within an evaluator.

Output a JSON array of {n} objects and nothing else."""

LANG_NAME = {"en": "English", "zh": "Chinese", "es": "Spanish", "ja": "Japanese"}


def _item_brief(i: int, s: Spec) -> str:
    bits = [f"{i + 1}. Scale: {s.n_levels} levels"]
    if s.numeric:
        bits.append("with a numeric value on each level")
    bits.append(f"Domain flavour: {s.domain.replace('_', ' ')}")
    bits.append(f"Length: {s.verbosity}")
    if s.polarity == "defect":
        bits.append("Frame it as the presence of a fault, levels from no violation to serious violation")
    if s.role_preamble:
        bits.append("Open by naming the judge's role")
    else:
        bits.append("Do not open with a role statement")
    if s.examples:
        bits.append(f"Include {s.examples} short worked example(s)")
    if s.tiebreak:
        bits.append("State an explicit tie breaking rule")
    if s.checklist:
        bits.append("Ask the judge to enumerate check items in reasoning, aggregate overall")
    if s.underspecified:
        bits.append("Deliberately leave criteria vague")
    if s.conflicting:
        bits.append("Include two criteria that pull in opposite directions")
    if s.language != "en":
        bits.append(f"Write in {LANG_NAME[s.language]}")
    return "   ".join(bits[:1]) + "\n   " + "\n   ".join(bits[1:])


def _build_gen_prompt(c: dict, specs: list[Spec]) -> str:
    """Build the generation prompt for one concept. Pure function, no LLM."""
    levels_set = sorted({s.n_levels for s in specs})
    n_levels_note = ("the number of levels stated for that evaluator"
                     if len(levels_set) > 1 else str(levels_set[0]))
    value_note = ('For evaluators marked "with a numeric value", also give "value" as a number, '
                  'evenly spread from 0.0 for worst to 1.0 for best.'
                  if any(s.numeric for s in specs) else "")
    return GENERATE_PROMPT.format(
        concept=c["concept"], level=c["level"], level_note=LEVEL_NOTE[c["level"]],
        n=len(specs),
        items="\n".join(_item_brief(i, s) for i, s in enumerate(specs)),
        n_levels_note=n_levels_note, value_note=value_note)


def _parse_gen_result(text: str, c: dict, specs: list[Spec]) -> tuple[list[dict], list[dict]]:
    """Parse one generation result into records and failures. Pure function."""
    records, failures = [], []
    parsed = extract_json(text)
    if not isinstance(parsed, list):
        failures.append({"concept_id": c["concept_id"], "why": "unparseable"})
        return records, failures
    for i, spec in enumerate(specs):
        if i >= len(parsed) or not isinstance(parsed[i], dict):
            failures.append({"concept_id": c["concept_id"], "index": i, "why": "missing"})
            continue
        obj = parsed[i]
        task = str(obj.get("task", "")).strip()
        name = str(obj.get("metric_name", "")).strip()
        scale_raw = obj.get("scale")
        if not task or not name or not isinstance(scale_raw, list):
            failures.append({"concept_id": c["concept_id"], "index": i, "why": "incomplete"})
            continue
        records.append({
            "concept_id": c["concept_id"],
            "concept": c["concept"],
            "metric_name": name,
            "task": task,
            "scale": scale_raw,
            "level": c["level"],
            "spec": spec.as_dict(),
        })
    return records, failures


def batch_generate(
    concepts: list[dict],
    specs_per_concept: dict[str, list[Spec]],
    client: "ModelClient",
) -> tuple[list[dict], list[dict]]:
    """Generate rubrics for a batch of concepts using client.map() for parallelism.

    Args:
        concepts: list of dicts with concept_id, concept and level
        specs_per_concept: mapping concept_id -> list of Spec
        client: model client

    Returns:
        (records, failures) where each record has metric_name, task, scale,
        and spec metadata, and failures have concept_id and error info.
    """
    prompts = []
    meta = []
    for c in concepts:
        specs = specs_per_concept.get(c["concept_id"], [])
        if not specs:
            continue
        prompts.append(_build_gen_prompt(c, specs))
        meta.append((c, specs))

    results = client.map(prompts, max_tokens=9000, desc="rubric-gen")

    records, failures = [], []
    for result, (c, specs) in zip(results, meta):
        r, f = _parse_gen_result(result.text, c, specs)
        records.extend(r)
        failures.extend(f)
    return records, failures
