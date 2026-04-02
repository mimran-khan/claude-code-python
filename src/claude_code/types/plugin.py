"""
Plugin type definitions.

This module defines types for the plugin system, including plugin manifests,
configurations, errors, and load results.

Migrated from: types/plugin.ts (364 lines)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

# ============================================================================
# Plugin Author
# ============================================================================


@dataclass
class PluginAuthor:
    """Author information for a plugin."""

    name: str
    email: str | None = None
    url: str | None = None


# ============================================================================
# Command Metadata
# ============================================================================


@dataclass
class CommandMetadata:
    """Metadata for a plugin command."""

    name: str
    description: str | None = None
    when_to_use: str | None = None
    version: str | None = None


# ============================================================================
# Plugin Manifest
# ============================================================================


@dataclass
class PluginManifest:
    """Manifest for a plugin."""

    name: str
    version: str
    description: str | None = None
    author: PluginAuthor | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None
    dependencies: list[str] | None = None
    lsp_servers: Any | None = None
    user_config: dict[str, Any] | None = None


# ============================================================================
# Bundled Skill Definition
# ============================================================================


@dataclass
class BundledSkillDefinition:
    """Definition for a bundled skill."""

    name: str
    description: str
    content: str | None = None
    when_to_use: str | None = None


# ============================================================================
# Hooks Settings (forward reference)
# ============================================================================

HooksSettings = dict[str, Any]


# ============================================================================
# MCP Server Config (forward reference)
# ============================================================================

McpServerConfig = dict[str, Any]


# ============================================================================
# LSP Server Config (forward reference)
# ============================================================================

LspServerConfig = dict[str, Any]


# ============================================================================
# Builtin Plugin Definition
# ============================================================================


@dataclass
class BuiltinPluginDefinition:
    """
    Definition for a built-in plugin that ships with the CLI.

    Built-in plugins appear in the /plugin UI and can be enabled/disabled
    by users (persisted to user settings).
    """

    name: str
    description: str
    version: str | None = None
    skills: list[BundledSkillDefinition] | None = None
    hooks: HooksSettings | None = None
    mcp_servers: dict[str, McpServerConfig] | None = None
    is_available: Callable[[], bool] | None = None
    default_enabled: bool = True


# ============================================================================
# Plugin Repository
# ============================================================================


@dataclass
class PluginRepository:
    """Repository configuration for a plugin."""

    url: str
    branch: str
    last_updated: str | None = None
    commit_sha: str | None = None


# ============================================================================
# Plugin Config
# ============================================================================


@dataclass
class PluginConfig:
    """Plugin configuration."""

    repositories: dict[str, PluginRepository] = field(default_factory=dict)


# ============================================================================
# Loaded Plugin
# ============================================================================


@dataclass
class LoadedPlugin:
    """A loaded plugin with all its metadata."""

    name: str
    manifest: PluginManifest
    path: str
    source: str
    repository: str
    enabled: bool = True
    is_builtin: bool = False
    sha: str | None = None
    commands_path: str | None = None
    commands_paths: list[str] | None = None
    commands_metadata: dict[str, CommandMetadata] | None = None
    agents_path: str | None = None
    agents_paths: list[str] | None = None
    skills_path: str | None = None
    skills_paths: list[str] | None = None
    output_styles_path: str | None = None
    output_styles_paths: list[str] | None = None
    hooks_config: HooksSettings | None = None
    mcp_servers: dict[str, McpServerConfig] | None = None
    lsp_servers: dict[str, LspServerConfig] | None = None
    settings: dict[str, Any] | None = None


# ============================================================================
# Plugin Component
# ============================================================================

PluginComponent = Literal["commands", "agents", "skills", "hooks", "output-styles"]


# ============================================================================
# Plugin Error Types
# ============================================================================


@dataclass
class PathNotFoundError:
    """Error when a path is not found."""

    type: Literal["path-not-found"] = "path-not-found"
    source: str = ""
    plugin: str | None = None
    path: str = ""
    component: PluginComponent = "commands"


@dataclass
class GitAuthFailedError:
    """Error when git authentication fails."""

    type: Literal["git-auth-failed"] = "git-auth-failed"
    source: str = ""
    plugin: str | None = None
    git_url: str = ""
    auth_type: Literal["ssh", "https"] = "https"


@dataclass
class GitTimeoutError:
    """Error when git operation times out."""

    type: Literal["git-timeout"] = "git-timeout"
    source: str = ""
    plugin: str | None = None
    git_url: str = ""
    operation: Literal["clone", "pull"] = "clone"


@dataclass
class NetworkError:
    """Error for network issues."""

    type: Literal["network-error"] = "network-error"
    source: str = ""
    plugin: str | None = None
    url: str = ""
    details: str | None = None


@dataclass
class ManifestParseError:
    """Error when manifest parsing fails."""

    type: Literal["manifest-parse-error"] = "manifest-parse-error"
    source: str = ""
    plugin: str | None = None
    manifest_path: str = ""
    parse_error: str = ""


@dataclass
class ManifestValidationError:
    """Error when manifest validation fails."""

    type: Literal["manifest-validation-error"] = "manifest-validation-error"
    source: str = ""
    plugin: str | None = None
    manifest_path: str = ""
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class PluginNotFoundError:
    """Error when plugin is not found."""

    type: Literal["plugin-not-found"] = "plugin-not-found"
    source: str = ""
    plugin_id: str = ""
    marketplace: str = ""


@dataclass
class MarketplaceNotFoundError:
    """Error when marketplace is not found."""

    type: Literal["marketplace-not-found"] = "marketplace-not-found"
    source: str = ""
    marketplace: str = ""
    available_marketplaces: list[str] = field(default_factory=list)


@dataclass
class MarketplaceLoadFailedError:
    """Error when marketplace loading fails."""

    type: Literal["marketplace-load-failed"] = "marketplace-load-failed"
    source: str = ""
    marketplace: str = ""
    reason: str = ""


@dataclass
class McpConfigInvalidError:
    """Error when MCP config is invalid."""

    type: Literal["mcp-config-invalid"] = "mcp-config-invalid"
    source: str = ""
    plugin: str = ""
    server_name: str = ""
    validation_error: str = ""


@dataclass
class LspConfigInvalidError:
    """Error when LSP config in a plugin is invalid."""

    type: Literal["lsp-config-invalid"] = "lsp-config-invalid"
    source: str = "plugin"
    plugin: str = ""
    server_name: str = ""
    validation_error: str = ""


@dataclass
class McpServerSuppressedDuplicateError:
    """Error when MCP server is a duplicate."""

    type: Literal["mcp-server-suppressed-duplicate"] = "mcp-server-suppressed-duplicate"
    source: str = ""
    plugin: str = ""
    server_name: str = ""
    duplicate_of: str = ""


@dataclass
class HookLoadFailedError:
    """Error when hook loading fails."""

    type: Literal["hook-load-failed"] = "hook-load-failed"
    source: str = ""
    plugin: str = ""
    hook_path: str = ""
    reason: str = ""


@dataclass
class ComponentLoadFailedError:
    """Error when component loading fails."""

    type: Literal["component-load-failed"] = "component-load-failed"
    source: str = ""
    plugin: str = ""
    component: PluginComponent = "commands"
    path: str = ""
    reason: str = ""


@dataclass
class GenericPluginError:
    """Generic plugin error."""

    type: Literal["generic-error"] = "generic-error"
    source: str = ""
    plugin: str | None = None
    error: str = ""


# Union type for all plugin errors
PluginError = (
    PathNotFoundError
    | GitAuthFailedError
    | GitTimeoutError
    | NetworkError
    | ManifestParseError
    | ManifestValidationError
    | PluginNotFoundError
    | MarketplaceNotFoundError
    | MarketplaceLoadFailedError
    | McpConfigInvalidError
    | LspConfigInvalidError
    | McpServerSuppressedDuplicateError
    | HookLoadFailedError
    | ComponentLoadFailedError
    | GenericPluginError
)

# ============================================================================
# Plugin Load Result
# ============================================================================


@dataclass
class PluginLoadResult:
    """Result of loading plugins."""

    enabled: list[LoadedPlugin] = field(default_factory=list)
    disabled: list[LoadedPlugin] = field(default_factory=list)
    errors: list[PluginError] = field(default_factory=list)


# ============================================================================
# Helper Functions
# ============================================================================


def get_plugin_error_message(error: PluginError) -> str:
    """
    Get a display message from any PluginError.

    Useful for logging and simple error displays.
    """
    error_type = error.type

    if error_type == "generic-error":
        return error.error  # type: ignore[union-attr]
    elif error_type == "path-not-found":
        return f"Path not found: {error.path} ({error.component})"  # type: ignore[union-attr]
    elif error_type == "git-auth-failed":
        return f"Git authentication failed ({error.auth_type}): {error.git_url}"  # type: ignore[union-attr]
    elif error_type == "git-timeout":
        return f"Git {error.operation} timeout: {error.git_url}"  # type: ignore[union-attr]
    elif error_type == "network-error":
        details = f" - {error.details}" if error.details else ""  # type: ignore[union-attr]
        return f"Network error: {error.url}{details}"  # type: ignore[union-attr]
    elif error_type == "manifest-parse-error":
        return f"Manifest parse error: {error.parse_error}"  # type: ignore[union-attr]
    elif error_type == "manifest-validation-error":
        return f"Manifest validation failed: {', '.join(error.validation_errors)}"  # type: ignore[union-attr]
    elif error_type == "plugin-not-found":
        return f"Plugin {error.plugin_id} not found in marketplace {error.marketplace}"  # type: ignore[union-attr]
    elif error_type == "marketplace-not-found":
        return f"Marketplace {error.marketplace} not found"  # type: ignore[union-attr]
    elif error_type == "marketplace-load-failed":
        return f"Marketplace {error.marketplace} failed to load: {error.reason}"  # type: ignore[union-attr]
    elif error_type == "mcp-config-invalid":
        return f"MCP server {error.server_name} invalid: {error.validation_error}"  # type: ignore[union-attr]
    elif error_type == "lsp-config-invalid":
        return (
            f"LSP server {error.server_name} invalid in plugin {error.plugin}: "  # type: ignore[union-attr]
            f"{error.validation_error}"  # type: ignore[union-attr]
        )
    elif error_type == "mcp-server-suppressed-duplicate":
        duplicate_of = error.duplicate_of  # type: ignore[union-attr]
        server_name = error.server_name  # type: ignore[union-attr]
        if duplicate_of.startswith("plugin:"):
            parts = duplicate_of.split(":")
            dup = f'server provided by plugin "{parts[1] if len(parts) > 1 else "?"}"'
        else:
            dup = f'already-configured "{duplicate_of}"'
        return f'MCP server "{server_name}" skipped — same command/URL as {dup}'
    elif error_type == "hook-load-failed":
        return f"Hook load failed: {error.reason}"  # type: ignore[union-attr]
    elif error_type == "component-load-failed":
        return f"{error.component} load failed from {error.path}: {error.reason}"  # type: ignore[union-attr]
    else:
        return f"Unknown plugin error: {error_type}"
