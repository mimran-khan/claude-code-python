"""
UUID utilities.

Provides functions for validating and generating UUIDs.

Migrated from: utils/uuid.ts (28 lines)
"""

from __future__ import annotations

import re
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types.ids import AgentId

# UUID format: 8-4-4-4-12 hex digits
UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_uuid(maybe_uuid: object) -> str | None:
    """
    Validate a UUID string.

    Args:
        maybe_uuid: The value to check if it is a valid UUID.

    Returns:
        The UUID string if valid, None otherwise.
    """
    if not isinstance(maybe_uuid, str):
        return None

    if UUID_REGEX.match(maybe_uuid):
        return maybe_uuid

    return None


def create_agent_id(label: str | None = None) -> AgentId:
    """
    Generate a new agent ID with prefix for consistency with task IDs.

    Format: a{label-}{16 hex chars}
    Example: aa3f2c1b4d5e6f7a8, acompact-a3f2c1b4d5e6f7a8

    Args:
        label: Optional label to include in the ID.

    Returns:
        A new agent ID.
    """
    from ..types.ids import AgentId as AgentIdType

    suffix = secrets.token_hex(8)
    if label:
        return AgentIdType(f"a{label}-{suffix}")
    return AgentIdType(f"a{suffix}")
