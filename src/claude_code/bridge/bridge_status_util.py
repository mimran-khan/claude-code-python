"""Bridge terminal status helpers (ported from bridge/bridgeStatusUtil.ts)."""

from __future__ import annotations

import datetime
import unicodedata
from typing import Literal, TypedDict

# TODO: get_claude_ai_base_url, get_remote_session_url from constants.product

TOOL_DISPLAY_EXPIRY_MS = 30_000
SHIMMER_INTERVAL_MS = 150
FAILED_FOOTER_TEXT = "Something went wrong, please try again"


def timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")


def format_duration(ms: float) -> str:
    if ms < 60_000:
        return f"{round(ms / 1000)}s"
    m = int(ms // 60_000)
    s = round((ms % 60_000) / 1000)
    return f"{m}m {s}s" if s > 0 else f"{m}m"


def truncate_prompt(text: str, width: int) -> str:
    """Visual-width truncate (approximation using East Asian width)."""
    w = 0
    out: list[str] = []
    for ch in text:
        ea = unicodedata.east_asian_width(ch)
        w += 2 if ea in ("F", "W") else 1
        if w > width:
            break
        out.append(ch)
    return "".join(out)


def abbreviate_activity(summary: str) -> str:
    return truncate_prompt(summary, 30)


def build_bridge_connect_url(environment_id: str, ingress_url: str | None = None) -> str:
    # TODO: get_claude_ai_base_url(undefined, ingress_url)
    base = ingress_url or "https://claude.ai"
    return f"{base.rstrip('/')}/code?bridge={environment_id}"


def build_bridge_session_url(
    session_id: str,
    environment_id: str,
    ingress_url: str | None = None,
) -> str:
    # TODO: get_remote_session_url(session_id, ingress_url)
    base = (ingress_url or "https://claude.ai").rstrip("/")
    return f"{base}/session/{session_id}?bridge={environment_id}"


def compute_glimmer_index(tick: int, message_width: int) -> int:
    cycle_length = message_width + 20
    return message_width + 10 - (tick % cycle_length)


def _string_width(s: str) -> int:
    w = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        w += 2 if ea in ("F", "W") else 1
    return w


def compute_shimmer_segments(
    text: str,
    glimmer_index: int,
) -> dict[str, str]:
    message_width = _string_width(text)
    shimmer_start = glimmer_index - 1
    shimmer_end = glimmer_index + 1
    if shimmer_start >= message_width or shimmer_end < 0:
        return {"before": text, "shimmer": "", "after": ""}
    clamped_start = max(0, shimmer_start)
    col_pos = 0
    before = ""
    shimmer = ""
    after = ""
    for ch in text:
        seg_w = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if col_pos + seg_w <= clamped_start:
            before += ch
        elif col_pos > shimmer_end:
            after += ch
        else:
            shimmer += ch
        col_pos += seg_w
    return {"before": before, "shimmer": shimmer, "after": after}


class BridgeStatusInfo(TypedDict):
    label: str
    color: Literal["error", "warning", "success"]


def get_bridge_status(
    *,
    error: str | None,
    connected: bool,
    session_active: bool,
    reconnecting: bool,
) -> BridgeStatusInfo:
    if error:
        return {"label": "Remote Control failed", "color": "error"}
    if reconnecting:
        return {"label": "Remote Control reconnecting", "color": "warning"}
    if session_active or connected:
        return {"label": "Remote Control active", "color": "success"}
    return {"label": "Remote Control connecting\u2026", "color": "warning"}


def build_idle_footer_text(url: str) -> str:
    return f"Code everywhere with the Claude app or {url}"


def build_active_footer_text(url: str) -> str:
    return f"Continue coding in the Claude app or {url}"


def wrap_with_osc8_link(text: str, url: str) -> str:
    return f"\x1b]8;;{url}\x07{text}\x1b]8;;\x07"
