"""
Migration: ``replBridgeEnabled`` → ``remoteControlAtStartup`` in global config.

Migrated from: migrations/migrateReplBridgeEnabledToRemoteControlAtStartup.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.utils.config_utils import save_global_config


@dataclass(frozen=True)
class MigrateReplBridgeSpec:
    """Metadata for repl bridge rename migration."""

    source_ts: str = "migrateReplBridgeEnabledToRemoteControlAtStartup.ts"
    old_key: str = "replBridgeEnabled"
    new_key: str = "remoteControlAtStartup"


def migrate_repl_bridge_enabled_to_remote_control_at_startup() -> None:
    def _migrate(prev: dict) -> dict:
        old_value = prev.get(MigrateReplBridgeSpec.old_key)
        if old_value is None:
            return prev
        if prev.get(MigrateReplBridgeSpec.new_key) is not None:
            return prev
        nxt = {**prev, MigrateReplBridgeSpec.new_key: bool(old_value)}
        nxt.pop(MigrateReplBridgeSpec.old_key, None)
        return nxt

    save_global_config(_migrate)
