"""
Server types.

Migrated from: server/types.ts
"""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ServerMessage:
    """Base server message."""

    type: str
    payload: dict[str, Any] | None = None


@dataclass
class StdoutMessage:
    """Message sent to stdout."""

    type: str
    content: str | None = None
    data: dict[str, Any] | None = None


@dataclass
class ServerEvent:
    """Server event."""

    event_type: str
    timestamp: float
    data: dict[str, Any] | None = None


@dataclass
class ControlRequest:
    """Control request from SDK."""

    type: Literal["control_request"] = "control_request"
    request_id: str = ""
    action: str = ""
    payload: dict[str, Any] | None = None


@dataclass
class ControlResponse:
    """Control response to SDK."""

    type: Literal["control_response"] = "control_response"
    request_id: str = ""
    success: bool = True
    error: str | None = None
    payload: dict[str, Any] | None = None


@dataclass
class PermissionRequest:
    """Permission request."""

    type: Literal["permission_request"] = "permission_request"
    request_id: str = ""
    tool_name: str = ""
    tool_input: dict[str, Any] | None = None
    context: dict[str, Any] | None = None


def is_stdout_message(value: Any) -> bool:
    """Check if value is a StdoutMessage."""
    return isinstance(value, dict) and "type" in value and isinstance(value.get("type"), str)


def is_control_request(value: Any) -> bool:
    """Check if value is a control request."""
    return isinstance(value, dict) and value.get("type") == "control_request"


def is_sdk_message(value: Any) -> bool:
    """Check if value is an SDK message (not control)."""
    if not isinstance(value, dict):
        return False
    msg_type = value.get("type")
    return msg_type not in ("control_request", "control_response", "control_cancel_request")
