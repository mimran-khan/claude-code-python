"""
Load agent definitions from built-ins, plugins, and project markdown.

Migrated from: ``tools/AgentTool/loadAgentsDir.ts``
(behavioral subset; TS has full Zod + analytics).

Provides ``get_agent_definitions_with_overrides`` used by plugin refresh and app state merge.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TypedDict

import yaml

from ...utils.debug import log_for_debugging
from ...utils.env_utils import is_env_truthy
from ...utils.log import log_error
from ...utils.plugins.load_plugin_agents import clear_plugin_agent_cache, get_plugin_agents
from .builtin_agents import AgentDefinition, get_builtin_agents


class AgentDefinitionsResult(TypedDict, total=False):
    """Shape expected by ``refresh_active_plugins`` (``allAgents`` / ``activeAgents`` lists)."""

    activeAgents: list[dict[str, Any]]
    allAgents: list[dict[str, Any]]
    failedFiles: list[dict[str, str]]
    allowedAgentTypes: list[str]


def _serialize_builtin(agent: AgentDefinition) -> dict[str, Any]:
    return {
        "agentType": agent.agent_type,
        "whenToUse": agent.description,
        "source": "built-in",
        "baseDir": "built-in",
        "tools": list(agent.tools),
        "model": agent.model,
        "readonly": agent.readonly,
        "systemPrompt": agent.system_prompt,
        "name": agent.name,
    }


def get_active_agents_from_list(all_agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merge by ``agentType`` with source precedence matching TS ``getActiveAgentsFromList``.

    Order: built-in → plugin → userSettings → projectSettings → flagSettings → policySettings.
    """
    order = (
        "built-in",
        "builtin",
        "plugin",
        "userSettings",
        "projectSettings",
        "localSettings",
        "flagSettings",
        "policySettings",
    )
    buckets: dict[str, list[dict[str, Any]]] = {k: [] for k in order}
    for a in all_agents:
        src = str(a.get("source", "built-in"))
        if src == "builtin":
            src = "built-in"
        if src not in buckets:
            src = "built-in"
        buckets[src].append(a)

    agent_map: dict[str, dict[str, Any]] = {}
    for key in order:
        for ag in buckets.get(key, []):
            at = ag.get("agentType")
            if isinstance(at, str) and at:
                agent_map[at] = ag
    return list(agent_map.values())


def has_required_mcp_servers(agent: dict[str, Any], available_servers: list[str]) -> bool:
    req = agent.get("requiredMcpServers")
    if not req or not isinstance(req, list):
        return True
    lower = [s.lower() for s in available_servers]
    for pattern in req:
        if not isinstance(pattern, str):
            continue
        p = pattern.lower()
        if not any(p in s for s in lower):
            return False
    return True


def filter_agents_by_mcp_requirements(
    agents: list[dict[str, Any]],
    available_servers: list[str],
) -> list[dict[str, Any]]:
    return [a for a in agents if has_required_mcp_servers(a, available_servers)]


def clear_agent_definitions_cache() -> None:
    clear_plugin_agent_cache()


async def _load_markdown_agents(cwd: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    failed: list[dict[str, str]] = []
    agents: list[dict[str, Any]] = []
    root = Path(cwd)
    for sub in (root / ".claude" / "agents", root / "claude" / "agents"):
        if not sub.is_dir():
            continue
        for md in sorted(sub.glob("*.md")):
            try:
                raw = md.read_text(encoding="utf-8", errors="replace")
                if not raw.startswith("---"):
                    continue
                parts = raw.split("---", 2)
                if len(parts) < 3:
                    failed.append({"path": str(md), "error": "Invalid frontmatter fence"})
                    continue
                fm = yaml.safe_load(parts[1]) or {}
                body = parts[2].lstrip("\n")
                name = fm.get("name")
                desc = fm.get("description")
                if not isinstance(name, str) or not name.strip():
                    continue
                if not isinstance(desc, str):
                    failed.append(
                        {"path": str(md), "error": 'Missing "description" in frontmatter'},
                    )
                    continue
                src = "projectSettings" if ".claude" in str(sub) else "userSettings"
                tools = fm.get("tools")
                tools_list = list(tools) if isinstance(tools, list) else None
                agents.append(
                    {
                        "agentType": name.strip(),
                        "whenToUse": desc.replace("\\n", "\n"),
                        "source": src,
                        "baseDir": str(sub),
                        "filename": md.stem,
                        "systemPrompt": body,
                        "tools": tools_list,
                        "model": fm.get("model") if isinstance(fm.get("model"), str) else None,
                    },
                )
            except OSError as e:
                failed.append({"path": str(md), "error": str(e)})
            except Exception as e:
                failed.append({"path": str(md), "error": str(e)})
                log_for_debugging(f"load_agents_dir: parse failed {md}: {e}")
    return agents, failed


async def get_agent_definitions_with_overrides(cwd: str) -> AgentDefinitionsResult:
    if is_env_truthy(os.getenv("CLAUDE_CODE_SIMPLE", "")):
        builtins = [_serialize_builtin(a) for a in get_builtin_agents()]
        return {"activeAgents": builtins, "allAgents": builtins}

    failed_files: list[dict[str, str]] = []
    try:
        custom, failed = await _load_markdown_agents(cwd)
        failed_files.extend(failed)

        plugin_raw = await get_plugin_agents()
        plugin_agents: list[dict[str, Any]] = []
        for p in plugin_raw:
            if isinstance(p, dict) and p.get("plugin"):
                plugin_agents.append(
                    {
                        "agentType": f"plugin:{p.get('plugin')}",
                        "whenToUse": f"Plugin agent metadata for {p.get('plugin')}",
                        "source": "plugin",
                        "baseDir": "plugin",
                        "plugin": p.get("plugin"),
                        "path": p.get("path"),
                    },
                )

        built = [_serialize_builtin(a) for a in get_builtin_agents()]
        all_list = [*built, *plugin_agents, *custom]
        active = get_active_agents_from_list(all_list)
        out: AgentDefinitionsResult = {"activeAgents": active, "allAgents": all_list}
        if failed_files:
            out["failedFiles"] = failed_files
        return out
    except Exception as exc:
        msg = str(exc)
        log_for_debugging(f"Error loading agent definitions: {msg}")
        log_error(exc)
        built = [_serialize_builtin(a) for a in get_builtin_agents()]
        return {
            "activeAgents": built,
            "allAgents": built,
            "failedFiles": [{"path": "unknown", "error": msg}],
        }


__all__ = [
    "AgentDefinitionsResult",
    "clear_agent_definitions_cache",
    "filter_agents_by_mcp_requirements",
    "get_active_agents_from_list",
    "get_agent_definitions_with_overrides",
    "has_required_mcp_servers",
]
