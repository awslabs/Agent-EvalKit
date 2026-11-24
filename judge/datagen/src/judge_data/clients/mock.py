"""A deterministic offline client for tests and dry runs.

`MockClient` recognises which stage is calling from the opening of the prompt and returns a
canned reply in the JSON shape that stage parses. Replies vary with a hash of the prompt, so
different prompts get different (but reproducible) answers. No network, no model.

`MockClient.calls` counts calls per stage, which tests use to check what ran.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from collections import Counter

from judge_data.clients.base import Result

# (stage name, prompt prefix). Order matters only where prefixes overlap.
STAGES = [
    ("author", "You are building a registry of evaluation concepts for an agent evaluation service.\n"
               "A concept is"),
    ("extract", "You are building a registry of evaluation concepts"),
    ("judgeable", "An online evaluation service scores live traffic"),
    ("relabel", "Restate each measured property below"),
    ("generate", "You are writing evaluator definitions"),
    ("synth", "You are generating synthetic agent execution traces"),
    ("verify", "Read the agent trace below and judge one property"),
    ("rubric_features", "You are annotating an evaluation rubric"),
    ("trace_features", "You are annotating an agent trace"),
]

CONCEPT_WORDS = ["stays on the user's stated goal", "grounds claims in tool output",
                 "asks before an irreversible action", "keeps the reply short",
                 "recovers from a failed tool call", "respects the spending limit",
                 "reports uncertainty honestly", "uses the right tool for the request"]
LABELS = {2: ["No", "Yes"], 3: ["Poor", "Fair", "Good"], 4: ["Poor", "Weak", "Solid", "Strong"],
          5: ["Very Poor", "Poor", "Fair", "Good", "Excellent"]}


def _h(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def _fence(obj) -> str:
    return "```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```"


def _labels(n: int) -> list[str]:
    return LABELS.get(n) or [f"Level {i + 1}" for i in range(n)]


class MockClient:
    """Satisfies `ModelClient`. Never fails unless `fail_every` is set."""

    def __init__(self, model_id: str = "mock", fail_every: int = 0):
        self.model_id = model_id
        self.total_in = 0
        self.total_out = 0
        self.calls: Counter = Counter()
        self.fail_every = fail_every
        self._lock = threading.Lock()
        self._n = 0

    # ── ModelClient ─────────────────────────────────────────────────────────
    def invoke(self, prompt: str, max_tokens: int = 4096,
               temperature: float | None = None) -> Result:
        stage = self.stage_of(prompt)
        with self._lock:
            self.calls[stage] += 1
            self._n += 1
            n = self._n
            self.total_in += len(prompt) // 4
        if self.fail_every and n % self.fail_every == 0:
            return Result(text="", ok=False, error="mock failure")
        text = getattr(self, f"_r_{stage}")(prompt)
        with self._lock:
            self.total_out += len(text) // 4
        return Result(text=text, input_tokens=len(prompt) // 4, output_tokens=len(text) // 4)

    def map(self, prompts: list[str], max_tokens: int = 4096,
            temperature: float | None = None, desc: str = "llm") -> list[Result]:
        return [self.invoke(p, max_tokens, temperature) for p in prompts]

    # ── dispatch ────────────────────────────────────────────────────────────
    @staticmethod
    def stage_of(prompt: str) -> str:
        for name, prefix in STAGES:
            if prompt.startswith(prefix):
                return name
        return "judge"

    # ── rubric_build ────────────────────────────────────────────────────────
    def _r_extract(self, p: str) -> str:
        out = []
        for idx in re.findall(r"^--- rubric_idx (\S+)$", p, re.M):
            k = _h(idx)
            out.append({"idx": int(idx) if idx.isdigit() else idx,
                        "concept": f"the agent {CONCEPT_WORDS[k % len(CONCEPT_WORDS)]}",
                        "level": ["SESSION", "TRACE", "TOOL_CALL"][k % 3],
                        "needs_reference": False, "agentic": bool(k % 2)})
        return json.dumps(out)

    def _r_author(self, p: str) -> str:
        n = int(re.search(r"Write (\d+) new concepts", p).group(1))
        k = _h(p)
        return json.dumps([{"concept": f"the agent {CONCEPT_WORDS[(k + i) % len(CONCEPT_WORDS)]} "
                                       f"in case {k % 997}-{i}",
                            "note": "visible in the tool calls"} for i in range(n)])

    @staticmethod
    def _candidates(p: str) -> int:
        tail = p.split("Candidates:", 1)[-1]
        return len(re.findall(r"^\d+\. ", tail, re.M))

    def _r_judgeable(self, p: str) -> str:
        return json.dumps([{"i": j, "ok": "yes"} for j in range(self._candidates(p))])

    def _r_relabel(self, p: str) -> str:
        return json.dumps([{"i": 0, "restated": "a restated observable property of the agent"}])

    def _r_generate(self, p: str) -> str:
        concept = re.search(r"## The property being measured\n(.*)\n", p).group(1).strip()
        items = re.split(r"^(?=\d+\. Scale: )", p.split("## Output format")[0], flags=re.M)[1:]
        out = []
        for j, block in enumerate(items):
            n = int(re.match(r"\d+\. Scale: (\d+) levels", block).group(1))
            numeric = "with a numeric value" in block
            scale = []
            for i, lab in enumerate(_labels(n)):
                s = {"label": lab, "definition": f"The evidence places the case at {lab.lower()}."}
                if numeric:
                    s["value"] = round(i / (n - 1), 4)
                scale.append(s)
            out.append({"metric_name": f"Mock Metric {j + 1}",
                        "task": (f"You judge one property of an agent: {concept}. Read the "
                                 f"evidence, compare what the agent did with the property, and "
                                 f"pick the level that fits best. Angle {j + 1}."),
                        "scale": scale})
        return json.dumps(out)

    # ── trace_synth ─────────────────────────────────────────────────────────
    def _r_synth(self, p: str) -> str:
        tools_block = p.split("### Tools available\n", 1)[-1].split("\n\n## ", 1)[0]
        tools = re.findall(r"^- ([^:\n]+)", tools_block, re.M) or ["lookup"]
        k = _h(p)
        t1, t2 = tools[k % len(tools)].strip(), tools[(k + 1) % len(tools)].strip()
        turns = [
            {"user": "I need help with my request from yesterday.", "reasoning": "",
             "assistant": "Sure. Let me look that up for you.",
             "tool_calls": [{"tool_name": t1, "arguments": {"query": f"request {k % 1000}"}}],
             "tool_results": [{"status": "ok", "items": 2}]},
            {"user": "Great, can you also check the second item?",
             "reasoning": "The user wants the second item checked too.",
             "assistant": "Checking the second item now.",
             "tool_calls": [{"tool_name": t2, "arguments": {"item": 2}}],
             "tool_results": [{"status": "ok", "detail": "in stock"}]},
            {"user": "Thanks, anything else I should know?", "reasoning": "",
             "assistant": f"Both items are confirmed. Reference number {k % 10000}.",
             "tool_calls": [], "tool_results": []},
        ]
        return json.dumps({"turns": turns, "note": "the property shows in the final reply"})

    def _r_verify(self, p: str) -> str:
        sev = ["absent", "partial", "full"][_h(p) % 3]
        return json.dumps({"reasoning": "Placed from the final reply.", "severity": sev})

    # ── rubric_trace_match ──────────────────────────────────────────────────
    def _r_rubric_features(self, p: str) -> str:
        return json.dumps({"behaviors_required": {"tool_usage": 0.5, "multi_turn_interaction": 0.3},
                           "min_turns": 1, "needs_tool_call": False,
                           "explanation": "any trace with a tool call"})

    def _r_trace_features(self, p: str) -> str:
        k = _h(p)
        return json.dumps({"behaviors_present": {"tool_usage": 0.4 + (k % 6) / 10,
                                                 "multi_turn_interaction": 0.5},
                           "domains": {"general": 1.0}, "trace_quality": 0.7,
                           "evaluable_turns": [{"turn_index": 0, "behaviors": ["tool_usage"],
                                                "reason": "first reply"}],
                           "evaluable_tool_calls": []})

    # ── annotate ────────────────────────────────────────────────────────────
    def _r_judge(self, p: str) -> str:
        enum: list = ["Yes", "No"]
        key = "score"
        m = re.search(r"Here is (?:the|your) output JSON schema:", p)
        if m:
            i = p.find("{", m.end())
            try:
                schema = json.JSONDecoder().raw_decode(p, i)[0]
                props = schema.get("properties", {})
                key = "score" if "score" in props else ("verdict" if "verdict" in props else "score")
                enum = props.get(key, {}).get("enum") or enum
            except ValueError:
                pass
        score = enum[_h(p) % len(enum)]
        return _fence({"reasoning": "The agent's actions match this level of the rubric.", key: score})
