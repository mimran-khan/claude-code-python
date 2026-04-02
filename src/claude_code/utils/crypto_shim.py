"""
Random UUID helper (Node ``crypto.randomUUID`` analogue).

Migrated from: utils/crypto.ts (re-export of ``crypto.randomUUID`` in Node builds).
"""

from __future__ import annotations

from uuid import uuid4


def random_uuid() -> str:
    """Return a new RFC 4122 UUID string."""

    return str(uuid4())


__all__ = ["random_uuid"]
