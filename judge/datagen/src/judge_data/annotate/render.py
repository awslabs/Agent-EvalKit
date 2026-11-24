"""Fill evidence into rubric prompts.

Handles both placeholder styles, ``<<MARKER>>`` markers and ``{slot}`` slots. The prompt text
says which one it uses.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# slot name -> marker
MARKERS = {
    "context": "<<CONVERSATION_CONTEXT>>",
    "assistant_turn": "<<ASSISTANT_FINAL_TURN>>",
    "available_tools": "<<AVAILABLE_TOOLS_CATALOG>>",
    "tool_turn": "<<JUDGED_TOOL_CALL>>",
}

# For detecting unfilled <<MARKERS>>
MARKER_RE = re.compile(r"<<([A-Z_]+)>>")

# For detecting unfilled {slot} placeholders
PLACEHOLDER_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


def load_rubric(path: str | Path, rubric_id: str) -> dict:
    with Path(path).open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("rubric_id") == rubric_id:
                return r
    raise KeyError(f"{rubric_id} not in {path}")


def fill(rubric: dict, evidence: dict[str, str]) -> str:
    """Substitute evidence into the rubric's rendered prompt.

    Two placeholder styles exist, and the prompt itself says which one it uses:
    - ``<<CONVERSATION_CONTEXT>>`` style markers
    - ``{context}`` style slots

    Evidence keys use the short slot names: context, assistant_turn,
    available_tools, tool_turn. For marker prompts, uppercase ``<<MARKER>>``
    keys (CONVERSATION_CONTEXT etc.) are also accepted.
    """
    p = rubric["rendered_prompt"]

    if MARKER_RE.search(p):
        # Try <<UPPERCASE>> keys first
        for marker in MARKER_RE.findall(p):
            if marker in evidence:
                p = p.replace(f"<<{marker}>>", evidence[marker])
        # Then try slot-name keys mapped to markers
        for slot, marker in MARKERS.items():
            if slot in evidence:
                p = p.replace(marker, evidence[slot])
    else:
        for slot in MARKERS:
            if slot in evidence:
                p = p.replace("{" + slot + "}", evidence[slot])
    return p


def unfillable(record: dict) -> set[str]:
    """Placeholders in the template that nothing here knows how to fill."""
    return set(PLACEHOLDER_RE.findall(record["rendered_prompt"])) - set(MARKERS)
