"""
Channel notifications: inbound MCP messages wrapped as <channel> XML.

Migrated from: services/mcp/channelNotification.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ...bootstrap.state import ChannelEntry
from ...constants.xml import CHANNEL_TAG
from ...utils.plugins.identifier import parse_plugin_identifier
from ...utils.xml_esc import escape_xml_attr
from .channel_allowlist import ChannelAllowlistEntry, get_channel_allowlist, is_channels_enabled

CHANNEL_PERMISSION_METHOD = "notifications/claude/channel/permission"
CHANNEL_PERMISSION_REQUEST_METHOD = "notifications/claude/channel/permission_request"

_SAFE_META_KEY = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def wrap_channel_message(
    server_name: str,
    content: str,
    meta: dict[str, str] | None = None,
) -> str:
    attrs = "".join(f' {k}="{escape_xml_attr(v)}"' for k, v in (meta or {}).items() if _SAFE_META_KEY.match(k))
    return f'<{CHANNEL_TAG} source="{escape_xml_attr(server_name)}"{attrs}>\n{content}\n</{CHANNEL_TAG}>'


def get_effective_channel_allowlist(
    subscription_type: str,
    org_list: list[ChannelAllowlistEntry] | None,
) -> tuple[list[ChannelAllowlistEntry], Literal["org", "ledger"]]:
    if subscription_type in ("team", "enterprise") and org_list is not None:
        return org_list, "org"
    return get_channel_allowlist(), "ledger"


def find_channel_entry(
    server_name: str,
    channels: list[ChannelEntry],
) -> ChannelEntry | None:
    parts = server_name.split(":")
    for c in channels:
        if c.kind == "server":
            if server_name == c.name:
                return c
        elif parts[0] == "plugin" and len(parts) > 1 and parts[1] == c.name:
            return c
    return None


@dataclass(frozen=True)
class ChannelGateRegister:
    action: Literal["register"] = field(default="register", init=False)


@dataclass(frozen=True)
class ChannelGateSkip:
    kind: Literal[
        "capability",
        "disabled",
        "auth",
        "policy",
        "session",
        "marketplace",
        "allowlist",
    ]
    reason: str
    action: Literal["skip"] = field(default="skip", init=False)


ChannelGateResult = ChannelGateRegister | ChannelGateSkip


def gate_channel_server(
    server_name: str,
    capabilities: dict[str, Any] | None,
    plugin_source: str | None,
    *,
    oauth_access_token: str | None,
    subscription_type: str,
    policy_channels_enabled: bool | None,
    policy_allowed_channel_plugins: list[ChannelAllowlistEntry] | None,
    allowed_channels: list[ChannelEntry],
) -> ChannelGateResult:
    experimental = (capabilities or {}).get("experimental")
    if not isinstance(experimental, dict) or not experimental.get("claude/channel"):
        return ChannelGateSkip(
            kind="capability",
            reason="server did not declare claude/channel capability",
        )
    if not is_channels_enabled():
        return ChannelGateSkip(
            kind="disabled",
            reason="channels feature is not currently available",
        )
    if not oauth_access_token:
        return ChannelGateSkip(
            kind="auth",
            reason="channels requires claude.ai authentication (run /login)",
        )
    managed = subscription_type in ("team", "enterprise")
    if managed and policy_channels_enabled is not True:
        return ChannelGateSkip(
            kind="policy",
            reason=("channels not enabled by org policy (set channelsEnabled: true in managed settings)"),
        )
    entry = find_channel_entry(server_name, allowed_channels)
    if entry is None:
        return ChannelGateSkip(
            kind="session",
            reason=f"server {server_name} not in --channels list for this session",
        )
    if entry.kind == "plugin":
        actual = None
        if plugin_source:
            actual = parse_plugin_identifier(plugin_source).marketplace
        if actual != entry.marketplace:
            return ChannelGateSkip(
                kind="marketplace",
                reason=(
                    f"you asked for plugin:{entry.name}@{entry.marketplace} "
                    f"but the installed {entry.name} plugin is from "
                    f"{actual or 'an unknown source'}"
                ),
            )
        if not entry.dev:
            entries, source = get_effective_channel_allowlist(
                subscription_type,
                policy_allowed_channel_plugins,
            )
            ok = any(e.plugin == entry.name and e.marketplace == entry.marketplace for e in entries)
            if not ok:
                if source == "org":
                    msg = (
                        f"plugin {entry.name}@{entry.marketplace} is not on your org's "
                        "approved channels list (set allowedChannelPlugins in managed settings)"
                    )
                else:
                    msg = (
                        f"plugin {entry.name}@{entry.marketplace} is not on the approved "
                        "channels allowlist (use --dangerously-load-development-channels "
                        "for local dev)"
                    )
                return ChannelGateSkip(kind="allowlist", reason=msg)
    elif not entry.dev:
        return ChannelGateSkip(
            kind="allowlist",
            reason=(
                f"server {entry.name} is not on the approved channels allowlist "
                "(use --dangerously-load-development-channels for local dev)"
            ),
        )
    return ChannelGateRegister()
