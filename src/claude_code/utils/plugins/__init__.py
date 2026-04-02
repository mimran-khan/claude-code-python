"""
Plugin utilities.

Migrated from: utils/plugins/*.ts
"""

from .cache_utils import (
    cleanup_orphaned_plugin_versions_in_background,
    clear_all_caches,
    clear_all_plugin_caches,
    mark_plugin_version_orphaned,
)
from .dependency_resolver import verify_and_demote
from .directories import delete_plugin_data_dir, get_plugin_cache_dir, get_plugin_data_dir
from .fetch_telemetry import classify_fetch_error, log_plugin_fetch
from .git_availability import (
    check_git_available,
    clear_git_availability_cache,
    mark_git_unavailable,
)
from .headless_plugin_install import (
    install_plugins_for_headless,
    perform_background_plugin_installations,
)
from .hint_recommendation import (
    PluginHintRecommendation,
    disable_hint_recommendations,
    mark_hint_plugin_shown,
    maybe_record_plugin_hint,
    resolve_plugin_hint,
)
from .identifier import PluginIdentifier, parse_plugin_identifier, scope_to_setting_source
from .install_counts import format_install_count, get_install_counts
from .installed_plugins_manager import (
    get_installed_plugins_file_path,
    load_installed_plugins_from_disk,
)
from .load_plugin_agents import clear_plugin_agent_cache, get_plugin_agents
from .load_plugin_commands import clear_plugin_command_cache, get_plugin_commands
from .load_plugin_hooks import (
    clear_plugin_hook_cache,
    load_plugin_hooks,
    prune_removed_plugin_hooks,
    setup_plugin_hook_hot_reload,
)
from .load_plugin_output_styles import OutputStyleConfig, load_plugin_output_styles
from .loader import clear_plugin_cache as clear_manifest_cache
from .loader import load_all_plugins as load_all_plugin_manifests
from .loader import load_plugin_manifest
from .lsp_integration import load_plugin_lsp_servers
from .managed_plugins import get_managed_plugin_names
from .marketplace_helpers import (
    format_source_for_display,
    get_blocked_marketplaces,
    is_local_marketplace_source,
)
from .marketplace_manager import (
    AddMarketplaceResult,
    DeclaredMarketplace,
    add_marketplace_source,
    clear_marketplaces_cache,
    get_declared_marketplaces,
    get_marketplace,
    get_marketplaces_cache_dir,
    get_plugin_by_id,
    load_known_marketplaces_config,
    load_known_marketplaces_config_safe,
    register_seed_marketplaces,
    save_known_marketplaces_config,
)
from .mcp_plugin_integration import load_plugin_mcp_servers
from .official_marketplace import OFFICIAL_MARKETPLACE_NAME, OFFICIAL_MARKETPLACE_SOURCE
from .official_marketplace_gcs import classify_gcs_error, fetch_official_marketplace_from_gcs
from .official_marketplace_startup_check import (
    OfficialMarketplaceCheckResult,
    OfficialMarketplaceSkipReason,
    check_and_install_official_marketplace,
    is_official_marketplace_auto_install_disabled,
    run_official_marketplace_startup_check,
)
from .orphaned_plugin_filter import (
    clear_plugin_cache_exclusions,
    get_glob_exclusions_for_plugin_cache,
)
from .parse_marketplace_input import (
    DirectoryMarketplaceSource,
    FileMarketplaceSource,
    GithubMarketplaceSource,
    GitMarketplaceSource,
    MarketplaceParseError,
    UrlMarketplaceSource,
    parse_marketplace_input,
)
from .plugin_blocklist import detect_and_uninstall_delisted_plugins, detect_delisted_plugins
from .plugin_directories import (
    get_plugin_data_dir as get_resolved_plugin_data_dir,
)
from .plugin_directories import (
    get_plugin_seed_dirs,
    get_plugins_directory,
    plugin_data_dir_path,
)
from .plugin_flagging import (
    add_flagged_plugin,
    get_flagged_plugins,
    load_flagged_plugins,
    remove_flagged_plugin,
)
from .plugin_identifier import (
    SETTING_SOURCE_TO_SCOPE,
    ParsedPluginIdentifier,
    build_plugin_id,
    is_official_marketplace_name,
    scope_to_editable_setting_source,
    setting_source_to_scope,
)
from .plugin_identifier import (
    parse_plugin_identifier as parse_plugin_identifier_simple,
)
from .plugin_loader import (
    cache_plugin_settings,
    clear_plugin_cache,
    get_plugin_cache_path,
    get_versioned_cache_path,
    get_versioned_cache_path_in,
    get_versioned_zip_cache_path,
    load_all_plugins,
    load_all_plugins_cache_only,
    merge_plugin_sources,
)
from .plugin_options_storage import (
    clear_plugin_options_cache,
    load_plugin_options,
    substitute_plugin_variables,
)
from .reconciler import MarketplaceDiff, ReconcileResult, diff_marketplaces, reconcile_marketplaces
from .refresh import RefreshActivePluginsResult, refresh_active_plugins
from .schemas import (
    ALLOWED_OFFICIAL_MARKETPLACE_NAMES,
    OFFICIAL_GITHUB_ORG,
    MarketplaceSource,
    PluginScope,
    is_blocked_official_name,
    is_marketplace_auto_update,
    validate_official_name_source,
)
from .versioning import calculate_plugin_version, compare_versions
from .walk_plugin_markdown import walk_plugin_markdown
from .zip_cache import (
    atomic_write_to_zip_cache,
    convert_directory_to_zip_in_place,
    create_zip_from_directory,
    extract_zip_to_directory,
    get_marketplace_json_relative_path,
    get_plugin_zip_cache_path,
    get_session_plugin_cache_path,
    is_plugin_zip_cache_enabled,
)
from .zip_cache_adapters import (
    read_zip_cache_known_marketplaces,
    sync_marketplaces_to_zip_cache,
    write_zip_cache_known_marketplaces,
)

__all__ = [
    "ALLOWED_OFFICIAL_MARKETPLACE_NAMES",
    "OFFICIAL_MARKETPLACE_NAME",
    "OFFICIAL_MARKETPLACE_SOURCE",
    "AddMarketplaceResult",
    "DeclaredMarketplace",
    "DirectoryMarketplaceSource",
    "FileMarketplaceSource",
    "GitMarketplaceSource",
    "GithubMarketplaceSource",
    "MarketplaceDiff",
    "MarketplaceParseError",
    "MarketplaceSource",
    "OfficialMarketplaceCheckResult",
    "OfficialMarketplaceSkipReason",
    "OFFICIAL_GITHUB_ORG",
    "OutputStyleConfig",
    "PluginHintRecommendation",
    "ParsedPluginIdentifier",
    "PluginIdentifier",
    "PluginScope",
    "RefreshActivePluginsResult",
    "ReconcileResult",
    "SETTING_SOURCE_TO_SCOPE",
    "UrlMarketplaceSource",
    "add_flagged_plugin",
    "add_marketplace_source",
    "atomic_write_to_zip_cache",
    "build_plugin_id",
    "cache_plugin_settings",
    "calculate_plugin_version",
    "check_and_install_official_marketplace",
    "check_git_available",
    "classify_fetch_error",
    "classify_gcs_error",
    "clear_git_availability_cache",
    "clear_marketplaces_cache",
    "cleanup_orphaned_plugin_versions_in_background",
    "clear_all_caches",
    "clear_all_plugin_caches",
    "clear_manifest_cache",
    "clear_plugin_agent_cache",
    "clear_plugin_cache",
    "clear_plugin_cache_exclusions",
    "clear_plugin_command_cache",
    "clear_plugin_hook_cache",
    "clear_plugin_options_cache",
    "compare_versions",
    "convert_directory_to_zip_in_place",
    "create_zip_from_directory",
    "delete_plugin_data_dir",
    "detect_and_uninstall_delisted_plugins",
    "detect_delisted_plugins",
    "diff_marketplaces",
    "disable_hint_recommendations",
    "extract_zip_to_directory",
    "fetch_official_marketplace_from_gcs",
    "format_install_count",
    "format_source_for_display",
    "get_blocked_marketplaces",
    "get_declared_marketplaces",
    "get_flagged_plugins",
    "get_install_counts",
    "get_glob_exclusions_for_plugin_cache",
    "get_installed_plugins_file_path",
    "get_plugin_agents",
    "get_plugin_cache_dir",
    "get_plugin_cache_path",
    "get_plugin_commands",
    "get_plugin_data_dir",
    "get_plugin_mcp_servers",
    "get_plugin_seed_dirs",
    "get_plugin_zip_cache_path",
    "get_plugins_directory",
    "get_resolved_plugin_data_dir",
    "get_session_plugin_cache_path",
    "get_versioned_cache_path",
    "get_versioned_cache_path_in",
    "get_versioned_zip_cache_path",
    "is_blocked_official_name",
    "is_local_marketplace_source",
    "is_marketplace_auto_update",
    "is_official_marketplace_name",
    "is_plugin_zip_cache_enabled",
    "load_all_plugin_manifests",
    "load_all_plugins",
    "load_all_plugins_cache_only",
    "load_installed_plugins_from_disk",
    "load_known_marketplaces_config_safe",
    "load_plugin_hooks",
    "load_plugin_lsp_servers",
    "load_plugin_manifest",
    "load_plugin_mcp_servers",
    "load_plugin_options",
    "load_plugin_output_styles",
    "mark_plugin_version_orphaned",
    "merge_plugin_sources",
    "parse_marketplace_input",
    "parse_plugin_identifier",
    "parse_plugin_identifier_simple",
    "plugin_data_dir_path",
    "prune_removed_plugin_hooks",
    "reconcile_marketplaces",
    "read_zip_cache_known_marketplaces",
    "refresh_active_plugins",
    "scope_to_editable_setting_source",
    "scope_to_setting_source",
    "setting_source_to_scope",
    "setup_plugin_hook_hot_reload",
    "substitute_plugin_variables",
    "sync_marketplaces_to_zip_cache",
    "validate_official_name_source",
    "verify_and_demote",
    "walk_plugin_markdown",
    "write_zip_cache_known_marketplaces",
    "get_managed_plugin_names",
    "get_marketplace",
    "get_marketplace_json_relative_path",
    "get_marketplaces_cache_dir",
    "get_plugin_by_id",
    "install_plugins_for_headless",
    "is_official_marketplace_auto_install_disabled",
    "load_flagged_plugins",
    "load_known_marketplaces_config",
    "log_plugin_fetch",
    "mark_git_unavailable",
    "mark_hint_plugin_shown",
    "maybe_record_plugin_hint",
    "perform_background_plugin_installations",
    "register_seed_marketplaces",
    "remove_flagged_plugin",
    "resolve_plugin_hint",
    "run_official_marketplace_startup_check",
    "save_known_marketplaces_config",
]
