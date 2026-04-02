"""
Base64 helpers (no TS counterpart in this tree; common utilities).

Safe encode/decode for text and bytes with explicit UTF-8 handling.
"""

from __future__ import annotations

import base64


def b64_encode_utf8(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def b64_decode_utf8(data: str) -> str:
    return base64.b64decode(data, validate=False).decode("utf-8", errors="replace")


def b64_encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64_decode_to_bytes(data: str) -> bytes:
    return base64.b64decode(data, validate=False)
