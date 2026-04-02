"""
Agent ID System.

Deterministic Agent ID formatting and parsing for the swarm/teammate system.

ID Formats:

Agent IDs: `agentName@teamName`
- Example: `team-lead@my-project`, `researcher@my-project`
- The @ symbol acts as a separator between agent name and team name

Request IDs: `{requestType}-{timestamp}@{agentId}`
- Example: `shutdown-1702500000000@researcher@my-project`
- Used for shutdown requests, plan approvals, etc.

Why Deterministic IDs?

1. Reproducibility: The same agent spawned with the same name in the same team
   always gets the same ID, enabling reconnection after crashes/restarts.

2. Human-readable: IDs are meaningful and debuggable (e.g., `tester@my-project`).

3. Predictable: Team leads can compute a teammate's ID without looking it up,
   simplifying message routing and task assignment.

Constraints:
- Agent names must NOT contain `@` (it's used as the separator)
"""

from __future__ import annotations

import time
from dataclasses import dataclass


def format_agent_id(agent_name: str, team_name: str) -> str:
    """Format an agent ID in the format `agentName@teamName`.

    Args:
        agent_name: The agent's name
        team_name: The team's name

    Returns:
        The formatted agent ID
    """
    return f"{agent_name}@{team_name}"


@dataclass
class ParsedAgentId:
    """Parsed agent ID components."""

    agent_name: str
    team_name: str


def parse_agent_id(agent_id: str) -> ParsedAgentId | None:
    """Parse an agent ID into its components.

    Args:
        agent_id: The agent ID to parse

    Returns:
        The parsed components, or None if invalid
    """
    at_index = agent_id.find("@")
    if at_index == -1:
        return None

    return ParsedAgentId(
        agent_name=agent_id[:at_index],
        team_name=agent_id[at_index + 1 :],
    )


def generate_request_id(request_type: str, agent_id: str) -> str:
    """Generate a request ID in the format `{requestType}-{timestamp}@{agentId}`.

    Args:
        request_type: The type of request (e.g., "shutdown", "plan_approval")
        agent_id: The agent ID

    Returns:
        The generated request ID
    """
    timestamp = int(time.time() * 1000)
    return f"{request_type}-{timestamp}@{agent_id}"


@dataclass
class ParsedRequestId:
    """Parsed request ID components."""

    request_type: str
    timestamp: int
    agent_id: str


def parse_request_id(request_id: str) -> ParsedRequestId | None:
    """Parse a request ID into its components.

    Args:
        request_id: The request ID to parse

    Returns:
        The parsed components, or None if invalid
    """
    at_index = request_id.find("@")
    if at_index == -1:
        return None

    prefix = request_id[:at_index]
    agent_id = request_id[at_index + 1 :]

    last_dash_index = prefix.rfind("-")
    if last_dash_index == -1:
        return None

    request_type = prefix[:last_dash_index]
    timestamp_str = prefix[last_dash_index + 1 :]

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return None

    return ParsedRequestId(
        request_type=request_type,
        timestamp=timestamp,
        agent_id=agent_id,
    )


def sanitize_agent_name(name: str) -> str:
    """Sanitize an agent name by removing @ characters.

    Args:
        name: The name to sanitize

    Returns:
        The sanitized name
    """
    return name.replace("@", "")
