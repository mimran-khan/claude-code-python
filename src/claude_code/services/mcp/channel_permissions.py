"""
Permission prompts relayed over MCP channel servers.

Migrated from: services/mcp/channelPermissions.ts
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from ..analytics.growthbook import get_feature_value_cached


def is_channel_permission_relay_enabled() -> bool:
    """GrowthBook gate ``tengu_harbor_permissions`` (cached stub)."""
    return bool(get_feature_value_cached("tengu_harbor_permissions", False))


@dataclass(frozen=True)
class ChannelPermissionResponse:
    behavior: Literal["allow", "deny"]
    from_server: str


class _ChannelClient(Protocol):
    type: str
    name: str
    capabilities: Any | None


PERMISSION_REPLY_RE = re.compile(r"^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$", re.IGNORECASE)

ID_ALPHABET = "abcdefghijkmnopqrstuvwxyz"

ID_AVOID_SUBSTRINGS = (
    "fuck",
    "shit",
    "cunt",
    "cock",
    "dick",
    "twat",
    "piss",
    "crap",
    "bitch",
    "whore",
    "ass",
    "tit",
    "cum",
    "fag",
    "dyke",
    "nig",
    "kike",
    "rape",
    "nazi",
    "damn",
    "poo",
    "pee",
    "wank",
    "anus",
)


def _hash_to_id(input_str: str) -> str:
    h = 0x811C9DC5
    for ch in input_str:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    s = ""
    for _ in range(5):
        s += ID_ALPHABET[h % 25]
        h //= 25
    return s


def short_request_id(tool_use_id: str) -> str:
    """Five-letter ID derived from tool use id (FNV-1a + blocklist)."""
    candidate = _hash_to_id(tool_use_id)
    for salt in range(10):
        if not any(bad in candidate for bad in ID_AVOID_SUBSTRINGS):
            return candidate
        candidate = _hash_to_id(f"{tool_use_id}:{salt}")
    return candidate


def truncate_for_preview(input_obj: Any) -> str:
    try:
        s = json.dumps(input_obj, default=str)
    except (TypeError, ValueError):
        return "(unserializable)"
    return s if len(s) <= 200 else s[:200] + "…"


def filter_permission_relay_clients(
    clients: list[_ChannelClient],
    is_in_allowlist: Callable[[str], bool],
) -> list[_ChannelClient]:
    """Keep connected clients in --channels with both channel capabilities."""

    def ok(c: _ChannelClient) -> bool:
        if c.type != "connected":
            return False
        if not is_in_allowlist(c.name):
            return False
        caps = c.capabilities
        if isinstance(caps, dict):
            exp = caps.get("experimental")
        else:
            exp = getattr(caps, "experimental", None) if caps is not None else None
        if not isinstance(exp, dict):
            return False
        return exp.get("claude/channel") is not None and exp.get("claude/channel/permission") is not None

    return [c for c in clients if ok(c)]


class ChannelPermissionCallbacks:
    """Pending permission resolvers (one map per session)."""

    def __init__(self) -> None:
        self._pending: dict[str, Callable[[ChannelPermissionResponse], None]] = {}

    def on_response(
        self,
        request_id: str,
        handler: Callable[[ChannelPermissionResponse], None],
    ) -> Callable[[], None]:
        key = request_id.lower()
        self._pending[key] = handler

        def unsubscribe() -> None:
            self._pending.pop(key, None)

        return unsubscribe

    def resolve(self, request_id: str, behavior: Literal["allow", "deny"], from_server: str) -> bool:
        key = request_id.lower()
        resolver = self._pending.pop(key, None)
        if resolver is None:
            return False
        resolver(ChannelPermissionResponse(behavior=behavior, from_server=from_server))
        return True


def create_channel_permission_callbacks() -> ChannelPermissionCallbacks:
    return ChannelPermissionCallbacks()
