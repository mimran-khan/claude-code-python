"""
Migration: move user-set autoUpdates preference to settings.json env.

Migrated from: migrations/migrateAutoUpdatesToSettings.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.debug import log_for_debugging
from claude_code.utils.log import log_error
from claude_code.utils.settings.settings import get_settings_for_source, update_settings_for_source


@dataclass(frozen=True)
class MigrateAutoUpdatesSpec:
    """Metadata for the auto-updates → settings migration."""

    source_ts: str = "migrateAutoUpdatesToSettings.ts"
    env_key: str = "DISABLE_AUTOUPDATER"


def migrate_auto_updates_to_settings() -> None:
    """
    Only migrates if the user explicitly disabled auto-updates (not native protection).

    Preserves intent via ``DISABLE_AUTOUPDATER`` in user settings and process env.
    """
    raw = load_global_config_dict()
    if raw.get("autoUpdates") is not False:
        return
    if raw.get("autoUpdatesProtectedForNative") is True:
        return

    try:
        user_settings = get_settings_for_source("userSettings") or {}
        env_block = dict(user_settings.get("env") or {})
        env_block[MigrateAutoUpdatesSpec.env_key] = "1"
        update_settings_for_source("userSettings", {"env": env_block})

        log_event(
            "tengu_migrate_autoupdates_to_settings",
            {
                "was_user_preference": True,
                "already_had_env_var": bool((user_settings.get("env") or {}).get(MigrateAutoUpdatesSpec.env_key)),
            },
        )

        os.environ[MigrateAutoUpdatesSpec.env_key] = "1"

        def _strip_auto_updates(current: dict) -> dict:
            out = dict(current)
            out.pop("autoUpdates", None)
            out.pop("autoUpdatesProtectedForNative", None)
            return out

        save_global_config(_strip_auto_updates)
    except Exception as exc:
        log_error(Exception(f"Failed to migrate auto-updates: {exc}"))
        log_event("tengu_migrate_autoupdates_error", {"has_error": True})
        log_for_debugging(f"migration: autoUpdates error: {exc}")
