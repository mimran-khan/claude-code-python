"""
Natural-language date/time parsing via a small Haiku call.

Migrated from: utils/mcp/dateTimeParser.ts
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from anthropic import AsyncAnthropic

from ..log import log_error

FormatKind = Literal["date", "date-time"]


@dataclass
class DateTimeParseSuccess:
    success: Literal[True] = True
    value: str = ""


@dataclass
class DateTimeParseFailure:
    success: Literal[False] = False
    error: str = ""


DateTimeParseResult = DateTimeParseSuccess | DateTimeParseFailure


def looks_like_iso8601(input_str: str) -> bool:
    return bool(__import__("re").match(r"^\d{4}-\d{2}-\d{2}(T|$)", input_str.strip()))


async def parse_natural_language_date_time(
    input_str: str,
    fmt: FormatKind,
    cancel_event: asyncio.Event | None = None,
) -> DateTimeParseResult:
    now = datetime.now().astimezone()
    current_iso = now.isoformat()
    offset_min = -int(now.utcoffset().total_seconds() // 60) if now.utcoffset() else 0
    sign = "+" if offset_min >= 0 else "-"
    ah = abs(offset_min) // 60
    am = abs(offset_min) % 60
    tz = f"{sign}{ah:02d}:{am:02d}"
    day_of_week = now.strftime("%A")

    system = (
        "You are a date/time parser that converts natural language into ISO 8601 format.\n"
        "You MUST respond with ONLY the ISO 8601 formatted string, with no explanation.\n"
        "If you cannot parse, respond with exactly INVALID."
    )
    fmt_desc = "YYYY-MM-DD (date only)" if fmt == "date" else f"YYYY-MM-DDTHH:MM:SS{tz} (full date-time with timezone)"
    user = (
        f"Current context:\n- Current date and time: {current_iso}\n"
        f"- Local timezone offset: {tz}\n- Day of week: {day_of_week}\n\n"
        f'User input: "{input_str}"\n\nOutput format: {fmt_desc}\n'
        "Return ONLY the formatted string or INVALID."
    )

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return DateTimeParseFailure(error="No API key configured for date parsing.")

    client = AsyncAnthropic(api_key=key)
    model = os.environ.get("ANTHROPIC_SMALL_FAST_MODEL", "claude-3-5-haiku-20241022")

    try:
        if cancel_event and cancel_event.is_set():
            return DateTimeParseFailure(error="Cancelled")

        resp = await asyncio.wait_for(
            client.messages.create(
                model=model,
                max_tokens=128,
                system=system,
                messages=[{"role": "user", "content": user}],
            ),
            timeout=60.0,
        )
        blocks = getattr(resp, "content", []) or []
        parts: list[str] = []
        for b in blocks:
            if getattr(b, "type", None) == "text":
                parts.append(getattr(b, "text", "") or "")
        parsed = "".join(parts).strip()
        if not parsed or parsed == "INVALID" or not parsed[:4].isdigit():
            return DateTimeParseFailure(error="Unable to parse date/time from input")
        return DateTimeParseSuccess(value=parsed)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log_error(e)
        return DateTimeParseFailure(
            error="Unable to parse date/time. Please enter ISO 8601 manually.",
        )
