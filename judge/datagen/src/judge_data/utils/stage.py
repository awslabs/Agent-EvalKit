"""Resumable stage runner.

Two layers of resume, because either one alone leaves a hole.

The model client cache is keyed on the prompt, so a rerun skips calls that already completed. That
alone is not enough: a stage that dies partway has done work the cache remembers but has written no
output, so the caller cannot tell what is left.

So a stage also appends every finished item to a JSONL file as it goes, keyed by a stable item id.
On restart the ids already present are skipped without consulting the cache.
"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterable

from judge_data.utils.io import read_jsonl


def _failed(rec: dict) -> bool:
    return rec.get("error") is not None or rec.get("ok") is False


def done_ids(path: str | Path, id_field: str = "id") -> set[str]:
    """Ids already finished in a stage output file.

    A record with an `error` field (or `ok: false`) does not count as finished unless it is marked
    `permanent`. Otherwise a rerun would skip exactly the items that need retrying.
    """
    out: set[str] = set()
    for rec in read_jsonl(path):
        if _failed(rec) and not rec.get("permanent"):
            continue
        if id_field in rec:
            out.add(str(rec[id_field]))
    return out


class Writer:
    """Append only JSONL writer that flushes every record, so the resume guarantee holds."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._f = self.path.open("a")
        self.n = 0

    def write(self, rec: dict) -> None:
        # A lone UTF-16 surrogate in trace content passes through json.dumps with
        # ensure_ascii=False and then fails to encode. Replace it: it is a broken byte, not data.
        line = json.dumps(rec, ensure_ascii=False).encode("utf-8", "replace").decode("utf-8")
        with self._lock:
            self._f.write(line + "\n")
            self._f.flush()
            os.fsync(self._f.fileno())
            self.n += 1

    def close(self) -> None:
        with self._lock:
            self._f.close()


def run_stage(items: Iterable[dict], out_path: str | Path, work: Callable[[dict], dict | None],
              workers: int = 32, desc: str = "stage", id_field: str = "id",
              report_every: int = 25) -> int:
    """Apply `work` to every item not already in `out_path`, appending results as they land.

    `work` returns the record to write, or None to skip the item without recording it (it is then
    retried on the next run). Record permanent failures with an error field and `permanent: true`.
    """
    items = list(items)
    already = done_ids(out_path, id_field)
    todo = [it for it in items if str(it[id_field]) not in already]
    print(f"[{desc}] {len(items)} items, {len(already)} already done, {len(todo)} to do", flush=True)
    if not todo:
        return 0

    w = Writer(out_path)
    t0 = time.time()
    counter = {"n": 0, "fail": 0}
    lock = threading.Lock()

    def one(it: dict) -> None:
        # The write is inside the guard: a record that cannot be serialised costs one item, not the run.
        try:
            rec = work(it)
            if rec is not None:
                w.write(rec)
        except Exception as e:  # noqa: BLE001
            with lock:
                counter["fail"] += 1
            print(f"[{desc}] item {it.get(id_field)} raised {type(e).__name__}: {e}", flush=True)
        with lock:
            counter["n"] += 1
            n = counter["n"]
        if n % report_every == 0 or n == len(todo):
            el = time.time() - t0
            rate = n / el if el else 0
            eta = (len(todo) - n) / rate if rate else 0
            print(f"[{desc}] {n}/{len(todo)}  written={w.n}  fail={counter['fail']}  "
                  f"{el:.0f}s  eta {eta / 60:.1f}m", flush=True)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        list(ex.map(one, todo))
    w.close()
    return w.n


def load_by_id(path: str | Path, id_field: str = "id") -> dict[str, dict]:
    """Read a stage output keyed by id. A success always beats a failure, otherwise later wins."""
    out: dict[str, dict] = {}
    for rec in read_jsonl(path):
        k = str(rec.get(id_field))
        if k in out and _failed(rec) and not _failed(out[k]):
            continue
        out[k] = rec
    return out
