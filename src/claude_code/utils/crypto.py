"""
``randomUUID`` parity for ``utils/crypto.ts`` (Node re-export).

Implementation: :func:`claude_code.utils.crypto_shim.random_uuid`.
"""

from __future__ import annotations

from claude_code.utils.crypto_shim import random_uuid

randomUUID = random_uuid

__all__ = ["randomUUID", "random_uuid"]
