from conftest import trace_row

from judge_data.rubric_trace_match import match, sample
from judge_data import traces


def _pool(n):
    out = []
    for i in range(n):
        row = trace_row(i)
        row["agent_id"] = f"ag{i % 4}"
        if i % 5 == 0:
            row["turns"] = row["turns"] * 6  # long traces
        out.append(traces.normalise(row))
    return out


def test_stratified_limit_cap_and_determinism():
    pool = _pool(80)
    a = sample.stratified(pool, 20, seed=1, keys=("topic",), max_per_agent=6, min_per_value=3)
    b = sample.stratified(pool, 20, seed=1, keys=("topic",), max_per_agent=6, min_per_value=3)
    assert [t.trace_id for t in a] == [t.trace_id for t in b]
    assert len(a) == 20 and len({t.trace_id for t in a}) == 20
    from collections import Counter
    assert max(Counter(t.agent_id for t in a).values()) <= 6
    assert {t.tags["topic"] for t in a} == {"shop", "travel"}
    assert sum(sample.is_valuable(t) for t in a) / 20 > sum(map(sample.is_valuable, pool)) / 80


def test_ground_truth_and_label_spread():
    t = {"target_labels": {"d": 1}, "primary_dim": "d"}
    assert match.is_primary(t, "d") and not match.is_primary(t, "e")
    assert match.ground_truth_dim({"rubric_id": "d"}, {"d"}) == "d"
    assert match.ground_truth_dim({"rubric_id": "d_0"}, {"d"}) is None
    assert match.ground_truth_dim({"rubric_id": "x", "ground_truth_dim": "d"}, {"d"}) == "d"
    pool = [traces.normalise(trace_row(i)).as_dict() for i in range(8)]
    tf = {p["trace_id"]: {"behaviors_present": {"tool_usage": 1.0}, "trace_quality": 0.5,
                          "evaluable_tool_calls": []} for p in pool}
    rec = {"level": "TOOL_CALL", "domain": "general", "ground_truth_dim": "args_grounded"}
    rf = {"behaviors_required": {"tool_usage": 1.0}}
    sel = match.select_for_rubric(rec, rf, pool, tf, cap=4, max_per_agent=4)
    labels = [next(p for p in pool if p["trace_id"] == s["trace_id"])["target_labels"]
              ["args_grounded"] for s in sel]
    assert sorted(labels) == [0, 0, 1, 1]
    assert all(s["target"]["call_index"] == 0 for s in sel)
