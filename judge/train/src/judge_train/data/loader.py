"""Read training records from JSONL files or globs."""

from __future__ import annotations

import glob
import json
from collections.abc import Iterator
from itertools import islice
from pathlib import Path

from judge_train.data.schema import Example, parse_example


def resolve_paths(path: str) -> list[str]:
    """Resolve a file path or glob pattern to a sorted list of files."""
    files = sorted(glob.glob(path))
    if not files:
        p = Path(path)
        if p.exists():
            files = [str(p)]
        else:
            raise FileNotFoundError(f"No files found matching: {path}")
    return files


def iter_examples(path: str) -> Iterator[dict]:
    """Stream raw dicts from JSONL. Blank lines are skipped."""
    for filepath in resolve_paths(path):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def build_stream(path: str, max_samples: int | None = None) -> Iterator[dict]:
    """Lazy stream of raw dicts, optionally truncated to max_samples."""
    stream = iter_examples(path)
    if max_samples:
        stream = islice(stream, max_samples)
    return stream


def load_examples(path: str) -> list[Example]:
    """Load and validate every record. Raises on the first invalid record."""
    records: list[Example] = []
    for i, raw in enumerate(iter_examples(path)):
        try:
            records.append(parse_example(raw))
        except ValueError as e:
            raise ValueError(f"Invalid record #{i} in {path}: {e}") from e
    return records
