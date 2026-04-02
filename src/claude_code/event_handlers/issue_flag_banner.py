"""
Internal session friction / container-compat heuristics (ant-only banner in TS).

Migrated from: hooks/useIssueFlagBanner.ts
"""

from __future__ import annotations

import re
import time
from collections.abc import Mapping, Sequence
from typing import Any

BASH_TOOL_NAME = "Bash"

_EXTERNAL_COMMAND_PATTERNS = (
    re.compile(r"\bcurl\b"),
    re.compile(r"\bwget\b"),
    re.compile(r"\bssh\b"),
    re.compile(r"\bkubectl\b"),
    re.compile(r"\bsrun\b"),
    re.compile(r"\bdocker\b"),
    re.compile(r"\bbq\b"),
    re.compile(r"\bgsutil\b"),
    re.compile(r"\bgcloud\b"),
    re.compile(r"\baws\b"),
    re.compile(r"\bgit\s+push\b"),
    re.compile(r"\bgit\s+pull\b"),
    re.compile(r"\bgit\s+fetch\b"),
    re.compile(r"\bgh\s+(pr|issue)\b"),
    re.compile(r"\bnc\b"),
    re.compile(r"\bncat\b"),
    re.compile(r"\btelnet\b"),
    re.compile(r"\bftp\b"),
)

_FRICTION_PATTERNS = (
    re.compile(r"^no[,!]\s", re.I),
    re.compile(r"\bthat'?s (wrong|incorrect|not (what|right|correct))\b", re.I),
    re.compile(r"\bnot what I (asked|wanted|meant|said)\b", re.I),
    re.compile(r"\bI (said|asked|wanted|told you|already said)\b", re.I),
    re.compile(r"\bwhy did you\b", re.I),
    re.compile(r"\byou should(n'?t| not)? have\b", re.I),
    re.compile(r"\byou were supposed to\b", re.I),
    re.compile(r"\btry again\b", re.I),
    re.compile(r"\b(undo|revert) (that|this|it|what you)\b", re.I),
)

MIN_SUBMIT_COUNT = 3
COOLDOWN_S = 30 * 60


def is_session_container_compatible(messages: Sequence[Mapping[str, Any]]) -> bool:
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        m = msg.get("message")
        if not isinstance(m, Mapping):
            continue
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, Mapping):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if not isinstance(name, str):
                continue
            if name.startswith("mcp__"):
                return False
            if name == BASH_TOOL_NAME:
                inp = block.get("input")
                cmd = ""
                if isinstance(inp, Mapping):
                    c = inp.get("command")
                    cmd = str(c) if c is not None else ""
                if any(p.search(cmd) for p in _EXTERNAL_COMMAND_PATTERNS):
                    return False
    return True


def has_friction_signal(messages: Sequence[Mapping[str, Any]]) -> bool:
    for msg in reversed(messages):
        if msg.get("type") != "user":
            continue
        text = _user_message_text(msg)
        if not text:
            continue
        return any(p.search(text) for p in _FRICTION_PATTERNS)
    return False


def _user_message_text(msg: Mapping[str, Any]) -> str:
    m = msg.get("message")
    if not isinstance(m, Mapping):
        return ""
    c = m.get("content")
    return str(c) if isinstance(c, str) else ""


class IssueFlagBannerState:
    """Mutable refs: last_triggered_monotonic, active_for_submit, mirrors TS refs."""

    def __init__(self) -> None:
        self.last_triggered_monotonic = 0.0
        self.active_for_submit = -1

    def should_show_banner(
        self,
        *,
        user_type_ant: bool,
        messages: Sequence[Mapping[str, Any]],
        submit_count: int,
    ) -> bool:
        if not user_type_ant:
            return False
        if self.active_for_submit == submit_count:
            return True
        now = time.monotonic()
        if now - self.last_triggered_monotonic < COOLDOWN_S:
            return False
        if submit_count < MIN_SUBMIT_COUNT:
            return False
        if not (is_session_container_compatible(messages) and has_friction_signal(messages)):
            return False
        self.last_triggered_monotonic = now
        self.active_for_submit = submit_count
        return True
