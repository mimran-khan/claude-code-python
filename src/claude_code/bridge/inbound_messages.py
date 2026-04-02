"""Inbound user message normalization (ported from bridge/inboundMessages.ts)."""

from __future__ import annotations

import copy
from typing import Any, TypedDict


class InboundMessageFields(TypedDict, total=False):
    content: str | list[dict[str, Any]]
    uuid: str | None


def extract_inbound_message_fields(msg: dict[str, Any]) -> InboundMessageFields | None:
    if msg.get("type") != "user":
        return None
    inner = msg.get("message")
    if not isinstance(inner, dict):
        return None
    content = inner.get("content")
    if content is None:
        return None
    if isinstance(content, list) and len(content) == 0:
        return None
    uuid = msg.get("uuid") if isinstance(msg.get("uuid"), str) else None
    norm = normalize_image_blocks(content) if isinstance(content, list) else content
    return {"content": norm, "uuid": uuid}


def _is_malformed_base64_image(block: dict[str, Any]) -> bool:
    if block.get("type") != "image":
        return False
    src = block.get("source")
    if not isinstance(src, dict) or src.get("type") != "base64":
        return False
    return not src.get("media_type")


def normalize_image_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not any(_is_malformed_base64_image(b) for b in blocks if isinstance(b, dict)):
        return blocks
    out: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict) or not _is_malformed_base64_image(block):
            out.append(block)
            continue
        b = copy.deepcopy(block)
        src = b.get("source")
        assert isinstance(src, dict)
        media = src.get("mediaType") or src.get("media_type")
        mt = media if isinstance(media, str) and media else "image/png"
        b["source"] = {"type": "base64", "media_type": mt, "data": src.get("data")}
        out.append(b)
    return out
