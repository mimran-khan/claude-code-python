"""`claude agents` handler. Migrated from: cli/handlers/agents.ts."""

from __future__ import annotations

from ...tools.agent_tool import AgentDefinition, get_builtin_agents
from ...utils.cwd import get_cwd


def _format_agent(agent: AgentDefinition) -> str:
    desc = agent.description
    if len(desc) > 60:
        desc = desc[:60] + "…"
    parts = [agent.agent_type, desc]
    return " · ".join(parts)


async def agents_handler() -> None:
    cwd = get_cwd()
    _ = cwd  # parity with TS (directory-based overrides may use cwd later)
    agents = get_builtin_agents()
    lines = [f"  {_format_agent(a)}" for a in agents]
    if not lines:
        print("No agents found.")
        return
    print(f"{len(lines)} active agents\n")
    print("\n".join(lines))
