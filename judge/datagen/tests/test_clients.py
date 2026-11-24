import json

import httpx
import pytest

from judge_data.clients import CachedClient, ModelClient, Result, make_client
from judge_data.clients.mock import MockClient
from judge_data.clients.openai_compat import OpenAICompatClient
from judge_data.rubric_build import embed


class Counting(CachedClient):
    def __init__(self, path):
        super().__init__("m", cache_path=path, concurrency=4)
        self.n = 0

    def _call(self, prompt, max_tokens, temperature):
        self.n += 1
        if prompt == "boom":
            raise RuntimeError("backend bug")
        return Result(text=prompt.upper(), input_tokens=1, output_tokens=2)


def test_cache_and_map_order(tmp_path):
    c = Counting(str(tmp_path / "c.sqlite"))
    assert isinstance(c, ModelClient)
    out = c.map(["a", "b", "c"])
    assert [r.text for r in out] == ["A", "B", "C"] and c.n == 3
    second = Counting(str(tmp_path / "c.sqlite"))
    assert second.invoke("b").cached and second.n == 0
    assert second.invoke("b", max_tokens=5).cached is False  # max tokens is part of the key
    bad = c.invoke("boom")
    assert not bad.ok and "backend bug" in bad.error


def test_make_client_validation():
    with pytest.raises(ValueError):
        make_client("vllm", model_id="m")
    with pytest.raises(ValueError):
        make_client("openai", base_url="http://x/v1")
    with pytest.raises(ValueError):
        make_client("nope")
    assert isinstance(make_client("mock"), MockClient)


def _serve(client, handler):
    client._http = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def test_openai_client_request_shape_and_routing():
    seen = []

    def handler(req):
        seen.append((str(req.url), json.loads(req.content)))
        if req.url.path.endswith("/embeddings"):
            return httpx.Response(200, json={"data": [{"index": 0, "embedding": [3.0, 4.0]}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": "<think>x</think> hi"},
                                                      "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 5, "completion_tokens": 1}})

    c = _serve(OpenAICompatClient("http://a/v1,http://b/v1", "m", cache_path=None,
                                  disable_thinking=True), handler)
    r = c.invoke("p", max_tokens=7, temperature=0.0)
    assert r.ok and r.text == "<think>x</think> hi" and c.total_in == 5
    body = seen[0][1]
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["max_tokens"] == 7 and body["temperature"] == 0.0
    c.invoke("q")
    assert {u.split("/v1")[0] for u, _ in seen} == {"http://a", "http://b"}

    t = _serve(OpenAICompatClient("http://a/v1", "m", cache_path=None,
                                  chat_template_kwargs={"enable_thinking": True}), handler)
    assert t.invoke("p").text == "hi"
    assert t.embed(["x"]) == [[3.0, 4.0]]


def test_openai_client_failure_is_a_result():
    def handler(req):
        return httpx.Response(400, json={"error": "bad request"})
    c = _serve(OpenAICompatClient("http://a/v1", "m", cache_path=None, max_retries=1), handler)
    r = c.invoke("p")
    assert not r.ok and "HTTP 400" in r.error


def test_mock_dispatch():
    m = MockClient()
    assert m.stage_of("You are generating synthetic agent execution traces ...") == "synth"
    assert m.stage_of("anything else") == "judge"
    assert json.loads(m.invoke("Read the agent trace below and judge one property.").text)["severity"]
    assert MockClient(fail_every=1).invoke("x").ok is False


def test_hash_embedder_and_fallback():
    v = embed.embed_texts(["the agent stops early", "the agent stops early", "totally different"],
                          embed.hash_embedder())
    assert v.shape[0] == 3 and abs(float(v[0] @ v[1]) - 1.0) < 1e-5 and float(v[0] @ v[2]) < 0.5

    def broken(texts):
        raise RuntimeError("no model")
    assert embed.embed_texts(["a", "b"], broken).shape[0] == 2
