"""
One-shot swarm / teammate context + hooks initialization.

Migrated from: hooks/useSwarmInitialization.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol


class SwarmInitContext(Protocol):
    """Inject Python equivalents of teammate reconnection helpers."""

    def is_agent_swarms_enabled(self) -> bool: ...

    def get_session_id(self) -> str: ...

    def initialize_teammate_context_from_session(
        self,
        set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
        team_name: str,
        agent_name: str,
    ) -> None: ...

    def read_team_file(self, team_name: str) -> Any | None: ...

    def initialize_teammate_hooks(
        self,
        set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
        session_id: str,
        ctx: dict[str, str],
    ) -> None: ...

    def get_dynamic_team_context(self) -> dict[str, str] | None: ...


def _message_team_fields(first: Any) -> tuple[str | None, str | None]:
    """Read teamName/agentName from object or mapping (TS resume transcript)."""
    if first is None:
        return None, None
    if isinstance(first, Mapping):
        tn = first.get("teamName")
        an = first.get("agentName")
        if not isinstance(tn, str):
            tn = first.get("team_name")
        if not isinstance(an, str):
            an = first.get("agent_name")
        return (tn if isinstance(tn, str) else None, an if isinstance(an, str) else None)
    tn = getattr(first, "team_name", None) or getattr(first, "teamName", None)
    an = getattr(first, "agent_name", None) or getattr(first, "agentName", None)
    tn_s = tn if isinstance(tn, str) else None
    an_s = an if isinstance(an, str) else None
    return tn_s, an_s


def run_swarm_initialization(
    ctx: SwarmInitContext,
    set_app_state: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], None],
    initial_messages: list[Any] | None,
    *,
    enabled: bool = True,
) -> None:
    if not enabled or not ctx.is_agent_swarms_enabled():
        return

    first = initial_messages[0] if initial_messages else None
    team_name, agent_name = _message_team_fields(first)

    if team_name and agent_name:
        ctx.initialize_teammate_context_from_session(set_app_state, team_name, agent_name)
        team_file = ctx.read_team_file(team_name)
        member = None
        if team_file is not None:
            if isinstance(team_file, Mapping):
                raw = team_file.get("members")
                members = raw if isinstance(raw, list) else []
            else:
                members = getattr(team_file, "members", None) or []
            for m in members:
                m_name = m.get("name") if isinstance(m, Mapping) else getattr(m, "name", None)
                if m_name == agent_name:
                    member = m
                    break
        if member is not None:
            aid = member.get("agentId") if isinstance(member, Mapping) else getattr(member, "agent_id", None)
            if aid is None and isinstance(member, Mapping):
                aid = member.get("agent_id")
            agent_id = str(aid) if aid is not None else ""
            ctx.initialize_teammate_hooks(
                set_app_state,
                ctx.get_session_id(),
                {"teamName": team_name, "agentId": agent_id, "agentName": agent_name},
            )
        return

    dyn = ctx.get_dynamic_team_context()
    if dyn and dyn.get("teamName") and dyn.get("agentId") and dyn.get("agentName"):
        ctx.initialize_teammate_hooks(
            set_app_state,
            ctx.get_session_id(),
            {
                "teamName": dyn["teamName"],
                "agentId": dyn["agentId"],
                "agentName": dyn["agentName"],
            },
        )
