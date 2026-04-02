"""
Leaf UTF-8 BOM stripping for JSON/text reads.

Migrated from: utils/jsonRead.ts
"""

from __future__ import annotations

_UTF8_BOM = "\ufeff"


def strip_bom(content: str) -> str:
    """Strip a leading UTF-8 BOM if present."""

    return content[1:] if content.startswith(_UTF8_BOM) else content


__all__ = ["strip_bom"]
