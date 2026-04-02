"""
Read settings from application state (reactive selector parity).

Migrated from: hooks/useSettings.ts
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def select_settings(app_state: Mapping[str, Any]) -> Any:
    return app_state.get("settings")
