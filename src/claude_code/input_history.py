"""
Input / paste history helpers for the REPL.

Migrated from: history.ts (core string helpers; file persistence omitted here).
"""

from __future__ import annotations

from .inbound_message_context import (
    format_image_ref,
    format_pasted_text_ref,
    get_pasted_text_ref_num_lines,
    parse_references,
)


def expand_pasted_text_refs(
    input_text: str,
    pasted_contents: dict[int, dict[str, str]],
) -> str:
    refs = parse_references(input_text)
    expanded = input_text
    for ref in reversed(refs):
        content = pasted_contents.get(ref["id"])
        if not content or content.get("type") != "text":
            continue
        body = content.get("content", "")
        expanded = expanded[: ref["index"]] + body + expanded[ref["index"] + len(ref["match"]) :]
    return expanded


__all__ = [
    "parse_references",
    "get_pasted_text_ref_num_lines",
    "format_pasted_text_ref",
    "format_image_ref",
    "expand_pasted_text_refs",
]
