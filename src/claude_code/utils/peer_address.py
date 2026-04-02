"""
Parse peer messaging addresses (UDS / bridge / legacy).

Migrated from: utils/peerAddress.ts
"""

from __future__ import annotations

from typing import Literal

Scheme = Literal["uds", "bridge", "other"]


def parse_address(to: str) -> dict[str, object]:
    """Split a URI-style or legacy path address into scheme and target."""

    if to.startswith("uds:"):
        return {"scheme": "uds", "target": to[4:]}
    if to.startswith("bridge:"):
        return {"scheme": "bridge", "target": to[7:]}
    if to.startswith("/"):
        return {"scheme": "uds", "target": to}
    return {"scheme": "other", "target": to}


__all__ = ["parse_address", "Scheme"]
