"""
Platform detection utilities.

Functions for detecting the current platform and WSL.

Migrated from: utils/platform.ts (151 lines)
"""

from __future__ import annotations

import asyncio
import os
import platform as py_platform
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal

from .log import log_error

Platform = Literal["macos", "windows", "wsl", "linux", "unknown"]

SUPPORTED_PLATFORMS: list[Platform] = ["macos", "wsl"]

_VCS_MARKERS: list[tuple[str, str]] = [
    (".git", "git"),
    (".hg", "mercurial"),
    (".svn", "svn"),
    (".p4config", "perforce"),
    ("$tf", "tfs"),
    (".tfvc", "tfs"),
    (".jj", "jujutsu"),
    (".sl", "sapling"),
]


@dataclass(frozen=True)
class LinuxDistroInfo:
    """Linux distribution metadata (aligned with ``LinuxDistroInfo`` in ``utils/platform.ts``)."""

    linux_kernel: str
    linux_distro_id: str | None = None
    linux_distro_version: str | None = None


@cache
def get_platform() -> Platform:
    """
    Detect the current platform.

    Returns:
        Platform identifier: macos, windows, wsl, linux, or unknown
    """
    try:
        system = py_platform.system().lower()

        if system == "darwin":
            return "macos"

        if system == "windows":
            return "windows"

        if system == "linux":
            # Check for WSL
            try:
                with open("/proc/version") as f:
                    proc_version = f.read().lower()
                if "microsoft" in proc_version or "wsl" in proc_version:
                    return "wsl"
            except Exception:
                pass

            return "linux"

        return "unknown"
    except Exception as e:
        log_error(e)
        return "unknown"


@cache
def get_wsl_version() -> str | None:
    """
    Get the WSL version if running in WSL.

    Returns:
        WSL version string ("1" or "2"), or None if not WSL
    """
    if get_platform() != "wsl":
        return None

    try:
        with open("/proc/version") as f:
            proc_version = f.read()

        # Check for explicit WSL version markers
        match = re.search(r"WSL(\d+)", proc_version, re.IGNORECASE)
        if match:
            return match.group(1)

        # If Microsoft but no explicit version, assume WSL1
        if "microsoft" in proc_version.lower():
            return "1"

        return None
    except Exception as e:
        log_error(e)
        return None


def _read_linux_distro_info_sync() -> LinuxDistroInfo | None:
    if py_platform.system().lower() != "linux":
        return None
    kernel = py_platform.release()
    distro_id: str | None = None
    distro_version: str | None = None
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^(ID|VERSION_ID)=(.*)$", line.strip())
                if not m:
                    continue
                key, raw = m.group(1), m.group(2)
                value = raw.strip().strip('"').strip("'")
                if key == "ID":
                    distro_id = value
                else:
                    distro_version = value
    except OSError:
        pass
    return LinuxDistroInfo(
        linux_kernel=kernel,
        linux_distro_id=distro_id,
        linux_distro_version=distro_version,
    )


@cache
def get_linux_distro_info() -> dict[str, str] | None:
    """
    Legacy dict shape: ``kernel``, ``distro_id``, ``distro_version``.

    Prefer :func:`load_linux_distro_info` for TS-aligned :class:`LinuxDistroInfo`.
    """
    info = _read_linux_distro_info_sync()
    if info is None:
        return None
    out: dict[str, str] = {"kernel": info.linux_kernel}
    if info.linux_distro_id:
        out["distro_id"] = info.linux_distro_id
    if info.linux_distro_version:
        out["distro_version"] = info.linux_distro_version
    return out


async def load_linux_distro_info() -> LinuxDistroInfo | None:
    """Async loader matching ``getLinuxDistroInfo`` in ``utils/platform.ts``."""
    return await asyncio.to_thread(_read_linux_distro_info_sync)


async def detect_vcs(directory: str | None = None) -> list[str]:
    """
    Detect version-control markers in ``directory`` (cwd if omitted).
    Mirrors ``detectVcs`` in ``utils/platform.ts``.
    """
    detected: set[str] = set()
    if os.environ.get("P4PORT"):
        detected.add("perforce")
    root = Path(directory or os.getcwd())
    try:
        names = {p.name for p in root.iterdir() if p.is_dir() or p.is_file()}
    except OSError:
        return sorted(detected)
    for marker, vcs in _VCS_MARKERS:
        if marker in names:
            detected.add(vcs)
    return sorted(detected)


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform() == "macos"


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "windows"


def is_linux() -> bool:
    """Check if running on Linux (not WSL)."""
    return get_platform() == "linux"


def is_wsl() -> bool:
    """Check if running in WSL."""
    return get_platform() == "wsl"


def is_unix_like() -> bool:
    """Check if running on a Unix-like system (macOS, Linux, WSL)."""
    return get_platform() in ("macos", "linux", "wsl")


def get_architecture() -> str:
    """Get the system architecture."""
    machine = py_platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        return "x64"
    if machine in ("arm64", "aarch64"):
        return "arm64"
    if machine in ("i386", "i686"):
        return "x86"

    return machine


def get_python_version() -> str:
    """Get the Python version string."""
    return py_platform.python_version()


def get_os_version() -> str:
    """Get the OS version string."""
    return py_platform.platform()


def get_hostname() -> str:
    """Get the system hostname."""
    return py_platform.node()


def get_cpu_count() -> int:
    """Get the number of CPU cores."""
    return os.cpu_count() or 1


def get_home_directory() -> str:
    """Get the user's home directory."""
    return os.path.expanduser("~")


def get_temp_directory() -> str:
    """Get the system temp directory."""
    import tempfile

    return tempfile.gettempdir()
