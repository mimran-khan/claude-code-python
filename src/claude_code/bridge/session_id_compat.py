"""Session ID tag translation for CCR v2 compat (ported from bridge/sessionIdCompat.ts)."""

from __future__ import annotations

from collections.abc import Callable

_is_cse_shim_enabled: Callable[[], bool] | None = None


def set_cse_shim_gate(gate: Callable[[], bool]) -> None:
    global _is_cse_shim_enabled
    _is_cse_shim_enabled = gate


def to_compat_session_id(id: str) -> str:
    if not id.startswith("cse_"):
        return id
    if _is_cse_shim_enabled is not None and not _is_cse_shim_enabled():
        return id
    return "session_" + id[len("cse_") :]


def to_infra_session_id(id: str) -> str:
    if not id.startswith("session_"):
        return id
    return "cse_" + id[len("session_") :]
