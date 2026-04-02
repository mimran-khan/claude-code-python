"""Migrated from: commands/privacy-settings/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _consumer_subscriber() -> bool:
    """Parity: isConsumerSubscriber(); stub via env until auth wiring exists."""

    return os.environ.get("CLAUDE_CODE_CONSUMER_SUBSCRIBER", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


PRIVACY_SETTINGS_COMMAND = CommandSpec(
    type="local-jsx",
    name="privacy-settings",
    description="View and update your privacy settings",
    is_enabled=_consumer_subscriber,
    load_symbol="claude_code.commands.privacy_settings.ui",
)

__all__ = ["PRIVACY_SETTINGS_COMMAND"]
