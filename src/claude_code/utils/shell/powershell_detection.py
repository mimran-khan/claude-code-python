"""
Locate PowerShell executables on the system.

Migrated from: utils/shell/powershellDetection.ts

Uses :func:`shutil.which` for PATH resolution and filesystem probes for Linux snap workarounds.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from claude_code.utils.platform import get_platform

_cached_powershell_path: str | None | object = object()


def _probe_file(p: Path) -> str | None:
    try:
        return str(p) if p.is_file() else None
    except OSError:
        return None


def _find_powershell_impl() -> str | None:
    """
    Find PowerShell via PATH.

    Prefers ``pwsh`` (PowerShell 7+), falls back to ``powershell`` (5.1).

    On Linux, if PATH resolves to a snap launcher, prefer direct binaries under
    ``/opt/microsoft/powershell/7/pwsh`` when present.
    """
    pwsh_path = shutil.which("pwsh")
    if pwsh_path:
        if get_platform() == "linux":
            try:
                resolved = str(Path(pwsh_path).resolve())
            except OSError:
                resolved = pwsh_path
            if pwsh_path.startswith("/snap/") or resolved.startswith("/snap/"):
                direct = _probe_file(Path("/opt/microsoft/powershell/7/pwsh")) or _probe_file(Path("/usr/bin/pwsh"))
                if direct:
                    try:
                        dres = str(Path(direct).resolve())
                    except OSError:
                        dres = direct
                    if not direct.startswith("/snap/") and not dres.startswith("/snap/"):
                        return direct
        return pwsh_path

    return shutil.which("powershell")


async def find_powershell() -> str | None:
    """Async wrapper (no blocking I/O beyond PATH/stat; kept for API parity)."""
    return _find_powershell_impl()


def get_cached_powershell_path_sync() -> str | None:
    """Memoized path lookup."""
    global _cached_powershell_path
    if _cached_powershell_path is object():
        _cached_powershell_path = _find_powershell_impl()
    return _cached_powershell_path  # type: ignore[return-value]


async def get_cached_powershell_path() -> str | None:
    """Memoized path lookup (async API matching TS)."""
    return get_cached_powershell_path_sync()


PowerShellEdition = Literal["core", "desktop"]


def get_powershell_edition() -> PowerShellEdition | None:
    """
    Infer edition from the binary basename (no subprocess).

    ``pwsh`` → ``core`` (7+ semantics). ``powershell`` → ``desktop`` (5.1).
    """
    p = get_cached_powershell_path_sync()
    if not p:
        return None
    base = Path(p).name.lower().removesuffix(".exe")
    return "core" if base == "pwsh" else "desktop"


def reset_powershell_cache() -> None:
    """Reset cached path (tests only)."""
    global _cached_powershell_path
    _cached_powershell_path = object()


__all__ = [
    "PowerShellEdition",
    "find_powershell",
    "get_cached_powershell_path",
    "get_cached_powershell_path_sync",
    "get_powershell_edition",
    "reset_powershell_cache",
]
