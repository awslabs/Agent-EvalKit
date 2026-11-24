"""Pull JSON out of model replies, including slightly malformed JSON from long generations."""
from __future__ import annotations

import json


def repair_json(s: str) -> str:
    """Escape stray double quotes inside JSON string values."""
    out = []
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if esc:
            out.append(ch)
            esc = False
            continue
        if ch == "\\":
            out.append(ch)
            esc = True
            continue
        if ch == '"':
            if not in_str:
                in_str = True
                out.append(ch)
                continue
            j = i + 1
            while j < len(s) and s[j] in " \t\r\n":
                j += 1
            if j < len(s) and s[j] in ",}]:":
                in_str = False
                out.append(ch)
            else:
                out.append('\\"')
            continue
        out.append(ch)
    return "".join(out)


def balance_brackets(s: str) -> str:
    """Insert the closers a generator forgot, e.g. `[{"a": 1]` -> `[{"a": 1}]`.

    Scans outside strings. When a closer does not match the innermost open bracket, the missing
    closers are emitted first. Unclosed brackets at the end are closed too.
    """
    pairs = {"{": "}", "[": "]"}
    out, stack, in_str, esc = [], [], False, False
    for ch in s:
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in pairs:
            stack.append(pairs[ch])
        elif ch in "}]":
            if ch in stack:
                while stack and stack[-1] != ch:
                    out.append(stack.pop())
                stack.pop()
            else:
                continue  # a stray closer with nothing to close
        out.append(ch)
    return "".join(out) + "".join(reversed(stack))


def extract_json(text: str | None) -> object | None:
    """Pull the first JSON object or array out of a model reply. Returns None when nothing parses."""
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    t = t.strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    # Every caller wants the outer object. Decode from the earliest opener first, then fall back to
    # the widest {..} span (with quote repair) before any [..] span. Taking the [..] span first
    # returns an array nested inside the object whenever text surrounds the JSON.
    starts = [i for i in (t.find("{"), t.find("[")) if i != -1]
    early = None
    if starts:
        try:
            early = json.JSONDecoder().raw_decode(t, min(starts))[0]
        except ValueError:
            early = None
        if isinstance(early, dict):
            return early
    for opener, closer in (("{", "}"), ("[", "]")):
        i = t.find(opener)
        j = t.rfind(closer)
        if i == -1 or j <= i:
            continue
        chunk = t[i:j + 1]
        for candidate in (chunk, repair_json(chunk)):
            try:
                return json.loads(candidate)
            except Exception:
                continue
    if early is not None:
        return early
    # Last resorts for long generated JSON: raw newlines inside strings, and objects the generator
    # forgot to close.
    i = t.find("{")
    if i != -1:
        body = t[i:]
        for candidate in (body, balance_brackets(body), repair_json(balance_brackets(body))):
            try:
                return json.JSONDecoder(strict=False).raw_decode(candidate)[0]
            except Exception:
                continue
    return None
