"""
Branded types for session and agent IDs.

These types use NewType to create distinct types that prevent accidentally
mixing up session IDs and agent IDs at type-check time.

Migrated from: types/ids.ts (45 lines)
"""

from __future__ import annotations

import re
from typing import NewType

# Branded type for session IDs.
# A session ID uniquely identifies a Claude Code session.
SessionId = NewType("SessionId", str)

# Branded type for agent IDs.
# An agent ID uniquely identifies a subagent within a session.
# When present, indicates the context is a subagent (not the main session).
AgentId = NewType("AgentId", str)

# Pattern for validating agent IDs.
# Matches format: `a` + optional `<label>-` + 16 hex chars
# Examples: "a1234567890abcdef", "atask-1234567890abcdef"
_AGENT_ID_PATTERN = re.compile(r"^a(?:.+-)?[0-9a-f]{16}$")


def as_session_id(id_str: str) -> SessionId:
    """
    Cast a raw string to SessionId.

    Use sparingly - prefer get_session_id() when possible.

    Args:
        id_str: The raw string to cast.

    Returns:
        The string branded as a SessionId.
    """
    return SessionId(id_str)


def as_agent_id(id_str: str) -> AgentId:
    """
    Cast a raw string to AgentId.

    Use sparingly - prefer create_agent_id() when possible.

    Args:
        id_str: The raw string to cast.

    Returns:
        The string branded as an AgentId.
    """
    return AgentId(id_str)


def to_agent_id(s: str) -> AgentId | None:
    """
    Validate and brand a string as AgentId.

    Matches the format produced by create_agent_id():
    `a` + optional `<label>-` + 16 hex chars.

    Args:
        s: The string to validate and convert.

    Returns:
        The string as AgentId if valid, None otherwise.
        Returns None for teammate names, team-addressing, etc.
    """
    if _AGENT_ID_PATTERN.match(s):
        return AgentId(s)
    return None
