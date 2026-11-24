"""Remove things from a trace that an evaluation service would never send, and detect what cannot be removed.

Two separate problems live here because they share one mechanism.

The first is target label leakage. A synthetic trace pool is often built by telling a generator
which labels a trace should end up carrying, and the generator sometimes narrates that instruction
into the trace. A trace that says "the label is 0, so I need to hallucinate some details"
hands the judge the answer. That is not label noise, it is a shortcut channel, and it is worse than
noise because real traffic contains nothing like it.

The second is internal reasoning. Some pools bake `<thinking>` blocks straight into the agent
response text, so they arrive as part of the response rather than as a separate field. An
evaluation service does not include them.

The mechanism is the same for both, because most leaks sit inside a thinking block. Removing
thinking blocks removes most leakage as a side effect. What survives removal is in tool results,
tool call arguments, or the agent's own prose, so those records are dropped rather than patched.

Three tag spellings are handled: `<thinking>`, `<think>` and `<reasoning>`. An opener with no closer
counts as unremovable.
"""
from __future__ import annotations

import hashlib
import re
from typing import Callable

# One alternation for all three spellings, with a backreference so an opener only closes with its
# own tag. Non greedy so adjacent blocks do not merge into one span.
BLOCK = re.compile(r"<(thinking|think|reasoning)\s*>(.*?)</\1\s*>", re.S | re.I)
ANY_TAG = re.compile(r"</?(?:thinking|think|reasoning)\s*>", re.I)

# Internal metadata vocabulary. Underscore dimension names cannot occur in natural agent prose, so
# they need no context to be conclusive. The phrase patterns are the generator narrating its own
# instructions back into the trace. Precision matters more than recall here: a bare word like
# "injected" fires on ordinary agent prose ("credentials are injected at runtime").
LEAK = [
    re.compile(r"target_labels"),
    re.compile(r"target (?:profile|label|spec)", re.I),
    re.compile(r"(?:I need to|I should|I must) (?:deliberately|intentionally|hallucinate"
               r"|use the wrong|pick the wrong|fail |ignore the)", re.I),
    re.compile(r"(?:this scenario|the scenario) (?:requires|specifies|calls for)"
               r"|per the (?:target|scenario)", re.I),
]


def leaks(text: str) -> bool:
    return any(p.search(text) for p in LEAK)


def has_tag(text: str) -> bool:
    return bool(ANY_TAG.search(text))


def strip_thinking(text: str, only: Callable[[str], bool] | None = None) -> tuple[str, int]:
    """Remove reasoning blocks and return the text with the number removed.

    With `only`, a block is removed just when the predicate holds on its body, which is how leak
    only removal keeps the rest of the agent's reasoning in place. Whether the result is acceptable
    is the caller's judgement, since the two modes have different success conditions: full removal
    wants no tag left, leak only removal wants no leak left.
    """
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        if only is not None and not only(m.group(2)):
            return m.group(0)
        n += 1
        return ""

    return BLOCK.sub(sub, text), n


def strip_all(text: str) -> str:
    return strip_thinking(text)[0]


def strip_leaky(text: str) -> str:
    return strip_thinking(text, only=leaks)[0]


FENCE = re.compile(r"\A```[a-zA-Z]*\s*|\s*```\Z")


def unfence(text: str) -> str:
    """Strip a markdown code fence, with or without a language tag, if there is one.

    Assembled targets are fenced, because the rubric's output block instructs the judge to wrap its
    reply in triple backticks. Annotation stage records are bare. Anything reading a completion has to
    accept both, and it has to be one function rather than a copy in each reader, because a parsing
    rule kept in two places drifts and then only one of them is right.
    """
    t = text.strip()
    return FENCE.sub("", t).strip() if t.startswith("```") else t


def bit(pair_id: str, salt: str, mod: int = 100) -> int:
    """Deterministic per record draw.

    md5 rather than `hash`, because Python randomises string hashing per process, so a rerun would
    assign different records and every prompt would change, which voids the prompt keyed LLM cache
    and silently doubles the bill. Salted so independent decisions on the same record do not
    correlate.
    """
    return int(hashlib.md5(f"{pair_id}:{salt}".encode()).hexdigest()[:8], 16) % mod
