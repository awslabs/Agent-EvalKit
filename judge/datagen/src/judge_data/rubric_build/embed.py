"""Sentence embeddings for concept deduplication. Pluggable, and it degrades gracefully.

Backends, chosen with `make_embedder(kind, ...)`:

  openai                 `/v1/embeddings` on any OpenAI compatible endpoint (vLLM serves these too)
  sentence-transformers  a local model, needs the `[embed]` extra
  hash                   hashed word and word pair counts. No model, no network. Good enough to
                         catch near verbatim duplicates, weak on paraphrases.
  auto                   openai when a base URL is given, else sentence-transformers when it is
                         installed, else hash

Every backend returns L2 normalised float32 rows, so a dot product is a cosine similarity. If the
chosen backend fails at call time, `embed_texts` logs a warning and falls back to `hash`.
"""
from __future__ import annotations

import hashlib
import re
from typing import Callable

import numpy as np

from judge_data.utils.io import log

DEFAULT_ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
Embedder = Callable[[list[str]], np.ndarray]
_WORD = re.compile(r"[a-z0-9]+")


def _normalise(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    if v.ndim == 1:
        v = v.reshape(1, -1)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)


def hash_embedder(dims: int = 1024) -> Embedder:
    def embed(texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), dims), dtype=np.float32)
        for i, t in enumerate(texts):
            w = _WORD.findall(t.lower())
            for tok in w + [f"{a} {b}" for a, b in zip(w, w[1:])]:
                h = int(hashlib.md5(tok.encode()).hexdigest()[:8], 16)
                out[i, h % dims] += 1.0 if " " not in tok else 0.5
        return _normalise(out) if len(texts) else out
    return embed


def openai_embedder(base_url: str, model: str, api_key: str | None = None) -> Embedder:
    from judge_data.clients.openai_compat import OpenAICompatClient

    client = OpenAICompatClient(base_url=base_url, model_id=model, api_key=api_key, cache_path=None,
                                concurrency=4)

    def embed(texts: list[str]) -> np.ndarray:
        return _normalise(np.asarray(client.embed(texts, model=model)))
    return embed


def st_embedder(model: str | None = None) -> Embedder:
    from sentence_transformers import SentenceTransformer

    m = SentenceTransformer(model or DEFAULT_ST_MODEL)

    def embed(texts: list[str]) -> np.ndarray:
        return _normalise(m.encode(texts, batch_size=64, normalize_embeddings=True))
    return embed


def make_embedder(kind: str = "auto", model: str | None = None, base_url: str | None = None,
                  api_key: str | None = None) -> Embedder:
    if kind == "auto":
        if base_url:
            kind = "openai"
        else:
            try:
                import sentence_transformers  # noqa: F401
                kind = "sentence-transformers"
            except ImportError:
                kind = "hash"
    if kind == "openai":
        if not (base_url and model):
            raise ValueError("the openai embedder needs --embed-base-url and --embed-model")
        return openai_embedder(base_url, model, api_key)
    if kind == "sentence-transformers":
        return st_embedder(model)
    if kind == "hash":
        return hash_embedder()
    raise ValueError(f"unknown embedder {kind!r}")


def embed_texts(texts: list[str], embedder: Embedder | None = None) -> np.ndarray:
    """(n, dims) unit vectors, one per text. Falls back to the hash embedder on any failure."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    emb = embedder or make_embedder("auto")
    try:
        return _normalise(emb(texts))
    except Exception as e:  # noqa: BLE001
        log(f"embedder failed ({type(e).__name__}: {str(e)[:120]}), falling back to hash embeddings")
        return hash_embedder()(texts)


def add_embed_args(ap) -> None:
    g = ap.add_argument_group("embeddings (concept deduplication)")
    g.add_argument("--embed-backend", default="auto",
                   choices=["auto", "openai", "sentence-transformers", "hash"])
    g.add_argument("--embed-model", default=None,
                   help=f"Embedding model (sentence-transformers default: {DEFAULT_ST_MODEL})")
    g.add_argument("--embed-base-url", default=None,
                   help="OpenAI compatible base URL serving /v1/embeddings")
    g.add_argument("--embed-api-key", default=None)


def embedder_from_args(a) -> Embedder:
    try:
        return make_embedder(a.embed_backend, a.embed_model, a.embed_base_url, a.embed_api_key)
    except Exception as e:  # noqa: BLE001
        log(f"could not build the {a.embed_backend} embedder ({e}), using hash embeddings")
        return hash_embedder()
