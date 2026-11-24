import json

import pytest

CONCEPTS = [
    {"concept_id": "c0001", "concept": "the agent retried a failing tool call without changing "
     "its approach", "level": "SESSION", "domain": "general"},
    {"concept_id": "c0002", "concept": "tool arguments are taken from the conversation rather "
     "than invented", "level": "TOOL_CALL", "domain": "ecommerce"},
]

AGENTS = [
    {"agent_id": "example/shop-assistant", "source_repo": "https://github.com/example/shop-assistant",
     "system_prompt": "You help customers with orders.",
     "tools": [{"name": "get_order", "description": "Look up an order"},
               {"name": "refund_order", "description": "Refund an order"}],
     "framework": "langgraph", "domain": "customer_support"},
    {"agent_id": "example/research-bot", "source_repo": "https://github.com/example/research-bot",
     "system_prompt": "You research topics on the web.", "tools": ["web_search", "fetch_page"],
     "framework": "strands", "domain": "web_research"},
]


def trace_row(i: int) -> dict:
    return {"trace_id": f"t{i}", "agent_id": f"example/agent-{i % 3}", "framework": "strands",
            "user_goal": "refund an order", "tags": {"topic": ["shop", "travel"][i % 2]},
            "target_labels": {"args_grounded": i % 2},
            "primary_dim": "args_grounded",
            "turns": [
                {"user": "Refund order 12", "reasoning": "",
                 "assistant": "<thinking>check the order first</thinking>Looking it up.",
                 "tool_calls": [{"tool_name": "get_order", "arguments": {"id": "12"}}],
                 "tool_results": [{"status": "ok"}]},
                {"user": "thanks", "assistant": "Refund issued.",
                 "tool_calls": [{"tool_name": "refund_order", "arguments": {"id": "12"}}],
                 "tool_results": [{"error": "timeout"} if i % 3 == 0 else {"ok": True}]}]}


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


@pytest.fixture
def concepts_file(tmp_path):
    return write_jsonl(tmp_path / "concepts.jsonl", CONCEPTS)


@pytest.fixture
def agents_file(tmp_path):
    return write_jsonl(tmp_path / "agents.jsonl", AGENTS)


@pytest.fixture
def pool_file(tmp_path):
    return write_jsonl(tmp_path / "pool.jsonl", [trace_row(i) for i in range(8)])
