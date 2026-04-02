"""
Remote permission bridge.

Migrated from: remote/remotePermissionBridge.ts
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .session import (
    RemotePermissionResponse,
    RemotePermissionResponseAllow,
    RemotePermissionResponseDeny,
)

logger = logging.getLogger(__name__)


@dataclass
class PendingPermission:
    """Pending permission request."""

    request_id: str
    tool_name: str
    tool_input: dict[str, Any]
    context: dict[str, Any]
    resolve: Callable[[RemotePermissionResponse], None]


@dataclass
class RemotePermissionBridge:
    """Bridges permission requests between remote session and local handler.

    When a remote session needs permission for a tool use,
    this bridge handles the request/response flow.
    """

    _pending: dict[str, PendingPermission] = field(default_factory=dict)
    _permission_handler: Callable[[PendingPermission], asyncio.Future] | None = None

    def set_handler(
        self,
        handler: Callable[[PendingPermission], asyncio.Future],
    ) -> None:
        """Set the permission handler."""
        self._permission_handler = handler

    async def handle_permission_request(
        self,
        request_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> RemotePermissionResponse:
        """Handle incoming permission request.

        Creates a pending permission and waits for resolution.
        """
        future: asyncio.Future[RemotePermissionResponse] = asyncio.Future()

        def resolve(response: RemotePermissionResponse) -> None:
            if not future.done():
                future.set_result(response)

        pending = PendingPermission(
            request_id=request_id,
            tool_name=tool_name,
            tool_input=tool_input,
            context=context or {},
            resolve=resolve,
        )

        self._pending[request_id] = pending

        try:
            if self._permission_handler:
                await self._permission_handler(pending)

            # Wait for resolution
            return await future
        finally:
            self._pending.pop(request_id, None)

    def approve(
        self,
        request_id: str,
        updated_input: dict[str, Any] | None = None,
    ) -> bool:
        """Approve a pending permission request."""
        pending = self._pending.get(request_id)
        if not pending:
            logger.warning(f"No pending permission for {request_id}")
            return False

        pending.resolve(
            RemotePermissionResponseAllow(
                updated_input=updated_input or pending.tool_input,
            )
        )
        return True

    def deny(
        self,
        request_id: str,
        message: str = "Permission denied",
    ) -> bool:
        """Deny a pending permission request."""
        pending = self._pending.get(request_id)
        if not pending:
            logger.warning(f"No pending permission for {request_id}")
            return False

        pending.resolve(RemotePermissionResponseDeny(message=message))
        return True

    def cancel(self, request_id: str) -> bool:
        """Cancel a pending permission request."""
        pending = self._pending.pop(request_id, None)
        if pending:
            pending.resolve(RemotePermissionResponseDeny(message="Request cancelled"))
            return True
        return False

    def get_pending(self, request_id: str) -> PendingPermission | None:
        """Get a pending permission by ID."""
        return self._pending.get(request_id)

    def get_all_pending(self) -> dict[str, PendingPermission]:
        """Get all pending permissions."""
        return dict(self._pending)

    def clear_all(self) -> None:
        """Clear all pending permissions."""
        for pending in list(self._pending.values()):
            pending.resolve(RemotePermissionResponseDeny(message="Session ended"))
        self._pending.clear()
