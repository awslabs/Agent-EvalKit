"""Concept extraction from seed rubrics, clustering, authoring, and filtering.

Clean room by construction: only a short concept label crosses over from a seed rubric. Rubric
prose is generated fresh from the label, so seed wording never enters a generation prompt.
`validate.relabel_if_copied` and `validate.cleanroom_check` verify that afterwards.

Each function takes explicit inputs and a ModelClient and returns results. No file IO inside
functions, callers manage persistence.
"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from judge_data.utils.jsonx import extract_json

if TYPE_CHECKING:
    from judge_data.clients import ModelClient

# ── Concept extraction ──────────────────────────────────────────────────────

EXTRACT_PROMPT = """You are building a registry of evaluation concepts for an agent evaluation service.

For each rubric below, output one JSON object. Work only from what the rubric measures. Do not
copy or paraphrase its wording.

Fields per object:
- "idx": the rubric_idx given.
- "concept": a short factual statement of WHAT IS MEASURED, at most 20 words, lowercase, no
  rubric jargon. Write it as an observable property, for example "the response asserts claims
  not supported by the provided context". This must be a statement of the measured property,
  not a rewrite of the rubric text.
- "level": the evaluation level this concept fits. "SESSION" judges a whole multi turn session.
  "TRACE" judges one assistant response in context. "TOOL_CALL" judges a single tool
  invocation. Pick the narrowest level that still works.
- "needs_reference": true if applying this concept requires a known correct answer, an expected
  response, or a gold trajectory. Otherwise false.
- "agentic": true if the concept is about agent behaviour such as tool use, planning, multi step
  execution, or stopping. False if it is about the text of a single reply.

Rubrics:
{rubrics}

Output a JSON array of {n} objects and nothing else."""


def _fmt_seed_rubric(r: dict) -> str:
    """Seed rubric fields: rubric_idx, metric_name, definition, and optionally scoring_scale,
    score_levels (label -> description), grading_instructions, category."""
    levels = r.get("score_levels") or {}
    lv = "; ".join(f"{k}={v}" for k, v in list(levels.items())[:3])
    return (f"--- rubric_idx {r['rubric_idx']}\n"
            f"name: {r.get('metric_name', '')}\n"
            f"definition: {r.get('definition', '')}\n"
            f"scale: {r.get('scoring_scale')}\n"
            f"levels: {lv[:400]}\n"
            f"instructions: {(r.get('grading_instructions') or '')[:500]}")


def batch_extract_concepts(
    rubrics: list[dict],
    client: "ModelClient",
    batch_size: int = 20,
) -> list[dict]:
    """Extract concepts from a batch of seed rubrics.

    Each rubric must have ``rubric_idx``, ``metric_name``, ``definition``,
    and optionally ``scoring_scale``, ``score_levels``, ``grading_instructions``.

    Returns a list of dicts with keys: rubric_idx, concept, level, needs_reference, agentic,
    seed_category.
    """
    batches = [rubrics[i:i + batch_size] for i in range(0, len(rubrics), batch_size)]
    prompts = [EXTRACT_PROMPT.format(
        rubrics="\n\n".join(_fmt_seed_rubric(r) for r in b),
        n=len(b),
    ) for b in batches]

    out: list[dict] = []
    results = client.map(prompts, max_tokens=8192, desc="concept-extract")
    for b, result in zip(batches, results):
        parsed = extract_json(result.text)
        if not isinstance(parsed, list):
            continue
        by_idx = {str(o["idx"]): o for o in parsed if isinstance(o, dict) and "idx" in o}
        for r in b:
            o = by_idx.get(str(r["rubric_idx"]))
            if not o or not o.get("concept"):
                continue
            out.append({
                "rubric_idx": r["rubric_idx"],
                "concept": str(o["concept"]).strip().rstrip("."),
                "level": o.get("level") if o.get("level") in ("SESSION", "TRACE", "TOOL_CALL")
                         else "TRACE",
                "needs_reference": bool(o.get("needs_reference", False)),
                "agentic": bool(o.get("agentic", False)),
                "seed_category": r.get("category"),
            })
    return out


# ── Clustering ──────────────────────────────────────────────────────────────

def _greedy_labels(embeddings, threshold: float) -> list[int]:
    """Leader clustering: each vector joins the first cluster whose centroid is within `threshold`
    cosine distance, else starts a new one. The fallback when scikit-learn is not installed."""
    import numpy as np

    centroids: list = []
    sums: list = []
    labels: list[int] = []
    for v in embeddings:
        if centroids:
            sims = np.stack(centroids) @ v
            j = int(np.argmax(sims))
            if 1.0 - float(sims[j]) <= threshold:
                labels.append(j)
                sums[j] = sums[j] + v
                centroids[j] = sums[j] / (np.linalg.norm(sums[j]) + 1e-9)
                continue
        labels.append(len(centroids))
        centroids.append(v)
        sums.append(v.copy())
    return labels


def cluster_labels(embeddings, threshold: float = 0.30) -> list[int]:
    """Average linkage agglomerative clustering on cosine distance (scikit-learn, the `[cluster]`
    extra), or greedy leader clustering when scikit-learn is missing."""
    if len(embeddings) < 2:
        return [0] * len(embeddings)
    try:
        from sklearn.cluster import AgglomerativeClustering
    except ImportError:
        return _greedy_labels(embeddings, threshold)
    model = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold,
                                    metric="cosine", linkage="average")
    return [int(x) for x in model.fit_predict(embeddings)]


def cluster_concepts(
    concepts: list[dict],
    embeddings,
    threshold: float = 0.30,
) -> list[dict]:
    """Cluster extracted concepts into a canonical registry.

    Args:
        concepts: list of dicts from batch_extract_concepts (must have 'concept', 'level', etc.)
        embeddings: numpy array of shape (len(concepts), dim), L2-normalised
        threshold: cosine distance threshold for clustering

    Returns:
        list of registry entries, each with concept_id, concept (canonical), level, etc.
    """
    import numpy as np

    labels = cluster_labels(embeddings, threshold)

    groups: dict[int, list[int]] = {}
    for i, c in enumerate(labels):
        groups.setdefault(int(c), []).append(i)

    registry: list[dict] = []
    for c, idxs in sorted(groups.items()):
        members = [concepts[i] for i in idxs]
        centroid = embeddings[idxs].mean(axis=0)
        centroid /= np.linalg.norm(centroid) + 1e-9
        best = max(idxs, key=lambda i: float(embeddings[i] @ centroid))
        level = Counter(m["level"] for m in members).most_common(1)[0][0]
        registry.append({
            "concept_id": f"cn{c:05d}",
            "concept": concepts[best]["concept"],
            "level": level,
            "agentic": sum(bool(m.get("agentic")) for m in members) * 2 >= len(members),
            "size": len(members),
            "seed_rubric_idx": sorted((m["rubric_idx"] for m in members), key=str)[:25],
            "variant_concepts": [m["concept"] for m in members[:8]],
            "source": "seed_rubrics",
        })
    return registry


# ── Authoring ───────────────────────────────────────────────────────────────

LEVEL_NOTE = {
    "SESSION": ("The judge sees every turn of the session and the tool catalogue. It does not see "
                "any single turn marked out as the target."),
    "TRACE": ("The judge sees the conversation so far plus one assistant response singled out as "
              "the target of the judgement."),
    "TOOL_CALL": ("The judge sees the conversation up to the call, the tool catalogue, and one "
                  "tool call singled out as the target. It does not see what happened after."),
}

AUTHOR_PROMPT = """You are building a registry of evaluation concepts for an agent evaluation service.
A concept is a short factual statement of an observable property that a judge could score.

## Category
{guidance}

## Evaluation level
{level}. {level_note}

## Already written in this category, write different ones
{already}

## Task
Write {n} new concepts for this category at this level.

Rules:
- Each concept is one observable property, at most 20 words, lowercase, no trailing period.
- Write the property, not an instruction. For example "the agent retried a failing tool call
  more than three times without changing its approach", not "check whether the agent retried".
- Each must be genuinely distinct from the others.
- Each must be judgeable from the evidence available at this level and with no reference answer,
  no expected output, and no gold trajectory.
- Spread them over different situations rather than rephrasing one idea.

Output a JSON array of {n} objects, each {{"concept": "...", "note": "one short clause on what
evidence in the trace would settle it"}}. Output nothing else."""


def author_missing(
    category: str,
    level: str,
    guidance: str,
    target: int,
    client: "ModelClient",
    batch_size: int = 24,
    max_calls: int = 7,
) -> list[dict]:
    """Author `target` concepts for one category at one level, in up to `max_calls` calls of
    `batch_size` concepts. Each call sees the concepts already written so it writes new ones.

    Returns a list of dicts with concept, note, category and level.
    """
    got: list[dict] = []
    failed = 0
    for _ in range(max_calls):
        if len(got) >= target:
            break
        need = min(batch_size, target - len(got) + 6)
        already = "\n".join(f"- {g['concept']}" for g in got[-60:]) or "- nothing yet"
        prompt = AUTHOR_PROMPT.format(
            guidance=guidance.strip(), level=level,
            level_note=LEVEL_NOTE[level], already=already, n=need)
        if failed:  # an identical retry would be a cache hit on the same unparseable reply
            prompt += f"\n\nNever put a raw double quote inside a string value. (retry {failed})"
        r = client.invoke(prompt, max_tokens=6000, temperature=1.0)
        parsed = extract_json(r.text)
        if not isinstance(parsed, list):
            failed += 1
            continue
        failed = 0
        seen = {g["concept"] for g in got}
        for o in parsed:
            if not isinstance(o, dict):
                continue
            c = str(o.get("concept", "")).strip().lower().rstrip(".")
            if not c or len(c.split()) > 26 or c in seen:
                continue
            seen.add(c)
            got.append({"concept": c, "note": str(o.get("note", ""))[:200],
                        "category": category, "level": level})

    return got[:target]


# Categories a seed corpus of public rubrics rarely supplies (it is mostly single response
# concepts): category -> (level, how many to author, guidance).
AUTHOR_PLAN = [
    ("business_policy", "SESSION", 96, """Business and operational policy adherence. These are the
metrics a company actually configures, not academic quality dimensions. Think about escalation
procedures, authority and spending limits, mandatory disclosures, consent capture before acting,
approved terminology and naming, required disclaimers, record keeping obligations, handoff
protocol to a human, and adherence to a documented standard operating procedure."""),
    ("failure_modes", "SESSION", 96, """Named agent failure modes over a whole session. Each mode is
one concept. Think about reusing context that has been invalidated, retrying a failing action
indefinitely, proceeding as though a failed step succeeded, abandoning a task partway, widening
the task beyond what was asked, losing a constraint introduced mid conversation, doing work twice,
and taking an irreversible action without confirming."""),
    ("failure_modes_tool", "TOOL_CALL", 96, """Named failure modes visible in a single tool call.
Think about argument values invented rather than taken from context, arguments in the wrong unit
or format, a call whose prerequisites were never satisfied, a call that repeats one already made,
a destructive or irreversible call made without care, a call that passes personal or secret data
it should not, a call whose scope is wider than the task needs, and a call made when the answer
was already available."""),
    ("domain_specialised_tool", "TOOL_CALL", 96, """Tool call checks where the criteria genuinely
change with the domain, not merely the subject matter. A medical dosage tool needs unit and range
checking that a refund tool does not. A financial transfer tool needs currency, rounding and limit
checking. A database tool needs checks on scope of a delete or update. An infrastructure tool
needs checks on environment targeting. Only write a concept when the check itself differs."""),
    ("conversation_dynamics", "SESSION", 72, """Session level conversational dynamics across turns.
Think about contradicting an earlier turn, forgetting a preference the user stated, repeating an
answer already given, re-asking for information already provided, drifting from the original
instruction over a long run, and failing to carry forward a correction the user made."""),
    ("honesty_self_knowledge", "SESSION", 72, """Self knowledge and honesty about its own actions.
Think about claiming work was done that was not done, reporting success when the outcome is
unknown, stating a limitation accurately, expressing uncertainty where uncertainty exists,
attributing information to a source that did not provide it, and describing its own capabilities
accurately."""),
    ("defect_presence_tool", "TOOL_CALL", 72, """Tool call concepts framed as the presence of a
defect rather than as quality. The measured property should be an observable fault, so the natural
scale runs from no violation to serious violation. Think about faults in argument construction,
call sequencing, permission scope, and data handling."""),
]

# ── Filtering ───────────────────────────────────────────────────────────────

FILTER_PROMPT = """An online evaluation service scores live traffic from AI agents. For each candidate
concept below, decide whether a judge could score it from trace evidence.

The only evidence a judge ever gets is:
- the turns of the conversation between the user and the agent
- the agent's own replies
- the catalogue of tools the agent could call, and the tool calls it made
There is never a reference answer, an expected output, a gold trajectory, a separate prompt
under review, a dataset, or a human annotation.

Answer "yes" when the concept is an observable property of the agent's own behaviour or output.
Answer "no" when the concept judges something that is not the agent's behaviour, for example the
quality of a prompt someone wrote, the design of a rubric, the rigour of an evaluation
methodology, or a dataset description. Also answer "no" when the concept is not a measurable
property at all.

Candidates:
{cands}

Output a JSON array of objects {{"i": <index>, "ok": "yes" or "no", "why": "<short clause, only
when no>"}} and nothing else."""


def filter_unjudgeable(
    concepts: list[dict],
    client: "ModelClient",
    batch_size: int = 50,
) -> tuple[list[dict], list[dict]]:
    """Drop concepts that cannot be judged from live agent traffic.

    Returns (kept, dropped) where each dropped item has a 'reject_reason' field.
    """
    keep, drop = [], []
    batches = [concepts[i:i + batch_size] for i in range(0, len(concepts), batch_size)]
    prompts = [FILTER_PROMPT.format(cands="\n".join(f"{j}. {c['concept']}" for j, c in enumerate(b)))
               for b in batches]
    results = client.map(prompts, max_tokens=6000, temperature=0.0, desc="judgeable-filter")
    for b, result in zip(batches, results):
        parsed = extract_json(result.text)
        verdict: dict[int, tuple[str, str]] = {}
        if isinstance(parsed, list):
            for o in parsed:
                if isinstance(o, dict) and "i" in o:
                    verdict[int(o["i"])] = (str(o.get("ok", "yes")).strip().lower(),
                                            str(o.get("why", ""))[:160])
        for j, c in enumerate(b):
            ok, why = verdict.get(j, ("yes", ""))
            if ok.startswith("y"):
                keep.append(c)
            else:
                d = dict(c)
                d["reject_reason"] = why or "not judgeable from trace evidence"
                drop.append(d)
    return keep, drop
