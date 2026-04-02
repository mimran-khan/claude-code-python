"""
Database and configuration migrations.

Each submodule corresponds to a TypeScript file under ``migrations/*.ts``.
"""

from __future__ import annotations

from .config import (
    migrate_auto_updates_to_settings,
    migrate_bypass_permissions_accepted_to_settings,
    migrate_bypass_permissions_to_settings,
    migrate_enable_all_project_mcp_servers,
    migrate_enable_all_project_mcp_servers_to_settings,
    migrate_repl_bridge_enabled_to_remote_control_at_startup,
)
from .migrate_auto_updates_to_settings import MigrateAutoUpdatesSpec
from .migrate_bypass_permissions_accepted_to_settings import MigrateBypassPermissionsSpec
from .migrate_enable_all_project_mcp_servers_to_settings import MigrateMcpApprovalFieldsSpec
from .migrate_fennec_to_opus import MigrateFennecToOpusSpec, migrate_fennec_to_opus
from .migrate_legacy_opus_to_current import MigrateLegacyOpusSpec, migrate_legacy_opus_to_current
from .migrate_opus_to_opus_1m import MigrateOpusToOpus1mSpec, migrate_opus_to_opus_1m
from .migrate_repl_bridge_enabled_to_remote_control_at_startup import MigrateReplBridgeSpec
from .migrate_sonnet_1m_to_sonnet_45 import (
    MigrateSonnet1mToSonnet45Spec,
    migrate_sonnet_1m_to_sonnet_45,
)
from .migrate_sonnet_45_to_sonnet_46 import (
    MigrateSonnet45ToSonnet46Spec,
    migrate_sonnet_45_to_sonnet_46,
)
from .model import MODEL_MIGRATIONS, migrate_model_in_config, migrate_model_name
from .records import MIGRATION_SOURCE_RECORDS, MigrationSourceRecord
from .reset_auto_mode_opt_in_for_default_offer import (
    ResetAutoModeOptInSpec,
    reset_auto_mode_opt_in,
    reset_auto_mode_opt_in_for_default_offer,
)
from .reset_pro_to_opus_default import ResetProToOpusDefaultSpec, reset_pro_to_opus_default
from .runner import (
    Migration,
    MigrationRunner,
    MigrationStatus,
    get_migration_runner,
    get_migration_status,
    run_migrations,
)
from .startup import CURRENT_MIGRATION_VERSION, run_sync_migrations
from .version_compare import (
    MigrationVersion,
    version_strings_gte,
    version_tuple_from_string,
    version_tuple_gte,
)

__all__ = [
    # Startup gate (main.tsx parity)
    "CURRENT_MIGRATION_VERSION",
    "run_sync_migrations",
    # Registry & version helpers
    "MIGRATION_SOURCE_RECORDS",
    "MigrationSourceRecord",
    "MigrationVersion",
    "version_tuple_from_string",
    "version_tuple_gte",
    "version_strings_gte",
    # Runner
    "Migration",
    "MigrationRunner",
    "MigrationStatus",
    "get_migration_runner",
    "run_migrations",
    "get_migration_status",
    # Config migrations
    "migrate_auto_updates_to_settings",
    "MigrateAutoUpdatesSpec",
    "migrate_bypass_permissions_accepted_to_settings",
    "migrate_bypass_permissions_to_settings",
    "MigrateBypassPermissionsSpec",
    "migrate_enable_all_project_mcp_servers_to_settings",
    "migrate_enable_all_project_mcp_servers",
    "MigrateMcpApprovalFieldsSpec",
    "migrate_repl_bridge_enabled_to_remote_control_at_startup",
    "MigrateReplBridgeSpec",
    # Model map
    "migrate_model_name",
    "migrate_model_in_config",
    "MODEL_MIGRATIONS",
    # Model setting migrations
    "migrate_fennec_to_opus",
    "MigrateFennecToOpusSpec",
    "migrate_legacy_opus_to_current",
    "MigrateLegacyOpusSpec",
    "migrate_opus_to_opus_1m",
    "MigrateOpusToOpus1mSpec",
    "migrate_sonnet_1m_to_sonnet_45",
    "MigrateSonnet1mToSonnet45Spec",
    "migrate_sonnet_45_to_sonnet_46",
    "MigrateSonnet45ToSonnet46Spec",
    # Resets
    "reset_auto_mode_opt_in_for_default_offer",
    "reset_auto_mode_opt_in",
    "ResetAutoModeOptInSpec",
    "reset_pro_to_opus_default",
    "ResetProToOpusDefaultSpec",
]
