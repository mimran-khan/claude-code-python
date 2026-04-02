"""
Configuration loading and management.

Migrated from: utils/config.ts (partial)
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..utils.env import get_claude_config_home_dir
from ..utils.json import safe_parse_json
from .types import GlobalConfig, ProjectConfig

CONFIG_FILE_NAME = "config.json"


def get_config_path() -> str:
    """
    Get the path to the global config file.

    Returns:
        The path to the config.json file.
    """
    config_dir = get_claude_config_home_dir()
    return os.path.join(config_dir, CONFIG_FILE_NAME)


def _load_config_file(path: str) -> dict[str, Any] | None:
    """Load a config file from disk."""
    try:
        if not os.path.exists(path):
            return None

        with open(path, encoding="utf-8") as f:
            content = f.read()

        # Strip BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        return safe_parse_json(content)
    except Exception:
        return None


def get_global_config() -> GlobalConfig:
    """
    Get the global configuration.

    Returns:
        The GlobalConfig instance.
    """
    config_path = get_config_path()
    data = _load_config_file(config_path)

    if data is None:
        return GlobalConfig()

    # Convert dict to GlobalConfig
    try:
        return GlobalConfig(
            api_key_helper=data.get("apiKeyHelper"),
            projects={k: _dict_to_project_config(v) for k, v in data.get("projects", {}).items()},
            num_startups=data.get("numStartups", 0),
            install_method=data.get("installMethod", "unknown"),
            auto_updates=data.get("autoUpdates", True),
            user_id=data.get("userID"),
            theme=data.get("theme", "dark"),
            has_completed_onboarding=data.get("hasCompletedOnboarding", False),
            editor_mode=data.get("editorMode", "default"),
            preferred_notif_channel=data.get("preferredNotifChannel", "auto"),
            verbose_mode=data.get("verboseMode", False),
            release_channel=data.get("releaseChannel", "stable"),
            mcp_servers=data.get("mcpServers", {}),
            history=[],  # Don't load history by default
            client_data_cache=data.get("clientDataCache"),
            has_acked_telemetry=data.get("hasAckedTelemetry", False),
        )
    except Exception:
        return GlobalConfig()


def _dict_to_project_config(data: dict[str, Any]) -> ProjectConfig:
    """Convert a dict to a ProjectConfig."""
    return ProjectConfig(
        allowed_tools=data.get("allowedTools", []),
        mcp_context_uris=data.get("mcpContextUris", []),
        mcp_servers=data.get("mcpServers"),
        last_api_duration=data.get("lastAPIDuration"),
        last_cost=data.get("lastCost"),
        last_session_id=data.get("lastSessionId"),
        has_trust_dialog_accepted=data.get("hasTrustDialogAccepted", False),
        has_completed_project_onboarding=data.get("hasCompletedProjectOnboarding", False),
        project_onboarding_seen_count=data.get("projectOnboardingSeenCount", 0),
    )


def get_project_config(project_path: str | None = None) -> ProjectConfig:
    """
    Get the configuration for a project.

    Args:
        project_path: The project path, or None for cwd.

    Returns:
        The ProjectConfig for the project.
    """
    if project_path is None:
        project_path = os.getcwd()

    # Normalize the path
    project_path = os.path.normpath(os.path.abspath(project_path))

    global_config = get_global_config()
    return global_config.projects.get(project_path, ProjectConfig())


def set_global_config(config: GlobalConfig) -> None:
    """
    Save the global configuration.

    Args:
        config: The GlobalConfig to save.
    """
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)

    # Ensure config directory exists
    os.makedirs(config_dir, exist_ok=True)

    # Convert to dict for JSON serialization
    data = _global_config_to_dict(config)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _global_config_to_dict(config: GlobalConfig) -> dict[str, Any]:
    """Convert a GlobalConfig to a dict for serialization."""
    return {
        "apiKeyHelper": config.api_key_helper,
        "projects": {k: _project_config_to_dict(v) for k, v in config.projects.items()},
        "numStartups": config.num_startups,
        "installMethod": config.install_method,
        "autoUpdates": config.auto_updates,
        "userID": config.user_id,
        "theme": config.theme,
        "hasCompletedOnboarding": config.has_completed_onboarding,
        "editorMode": config.editor_mode,
        "preferredNotifChannel": config.preferred_notif_channel,
        "verboseMode": config.verbose_mode,
        "releaseChannel": config.release_channel,
        "mcpServers": config.mcp_servers,
        "clientDataCache": config.client_data_cache,
        "hasAckedTelemetry": config.has_acked_telemetry,
    }


def _project_config_to_dict(config: ProjectConfig) -> dict[str, Any]:
    """Convert a ProjectConfig to a dict for serialization."""
    return {
        "allowedTools": config.allowed_tools,
        "mcpContextUris": config.mcp_context_uris,
        "mcpServers": config.mcp_servers,
        "lastAPIDuration": config.last_api_duration,
        "lastCost": config.last_cost,
        "lastSessionId": config.last_session_id,
        "hasTrustDialogAccepted": config.has_trust_dialog_accepted,
        "hasCompletedProjectOnboarding": config.has_completed_project_onboarding,
        "projectOnboardingSeenCount": config.project_onboarding_seen_count,
    }
