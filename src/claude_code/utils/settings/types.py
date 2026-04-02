"""
Settings types.

Defines the type structures for Claude Code settings.

Migrated from: utils/settings/types.ts (1149 lines) - Type definitions only
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PermissionsSettings:
    """Permissions section of settings."""

    allow: list[str] = field(default_factory=list)
    deny: list[str] = field(default_factory=list)
    ask: list[str] = field(default_factory=list)
    default_mode: str | None = None
    disable_bypass_permissions_mode: str | None = None
    disable_auto_mode: str | None = None
    additional_directories: list[str] = field(default_factory=list)


@dataclass
class HookMatcher:
    """Matcher configuration for a hook."""

    tool: str | list[str] | None = None
    mcp_server: str | None = None
    event: str | None = None


@dataclass
class HookCommand:
    """Command to execute for a hook."""

    command: str
    timeout: int | None = None
    working_dir: str | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Hook:
    """A single hook configuration."""

    matcher: HookMatcher
    commands: list[HookCommand] = field(default_factory=list)
    http: dict[str, Any] | None = None


@dataclass
class HooksSettings:
    """Hooks configuration section of settings."""

    hooks: list[Hook] = field(default_factory=list)


@dataclass
class McpServerConfig:
    """Configuration for a single MCP server."""

    command: str | list[str] | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    transport: str | None = None


@dataclass
class McpSettings:
    """MCP servers configuration section of settings."""

    servers: dict[str, McpServerConfig] = field(default_factory=dict)


@dataclass
class ContextSettings:
    """Context provider settings."""

    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass
class SettingsJson:
    """
    Full settings JSON structure.

    This represents the parsed and validated settings from
    settings.json, settings.local.json, etc.
    """

    # Schema URL for validation
    schema_: str | None = None

    # Permissions configuration
    permissions: PermissionsSettings | dict[str, Any] | None = None

    # Hooks configuration
    hooks: HooksSettings | list[dict[str, Any]] | None = None

    # MCP server configuration
    mcp_servers: McpSettings | dict[str, Any] | None = None

    # Environment variables
    env: dict[str, str] | None = None

    # Context providers
    context: ContextSettings | dict[str, Any] | None = None

    # Model configuration
    model: str | None = None
    small_model: str | None = None

    # API configuration
    api_base_url: str | None = None
    api_key_helper: str | None = None

    # Feature flags
    features: dict[str, bool] | None = None

    # Custom instructions
    system_prompt: str | None = None

    # Additional raw fields for passthrough
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {}

        if self.schema_:
            result["$schema"] = self.schema_

        if self.permissions:
            if isinstance(self.permissions, PermissionsSettings):
                result["permissions"] = {
                    "allow": self.permissions.allow,
                    "deny": self.permissions.deny,
                    "ask": self.permissions.ask,
                }
                if self.permissions.default_mode:
                    result["permissions"]["defaultMode"] = self.permissions.default_mode
                if self.permissions.additional_directories:
                    result["permissions"]["additionalDirectories"] = self.permissions.additional_directories
            else:
                result["permissions"] = self.permissions

        if self.hooks:
            result["hooks"] = self.hooks

        if self.mcp_servers:
            result["mcpServers"] = self.mcp_servers

        if self.env:
            result["env"] = self.env

        if self.context:
            result["context"] = self.context

        if self.model:
            result["model"] = self.model

        if self.small_model:
            result["smallModel"] = self.small_model

        if self.api_base_url:
            result["apiBaseUrl"] = self.api_base_url

        if self.features:
            result["features"] = self.features

        if self.system_prompt:
            result["systemPrompt"] = self.system_prompt

        # Merge raw fields
        result.update(self.raw)

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SettingsJson:
        """Create from dictionary."""
        settings = cls()

        settings.schema_ = data.get("$schema")

        # Parse permissions
        if "permissions" in data:
            perms = data["permissions"]
            if isinstance(perms, dict):
                settings.permissions = PermissionsSettings(
                    allow=perms.get("allow", []),
                    deny=perms.get("deny", []),
                    ask=perms.get("ask", []),
                    default_mode=perms.get("defaultMode"),
                    disable_bypass_permissions_mode=perms.get("disableBypassPermissionsMode"),
                    additional_directories=perms.get("additionalDirectories", []),
                )
            else:
                settings.permissions = perms

        settings.hooks = data.get("hooks")
        settings.mcp_servers = data.get("mcpServers")
        settings.env = data.get("env")
        settings.context = data.get("context")
        settings.model = data.get("model")
        settings.small_model = data.get("smallModel")
        settings.api_base_url = data.get("apiBaseUrl")
        settings.api_key_helper = data.get("apiKeyHelper")
        settings.features = data.get("features")
        settings.system_prompt = data.get("systemPrompt")

        # Store unrecognized fields in raw
        known_keys = {
            "$schema",
            "permissions",
            "hooks",
            "mcpServers",
            "env",
            "context",
            "model",
            "smallModel",
            "apiBaseUrl",
            "apiKeyHelper",
            "features",
            "systemPrompt",
        }
        settings.raw = {k: v for k, v in data.items() if k not in known_keys}

        return settings


# Settings validation schema URL
CLAUDE_CODE_SETTINGS_SCHEMA_URL = "https://claude.ai/schemas/claude-code-settings.json"
