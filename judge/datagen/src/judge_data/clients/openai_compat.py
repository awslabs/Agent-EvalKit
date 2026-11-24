"""Client for any OpenAI compatible endpoint: vLLM, SGLang, LiteLLM proxies, hosted APIs.

* Several replicas of one model can be given as a comma separated `base_url`. Each request goes to
  the replica with the fewest requests in flight, which keeps a slightly slower replica from piling
  up work and preempting.
* Retries with exponential backoff on transport errors and 429/5xx replies.
* `embed()` calls `/embeddings` on the same endpoint, for concept deduplication.
"""
from __future__ import annotations

import itertools
import logging
import threading
import time

import httpx

from judge_data.clients.base import CachedClient, Result

logger = logging.getLogger(__name__)

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class OpenAICompatClient(CachedClient):
    """Chat completions over HTTP with an SQLite reply cache.

    `disable_thinking=True` sends `chat_template_kwargs={"enable_thinking": false}` unless explicit
    `chat_template_kwargs` are given, which is what vLLM serves for hybrid reasoning models. Leave it
    off for endpoints that reject unknown request fields. When thinking is on, everything up to the
    first `</think>` is dropped from the reply.
    """

    def __init__(self, base_url: str, model_id: str, api_key: str | None = None,
                 cache_path: str | None = "llm_cache.sqlite", concurrency: int = 256,
                 max_retries: int = 4, timeout: float = 1800.0,
                 chat_template_kwargs: dict | None = None, disable_thinking: bool = False):
        super().__init__(model_id=model_id, cache_path=cache_path, concurrency=concurrency)
        self.base_urls = [u.strip().rstrip("/") for u in base_url.split(",") if u.strip()]
        if not self.base_urls:
            raise ValueError("base_url is empty")
        self._inflight = {u: 0 for u in self.base_urls}
        self._tie = itertools.count()
        self._route_lock = threading.Lock()
        self.max_retries = max_retries
        self.chat_template_kwargs = chat_template_kwargs
        if chat_template_kwargs is None and disable_thinking:
            self.chat_template_kwargs = {"enable_thinking": False}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        limits = httpx.Limits(max_connections=self.concurrency + 8,
                              max_keepalive_connections=self.concurrency + 8)
        self._http = httpx.Client(headers=headers, timeout=timeout, limits=limits)

    def _key_extra(self) -> object:
        return self.chat_template_kwargs

    def _acquire(self) -> str:
        with self._route_lock:
            start = next(self._tie) % len(self.base_urls)
            order = self.base_urls[start:] + self.base_urls[:start]
            base = min(order, key=self._inflight.__getitem__)
            self._inflight[base] += 1
            return base

    def _release(self, base: str) -> None:
        with self._route_lock:
            self._inflight[base] -= 1

    def _post(self, path: str, body: dict) -> dict:
        last: Exception | None = None
        for attempt in range(self.max_retries):
            base = self._acquire()
            try:
                resp = self._http.post(f"{base}{path}", json=body)
                if resp.status_code in RETRY_STATUS:
                    raise httpx.HTTPStatusError(f"HTTP {resp.status_code}", request=resp.request,
                                                response=resp)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                last = e
                if e.response is not None and e.response.status_code not in RETRY_STATUS:
                    raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text[:300]}") from e
            except (httpx.TransportError, ValueError) as e:
                last = e
            finally:
                self._release(base)
            wait = min(2 ** attempt, 30)
            logger.warning("request failed (%s), attempt %d/%d, retrying in %ds",
                           last, attempt + 1, self.max_retries, wait)
            time.sleep(wait)
        raise RuntimeError(f"failed after {self.max_retries} attempts: {last}")

    def _call(self, prompt: str, max_tokens: int, temperature: float | None) -> Result:
        body: dict = {"model": self.model_id,
                      "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": max_tokens}
        if temperature is not None:
            body["temperature"] = temperature
        if self.chat_template_kwargs is not None:
            body["chat_template_kwargs"] = self.chat_template_kwargs
        try:
            data = self._post("/chat/completions", body)
        except RuntimeError as e:
            return Result(text="", ok=False, error=str(e)[:400])
        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content") or ""
        if (self.chat_template_kwargs or {}).get("enable_thinking"):
            # Reasoning that never closed (ran out of tokens) leaves no answer at all.
            text = text.split("</think>", 1)[1].lstrip() if "</think>" in text else ""
        usage = data.get("usage") or {}
        filtered = choice.get("finish_reason") == "content_filter"
        return Result(text=text, ok=bool(text), error=None if text else
                      f"empty reply (finish_reason={choice.get('finish_reason')})",
                      input_tokens=usage.get("prompt_tokens", 0) or 0,
                      output_tokens=usage.get("completion_tokens", 0) or 0, filtered=filtered)

    def embed(self, texts: list[str], model: str | None = None, batch_size: int = 64) -> list[list[float]]:
        """Embeddings from `/embeddings`. Raises on failure, the caller decides how to degrade."""
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = [t[:8000] for t in texts[i:i + batch_size]]
            data = self._post("/embeddings", {"model": model or self.model_id, "input": chunk})
            rows = sorted(data["data"], key=lambda d: d.get("index", 0))
            out.extend(r["embedding"] for r in rows)
        return out
