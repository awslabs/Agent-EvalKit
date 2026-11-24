import random

import pytest

from judge_data.rubric_build import assemble, generate, render, validate

SCALE = [{"label": "Bad", "definition": "clearly bad"}, {"label": "Good", "definition": "clearly good"}]
NUM_SCALE = [{"label": "Low", "definition": "low", "value": 0.0},
             {"label": "High", "definition": "high", "value": 1.0}]


@pytest.mark.parametrize("level", ["SESSION", "TRACE", "TOOL_CALL"])
@pytest.mark.parametrize("rid", ["r1", "r2", "r3", "r4", "r5", "r6"])
def test_render_record_slots_match_level(level, rid):
    spec = generate.sample_spec(random.Random(rid), level).as_dict()
    r = render.render_record(rid, "a concept", level, "Judge the thing.", SCALE, spec)
    assert validate.check_schema(r) == []
    assert r["placeholders"] == [n for _h, n, *_ in render.EVIDENCE[level]]
    markers = "<<" in r["rendered_prompt"]
    for _h, name, _o, _c, marker in render.EVIDENCE[level]:
        assert (marker if markers else "{" + name + "}") in r["rendered_prompt"]
    assert set(r) <= set(assemble.LIBRARY_FIELDS)
    assert "output_enum" not in r  # categorical scale, so the answer is the label


def test_render_is_deterministic():
    spec = generate.sample_spec(random.Random(1), "TRACE").as_dict()
    a = render.render_record("same", "c", "TRACE", "t", SCALE, spec)
    b = render.render_record("same", "c", "TRACE", "t", SCALE, spec)
    assert a == b


def test_both_layouts_occur():
    styles = {"<<" in render.render_record(f"x{i}", "c", "TRACE", "t", SCALE, {})["rendered_prompt"]
              for i in range(20)}
    assert styles == {True, False}


def test_literal_brace_forces_sectioned_layout():
    for i in range(20):
        r = render.render_record(f"b{i}", "c", "TRACE", "Return {x} as is.", SCALE, {})
        assert "<<CONVERSATION_CONTEXT>>" in r["rendered_prompt"]


def test_sectioned_layout_separates_sections():
    r = next(r for r in (render.render_record(f"s{i}", "c", "TRACE", "t", SCALE, {})
                         for i in range(20)) if "<<" in r["rendered_prompt"])
    assert "</context>\n\n### Assistant Turn" in r["rendered_prompt"]
    assert "</assistant_response>\n\n## Evaluation Task" in r["rendered_prompt"]


def test_compact_numeric_answers_by_value():
    assert render.output_enum(NUM_SCALE, "compact") == [0.0, 1.0]
    assert render.output_enum(NUM_SCALE, "sectioned") == ["Low", "High"]
    p = render.render_compact("Judge it.\n{context}", NUM_SCALE)
    assert "0.0: low, 1.0: high" in p and '"type": "float"' in p
    compact = next(r for r in (render.render_record(f"n{i}", "c", "TRACE", "t", NUM_SCALE, {})
                               for i in range(40)) if "<<" not in r["rendered_prompt"])
    assert compact["output_enum"] == [0.0, 1.0] and compact["scale_type"] == "numerical"


def test_output_block_enum_and_style():
    s = render.output_block(["A", "B"], style={"fence": True, "quote": "backtick_or"})
    assert '"enum": ["A", "B"]' in s and "`A` or `B`" in s and "```\n{" in s


def test_normalize_scale():
    assert render.normalize_scale([{"label": "a"}], False) is None
    assert render.normalize_scale([{"label": "a"}, {"label": "a"}], False) is None
    rev = render.normalize_scale([{"label": "hi", "value": 1}, {"label": "lo", "value": 0}], True)
    assert [x["label"] for x in rev] == ["lo", "hi"]
    assert render.normalize_scale([{"label": "a"}, {"label": "b", "value": "x"}], True) is None


def test_specs_for_concept_vary_and_pin_domain():
    specs = generate.sample_specs_for_concept(random.Random(3), "TRACE", k=4, domain="legal")
    assert {s.domain for s in specs} == {"legal"}
    assert len({s.scale_family for s in specs}) >= 3
