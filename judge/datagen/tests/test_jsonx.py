from judge_data.utils.jsonx import balance_brackets, extract_json, repair_json


def test_plain_and_fenced():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"score": "Yes"}\n```') == {"score": "Yes"}
    assert extract_json("```\n[1, 2]\n```") == [1, 2]


def test_surrounding_text_prefers_outer_object():
    text = 'Here you go: {"turns": [{"user": "hi"}], "note": "x"} hope that helps'
    assert extract_json(text) == {"turns": [{"user": "hi"}], "note": "x"}


def test_stray_quote_repaired():
    bad = '{"reasoning": "the agent said "done" too early", "score": "No"}'
    assert extract_json(bad) == {"reasoning": 'the agent said "done" too early', "score": "No"}
    assert '\\"done\\"' in repair_json(bad)


def test_unclosed_brackets():
    assert balance_brackets('[{"a": 1]') == '[{"a": 1}]'
    assert balance_brackets('{"a": {"b": 1}]') == '{"a": {"b": 1}}'  # a stray closer is dropped
    assert extract_json('noise {"a": [1, 2') == {"a": [1, 2]}


def test_raw_newline_in_string():
    assert extract_json('x {"a": "line one\nline two"}') == {"a": "line one\nline two"}


def test_nothing_parses():
    assert extract_json("") is None
    assert extract_json(None) is None
    assert extract_json("no json here") is None
