"""
Plugin Types.

Type definitions for the plugin system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

# Plugin types
PluginType = Literal[
    "mcp",
    "commands",
    "hooks",
    "agents",
    "rules",
    "skills",
]

# Plugin status
PluginStatus = Literal[
    "installed",
    "loading",
    "active",
    "disabled",
    "error",
]


@dataclass
class PluginConfig:
    """Plugin configuration."""

    enabled: bool = True
    auto_update: bool = True
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginManifest:
    """Plugin manifest (plugin.json)."""

    name: str
    version: str
    description: str = ""
    author: str = ""

    # Plugin capabilities
    type: PluginType | list[PluginType] = "mcp"

    # Entry points
    mcp_server: str | None = None
    commands: str | None = None
    hooks: str | None = None
    agents: str | None = None
    rules: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

    # Dependencies
    dependencies: dict[str, str] = field(default_factory=dict)

    # Metadata
    homepage: str = ""
    repository: str = ""
    license: str = ""
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "version": self.version,
        }

        if self.description:
            result["description"] = self.description
        if self.author:
            result["author"] = self.author
        if self.type:
            result["type"] = self.type
        if self.mcp_server:
            result["mcpServer"] = self.mcp_server
        if self.commands:
            result["commands"] = self.commands
        if self.hooks:
            result["hooks"] = self.hooks
        if self.agents:
            result["agents"] = self.agents
        if self.rules:
            result["rules"] = self.rules
        if self.skills:
            result["skills"] = self.skills
        if self.dependencies:
            result["dependencies"] = self.dependencies
        if self.homepage:
            result["homepage"] = self.homepage
        if self.repository:
            result["repository"] = self.repository
        if self.license:
            result["license"] = self.license
        if self.keywords:
            result["keywords"] = self.keywords

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            version=data.get("version", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            type=data.get("type", "mcp"),
            mcp_server=data.get("mcpServer"),
            commands=data.get("commands"),
            hooks=data.get("hooks"),
            agents=data.get("agents"),
            rules=data.get("rules", []),
            skills=data.get("skills", []),
            dependencies=data.get("dependencies", {}),
            homepage=data.get("homepage", ""),
            repository=data.get("repository", ""),
            license=data.get("license", ""),
            keywords=data.get("keywords", []),
        )


@dataclass
class PluginInfo:
    """Information about an installed plugin."""

    id: str
    manifest: PluginManifest
    status: PluginStatus = "installed"
    path: str = ""

    # Installation info
    installed_at: float = 0.0
    updated_at: float = 0.0
    source: str = ""

    # Configuration
    config: PluginConfig = field(default_factory=PluginConfig)

    # Error information
    error: str | None = None

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return self.manifest.name

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return self.manifest.version

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return self.manifest.description

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self.config.enabled and self.status in ("installed", "active")

    @property
    def is_active(self) -> bool:
        """Check if plugin is active."""
        return self.status == "active"

    @property
    def has_error(self) -> bool:
        """Check if plugin has an error."""
        return self.status == "error" or self.error is not None
