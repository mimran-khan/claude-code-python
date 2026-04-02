"""
Plugin identifier parsing and scope mapping.

Migrated from: utils/plugins/pluginIdentifier.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .schemas import ALLOWED_OFFICIAL_MARKETPLACE_NAMES

PluginScope = Literal["user", "project", "local", "managed"]
ExtendedPluginScope = Literal["user", "project", "local", "managed", "flag"]
EditableSettingSource = Literal["userSettings", "projectSettings", "localSettings"]

SETTING_SOURCE_TO_SCOPE: dict[str, ExtendedPluginScope] = {
    "policySettings": "managed",
    "userSettings": "user",
    "projectSettings": "project",
    "localSettings": "local",
    "flagSettings": "flag",
}


@dataclass
class ParsedPluginIdentifier:
    name: str
    marketplace: str | None = None


def parse_plugin_identifier(plugin: str) -> ParsedPluginIdentifier:
    if "@" in plugin:
        parts = plugin.split("@", 1)
        return ParsedPluginIdentifier(name=parts[0] or "", marketplace=parts[1])
    return ParsedPluginIdentifier(name=plugin)


def build_plugin_id(name: str, marketplace: str | None = None) -> str:
    return f"{name}@{marketplace}" if marketplace else name


def is_official_marketplace_name(marketplace: str | None) -> bool:
    return marketplace is not None and marketplace.lower() in ALLOWED_OFFICIAL_MARKETPLACE_NAMES


def scope_to_editable_setting_source(
    scope: Literal["user", "project", "local"],
) -> EditableSettingSource:
    mapping: dict[str, EditableSettingSource] = {
        "user": "userSettings",
        "project": "projectSettings",
        "local": "localSettings",
    }
    return mapping[scope]


def setting_source_to_scope(source: str) -> ExtendedPluginScope | None:
    return SETTING_SOURCE_TO_SCOPE.get(source)


__all__ = [
    "SETTING_SOURCE_TO_SCOPE",
    "ParsedPluginIdentifier",
    "build_plugin_id",
    "is_official_marketplace_name",
    "parse_plugin_identifier",
    "scope_to_editable_setting_source",
    "setting_source_to_scope",
]
