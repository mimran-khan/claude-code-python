"""
Synchronous migration batch (``main.tsx`` ``runMigrations`` parity).

Bumps ``migrationVersion`` in global config when the set changes; keep in sync
with ``CURRENT_MIGRATION_VERSION`` in the TypeScript source.
"""

from __future__ import annotations

from claude_code.utils.config_utils import load_global_config_dict, save_global_config

# Bump when adding a new sync migration (see main.tsx CURRENT_MIGRATION_VERSION).
CURRENT_MIGRATION_VERSION = 11


def run_sync_migrations() -> None:
    """
    Run all gated migrations once per version bump.

    Idempotent for users already at ``CURRENT_MIGRATION_VERSION``.
    Individual migrations remain internally idempotent.
    """
    raw = load_global_config_dict()
    if raw.get("migrationVersion") == CURRENT_MIGRATION_VERSION:
        return

    from .migrate_auto_updates_to_settings import migrate_auto_updates_to_settings
    from .migrate_bypass_permissions_accepted_to_settings import (
        migrate_bypass_permissions_accepted_to_settings,
    )
    from .migrate_enable_all_project_mcp_servers_to_settings import (
        migrate_enable_all_project_mcp_servers_to_settings,
    )
    from .migrate_fennec_to_opus import migrate_fennec_to_opus
    from .migrate_legacy_opus_to_current import migrate_legacy_opus_to_current
    from .migrate_opus_to_opus_1m import migrate_opus_to_opus_1m
    from .migrate_repl_bridge_enabled_to_remote_control_at_startup import (
        migrate_repl_bridge_enabled_to_remote_control_at_startup,
    )
    from .migrate_sonnet_1m_to_sonnet_45 import migrate_sonnet_1m_to_sonnet_45
    from .migrate_sonnet_45_to_sonnet_46 import migrate_sonnet_45_to_sonnet_46
    from .reset_auto_mode_opt_in_for_default_offer import (
        reset_auto_mode_opt_in_for_default_offer,
    )
    from .reset_pro_to_opus_default import reset_pro_to_opus_default

    migrate_auto_updates_to_settings()
    migrate_bypass_permissions_accepted_to_settings()
    migrate_enable_all_project_mcp_servers_to_settings()
    reset_pro_to_opus_default()
    migrate_sonnet_1m_to_sonnet_45()
    migrate_legacy_opus_to_current()
    migrate_sonnet_45_to_sonnet_46()
    migrate_opus_to_opus_1m()
    migrate_repl_bridge_enabled_to_remote_control_at_startup()
    reset_auto_mode_opt_in_for_default_offer()
    migrate_fennec_to_opus()

    def _bump_version(current: dict) -> dict:
        if current.get("migrationVersion") == CURRENT_MIGRATION_VERSION:
            return current
        return {**current, "migrationVersion": CURRENT_MIGRATION_VERSION}

    save_global_config(_bump_version)
