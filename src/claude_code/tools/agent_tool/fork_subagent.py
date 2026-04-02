"""
Implicit fork subagent experiment (inherits parent context).

Migrated from: tools/AgentTool/forkSubagent.ts (simplified feature gates).
"""

from __future__ import annotations

import os
from typing import Any, Literal, TypedDict

FORK_SUBAGENT_TYPE = "fork"
FORK_BOILERPLATE_TAG = "fork-boilerplate"
FORK_DIRECTIVE_PREFIX = "/fork "


def is_fork_subagent_enabled() -> bool:
    if os.environ.get("FORK_SUBAGENT", "").lower() not in ("1", "true", "yes"):
        return False
    return os.environ.get("NON_INTERACTIVE", "").lower() not in ("1", "true", "yes")


class _ForkAgentDict(TypedDict, total=False):
    agentType: str
    whenToUse: str
    tools: list[str]
    maxTurns: int
    model: str
    permissionMode: str
    source: Literal["built-in"]
    baseDir: Literal["built-in"]


FORK_AGENT: _ForkAgentDict = {
    "agentType": FORK_SUBAGENT_TYPE,
    "whenToUse": (
        "Implicit fork — inherits full conversation context. "
        "Not selectable via subagent_type; triggered when fork experiment is active."
    ),
    "tools": ["*"],
    "maxTurns": 200,
    "model": "inherit",
    "permissionMode": "bubble",
    "source": "built-in",
    "baseDir": "built-in",
}


def is_in_fork_child(messages: list[dict[str, Any]]) -> bool:
    for m in messages:
        if m.get("type") != "user":
            continue
        content = m.get("content")
        if isinstance(content, str) and FORK_BOILERPLATE_TAG in content:
            return True
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    t = block.get("text") or block.get("content")
                    if isinstance(t, str) and FORK_BOILERPLATE_TAG in t:
                        return True
    return False


def fork_directive_body(message: str) -> str | None:
    raw = message.strip()
    prefix = FORK_DIRECTIVE_PREFIX.strip()
    if not raw.lower().startswith(prefix.lower()):
        return None
    rest = raw[len(prefix) :].strip()
    return rest or None


__all__ = [
    "FORK_AGENT",
    "FORK_BOILERPLATE_TAG",
    "FORK_DIRECTIVE_PREFIX",
    "FORK_SUBAGENT_TYPE",
    "fork_directive_body",
    "is_fork_subagent_enabled",
    "is_in_fork_child",
]
