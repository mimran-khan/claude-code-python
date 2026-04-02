"""
Resolve selected default environment from merged settings.

Migrated from: utils/teleport/environmentSelection.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .remote_environments import EnvironmentResource


@dataclass
class EnvironmentSelectionInfo:
    available_environments: list[EnvironmentResource]
    selected_environment: EnvironmentResource | None
    selected_environment_source: str | None


async def get_environment_selection_info() -> EnvironmentSelectionInfo:
    from claude_code.utils.settings.constants import SETTING_SOURCES
    from claude_code.utils.settings.settings import (
        get_merged_settings,
        get_settings_for_source,
    )

    from .remote_environments import fetch_environments

    environments = await fetch_environments()
    if not environments:
        return EnvironmentSelectionInfo([], None, None)

    merged = get_merged_settings() or {}
    remote = merged.get("remote")
    default_id = None
    if isinstance(remote, dict):
        default_id = remote.get("defaultEnvironmentId")

    non_bridge = next((e for e in environments if e.kind != "bridge"), None)
    selected = non_bridge or environments[0]
    source: str | None = None

    if default_id:
        match = next((e for e in environments if e.environment_id == default_id), None)
        if match:
            selected = match
            for s in reversed(SETTING_SOURCES):
                if s == "flagSettings":
                    continue
                ss = get_settings_for_source(s) or {}
                r = ss.get("remote")
                if isinstance(r, dict) and r.get("defaultEnvironmentId") == default_id:
                    source = s
                    break

    return EnvironmentSelectionInfo(
        available_environments=environments,
        selected_environment=selected,
        selected_environment_source=source,
    )
