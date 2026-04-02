"""
Extra-usage billing hints for subscriber + 1M models.

Migrated from: utils/extraUsage.ts
"""

from __future__ import annotations

import re

from claude_code.bridge.bridge_enabled import is_claude_ai_subscriber

from .context import has_1m_context


def is_billed_as_extra_usage(
    model: str | None,
    is_fast_mode: bool,
    is_opus_1m_merged: bool,
) -> bool:
    if not is_claude_ai_subscriber():
        return False
    if is_fast_mode:
        return True
    if model is None or not has_1m_context(model):
        return False

    m = re.sub(r"\[1m\]$", "", model.lower(), flags=re.IGNORECASE).strip()
    is_opus_46 = m == "opus" or "opus-4-6" in m
    is_sonnet_46 = m == "sonnet" or "sonnet-4-6" in m

    if is_opus_46 and is_opus_1m_merged:
        return False

    return is_opus_46 or is_sonnet_46
