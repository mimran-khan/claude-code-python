"""
Flatten messages to searchable plain text (transcript / slash search).

Migrated from: utils/transcriptSearch.ts
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .messages import INTERRUPT_MESSAGE, INTERRUPT_MESSAGE_FOR_TOOL_USE

_SYSTEM_REMINDER_CLOSE = "</system-reminder>"

_RENDERED_AS_SENTINEL = frozenset({INTERRUPT_MESSAGE, INTERRUPT_MESSAGE_FOR_TOOL_USE})

# Message objects are often dicts (not weakref-able); skip WeakKeyDictionary.
_search_text_cache: dict[int, str] = {}


def _strip_system_reminders(raw: str) -> str:
    t = raw
    open_idx = t.find("<system-reminder>")
    while open_idx >= 0:
        close_idx = t.find(_SYSTEM_REMINDER_CLOSE, open_idx)
        if close_idx < 0:
            break
        t = t[:open_idx] + t[close_idx + len(_SYSTEM_REMINDER_CLOSE) :]
        open_idx = t.find("<system-reminder>")
    return t


def tool_use_search_text(inp: Any) -> str:
    if not inp or not isinstance(inp, dict):
        return ""
    parts: list[str] = []
    for k in (
        "command",
        "pattern",
        "file_path",
        "path",
        "prompt",
        "description",
        "query",
        "url",
        "skill",
    ):
        v = inp.get(k)
        if isinstance(v, str):
            parts.append(v)
    for k in ("args", "files"):
        v = inp.get(k)
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            parts.append(" ".join(v))
    return "\n".join(parts)


def tool_result_search_text(r: Any) -> str:
    if r is None:
        return ""
    if isinstance(r, str):
        return r
    if not isinstance(r, dict):
        return ""
    o = r
    if isinstance(o.get("stdout"), str):
        err = o.get("stderr")
        err_s = err if isinstance(err, str) else ""
        base = o["stdout"]
        return base + ("\n" + err_s if err_s else "")
    f = o.get("file")
    if isinstance(f, dict) and isinstance(f.get("content"), str):
        return f["content"]
    parts: list[str] = []
    for k in ("content", "output", "result", "text", "message"):
        v = o.get(k)
        if isinstance(v, str):
            parts.append(v)
    for k in ("filenames", "lines", "results"):
        v = o.get(k)
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            parts.append("\n".join(v))
    return "\n".join(parts)


def _compute_search_text(msg: Any) -> str:
    raw = ""
    mtype = getattr(msg, "type", None) or (msg.get("type") if isinstance(msg, dict) else None)
    if mtype == "user":
        message = getattr(msg, "message", None) or (msg.get("message") if isinstance(msg, dict) else None)
        if not isinstance(message, dict):
            return ""
        c = message.get("content")
        if isinstance(c, str):
            raw = "" if c in _RENDERED_AS_SENTINEL else c
        elif isinstance(c, list):
            parts: list[str] = []
            tool_res = getattr(msg, "tool_use_result", None) or (
                msg.get("toolUseResult") if isinstance(msg, dict) else None
            )
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    t = b.get("text", "")
                    if t not in _RENDERED_AS_SENTINEL:
                        parts.append(t)
                elif b.get("type") == "tool_result":
                    parts.append(tool_result_search_text(tool_res))
            raw = "\n".join(parts)
    elif mtype == "assistant":
        message = getattr(msg, "message", None) or (msg.get("message") if isinstance(msg, dict) else None)
        if not isinstance(message, dict):
            return ""
        c = message.get("content")
        if isinstance(c, list):
            chunks: list[str] = []
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    chunks.append(str(b.get("text", "")))
                elif b.get("type") == "tool_use":
                    chunks.append(tool_use_search_text(b.get("input")))
            raw = "\n".join(chunks)
    elif mtype == "attachment":
        att = getattr(msg, "attachment", None) or (msg.get("attachment") if isinstance(msg, dict) else None)
        if not isinstance(att, Mapping):
            return ""
        at = att.get("type")
        if at == "relevant_memories":
            mems = att.get("memories") or []
            raw = "\n".join(str(m.get("content", "")) for m in mems if isinstance(m, dict))
        elif at == "queued_command":
            if att.get("commandMode") == "task-notification" or att.get("isMeta"):
                raw = ""
            else:
                p = att.get("prompt")
                if isinstance(p, str):
                    raw = p
                elif isinstance(p, list):
                    texts = [str(b.get("text", "")) for b in p if isinstance(b, dict) and b.get("type") == "text"]
                    raw = "\n".join(texts)
    elif mtype == "collapsed_read_search":
        rel = getattr(msg, "relevant_memories", None) or (
            msg.get("relevantMemories") if isinstance(msg, dict) else None
        )
        if rel:
            raw = "\n".join(str(m.get("content", "")) for m in rel if isinstance(m, dict))
    return _strip_system_reminders(raw)


def renderable_search_text(msg: Any) -> str:
    if not isinstance(msg, dict):
        key = id(msg)
        cached = _search_text_cache.get(key)
        if cached is not None:
            return cached
        result = _compute_search_text(msg).lower()
        _search_text_cache[key] = result
        return result
    return _compute_search_text(msg).lower()
