"""
Bridge inbound user message helpers.

Migrated from: context.ts (root)
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID


def extract_inbound_message_fields(
    msg: dict[str, Any],
) -> tuple[str | list[dict[str, Any]], UUID | None] | None:
    if msg.get("type") != "user":
        return None
    content = (msg.get("message") or {}).get("content")
    if content is None:
        return None
    if isinstance(content, list) and len(content) == 0:
        return None
    uid = msg.get("uuid")
    uuid_val = UUID(uid) if isinstance(uid, str) else None
    if isinstance(content, list):
        return normalize_image_blocks(content), uuid_val
    return str(content), uuid_val


def normalize_image_blocks(
    blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not any(_is_malformed_base64_image(b) for b in blocks):
        return blocks
    out: list[dict[str, Any]] = []
    for block in blocks:
        if not _is_malformed_base64_image(block):
            out.append(block)
            continue
        src = block.get("source") or {}
        media = src.get("mediaType") or src.get("media_type")
        data = src.get("data", "")
        if not isinstance(data, str):
            out.append(block)
            continue
        if not isinstance(media, str) or not media:
            media = _detect_image_format_from_base64(data)
        out.append(
            {
                **block,
                "source": {"type": "base64", "media_type": media, "data": data},
            }
        )
    return out


def _is_malformed_base64_image(block: dict[str, Any]) -> bool:
    if block.get("type") != "image":
        return False
    src = block.get("source")
    if not isinstance(src, dict) or src.get("type") != "base64":
        return False
    return "media_type" not in src and "mediaType" not in src


def _detect_image_format_from_base64(data: str) -> str:
    raw = data.strip()
    if raw.startswith("iVBOR"):
        return "image/png"
    if raw.startswith("/9j/"):
        return "image/jpeg"
    if raw.startswith("R0lGOD"):
        return "image/gif"
    if raw.startswith("UklGR"):
        return "image/webp"
    return "image/png"


def parse_references(input_text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"\[(Pasted text|Image|\.\.\.Truncated text) #(\d+)(?: \+\d+ lines)?(\.)*\]")
    return [
        {"id": int(m.group(2)), "match": m.group(0), "index": m.start()}
        for m in pattern.finditer(input_text)
        if int(m.group(2)) > 0
    ]


def get_pasted_text_ref_num_lines(text: str) -> int:
    return len(re.findall(r"\r\n|\r|\n", text))


def format_pasted_text_ref(id_: int, num_lines: int) -> str:
    if num_lines == 0:
        return f"[Pasted text #{id_}]"
    return f"[Pasted text #{id_} +{num_lines} lines]"


def format_image_ref(id_: int) -> str:
    return f"[Image #{id_}]"
