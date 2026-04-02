"""
Plugin dependency verification (demote / errors).

Migrated from: utils/plugins/dependencyResolver.ts (minimal port).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


async def verify_and_demote(
    plugins: list[Any],
) -> tuple[set[str], list[Any]]:
    """
    Verify plugin dependencies. Returns (demoted_sources, errors).

    Full TS implementation resolves manifest dependencies; this port is a
    no-op placeholder that preserves the public API.
    """
    return set(), []


__all__ = ["verify_and_demote"]
