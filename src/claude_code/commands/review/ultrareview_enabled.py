"""
Migrated from: commands/review/ultrareviewEnabled.ts

Runtime gate for /ultrareview (GrowthBook parity via env until analytics is wired).
"""

from __future__ import annotations

import json
import os


def is_ultrareview_enabled() -> bool:
    raw = os.environ.get("TENGU_REVIEW_BUGHUNTER_CONFIG", "")
    if not raw.strip():
        return False
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError:
        return False
    return isinstance(cfg, dict) and cfg.get("enabled") is True


__all__ = ["is_ultrareview_enabled"]
