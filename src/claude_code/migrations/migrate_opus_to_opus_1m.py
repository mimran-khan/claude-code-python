"""
Migration: pin ``opus`` → ``opus[1m]`` for merged Opus 1M eligibility (1P, non-Pro).

Migrated from: migrations/migrateOpusToOpus1m.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from claude_code.services.analytics.events import log_event
from claude_code.utils.model.model import (
    get_default_main_loop_model_setting,
    is_opus_1m_merge_enabled,
    parse_user_specified_model,
)
from claude_code.utils.settings.settings import (
    get_settings_file_path_for_source,
    get_settings_for_source,
    reset_settings_cache,
    update_settings_for_source,
)


@dataclass(frozen=True)
class MigrateOpusToOpus1mSpec:
    """Metadata for opus → opus[1m] migration."""

    source_ts: str = "migrateOpusToOpus1m.ts"


def _persist_user_settings_model(model: str | None) -> bool:
    """Set or remove ``model`` in user settings (TS allows ``undefined`` to mean default)."""
    path = get_settings_file_path_for_source("userSettings")
    if not path:
        return False
    try:
        existing: dict[str, Any] = dict(get_settings_for_source("userSettings") or {})
        if model is None:
            existing.pop("model", None)
        else:
            existing["model"] = model
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        reset_settings_cache()
        return True
    except OSError:
        return False


def migrate_opus_to_opus_1m() -> None:
    if not is_opus_1m_merge_enabled():
        return

    model = (get_settings_for_source("userSettings") or {}).get("model")
    if model != "opus":
        return

    migrated = "opus[1m]"
    default_setting = get_default_main_loop_model_setting()
    if parse_user_specified_model(migrated) == parse_user_specified_model(default_setting):
        model_to_set: str | None = None
    else:
        model_to_set = migrated

    if model_to_set is None:
        _persist_user_settings_model(None)
    else:
        update_settings_for_source("userSettings", {"model": model_to_set})

    log_event("tengu_opus_to_opus1m_migration", {})
