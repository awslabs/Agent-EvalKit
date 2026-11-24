from conftest import trace_row

from judge_data import traces
from judge_data.trace_synth import synth


def test_severities_follow_scale_positions():
    sev = synth.severities_for_scale(["A", "B", "C", "D", "E"])
    assert [s[0] for s in sev] == ["A", "B", "C", "D", "E"]
    assert [synth.coarse_bucket(i, 5) for i in range(5)] == ["absent", "absent", "partial",
                                                            "full", "full"]
    assert [synth.coarse_bucket(i, 2) for i in range(2)] == ["absent", "full"]
    assert "level 3 of 5" in sev[2][1] and "genuinely mixed" in sev[2][1]


def test_build_prompt_variation_and_tools():
    seed = {"agent_id": "a", "framework": "f", "goal": "g", "domain": "general",
            "tools": [{"name": "t1", "description": "does one"}, "t2"]}
    p0 = synth.build_prompt("c", "TRACE", ("x", "y"), seed)
    p1 = synth.build_prompt("c", "TRACE", ("x", "y"), seed, variation=1)
    assert p0 != p1 and "variation 2" in p1
    assert "- t1: does one\n- t2" in p0


def test_to_trace_validates_and_aligns_calls():
    obj = {"turns": [{"user": "u", "assistant": "a",
                      "tool_calls": ["bad", {"tool_name": "x", "arguments": {}}],
                      "tool_results": ["r_bad", "r_x"]}]}
    t = synth.to_trace(obj, "id", {"agent_id": "ag"}, "c", "absent")
    assert t["tool_calls"][0]["tool_name"] == "x" and t["tool_calls"][0]["result"] == "r_x"
    assert t["tool_catalogue"] == ["x"] and t["user_goal"] == "u"
    assert synth.to_trace({"turns": []}, "id", {"agent_id": "a"}, "c", "s") is None
    assert synth.to_trace({"turns": [{"user": "u", "assistant": ""}]}, "i", {"agent_id": "a"},
                          "c", "s") is None
    flat = synth.flatten_for_verify(t)
    assert "Tool call: x({})" in flat and "Agent: a" in flat


def test_normalise_both_schemas():
    t = traces.normalise(trace_row(0))
    assert t.trace_id == "t0" and t.num_turns == 2 and t.tags == {"topic": "shop"}
    assert t.tool_catalogue == ["get_order", "refund_order"]
    raw = {"scenario_id": "s1", "agent_id": "a",
           "turns": [{"user_input": "hi", "agent_response": "hello",
                      "tool_calls": [{"name": "q", "arguments": {}}]}],
           "tools": [{"name": "unused"}]}
    r = traces.normalise(raw)
    assert r.trace_id == "s1" and r.turns[0]["assistant"] == "hello"
    assert r.tool_catalogue == ["q", "unused"] and r.tool_calls[0]["tool_name"] == "q"
    assert traces.normalise({"turns": []}) is None


def test_evidence_for_each_level():
    t = traces.normalise(trace_row(1))
    s = traces.evidence_for(t, "SESSION")
    assert set(s) == {"context", "available_tools"} and "Refund issued." in s["context"]
    tr = traces.evidence_for(t, "TRACE", {"turn_index": 1})
    assert tr["assistant_turn"] == "Refund issued." and "Refund issued." not in tr["context"]
    tc = traces.evidence_for(t, "TOOL_CALL", {"turn_index": 1, "call_index": 0})
    assert tc["tool_turn"].startswith("refund_order(")
    assert "refund_order" not in tc["context"]  # a tool call judge never sees the judged call
    flat = traces.evidence_for(t, "SESSION", turn_labels=False)
    assert not traces.HEADER.search(flat["context"]) and traces.HEADER.search(s["context"])
    prod = traces.evidence_repr(t, "TOOL_CALL", {"turn_index": 1, "call_index": 0})
    assert "'tool_call': {'name': 'refund_order'" in prod["tool_turn"]


def test_scrub_reaches_judged_turn():
    from judge_data.annotate import scrub
    t = traces.normalise(trace_row(0))
    ev = traces.evidence_for(t, "TRACE", {"turn_index": 0}, scrub=scrub.strip_all)
    assert ev["assistant_turn"] == "Looking it up."
