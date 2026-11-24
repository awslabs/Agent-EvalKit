"""Stratified trace sampling over any trace pool in the normalised Trace schema.

A uniform sample draws rare strata in proportion to their rarity, and the rare strata are exactly
the ones that make agentic rubrics judgeable: long traces and traces where a tool call failed. The
symptom is a high not applicable rate on narrow concepts like tool faults and failure recovery. So
sampling is stratified, with three departures from plain proportional allocation.

* Valuable strata are over sampled: long and very long traces, and traces with a failed tool call.
* No agent contributes more than `max_per_agent`, so scenario variety does not collapse onto
  whichever agent happens to be common.
* Every value of every stratification key gets a floor, so a domain flavoured rubric can always
  find something to match.

The primary cells are the values of `keys` (taken from `trace.tags`) plus whether the trace makes
tool calls. Length is spread within a cell by round robin rather than added to the key, because a
full cross product has more cells than the sample has traces.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict

from judge_data.traces import Trace

OVERSAMPLE = 3.0


def length_bucket(t: Trace) -> str:
    n = t.num_turns
    return "short" if n <= 2 else "medium" if n <= 5 else "long" if n <= 10 else "very_long"


def has_tool_error(t: Trace) -> bool:
    for c in t.tool_calls:
        r = c.get("result")
        if isinstance(r, dict) and (r.get("error") or str(r.get("status", "")).lower() == "error"):
            return True
        if isinstance(r, str) and r.lower().startswith(("error", "exception", "traceback")):
            return True
    return False


def is_valuable(t: Trace) -> bool:
    return length_bucket(t) in ("long", "very_long") or has_tool_error(t)


def _cell(t: Trace, keys: tuple[str, ...]) -> tuple:
    return tuple(t.tags.get(k, "") for k in keys) + (bool(t.tool_calls),)


def stratified(traces: list[Trace], limit: int, seed: int = 2026,
               keys: tuple[str, ...] = ("topic", "flow_type"), max_per_agent: int = 50,
               min_per_value: int = 20, oversample: float = OVERSAMPLE) -> list[Trace]:
    """Return up to `limit` traces, stratified. Deterministic for a given seed and pool order."""
    if limit <= 0 or limit >= len(traces):
        return list(traces)
    rng = random.Random(seed)
    cells: dict[tuple, list[Trace]] = defaultdict(list)
    for t in traces:
        cells[_cell(t, keys)].append(t)

    weights = {}
    for k, members in cells.items():
        frac = sum(1 for t in members if is_valuable(t)) / len(members)
        weights[k] = len(members) * (1.0 + (oversample - 1.0) * frac)
    total = sum(weights.values())
    target = {k: max(1, round(limit * w / total)) for k, w in weights.items()}

    per_agent: Counter = Counter()
    chosen: list[Trace] = []
    chosen_ids: set[str] = set()

    def take_from(members: list[Trace], want: int) -> None:
        by_len: dict[str, list[Trace]] = defaultdict(list)
        for t in members:
            by_len[length_bucket(t)].append(t)
        for v in by_len.values():
            rng.shuffle(v)
            v.sort(key=is_valuable)  # valuable last, so pop() takes them first
        order = sorted(by_len)
        got = i = 0
        while got < want and any(by_len[k] for k in order):
            k = order[i % len(order)]
            i += 1
            while by_len[k]:
                t = by_len[k].pop()
                if t.trace_id in chosen_ids or per_agent[t.agent_id] >= max_per_agent:
                    continue
                per_agent[t.agent_id] += 1
                chosen.append(t)
                chosen_ids.add(t.trace_id)
                got += 1
                break

    for k in sorted(cells, key=str):
        take_from(cells[k], target[k])

    # Floors per value of each key.
    for key in keys:
        have = Counter(t.tags.get(key, "") for t in chosen)
        groups: dict[str, list[Trace]] = defaultdict(list)
        for t in traces:
            groups[t.tags.get(key, "")].append(t)
        for val, members in sorted(groups.items()):
            short = min(min_per_value, len(members)) - have.get(val, 0)
            if short > 0:
                take_from(members, short)

    if len(chosen) > limit:
        rng.shuffle(chosen)
        chosen = chosen[:limit]
    elif len(chosen) < limit:
        rest = [t for t in traces if t.trace_id not in chosen_ids]
        rng.shuffle(rest)
        for t in rest:
            if len(chosen) >= limit:
                break
            if per_agent[t.agent_id] >= max_per_agent:
                continue
            per_agent[t.agent_id] += 1
            chosen.append(t)
            chosen_ids.add(t.trace_id)
    return chosen


def report(chosen: list[Trace], pool: list[Trace], keys: tuple[str, ...] = ("topic", "flow_type")) -> None:
    print(f"stratified sample: {len(chosen)} of {len(pool)} traces")
    for name, fn in [*((k, lambda t, k=k: t.tags.get(k, "")) for k in keys),
                     ("length", length_bucket), ("tool_calls", lambda t: bool(t.tool_calls))]:
        cs, cp = Counter(map(fn, chosen)), Counter(map(fn, pool))
        print(f"  {name}: {len(cs)} of {len(cp)} values present")
        for v, n in cs.most_common(5):
            print(f"      {str(v)[:22]:24s} sample {100 * n / max(len(chosen), 1):5.1f}%   "
                  f"pool {100 * cp[v] / len(pool):5.1f}%")
    ag = Counter(t.agent_id for t in chosen)
    if ag:
        print(f"  agents: {len(ag)} distinct, max per agent {max(ag.values())}")
