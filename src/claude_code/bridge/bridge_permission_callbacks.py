"""Bridge permission callback types (ported from bridge/bridgePermissionCallbacks.ts)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol, TypedDict


class BridgePermissionResponse(TypedDict, total=False):
    behavior: Literal["allow", "deny"]
    updated_input: dict[str, Any]
    updated_permissions: list[Any]  # TODO: PermissionUpdate from permissions schema
    message: str


class BridgePermissionCallbacks(Protocol):
    def send_request(
        self,
        request_id: str,
        tool_name: str,
        input: dict[str, Any],
        tool_use_id: str,
        description: str,
        permission_suggestions: list[Any] | None = None,
        blocked_path: str | None = None,
    ) -> None: ...

    def send_response(self, request_id: str, response: BridgePermissionResponse) -> None: ...

    def cancel_request(self, request_id: str) -> None: ...

    def on_response(
        self,
        request_id: str,
        handler: Callable[[BridgePermissionResponse], None],
    ) -> Callable[[], None]: ...


def is_bridge_permission_response(value: object) -> bool:
    if not value or not isinstance(value, dict):
        return False
    b = value.get("behavior")
    return b in ("allow", "deny")
