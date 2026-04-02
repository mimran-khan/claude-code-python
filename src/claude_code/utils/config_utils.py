"""
Configuration utilities.

Functions for loading, saving, and managing configuration.

Migrated from: utils/config.ts (1817 lines) - Core functionality
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from .errors import ConfigParseError

T = TypeVar("T")


@dataclass
class ProjectConfig:
    """Project-level configuration."""

    allowed_tools: list[str] = field(default_factory=list)
    mcp_context_uris: list[str] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    enabled_mcp_servers: list[str] = field(default_factory=list)
    disabled_mcp_servers: list[str] = field(default_factory=list)
    has_trust_dialog_accepted: bool = False
    project_onboarding_seen_count: int = 0
    last_session_id: str | None = None


@dataclass
class GlobalConfig:
    """Global configuration."""

    num_startups: int = 0
    theme: str = "dark"
    verbose_mode: bool = False
    editor_mode: str = "default"
    auto_updates: bool = True
    user_id: str | None = None
    has_completed_onboarding: bool = False
    projects: dict[str, ProjectConfig] = field(default_factory=dict)
    api_key: str | None = None
    model: str | None = None
    mcp_servers: dict[str, Any] = field(default_factory=dict)
    # OAuth account snapshot (camelCase in JSON as oauthAccount)
    oauth_account: dict[str, Any] | None = None
    # Client-side experiment flags (e.g. coral_reef_sonnet) from ~/.claude.json
    client_data_cache: dict[str, str] | None = None
    # Official marketplace auto-install / retry (camelCase in JSON)
    official_marketplace_auto_install_attempted: bool | None = None
    official_marketplace_auto_installed: bool | None = None
    official_marketplace_auto_install_fail_reason: str | None = None
    official_marketplace_auto_install_retry_count: int | None = None
    official_marketplace_auto_install_next_retry_time: int | None = None
    official_marketplace_auto_install_last_attempt_time: int | None = None
    # Plugin install hints from stderr protocol (claudeCodeHints in JSON)
    claude_code_hints: dict[str, Any] | None = None


# Cache for loaded configs
_global_config_cache: GlobalConfig | None = None
_project_config_cache: dict[str, ProjectConfig] = {}


def get_claude_config_dir() -> str:
    """Get the Claude configuration directory."""
    # Check for override
    config_home = os.getenv("CLAUDE_CONFIG_DIR")
    if config_home:
        return config_home

    # Default to ~/.claude
    return os.path.expanduser("~/.claude")


def get_global_config_path() -> str:
    """Get the path to the global config file."""
    return os.path.join(get_claude_config_dir(), "config.json")


def load_global_config_dict() -> dict[str, Any]:
    """
    Load the global config JSON file as a plain dict (all keys preserved).

    Used by migrations that read flags not present on the typed ``GlobalConfig``.
    """
    path = get_global_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data: Any = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_project_config_path(project_path: str | None = None) -> str:
    """Get the path to the project config file."""
    if project_path is None:
        from .cwd import get_cwd

        project_path = get_cwd()

    return os.path.join(project_path, ".claude", "config.json")


def get_global_config() -> GlobalConfig:
    """
    Get the global configuration.

    Loads from disk on first call, then returns cached value.
    """
    global _global_config_cache

    if _global_config_cache is not None:
        return _global_config_cache

    config_path = get_global_config_path()

    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            _global_config_cache = _parse_global_config(data)
        else:
            _global_config_cache = GlobalConfig()
    except json.JSONDecodeError as e:
        raise ConfigParseError(
            f"Invalid JSON in config file: {e}",
            config_path,
            GlobalConfig(),
        )
    except Exception:
        _global_config_cache = GlobalConfig()

    return _global_config_cache


def _parse_global_config(data: dict[str, Any]) -> GlobalConfig:
    """Parse global config from dict."""
    projects = {}
    for path, proj_data in data.get("projects", {}).items():
        projects[path] = _parse_project_config(proj_data)

    return GlobalConfig(
        num_startups=data.get("numStartups", 0),
        theme=data.get("theme", "dark"),
        verbose_mode=data.get("verboseMode", False),
        editor_mode=data.get("editorMode", "default"),
        auto_updates=data.get("autoUpdates", True),
        user_id=data.get("userID"),
        has_completed_onboarding=data.get("hasCompletedOnboarding", False),
        projects=projects,
        api_key=data.get("apiKey"),
        model=data.get("model"),
        mcp_servers=data.get("mcpServers", {}),
        oauth_account=data.get("oauthAccount") if isinstance(data.get("oauthAccount"), dict) else None,
        client_data_cache=data.get("clientDataCache") if isinstance(data.get("clientDataCache"), dict) else None,
        official_marketplace_auto_install_attempted=data.get("officialMarketplaceAutoInstallAttempted")
        if isinstance(data.get("officialMarketplaceAutoInstallAttempted"), bool)
        else None,
        official_marketplace_auto_installed=data.get("officialMarketplaceAutoInstalled")
        if isinstance(data.get("officialMarketplaceAutoInstalled"), bool)
        else None,
        official_marketplace_auto_install_fail_reason=data.get("officialMarketplaceAutoInstallFailReason")
        if isinstance(data.get("officialMarketplaceAutoInstallFailReason"), str)
        else None,
        official_marketplace_auto_install_retry_count=data.get("officialMarketplaceAutoInstallRetryCount")
        if isinstance(data.get("officialMarketplaceAutoInstallRetryCount"), int)
        else None,
        official_marketplace_auto_install_next_retry_time=data.get("officialMarketplaceAutoInstallNextRetryTime")
        if isinstance(data.get("officialMarketplaceAutoInstallNextRetryTime"), int)
        else None,
        official_marketplace_auto_install_last_attempt_time=data.get("officialMarketplaceAutoInstallLastAttemptTime")
        if isinstance(data.get("officialMarketplaceAutoInstallLastAttemptTime"), int)
        else None,
        claude_code_hints=data.get("claudeCodeHints") if isinstance(data.get("claudeCodeHints"), dict) else None,
    )


def _parse_project_config(data: dict[str, Any]) -> ProjectConfig:
    """Parse project config from dict."""
    return ProjectConfig(
        allowed_tools=data.get("allowedTools", []),
        mcp_context_uris=data.get("mcpContextUris", []),
        mcp_servers=data.get("mcpServers", {}),
        enabled_mcp_servers=data.get("enabledMcpServers", []),
        disabled_mcp_servers=data.get("disabledMcpServers", []),
        has_trust_dialog_accepted=data.get("hasTrustDialogAccepted", False),
        project_onboarding_seen_count=data.get("projectOnboardingSeenCount", 0),
        last_session_id=data.get("lastSessionId"),
    )


def save_global_config(
    updater: Callable[[dict[str, Any]], dict[str, Any]],
) -> None:
    """
    Save the global configuration.

    Args:
        updater: Function that takes current config dict and returns updated dict
    """
    global _global_config_cache

    config_path = get_global_config_path()

    # Load current config
    current: dict[str, Any] = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                current = json.load(f)
    except Exception:
        pass

    # Apply update
    updated = updater(current)

    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Write config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    # Invalidate cache
    _global_config_cache = None


def get_current_project_config() -> ProjectConfig:
    """Get the configuration for the current project."""
    from .cwd import get_cwd

    cwd = get_cwd()
    return get_project_config(cwd)


def get_project_config(project_path: str) -> ProjectConfig:
    """Get the configuration for a specific project."""
    if project_path in _project_config_cache:
        return _project_config_cache[project_path]

    config_path = get_project_config_path(project_path)

    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            config = _parse_project_config(data)
        else:
            # Check global config for project entry
            global_config = get_global_config()
            normalized_path = _normalize_path_for_config(project_path)
            config = global_config.projects.get(normalized_path, ProjectConfig())
    except Exception:
        config = ProjectConfig()

    _project_config_cache[project_path] = config
    return config


def save_current_project_config(
    updater: Callable[[dict[str, Any]], dict[str, Any]],
) -> None:
    """Save the current project configuration."""
    from .cwd import get_cwd

    cwd = get_cwd()
    save_project_config(cwd, updater)


def save_project_config(
    project_path: str,
    updater: Callable[[dict[str, Any]], dict[str, Any]],
) -> None:
    """
    Save a project configuration.

    Args:
        project_path: Path to the project
        updater: Function that takes current config dict and returns updated dict
    """
    config_path = get_project_config_path(project_path)

    # Load current config
    current: dict[str, Any] = {}
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                current = json.load(f)
    except Exception:
        pass

    # Apply update
    updated = updater(current)

    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Write config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)

    # Invalidate cache
    _project_config_cache.pop(project_path, None)


def _normalize_path_for_config(path: str) -> str:
    """Normalize a path for use as a config key."""
    return os.path.normpath(os.path.expanduser(path))


def get_memory_path() -> str:
    """Get the path to the memory directory."""
    return os.path.join(get_claude_config_dir(), "memory")


def clear_config_cache() -> None:
    """Clear all config caches."""
    global _global_config_cache, _project_config_cache
    _global_config_cache = None
    _project_config_cache.clear()


def get_api_key() -> str | None:
    """Get the API key from config or environment."""
    # Check environment first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # Check config
    config = get_global_config()
    return config.api_key


def get_model() -> str:
    """Get the model to use."""
    # Check environment
    model = os.getenv("CLAUDE_CODE_MODEL")
    if model:
        return model

    # Check config
    config = get_global_config()
    if config.model:
        return config.model

    # Default
    return "claude-sonnet-4-20250514"


def load_json_config(path: str | Path) -> dict[str, Any]:
    """
    Load a JSON object from ``path``.

    Raises:
        FileNotFoundError: If the path does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)
    if not isinstance(data, dict):
        raise ConfigParseError(
            f"Expected JSON object at root, got {type(data).__name__}",
            str(p),
            {},
        )
    return data


def merge_settings(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """
    Deep-merge ``override`` onto ``base`` (override wins for leaves and nested dicts).
    """
    from .json_utils import deep_merge

    return deep_merge(base, override)


def apply_defaults(
    config: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a new dict with ``defaults`` applied first, then ``config`` (user wins).
    """
    from .json_utils import deep_merge

    return deep_merge(defaults, config)
