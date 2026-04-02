"""
NDJSON-safe JSON serialization.

Migrated from: cli/ndjsonSafeStringify.ts
Escapes U+2028 / U+2029 so line-based NDJSON parsers never split inside a string.
"""

from __future__ import annotations

import json
from typing import Any


def _escape_js_line_terminators(serialized: str) -> str:
    out = serialized
    out = out.replace("\u2028", "\\u2028")
    out = out.replace("\u2029", "\\u2029")
    return out


def ndjson_safe_stringify(value: Any) -> str:
    """JSON-serialize *value* for one-message-per-line transports."""
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return _escape_js_line_terminators(raw)
