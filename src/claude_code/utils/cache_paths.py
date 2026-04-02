"""
Per-project cache directory layout under the app cache root.

Migrated from: utils/cachePaths.ts
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .hash import djb2_hash


def _cache_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "claude-cli"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local) / "claude-cli" / "Cache"
    xdg = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(xdg) / "claude-cli"


_MAX_SANITIZED_LENGTH = 200
_BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def _to_base36(n: int) -> str:
    if n == 0:
        return "0"
    digits: list[str] = []
    while n:
        n, r = divmod(n, 36)
        digits.append(_BASE36[r])
    return "".join(reversed(digits))


def _sanitize_path(name: str) -> str:
    sanitized = "".join(c if c.isalnum() else "-" for c in name)
    if len(sanitized) <= _MAX_SANITIZED_LENGTH:
        return sanitized
    suffix = abs(djb2_hash(name))
    return f"{sanitized[:_MAX_SANITIZED_LENGTH]}-{_to_base36(suffix)}"


def _project_dir(cwd: str) -> str:
    return _sanitize_path(cwd)


class CachePaths:
    """Namespace object mirroring TS ``CACHE_PATHS``."""

    @staticmethod
    def base_logs() -> str:
        cwd = os.getcwd()
        return str(_cache_root() / _project_dir(cwd))

    @staticmethod
    def errors() -> str:
        cwd = os.getcwd()
        return str(_cache_root() / _project_dir(cwd) / "errors")

    @staticmethod
    def messages() -> str:
        cwd = os.getcwd()
        return str(_cache_root() / _project_dir(cwd) / "messages")

    @staticmethod
    def mcp_logs(server_name: str) -> str:
        cwd = os.getcwd()
        safe_server = _sanitize_path(server_name)
        return str(_cache_root() / _project_dir(cwd) / f"mcp-logs-{safe_server}")


CACHE_PATHS = CachePaths

__all__ = ["CACHE_PATHS", "CachePaths"]
