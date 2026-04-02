"""
Plugin-hint recommendations (stderr ``<claude-code-hint />`` protocol).

Migrated from: utils/plugins/hintRecommendation.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from claude_code.services.analytics.events import log_event
from claude_code.services.analytics.growthbook import get_feature_value_cached

from ..claude_code_hints import (
    ClaudeCodeHint,
    has_shown_hint_this_session,
    set_pending_hint,
)
from ..config_utils import get_global_config, save_global_config
from ..debug import log_for_debugging
from .installed_manager import is_plugin_installed
from .marketplace_manager import get_plugin_by_id
from .plugin_identifier import is_official_marketplace_name, parse_plugin_identifier
from .policy import is_plugin_blocked_by_policy

MAX_SHOWN_PLUGINS = 100

_tried_this_session: set[str] = set()


@dataclass
class PluginHintRecommendation:
    plugin_id: str
    plugin_name: str
    marketplace_name: str
    plugin_description: str | None
    source_command: str


def reset_hint_recommendation_for_testing() -> None:
    _tried_this_session.clear()


def maybe_record_plugin_hint(hint: ClaudeCodeHint) -> None:
    if not get_feature_value_cached("tengu_lapis_finch", False):
        return
    if has_shown_hint_this_session():
        return

    cfg = get_global_config()
    hints_state = cfg.claude_code_hints or {}
    if hints_state.get("disabled"):
        return

    shown = hints_state.get("plugin") if isinstance(hints_state.get("plugin"), list) else []
    if len(shown) >= MAX_SHOWN_PLUGINS:
        return

    plugin_id = hint.value
    parsed = parse_plugin_identifier(plugin_id)
    if not parsed.name or not parsed.marketplace:
        return
    if not is_official_marketplace_name(parsed.marketplace):
        return
    if plugin_id in shown:
        return
    if is_plugin_installed(plugin_id):
        return
    if is_plugin_blocked_by_policy(plugin_id):
        return
    if plugin_id in _tried_this_session:
        return
    _tried_this_session.add(plugin_id)

    set_pending_hint(hint)


async def resolve_plugin_hint(hint: ClaudeCodeHint) -> PluginHintRecommendation | None:
    plugin_id = hint.value
    parsed = parse_plugin_identifier(plugin_id)
    plugin_data = await get_plugin_by_id(plugin_id)

    log_event(
        "tengu_plugin_hint_detected",
        {
            "_PROTO_plugin_name": parsed.name or "",
            "_PROTO_marketplace_name": parsed.marketplace or "",
            "result": "passed" if plugin_data else "not_in_cache",
        },
    )

    if not plugin_data:
        log_for_debugging(f"[hintRecommendation] {plugin_id} not found in marketplace cache")
        return None

    entry = plugin_data.get("entry")
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    if not isinstance(name, str):
        return None
    desc = entry.get("description")
    description = str(desc) if desc is not None else None

    return PluginHintRecommendation(
        plugin_id=plugin_id,
        plugin_name=name,
        marketplace_name=parsed.marketplace or "",
        plugin_description=description,
        source_command=hint.source_command,
    )


def mark_hint_plugin_shown(plugin_id: str) -> None:
    def updater(current: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current)
        hints = dict(merged.get("claudeCodeHints") or {})
        existing = list(hints.get("plugin") or [])
        if plugin_id in existing:
            return merged
        hints["plugin"] = [*existing, plugin_id]
        merged["claudeCodeHints"] = hints
        return merged

    save_global_config(updater)


def disable_hint_recommendations() -> None:
    def updater(current: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current)
        hints = dict(merged.get("claudeCodeHints") or {})
        if hints.get("disabled"):
            return merged
        hints["disabled"] = True
        merged["claudeCodeHints"] = hints
        return merged

    save_global_config(updater)


__all__ = [
    "PluginHintRecommendation",
    "disable_hint_recommendations",
    "mark_hint_plugin_shown",
    "maybe_record_plugin_hint",
    "reset_hint_recommendation_for_testing",
    "resolve_plugin_hint",
]
