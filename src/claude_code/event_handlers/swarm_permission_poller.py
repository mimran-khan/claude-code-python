"""
Swarm worker permission response registry + mailbox dispatch.

Migrated from: hooks/useSwarmPermissionPoller.ts
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

POLL_INTERVAL_S = 0.5


@dataclass
class PermissionResponseCallback:
    request_id: str
    tool_use_id: str
    on_allow: Callable[..., None]
    on_reject: Callable[..., None]


@dataclass
class SandboxPermissionResponseCallback:
    request_id: str
    host: str
    resolve: Callable[[bool], None]


_pending: dict[str, PermissionResponseCallback] = {}
_pending_sandbox: dict[str, SandboxPermissionResponseCallback] = {}


def register_permission_callback(cb: PermissionResponseCallback) -> None:
    _pending[cb.request_id] = cb


def unregister_permission_callback(request_id: str) -> None:
    _pending.pop(request_id, None)


def has_permission_callback(request_id: str) -> bool:
    return request_id in _pending


def clear_all_pending_callbacks() -> None:
    _pending.clear()
    _pending_sandbox.clear()


def parse_permission_updates(
    raw: object,
    *,
    warn: Callable[[str], None] | None = None,
) -> list[Mapping[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[Mapping[str, Any]] = []
    for entry in raw:
        if isinstance(entry, Mapping):
            out.append(entry)
        elif warn is not None:
            warn("malformed permissionUpdate entry dropped")
    return out


def process_mailbox_permission_response(
    *,
    request_id: str,
    decision: str,
    feedback: str | None = None,
    updated_input: Mapping[str, Any] | None = None,
    permission_updates: object = None,
) -> bool:
    cb = _pending.get(request_id)
    if cb is None:
        return False
    del _pending[request_id]
    if decision == "approved":
        cb.on_allow(updated_input or {}, parse_permission_updates(permission_updates))
    else:
        cb.on_reject(feedback)
    return True


def register_sandbox_permission_callback(cb: SandboxPermissionResponseCallback) -> None:
    _pending_sandbox[cb.request_id] = cb


def has_sandbox_permission_callback(request_id: str) -> bool:
    return request_id in _pending_sandbox


def process_sandbox_permission_response(*, request_id: str, host: str, allow: bool) -> bool:
    cb = _pending_sandbox.get(request_id)
    if cb is None:
        return False
    del _pending_sandbox[request_id]
    cb.resolve(allow)
    _ = host
    return True
