"""The `ModelClient` protocol, its `Result`, and a base class with caching and a parallel `map`.

Every stage that calls a model takes a `ModelClient`. Backends never raise from `invoke`: a call
that fails after retries comes back as `Result(ok=False, error=...)`, so one bad request cannot take
down a long run.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from judge_data.utils.cache import SqliteCache, cache_key


@dataclass
class Result:
    """One model reply."""
    text: str
    ok: bool = True
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached: bool = False
    filtered: bool = False  # the provider refused on content grounds; retrying will not help


@runtime_checkable
class ModelClient(Protocol):
    """What every backend provides."""

    model_id: str
    total_in: int
    total_out: int

    def invoke(self, prompt: str, max_tokens: int = 4096,
               temperature: float | None = None) -> Result:
        """Send one user message and return the reply."""
        ...

    def map(self, prompts: list[str], max_tokens: int = 4096,
            temperature: float | None = None, desc: str = "llm") -> list[Result]:
        """Send many prompts in parallel. Results come back in input order."""
        ...


class CachedClient:
    """Shared plumbing: response cache, token counters, and a thread pool `map`.

    Subclasses implement `_call(prompt, max_tokens, temperature) -> Result` and may extend
    `_key_extra()` with anything else that changes a reply.
    """

    def __init__(self, model_id: str, cache_path: str | None = None, concurrency: int = 32):
        self.model_id = model_id
        self.cache = SqliteCache(cache_path)
        self.concurrency = max(1, int(concurrency))
        self.total_in = 0
        self.total_out = 0
        self._stat_lock = threading.Lock()

    def _key_extra(self) -> object:
        return None

    def _call(self, prompt: str, max_tokens: int, temperature: float | None) -> Result:
        raise NotImplementedError

    def invoke(self, prompt: str, max_tokens: int = 4096,
               temperature: float | None = None) -> Result:
        key = cache_key(self.model_id, max_tokens, temperature, self._key_extra(), prompt)
        hit = self.cache.get(key)
        if hit is not None:
            d = json.loads(hit)
            return Result(text=d["text"], input_tokens=d.get("in", 0),
                          output_tokens=d.get("out", 0), cached=True)
        try:
            r = self._call(prompt, max_tokens, temperature)
        except Exception as e:  # noqa: BLE001 - a backend bug must not kill the run
            r = Result(text="", ok=False, error=f"{type(e).__name__}: {str(e)[:300]}")
        with self._stat_lock:
            self.total_in += r.input_tokens
            self.total_out += r.output_tokens
        if r.ok and r.text:
            self.cache.put(key, json.dumps({"text": r.text, "in": r.input_tokens,
                                            "out": r.output_tokens}))
        return r

    def map(self, prompts: list[str], max_tokens: int = 4096,
            temperature: float | None = None, desc: str = "llm") -> list[Result]:
        out: list[Result | None] = [None] * len(prompts)
        if not prompts:
            return []
        done = 0
        lock = threading.Lock()
        t0 = time.time()
        step = max(25, len(prompts) // 20)

        def work(ip: tuple[int, str]) -> None:
            nonlocal done
            i, p = ip
            r = self.invoke(p, max_tokens=max_tokens, temperature=temperature)
            with lock:
                out[i] = r
                done += 1
                if done % step == 0 or done == len(prompts):
                    fails = sum(1 for x in out if x is not None and not x.ok)
                    print(f"  [{desc}] {done}/{len(prompts)}  fail={fails}  "
                          f"{time.time() - t0:.0f}s  in={self.total_in} out={self.total_out}",
                          flush=True)

        with ThreadPoolExecutor(max_workers=min(self.concurrency, len(prompts))) as ex:
            list(ex.map(work, enumerate(prompts)))
        return [r if r is not None else Result(text="", ok=False, error="not run") for r in out]
