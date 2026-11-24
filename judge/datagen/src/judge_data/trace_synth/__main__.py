"""CLI: synthesize agent traces from a rubric library and an agent registry.

    python -m judge_data.trace_synth \\
        --rubric-library out/rubric_library.jsonl --agent-registry agent_registry.jsonl \\
        --out out/pairs.jsonl --traces-per-level 2 --verify \\
        --backend vllm --base-url http://localhost:8000/v1 --model-id MiMo-V2.6-Pro-MOPD

For every rubric and every level of its score scale, `--traces-per-level` traces are generated.
Each one simulates an agent drawn from the registry (domain matched where possible: its system
prompt and tools) and is asked to exhibit the rubric's concept at that level. Everything except
the measured property is meant to stay ordinary, so the judge cannot learn length or drama.

With `--verify`, an independent call places each trace on the coarse absent / partial / full
scale without being told the target, and the result is stored on the pair as `verified_severity`
next to `target_bucket`. `--drop-mismatch` keeps only traces that landed in their target bucket.

Output: one pair per line, `{id, concept, severity, target_bucket, agent_id, rubric, trace, ...}`,
where `trace` is the raw generated JSON text. Feed it to `python -m judge_data.annotate`.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter

from judge_data.clients import add_backend_args, client_from_args
from judge_data.trace_synth import synth
from judge_data.utils.io import log, read_jsonl
from judge_data.utils.jsonx import extract_json

# Agent registry domains -> rubric domains, so a finance rubric is played by a finance agent.
AGENT_TO_RUBRIC_DOMAIN = {
    "healthcare": "healthcare_medical",
    "legal_analysis": "legal",
    "financial_analysis": "finance",
    "code_review": "software_engineering",
    "debugging": "software_engineering",
    "api_integration": "software_engineering",
    "customer_support": "customer_service",
    "trip_planning": "travel_booking",
    "hiring": "hr_recruiting",
    "security_audit": "security",
    "content_writing": "creative_writing",
    "market_research": "general",
    "web_research": "general",
    "social_media": "general",
    "project_management": "general",
}


def agent_seed(agent: dict) -> dict:
    dom = agent.get("domain") or "general"
    return {
        "agent_id": agent["agent_id"],
        "framework": str(agent.get("framework") or "")[:160],
        "system_prompt": agent.get("system_prompt") or "",
        "tools": (agent.get("tools") or [])[:12],
        "domain": dom,
        "goal": agent.get("goal") or f"Complete a task in the {dom} domain",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubric-library", required=True)
    ap.add_argument("--agent-registry", required=True,
                    help="Agent registry JSONL (agent_id, source_repo, system_prompt, tools, "
                         "framework, domain)")
    ap.add_argument("--out", required=True, help="Output pairs JSONL")
    ap.add_argument("--concepts", type=int, default=0,
                    help="Use only this many rubrics, sampled (0 = all)")
    ap.add_argument("--splits", default=None,
                    help="Only rubrics in these library splits, comma separated (e.g. train)")
    ap.add_argument("--traces-per-level", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--verify", action="store_true",
                    help="Place each trace on absent/partial/full with an independent call")
    ap.add_argument("--drop-mismatch", action="store_true",
                    help="With --verify, drop traces whose verified bucket is not the target")
    ap.add_argument("--seed", type=int, default=2026)
    add_backend_args(ap)
    a = ap.parse_args()

    client = client_from_args(a)
    rng = random.Random(a.seed)

    rubrics = read_jsonl(a.rubric_library)
    agents = [x for x in read_jsonl(a.agent_registry) if x.get("agent_id")]
    if not agents:
        raise SystemExit(f"no agents with an agent_id in {a.agent_registry}")
    log(f"{len(rubrics)} rubrics, {len(agents)} agents")

    agents_by_domain: dict[str, list[dict]] = {}
    for ag in agents:
        d = ag.get("domain") or "general"
        agents_by_domain.setdefault(AGENT_TO_RUBRIC_DOMAIN.get(d, d), []).append(ag)
    if not agents_by_domain.get("general"):
        agents_by_domain["general"] = agents

    def pick_agent(rubric_domain: str) -> dict:
        pool = agents_by_domain.get(rubric_domain) or agents_by_domain["general"]
        return pool[rng.randrange(len(pool))]

    base = [r for r in rubrics if r.get("concept")]
    if a.splits:
        want = set(a.splits.split(","))
        base = [r for r in base if r.get("split", "train") in want]
    if a.concepts > 0:
        base = rng.sample(base, min(a.concepts, len(base)))

    prompts, meta = [], []
    seen: dict[str, int] = {}  # base prompt -> times drawn, to keep repeats distinct
    for i, rubric in enumerate(base):
        level = rubric.get("level", "TRACE")
        enum = rubric.get("score_enum") or ["No", "Yes"]
        for si, sev in enumerate(synth.severities_for_scale(enum)):
            for k in range(a.traces_per_level):
                agent = pick_agent(rubric.get("domain", "general"))
                seed = agent_seed(agent)
                p = synth.build_prompt(rubric["concept"], level, sev, seed)
                n = seen.get(p, 0)
                seen[p] = n + 1
                prompts.append(p if n == 0 else synth.build_prompt(rubric["concept"], level, sev,
                                                                  seed, variation=n))
                meta.append({
                    "id": f"synth-{i:05d}-{si}-{k}",
                    "concept": rubric["concept"], "severity": sev[0],
                    "target_bucket": synth.coarse_bucket(si, len(enum)),
                    "agent_id": agent["agent_id"], "rubric": rubric,
                })
    n_rep = sum(v - 1 for v in seen.values())
    log(f"{len(base)} rubrics -> {len(prompts)} traces to synthesize "
        f"({n_rep} repeat draws given a variation)")
    results = client.map(prompts, max_tokens=a.max_tokens, desc="synth")

    pairs = []
    for r, m in zip(results, meta):
        if r.text and len(r.text) > 50:
            pairs.append({**m, "trace": r.text})
    log(f"{len(pairs)} of {len(prompts)} traces came back")

    if a.verify and pairs:
        vprompts, vidx = [], []
        for j, p in enumerate(pairs):
            obj = extract_json(p["trace"])
            t = synth.to_trace(obj, p["id"], {"agent_id": p["agent_id"]}, "", p["severity"]) \
                if isinstance(obj, dict) else None
            if t is None:
                continue
            vprompts.append(synth.build_verify_prompt(p["concept"], synth.flatten_for_verify(t)))
            vidx.append(j)
        vres = client.map(vprompts, max_tokens=800, desc="verify")
        names = [s[0] for s in synth.SEVERITIES]
        for j, r in zip(vidx, vres):
            obj = extract_json(r.text)
            v = str(obj.get("severity", "")).strip().lower() if isinstance(obj, dict) else ""
            pairs[j]["verified_severity"] = v if v in names else None
        hit = Counter((p["target_bucket"], p.get("verified_severity")) for p in pairs)
        judged = sum(n for (t, v), n in hit.items() if v)
        exact = sum(n for (t, v), n in hit.items() if v and t == v)
        log(f"verification: {judged} judged, {exact} landed in their target bucket "
            f"({100 * exact / max(judged, 1):.0f}%): "
            f"{ {f'{t}->{v}': n for (t, v), n in sorted(hit.items(), key=str)} }")
        if a.drop_mismatch:
            before = len(pairs)
            pairs = [p for p in pairs if p.get("verified_severity") == p["target_bucket"]]
            log(f"dropped {before - len(pairs)} traces that missed their target bucket")

    with open(a.out, "w") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    log(f"{len(pairs)} pairs -> {a.out}  (tokens in={client.total_in} out={client.total_out})")


if __name__ == "__main__":
    main()
