"""JSONL helpers and a timestamped logger."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def read_jsonl(path: str | Path) -> list[dict]:
    """Read a JSONL file. Blank and torn lines are skipped. A missing file reads as empty."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with p.open(errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n
