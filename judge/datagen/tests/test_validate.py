from judge_data.clients.mock import MockClient
from judge_data.rubric_build import validate


def test_check_schema_errors():
    errs = validate.check_schema({"rubric_id": "x", "concept": "c", "level": "TRACE",
                                  "score_enum": ["A", "A"],
                                  "rendered_prompt": "<<CONVERSATION_CONTEXT>> <<JUDGED_TOOL_CALL>>"})
    assert "duplicate labels in score_enum" in errs
    assert any("missing evidence slots" in e for e in errs)
    assert any("unexpected placeholders" in e for e in errs)
    mixed = validate.check_schema({"rubric_id": "x", "concept": "c", "level": "SESSION",
                                   "score_enum": ["A", "B"],
                                   "rendered_prompt": "<<CONVERSATION_CONTEXT>> {available_tools}"})
    assert any("mixes" in e for e in mixed)
    ok = {"rubric_id": "x", "concept": "c", "level": "SESSION", "score_enum": ["A", "B"],
          "placeholders": ["context"], "rendered_prompt": "<<CONVERSATION_CONTEXT>>"}
    assert validate.check_schema(ok) == []
    assert any(e.startswith("invalid level") for e in validate.check_schema({"level": "X"}))


def test_cleanroom_flags_copied_prose():
    seed = {"metric_name": "Politeness", "definition": "the response addresses the user politely "
            "and never uses dismissive or condescending language toward them"}
    copied = {"rubric_id": "bad", "scale": [],
              "task": "Check that the response addresses the user politely and never uses "
                      "dismissive or condescending language."}
    fresh = {"rubric_id": "good", "scale": [],
             "task": "Decide whether the agent's tone stays respectful throughout."}
    res = validate.cleanroom_check([copied, fresh], [validate.seed_text(seed)])
    assert res["failed_ids"] == ["bad"] and res["checked"] == 2
    assert res["worst"][0]["longest_run"] >= 8


def test_relabel_only_when_copied():
    c = MockClient()
    src = "the response asserts claims that are not supported by the provided context at all"
    assert validate.relabel_if_copied("keeps things short", src, c) == "keeps things short"
    assert c.calls["relabel"] == 0
    new = validate.relabel_if_copied("the response asserts claims that are not supported by the "
                                     "provided context", src, c)
    assert new != "the response asserts claims" and c.calls["relabel"] == 1


def test_functional_test_fills_every_slot():
    rubric = {"level": "TOOL_CALL", "output_enum": ["No", "Yes"],
              "rendered_prompt": "{context}\n{available_tools}\n{tool_turn}\nHere is the output "
              'JSON schema:\n{"properties": {"score": {"enum": ["No", "Yes"]}}}'}
    res = validate.functional_test(rubric, MockClient())
    assert res["parsed"] and res["in_enum"]
