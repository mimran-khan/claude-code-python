"""
Permission mode utilities.

Defines permission modes and their configurations.

Migrated from: utils/permissions/PermissionMode.ts (142 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Permission mode types
ExternalPermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

PermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",
    "bubble",
]

# Constants
EXTERNAL_PERMISSION_MODES: list[ExternalPermissionMode] = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

PERMISSION_MODES: list[PermissionMode] = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",
]

# Icons
PAUSE_ICON = "⏸"


@dataclass
class PermissionModeConfig:
    """Configuration for a permission mode."""

    title: str
    short_title: str
    symbol: str
    color: str
    external: ExternalPermissionMode


PERMISSION_MODE_CONFIG: dict[PermissionMode, PermissionModeConfig] = {
    "default": PermissionModeConfig(
        title="Default",
        short_title="Default",
        symbol="",
        color="text",
        external="default",
    ),
    "plan": PermissionModeConfig(
        title="Plan Mode",
        short_title="Plan",
        symbol=PAUSE_ICON,
        color="planMode",
        external="plan",
    ),
    "acceptEdits": PermissionModeConfig(
        title="Accept edits",
        short_title="Accept",
        symbol="⏵⏵",
        color="autoAccept",
        external="acceptEdits",
    ),
    "bypassPermissions": PermissionModeConfig(
        title="Bypass Permissions",
        short_title="Bypass",
        symbol="⏵⏵",
        color="error",
        external="bypassPermissions",
    ),
    "dontAsk": PermissionModeConfig(
        title="Don't Ask",
        short_title="DontAsk",
        symbol="⏵⏵",
        color="error",
        external="dontAsk",
    ),
    "auto": PermissionModeConfig(
        title="Auto mode",
        short_title="Auto",
        symbol="⏵⏵",
        color="warning",
        external="default",
    ),
}


def is_external_permission_mode(mode: PermissionMode) -> bool:
    """Check if a PermissionMode is an ExternalPermissionMode."""
    return mode in EXTERNAL_PERMISSION_MODES


def permission_mode_title(mode: PermissionMode) -> str:
    """Get the title for a permission mode."""
    config = PERMISSION_MODE_CONFIG.get(mode)
    return config.title if config else mode


def permission_mode_short_title(mode: PermissionMode) -> str:
    """Get the short title for a permission mode."""
    config = PERMISSION_MODE_CONFIG.get(mode)
    return config.short_title if config else mode


def permission_mode_symbol(mode: PermissionMode) -> str:
    """Get the symbol for a permission mode."""
    config = PERMISSION_MODE_CONFIG.get(mode)
    return config.symbol if config else ""


def permission_mode_color(mode: PermissionMode) -> str:
    """Get the color key for a permission mode."""
    config = PERMISSION_MODE_CONFIG.get(mode)
    return config.color if config else "text"


def get_external_mode(mode: PermissionMode) -> ExternalPermissionMode:
    """Get the external permission mode for an internal mode."""
    config = PERMISSION_MODE_CONFIG.get(mode)
    return config.external if config else "default"


def validate_permission_mode(mode: str) -> PermissionMode | None:
    """Validate and return a permission mode string."""
    if mode in PERMISSION_MODES:
        return mode  # type: ignore
    return None


def validate_external_permission_mode(mode: str) -> ExternalPermissionMode | None:
    """Validate and return an external permission mode string."""
    if mode in EXTERNAL_PERMISSION_MODES:
        return mode  # type: ignore
    return None
