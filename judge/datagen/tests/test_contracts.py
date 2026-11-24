import json
import re

import pytest

from judge_data.annotate import contracts
from judge_data.rubric_build import render

ENUM = ["Bad", "Good"]


def _prompt(fence=True):
    return "Judge it.\n\n" + render.output_block(ENUM, style={"fence": fence})


@pytest.mark.parametrize("c", contracts.CONTRACTS)
def test_every_contract_applies_and_target_matches(c):
    p = contracts.apply(_prompt(), c, ENUM)
    assert p is not None and p.startswith("Judge it.")
    t = contracts.target("because", "Good", c)
    if c == "keyvalue":
        assert t == "Reasoning: because\nScore: Good" and "Score: <one of 'Bad' or 'Good'>" in p
    elif c == "xml":
        assert "<score>Good</score>" in t and "<score>one of" in p
    else:
        body = t if c == "verdict_bare" else re.match(r"```json\n(.*)\n```", t, re.S).group(1)
        obj = json.loads(body)
        key = "verdict" if c.startswith("verdict") else "score"
        assert obj[key] == "Good"
        if c == "score_only":
            assert list(obj) == ["score"] and '"reasoning"' not in p
        if c == "score_first":
            assert list(obj) == ["score", "reasoning"]
            schema = json.loads(p[p.index("{", p.index("Here is the output JSON schema:")):].split("\n")[0])
            assert list(schema["properties"]) == ["score", "reasoning"]


def test_verdict_bare_drops_every_fence():
    p = contracts.apply(_prompt(fence=True), "verdict_bare", ENUM)
    assert "```" not in p and p.endswith(contracts.BARE_TAIL)
    assert '"verdict"' in p and '"score"' not in p


def test_apply_refuses_when_block_missing():
    assert contracts.apply("no output block here", "xml", ENUM) is None
    assert contracts.apply("no output block here", "native", ENUM) == "no output block here"


def test_pick_is_deterministic_and_respects_weights():
    w = contracts.parse_weights("native:1,xml:1")
    picks = {contracts.pick(f"id{i}", w) for i in range(200)}
    assert picks == {"native", "xml"}
    assert contracts.pick("same", w) == contracts.pick("same", w)
    with pytest.raises(ValueError):
        contracts.parse_weights("bogus:1")
