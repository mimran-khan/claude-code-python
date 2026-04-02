"""Permission context handling."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass
class PermissionApprovalSource:
    """Source of permission approval."""

    type: Literal["hook", "user", "classifier"]
    permanent: bool = False


@dataclass
class PermissionRejectionSource:
    """Source of permission rejection."""

    type: Literal["hook", "user_abort", "user_reject"]
    has_feedback: bool = False


class PermissionQueueOps(Protocol):
    """Interface for permission queue operations."""

    def push(self, item: Any) -> None:
        """Add item to queue."""
        ...

    def remove(self, tool_use_id: str) -> None:
        """Remove item from queue."""
        ...

    def update(self, tool_use_id: str, patch: dict[str, Any]) -> None:
        """Update item in queue."""
        ...


@dataclass
class ResolveOnce:
    """Thread-safe resolution handler."""

    _resolve: Callable[[Any], None]
    _claimed: bool = False
    _delivered: bool = False

    def resolve(self, value: Any) -> None:
        """Resolve with value."""
        if self._delivered:
            return
        self._delivered = True
        self._claimed = True
        self._resolve(value)

    def is_resolved(self) -> bool:
        """Check if already resolved."""
        return self._claimed

    def claim(self) -> bool:
        """Atomically claim resolution rights."""
        if self._claimed:
            return False
        self._claimed = True
        return True


def create_resolve_once(resolve: Callable[[Any], None]) -> ResolveOnce:
    """Create a ResolveOnce handler."""
    return ResolveOnce(_resolve=resolve)


def create_permission_context(
    tool: Any,
    input_data: dict[str, Any],
    tool_use_context: Any,
    assistant_message: Any,
    tool_use_id: str,
    permission_queue_ops: PermissionQueueOps | None = None,
) -> dict[str, Any]:
    """Create permission context for a tool use.

    In full implementation, would set up the full permission checking context.
    """
    return {
        "tool": tool,
        "input": input_data,
        "context": tool_use_context,
        "message": assistant_message,
        "tool_use_id": tool_use_id,
    }


async def resolve_permission_decision(
    context: dict[str, Any],
    permission_context: Any,
) -> dict[str, Any]:
    """Resolve a permission decision.

    In full implementation, would:
    1. Check hook-based permissions
    2. Check classifier approvals
    3. Queue for user approval if needed
    """
    return {
        "behavior": "allow",
        "message": "Approved",
    }
