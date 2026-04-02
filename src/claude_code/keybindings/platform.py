"""
Runtime platform detection for keybinding defaults and display.

Migrated from: utils/platform.js (subset used by keybindings).
"""

from __future__ import annotations

import sys
from typing import Literal

from .types import DisplayPlatform

PlatformName = Literal["macos", "windows", "linux", "wsl", "unknown"]


def get_platform() -> PlatformName:
    """Return coarse OS family for keybinding behavior."""
    plat = sys.platform
    if plat == "darwin":
        return "macos"
    if plat == "win32":
        return "windows"
    return "linux"


def to_display_platform(
    platform: PlatformName | DisplayPlatform | None = None,
) -> DisplayPlatform:
    """Map platform to display tier (WSL/unknown fold to linux)."""
    p: str = platform or get_platform()
    if p in ("wsl", "unknown"):
        return "linux"
    return p  # type: ignore[return-value]


def supports_terminal_vt_mode() -> bool:
    """
    Whether shift+tab style chords are expected to work in the terminal.

    TypeScript gates Windows on Node/Bun semver; Python uses a conservative default.
    """
    if get_platform() != "windows":
        return True
    # Python 3.12+ on Windows generally improves console handling; align loosely with TS intent.
    return sys.version_info >= (3, 12)
