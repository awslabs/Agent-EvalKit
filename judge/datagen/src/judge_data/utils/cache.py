"""Thread safe SQLite key value cache for model replies.

Keys are hashes of everything that changes a reply (model, prompt, max tokens, temperature, extra
request fields), so an interrupted run resumes with zero repeated calls.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path


def cache_key(*parts: object) -> str:
    raw = "|".join(p if isinstance(p, str) else json.dumps(p, sort_keys=True, default=str)
                   for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()


class SqliteCache:
    """`get` and `put` on string values. Pass `path=None` for a cache that stores nothing."""

    def __init__(self, path: str | Path | None):
        self._lock = threading.Lock()
        self._conn = None
        if path and str(path).lower() != "none":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("CREATE TABLE IF NOT EXISTS c (k TEXT PRIMARY KEY, v TEXT)")
            self._conn.commit()

    def get(self, k: str) -> str | None:
        if self._conn is None:
            return None
        with self._lock:
            row = self._conn.execute("SELECT v FROM c WHERE k = ?", (k,)).fetchone()
        return row[0] if row else None

    def put(self, k: str, v: str) -> None:
        if self._conn is None:
            return
        with self._lock:
            self._conn.execute("INSERT OR REPLACE INTO c VALUES (?, ?)", (k, v))
            self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            with self._lock:
                self._conn.close()
                self._conn = None
