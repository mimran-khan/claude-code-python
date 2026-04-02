"""
Message fingerprinting for attribution (migrated from ``utils/fingerprint.ts``).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

FINGERPRINT_SALT = "59cf53e54c78"


def extract_first_message_text(messages: Sequence[dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("type") != "user":
            continue
        inner = msg.get("message") or {}
        content = inner.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text")
                    if isinstance(t, str):
                        return t
        return ""
    return ""


def compute_fingerprint(message_text: str, version: str) -> str:
    indices = (4, 7, 20)
    chars = "".join(message_text[i] if i < len(message_text) else "0" for i in indices)
    payload = f"{FINGERPRINT_SALT}{chars}{version}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:3]


def compute_fingerprint_from_messages(messages: Sequence[dict[str, Any]]) -> str:
    from claude_code import __version__

    return compute_fingerprint(extract_first_message_text(messages), __version__)


__all__ = [
    "FINGERPRINT_SALT",
    "compute_fingerprint",
    "compute_fingerprint_from_messages",
    "extract_first_message_text",
]
