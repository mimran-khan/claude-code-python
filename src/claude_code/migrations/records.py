"""
Registry of migration modules (TypeScript ↔ Python parity).

``dispatch_order`` matches ``main.tsx`` ``runMigrations`` call sequence.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MigrationSourceRecord:
    """One migrated ``migrations/*.ts`` file and its Python implementation."""

    ts_file: str
    python_module: str
    callable_name: str
    dispatch_order: int


MIGRATION_SOURCE_RECORDS: tuple[MigrationSourceRecord, ...] = (
    MigrationSourceRecord(
        ts_file="migrateAutoUpdatesToSettings.ts",
        python_module="claude_code.migrations.migrate_auto_updates_to_settings",
        callable_name="migrate_auto_updates_to_settings",
        dispatch_order=1,
    ),
    MigrationSourceRecord(
        ts_file="migrateBypassPermissionsAcceptedToSettings.ts",
        python_module="claude_code.migrations.migrate_bypass_permissions_accepted_to_settings",
        callable_name="migrate_bypass_permissions_accepted_to_settings",
        dispatch_order=2,
    ),
    MigrationSourceRecord(
        ts_file="migrateEnableAllProjectMcpServersToSettings.ts",
        python_module="claude_code.migrations.migrate_enable_all_project_mcp_servers_to_settings",
        callable_name="migrate_enable_all_project_mcp_servers_to_settings",
        dispatch_order=3,
    ),
    MigrationSourceRecord(
        ts_file="resetProToOpusDefault.ts",
        python_module="claude_code.migrations.reset_pro_to_opus_default",
        callable_name="reset_pro_to_opus_default",
        dispatch_order=4,
    ),
    MigrationSourceRecord(
        ts_file="migrateSonnet1mToSonnet45.ts",
        python_module="claude_code.migrations.migrate_sonnet_1m_to_sonnet_45",
        callable_name="migrate_sonnet_1m_to_sonnet_45",
        dispatch_order=5,
    ),
    MigrationSourceRecord(
        ts_file="migrateLegacyOpusToCurrent.ts",
        python_module="claude_code.migrations.migrate_legacy_opus_to_current",
        callable_name="migrate_legacy_opus_to_current",
        dispatch_order=6,
    ),
    MigrationSourceRecord(
        ts_file="migrateSonnet45ToSonnet46.ts",
        python_module="claude_code.migrations.migrate_sonnet_45_to_sonnet_46",
        callable_name="migrate_sonnet_45_to_sonnet_46",
        dispatch_order=7,
    ),
    MigrationSourceRecord(
        ts_file="migrateOpusToOpus1m.ts",
        python_module="claude_code.migrations.migrate_opus_to_opus_1m",
        callable_name="migrate_opus_to_opus_1m",
        dispatch_order=8,
    ),
    MigrationSourceRecord(
        ts_file="migrateReplBridgeEnabledToRemoteControlAtStartup.ts",
        python_module=("claude_code.migrations.migrate_repl_bridge_enabled_to_remote_control_at_startup"),
        callable_name="migrate_repl_bridge_enabled_to_remote_control_at_startup",
        dispatch_order=9,
    ),
    MigrationSourceRecord(
        ts_file="resetAutoModeOptInForDefaultOffer.ts",
        python_module="claude_code.migrations.reset_auto_mode_opt_in_for_default_offer",
        callable_name="reset_auto_mode_opt_in_for_default_offer",
        dispatch_order=10,
    ),
    MigrationSourceRecord(
        ts_file="migrateFennecToOpus.ts",
        python_module="claude_code.migrations.migrate_fennec_to_opus",
        callable_name="migrate_fennec_to_opus",
        dispatch_order=11,
    ),
)
