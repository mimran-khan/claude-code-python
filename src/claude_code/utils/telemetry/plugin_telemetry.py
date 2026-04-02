"""
Plugin lifecycle telemetry field builders and event emission.

Migrated from: utils/telemetry/pluginTelemetry.ts
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Literal, Protocol, runtime_checkable

from ...types.plugin import LoadedPlugin, PluginError, PluginManifest
from ..plugins.plugin_identifier import (
    is_official_marketplace_name,
    parse_plugin_identifier,
)

BUILTIN_MARKETPLACE_NAME = "builtin"
PLUGIN_ID_HASH_SALT = "claude-plugin-telemetry-v1"

TelemetryPluginScope = Literal["official", "org", "user-local", "default-bundle"]
EnabledVia = Literal["user-install", "org-policy", "default-enable", "seed-mount"]
InvocationTrigger = Literal["user-slash", "claude-proactive", "nested-skill"]
SkillExecutionContext = Literal["fork", "inline", "remote"]
InstallSource = Literal["cli-explicit", "ui-discover", "ui-suggestion", "deep-link"]
PluginCommandErrorCategory = Literal["network", "not-found", "permission", "validation", "unknown"]


def hash_plugin_id(name: str, marketplace: str | None = None) -> str:
    key = f"{name}@{marketplace.lower()}" if marketplace else name
    return hashlib.sha256((key + PLUGIN_ID_HASH_SALT).encode()).hexdigest()[:16]


def get_telemetry_plugin_scope(
    name: str,
    marketplace: str | None,
    managed_names: set[str] | None,
) -> TelemetryPluginScope:
    if marketplace == BUILTIN_MARKETPLACE_NAME:
        return "default-bundle"
    if is_official_marketplace_name(marketplace):
        return "official"
    if managed_names and name in managed_names:
        return "org"
    return "user-local"


def get_enabled_via(
    plugin: LoadedPlugin,
    managed_names: set[str] | None,
    seed_dirs: list[str],
) -> EnabledVia:
    if plugin.is_builtin:
        return "default-enable"
    if managed_names and plugin.name in managed_names:
        return "org-policy"
    sep = os.sep
    for d in seed_dirs:
        prefix = d if d.endswith(sep) else d + sep
        if plugin.path.startswith(prefix):
            return "seed-mount"
    return "user-install"


def build_plugin_telemetry_fields(
    name: str,
    marketplace: str | None,
    managed_names: set[str] | None = None,
) -> dict[str, Any]:
    scope = get_telemetry_plugin_scope(name, marketplace, managed_names)
    is_anthropic_controlled = scope in ("official", "default-bundle")
    return {
        "plugin_id_hash": hash_plugin_id(name, marketplace),
        "plugin_scope": scope,
        "plugin_name_redacted": name if is_anthropic_controlled else "third-party",
        "marketplace_name_redacted": (marketplace or "third-party") if is_anthropic_controlled else "third-party",
        "is_official_plugin": is_anthropic_controlled,
    }


@runtime_checkable
class PluginCommandInfo(Protocol):
    plugin_manifest: PluginManifest
    repository: str


def build_plugin_command_telemetry_fields(
    plugin_info: PluginCommandInfo,
    managed_names: set[str] | None = None,
) -> dict[str, Any]:
    parsed = parse_plugin_identifier(plugin_info.repository)
    return build_plugin_telemetry_fields(
        plugin_info.plugin_manifest.name,
        parsed.marketplace,
        managed_names,
    )


def log_plugins_enabled_for_session(
    plugins: list[LoadedPlugin],
    managed_names: set[str] | None,
    seed_dirs: list[str],
) -> None:
    from ...services.analytics import log_event

    for plugin in plugins:
        marketplace = parse_plugin_identifier(plugin.repository).marketplace
        manifest_version = getattr(plugin.manifest, "version", None)
        log_event(
            "tengu_plugin_enabled_for_session",
            {
                "_PROTO_plugin_name": plugin.name,
                **({"_PROTO_marketplace_name": marketplace} if marketplace else {}),
                **build_plugin_telemetry_fields(plugin.name, marketplace, managed_names),
                "enabled_via": get_enabled_via(plugin, managed_names, seed_dirs),
                "skill_path_count": (1 if plugin.skills_path else 0) + (len(plugin.skills_paths or [])),
                "command_path_count": (1 if plugin.commands_path else 0) + (len(plugin.commands_paths or [])),
                "has_mcp": plugin.mcp_servers is not None,
                "has_hooks": plugin.hooks_config is not None,
                **({"version": manifest_version} if manifest_version else {}),
            },
        )


def classify_plugin_command_error(error: BaseException | object) -> PluginCommandErrorCategory:
    msg = str(getattr(error, "message", error))
    network_pat = (
        r"ENOTFOUND|ECONNREFUSED|EAI_AGAIN|ETIMEDOUT|ECONNRESET|network|"
        r"Could not resolve|Connection refused|timed out"
    )
    if re.search(network_pat, msg, re.I):
        return "network"
    if re.search(r"\b404\b|not found|does not exist|no such plugin", msg, re.I):
        return "not-found"
    if re.search(r"\b40[13]\b|EACCES|EPERM|permission denied|unauthorized", msg, re.I):
        return "permission"
    if re.search(r"invalid|malformed|schema|validation|parse error", msg, re.I):
        return "validation"
    return "unknown"


def log_plugin_load_errors(errors: list[PluginError], managed_names: set[str] | None) -> None:
    from ...services.analytics import log_event

    for err in errors:
        parsed = parse_plugin_identifier(err.source)
        name, marketplace = parsed.name, parsed.marketplace
        plugin_name = getattr(err, "plugin", None) or name
        log_event(
            "tengu_plugin_load_failed",
            {
                "error_category": err.type,
                "_PROTO_plugin_name": plugin_name,
                **({"_PROTO_marketplace_name": marketplace} if marketplace else {}),
                **build_plugin_telemetry_fields(plugin_name, marketplace, managed_names),
            },
        )
