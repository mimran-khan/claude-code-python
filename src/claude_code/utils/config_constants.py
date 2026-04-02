"""
Settings-related constant lists (dependency-free).

Migrated from: utils/configConstants.ts
"""

from __future__ import annotations

from typing import Literal

NOTIFICATION_CHANNELS: tuple[str, ...] = (
    "auto",
    "iterm2",
    "iterm2_with_bell",
    "terminal_bell",
    "kitty",
    "ghostty",
    "notifications_disabled",
)

EDITOR_MODES: tuple[str, ...] = ("normal", "vim")

TEAMMATE_MODES: tuple[str, ...] = ("auto", "tmux", "in-process")

NotificationChannel = Literal[
    "auto",
    "iterm2",
    "iterm2_with_bell",
    "terminal_bell",
    "kitty",
    "ghostty",
    "notifications_disabled",
]
EditorMode = Literal["normal", "vim"]
TeammateMode = Literal["auto", "tmux", "in-process"]

__all__ = [
    "NOTIFICATION_CHANNELS",
    "EDITOR_MODES",
    "TEAMMATE_MODES",
    "NotificationChannel",
    "EditorMode",
    "TeammateMode",
]
