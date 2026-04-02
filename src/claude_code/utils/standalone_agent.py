"""
Standalone agent name helper (non-swarm sessions).

Migrated from: utils/standaloneAgent.ts
"""

from __future__ import annotations

from typing import Any

from .teammate import get_team_name


def get_standalone_agent_name(app_state: Any) -> str | None:
    """
    Return ``app_state.standalone_agent_context.name`` when not in a swarm team.

    ``app_state`` is typically bootstrap state or a dict-like session object.
    """
    if get_team_name():
        return None
    ctx = getattr(app_state, "standalone_agent_context", None)
    if ctx is None and isinstance(app_state, dict):
        ctx = app_state.get("standaloneAgentContext") or app_state.get("standalone_agent_context")
    if ctx is None:
        return None
    name = getattr(ctx, "name", None)
    if name is None and isinstance(ctx, dict):
        name = ctx.get("name")
    return str(name) if name else None
