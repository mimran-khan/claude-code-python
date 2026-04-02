"""
Migration: move bypassPermissionsModeAccepted from global config to settings.json.

Migrated from: migrations/migrateBypassPermissionsAcceptedToSettings.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.log import log_error
from claude_code.utils.settings.settings import (
    has_skip_dangerous_mode_permission_prompt,
    update_settings_for_source,
)


@dataclass(frozen=True)
class MigrateBypassPermissionsSpec:
    """Metadata for bypass-permissions migration."""

    source_ts: str = "migrateBypassPermissionsAcceptedToSettings.ts"
    global_key: str = "bypassPermissionsModeAccepted"
    settings_key: str = "skipDangerousModePermissionPrompt"


def migrate_bypass_permissions_accepted_to_settings() -> None:
    raw = load_global_config_dict()
    if not raw.get(MigrateBypassPermissionsSpec.global_key):
        return

    try:
        if not has_skip_dangerous_mode_permission_prompt():
            update_settings_for_source(
                "userSettings",
                {MigrateBypassPermissionsSpec.settings_key: True},
            )

        log_event("tengu_migrate_bypass_permissions_accepted", {})

        def _drop_key(current: dict) -> dict:
            if MigrateBypassPermissionsSpec.global_key not in current:
                return current
            out = dict(current)
            out.pop(MigrateBypassPermissionsSpec.global_key, None)
            return out

        save_global_config(_drop_key)
    except Exception as exc:
        log_error(Exception(f"Failed to migrate bypass permissions accepted: {exc}"))


# Back-compat alias (older Python name)
def migrate_bypass_permissions_to_settings() -> None:
    migrate_bypass_permissions_accepted_to_settings()
