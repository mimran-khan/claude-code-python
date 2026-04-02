"""
Web setup entry (same TS source as remote-setup; command name `web-setup`).

Migrated from: commands/remote-setup/index.ts
"""

from ..remote.setup_command import (
    WebSetupCommand,
    web_setup_is_enabled,
    web_setup_is_hidden,
)

__all__ = [
    "WebSetupCommand",
    "web_setup_is_enabled",
    "web_setup_is_hidden",
]
