"""
Registry of supported configuration keys (subset of TypeScript SUPPORTED_SETTINGS).

Migrated from: tools/ConfigTool/supportedSettings.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

SettingSource = Literal["global", "settings"]


@dataclass(frozen=True)
class SettingConfig:
    source: SettingSource
    type: Literal["boolean", "string", "number"]
    description: str
    path: tuple[str, ...] = ()
    options: tuple[str, ...] | None = None
    app_state_key: str | None = None
    validate_on_write: Callable[[Any], Any] | None = None  # async in full port
    format_on_read: Callable[[Any], Any] | None = None


# Static subset mirroring common TS entries; extend as Python config layer grows.
SUPPORTED_SETTINGS: dict[str, SettingConfig] = {
    "theme": SettingConfig(
        source="global",
        type="string",
        description="Color theme for the UI",
        options=("light", "dark", "system"),
    ),
    "verbose": SettingConfig(
        source="global",
        type="boolean",
        description="Show detailed debug output",
        app_state_key="verbose",
    ),
    "model": SettingConfig(
        source="settings",
        type="string",
        description="Override the default model",
        app_state_key="mainLoopModel",
    ),
    "permissions.defaultMode": SettingConfig(
        source="settings",
        type="string",
        description="Default permission mode for tool usage",
        options=("default", "plan", "acceptEdits", "dontAsk", "auto"),
    ),
    "outputStyle": SettingConfig(
        source="settings",
        type="string",
        description="Output style",
        options=("default", "Explanatory", "Learning"),
    ),
    "editorMode": SettingConfig(
        source="global",
        type="string",
        description="Key binding mode",
        options=("default", "vim", "emacs"),
    ),
    "remoteControlAtStartup": SettingConfig(
        source="global",
        type="boolean",
        description="Enable REPL / remote control bridge at startup",
    ),
}


def is_supported(setting: str) -> bool:
    return setting in SUPPORTED_SETTINGS


def get_config(setting: str) -> SettingConfig | None:
    return SUPPORTED_SETTINGS.get(setting)


def get_path(setting: str) -> tuple[str, ...]:
    cfg = SUPPORTED_SETTINGS.get(setting)
    if not cfg:
        return ()
    if cfg.path:
        return cfg.path
    return (setting,)


def get_options_for_setting(setting: str) -> list[str] | None:
    cfg = SUPPORTED_SETTINGS.get(setting)
    if not cfg or not cfg.options:
        return None
    return list(cfg.options)
