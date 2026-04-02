"""
Session-scoped environment variables (e.g. set via /env).

Applied to spawned child processes, not the host REPL process.

Migrated from: utils/sessionEnvVars.ts
"""

from __future__ import annotations

from collections.abc import Mapping

_session_env_vars: dict[str, str] = {}


def get_session_env_vars() -> Mapping[str, str]:
    """Return a read-only view of session env overrides."""
    return _session_env_vars


def set_session_env_var(name: str, value: str) -> None:
    _session_env_vars[name] = value


def delete_session_env_var(name: str) -> None:
    _session_env_vars.pop(name, None)


def clear_session_env_vars() -> None:
    _session_env_vars.clear()
