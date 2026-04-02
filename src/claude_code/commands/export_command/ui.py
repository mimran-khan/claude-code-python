"""
/export local-jsx handler (conversation export).

Migrated from: commands/export/export.tsx
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any


def format_timestamp(date: datetime) -> str:
    return f"{date.year}-{date.month:02d}-{date.day:02d}-{date.hour:02d}{date.minute:02d}{date.second:02d}"


def extract_first_prompt(messages: list[Any]) -> str:
    for msg in messages:
        mtype = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
        if mtype != "user":
            continue
        body = msg.get("message") if isinstance(msg, dict) else getattr(msg, "message", None)
        content: Any = None
        if isinstance(body, dict):
            content = body.get("content")
        elif body is not None and hasattr(body, "content"):
            content = getattr(body, "content", None)
        result = ""
        if isinstance(content, str):
            result = content.strip()
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                    result = str(item["text"]).strip()
                    break
        first = (result.split("\n", 1)[0] if result else "").strip()
        if len(first) > 50:
            return first[:49] + "…"
        return first
    return ""


def sanitize_filename(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def render_messages_to_plain_text(messages: list[Any], _tools: list[Any] | None) -> str:
    """
    Plain-text export of conversation (subset of TS renderMessagesToPlainText).

    Full parity with the TypeScript renderer (tool blocks, rich content) can
    extend this function.
    """
    lines: list[str] = []
    for msg in messages:
        mtype = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", None)
        label = {None: "?", "user": "User", "assistant": "Assistant"}.get(
            mtype,
            str(mtype),
        )
        body = msg.get("message") if isinstance(msg, dict) else getattr(msg, "message", None)
        content: Any = None
        if isinstance(body, dict):
            content = body.get("content")
        elif body is not None and hasattr(body, "content"):
            content = getattr(body, "content", None)
        chunk = ""
        if isinstance(content, str):
            chunk = content
        elif isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and "text" in item:
                        parts.append(str(item["text"]))
                    else:
                        parts.append(str(item))
                else:
                    parts.append(str(item))
            chunk = "\n".join(parts)
        else:
            chunk = str(content) if content is not None else ""
        lines.append(f"--- {label} ---\n{chunk.strip()}\n")
    return "\n".join(lines).strip()


async def export_with_react_renderer(context: Any) -> str:
    tools: list[Any] = []
    opts = getattr(context, "options", None)
    if opts is not None:
        tools = list(getattr(opts, "tools", None) or [])
    messages = list(getattr(context, "messages", None) or [])
    return render_messages_to_plain_text(messages, tools)


async def call(
    args: str,
    *,
    context: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Export conversation to a file (with filename arg) or return dialog payload.

    Hosts that cannot render ``export_dialog`` should treat it as a stub and
    write ``content`` to a path of their choice.
    """
    _ = kwargs
    if context is None:
        return {
            "type": "text",
            "value": "Export requires a session context with messages.",
        }

    content = await export_with_react_renderer(context)
    filename = (args or "").strip()

    from claude_code.utils.cwd import get_cwd

    if filename:
        final_name = filename if filename.endswith(".txt") else re.sub(r"\.[^.]+$", "", filename) + ".txt"
        filepath = Path(get_cwd()) / final_name
        try:
            filepath.write_text(content, encoding="utf-8", newline="\n")
            return {
                "type": "text",
                "value": f"Conversation exported to: {filepath}",
            }
        except OSError as e:
            return {
                "type": "text",
                "value": f"Failed to export conversation: {e}",
            }

    first_prompt = extract_first_prompt(list(getattr(context, "messages", None) or []))
    timestamp = format_timestamp(datetime.now())
    if first_prompt:
        sanitized = sanitize_filename(first_prompt)
        default_filename = f"{timestamp}-{sanitized}.txt" if sanitized else f"conversation-{timestamp}.txt"
    else:
        default_filename = f"conversation-{timestamp}.txt"

    return {
        "type": "export_dialog",
        "content": content,
        "defaultFilename": default_filename,
    }


__all__ = [
    "call",
    "export_with_react_renderer",
    "extract_first_prompt",
    "format_timestamp",
    "render_messages_to_plain_text",
    "sanitize_filename",
]
