"""Channel plugin allowlist (GrowthBook-backed).

Migrated from: services/mcp/channelAllowlist.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..analytics.growthbook import get_feature_value_cached


@dataclass(frozen=True)
class ChannelAllowlistEntry:
    marketplace: str
    plugin: str


def _parse_plugin_identifier(plugin_source: str) -> tuple[str, str | None]:
    if "@" not in plugin_source:
        return (plugin_source, None)
    name, _, marketplace = plugin_source.partition("@")
    return (name, marketplace or None)


def get_channel_allowlist() -> list[ChannelAllowlistEntry]:
    raw = get_feature_value_cached("tengu_harbor_ledger", [])
    if not isinstance(raw, list):
        return []
    out: list[ChannelAllowlistEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        mp = item.get("marketplace")
        pl = item.get("plugin")
        if isinstance(mp, str) and isinstance(pl, str):
            out.append(ChannelAllowlistEntry(marketplace=mp, plugin=pl))
    return out


def is_channels_enabled() -> bool:
    return bool(get_feature_value_cached("tengu_harbor", False))


def is_channel_allowlisted(plugin_source: str | None) -> bool:
    if not plugin_source:
        return False
    name, marketplace = _parse_plugin_identifier(plugin_source)
    if not marketplace:
        return False
    return any(e.plugin == name and e.marketplace == marketplace for e in get_channel_allowlist())
