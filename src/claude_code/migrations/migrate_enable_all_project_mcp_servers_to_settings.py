"""
Migration: move MCP approval fields from project config to local settings.

Migrated from: migrations/migrateEnableAllProjectMcpServersToSettings.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import get_project_config_path, save_current_project_config
from claude_code.utils.cwd import get_cwd
from claude_code.utils.log import log_error
from claude_code.utils.settings.settings import get_settings_for_source, update_settings_for_source


@dataclass(frozen=True)
class MigrateMcpApprovalFieldsSpec:
    """Metadata for MCP project → local settings migration."""

    source_ts: str = "migrateEnableAllProjectMcpServersToSettings.ts"


def _load_project_config_dict() -> dict[str, Any]:
    path = get_project_config_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data: Any = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def migrate_enable_all_project_mcp_servers_to_settings() -> None:
    _ = get_cwd()
    project_config = _load_project_config_dict()

    has_enable_all = project_config.get("enableAllProjectMcpServers") is not None
    enabled = project_config.get("enabledMcpjsonServers") or []
    disabled = project_config.get("disabledMcpjsonServers") or []
    has_enabled_servers = isinstance(enabled, list) and len(enabled) > 0
    has_disabled_servers = isinstance(disabled, list) and len(disabled) > 0

    if not has_enable_all and not has_enabled_servers and not has_disabled_servers:
        return

    try:
        existing_settings = get_settings_for_source("localSettings") or {}
        updates: dict[str, Any] = {}
        fields_to_remove: list[str] = []

        if has_enable_all and existing_settings.get("enableAllProjectMcpServers") is None:
            updates["enableAllProjectMcpServers"] = project_config.get("enableAllProjectMcpServers")
            fields_to_remove.append("enableAllProjectMcpServers")
        elif has_enable_all:
            fields_to_remove.append("enableAllProjectMcpServers")

        if has_enabled_servers and isinstance(enabled, list):
            prev = existing_settings.get("enabledMcpjsonServers") or []
            if not isinstance(prev, list):
                prev = []
            updates["enabledMcpjsonServers"] = sorted(set(prev) | set(enabled))
            fields_to_remove.append("enabledMcpjsonServers")

        if has_disabled_servers and isinstance(disabled, list):
            prev_d = existing_settings.get("disabledMcpjsonServers") or []
            if not isinstance(prev_d, list):
                prev_d = []
            updates["disabledMcpjsonServers"] = sorted(set(prev_d) | set(disabled))
            fields_to_remove.append("disabledMcpjsonServers")

        if updates:
            update_settings_for_source("localSettings", updates)

        if fields_to_remove:

            def _strip_project_fields(current: dict[str, Any]) -> dict[str, Any]:
                out = dict(current)
                for k in fields_to_remove:
                    out.pop(k, None)
                return out

            save_current_project_config(_strip_project_fields)

        log_event(
            "tengu_migrate_mcp_approval_fields_success",
            {"migratedCount": len(fields_to_remove)},
        )
    except Exception as exc:
        log_error(exc)
        log_event("tengu_migrate_mcp_approval_fields_error", {})


# Back-compat alias
def migrate_enable_all_project_mcp_servers() -> None:
    migrate_enable_all_project_mcp_servers_to_settings()
