from judge_data.annotate import parse, render, scrub
from judge_data.utils.jsonx import extract_json


def p(text, enum):
    return parse.parse(text, enum, extract_json)


def test_parse_ok_na_and_out_of_enum():
    ok = p('```json\n{"reasoning": "fine", "score": "Good"}\n```', ["Bad", "Good"])
    assert ok == {"ok": True, "na": False, "score": "Good", "reasoning": "fine",
                  "reply_quotes_reasoning": False}
    na = p('{"reasoning": "n/a", "score": "Not Applicable"}', ["Bad", "Good"])
    assert na["ok"] and na["na"] and na["score"] == "N/A"
    bad = p('{"reasoning": "x", "score": "Great"}', ["Bad", "Good"])
    assert not bad["ok"] and bad["why"] == "score outside the declared scale"
    assert not p("not json", ["Bad"])["ok"]
    assert "missing reasoning or score" in p('{"score": "Bad"}', ["Bad"])["why"]


def test_parse_numeric_enum():
    assert p('{"reasoning": "x", "score": 0.5}', [0.0, 0.5, 1.0])["ok"]
    assert p('{"reasoning": "x", "score": "1"}', [0.0, 1.0])["ok"]
    assert not p('{"reasoning": "x", "score": 0.3}', [0.0, 1.0])["ok"]


def test_parse_flags_quoted_reasoning_tags():
    r = p('{"reasoning": "the agent wrote <thinking>x</thinking>", "score": "Bad"}', ["Bad"])
    assert r["reply_quotes_reasoning"] is True


def test_fill_both_layouts_and_unfillable():
    ev = {"context": "CTX", "assistant_turn": "TURN"}
    markers = {"rendered_prompt": "<<CONVERSATION_CONTEXT>> / <<ASSISTANT_FINAL_TURN>>"}
    assert render.fill(markers, ev) == "CTX / TURN"
    inline = {"rendered_prompt": '{context} / {assistant_turn} {"a": 1}'}
    assert render.fill(inline, ev) == 'CTX / TURN {"a": 1}'
    assert render.unfillable({"rendered_prompt": "{context} {expected_output}"}) == {"expected_output"}


def test_scrub_strip_and_leaks():
    text = "<thinking>I need to deliberately fail</thinking>Done. <think>ok</think>"
    assert scrub.leaks(text)
    assert scrub.strip_all(text) == "Done. "
    assert scrub.strip_leaky(text) == "Done. <think>ok</think>"
    assert not scrub.leaks("credentials are injected at runtime")
    assert scrub.unfence('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert scrub.bit("x", "s") == scrub.bit("x", "s")
