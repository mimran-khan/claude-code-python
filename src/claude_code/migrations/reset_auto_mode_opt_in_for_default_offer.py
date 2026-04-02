"""
One-shot migration: clear skipAutoPermissionPrompt for old AutoModeOptInDialog users.

Migrated from: migrations/resetAutoModeOptInForDefaultOffer.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.env_utils import is_env_truthy
from claude_code.utils.log import log_error
from claude_code.utils.permissions.permission_setup import get_auto_mode_enabled_state
from claude_code.utils.settings.settings import (
    get_settings_file_path_for_source,
    get_settings_for_source,
    reset_settings_cache,
)


@dataclass(frozen=True)
class ResetAutoModeOptInSpec:
    """Guard + flag keys (global config survives settings resets)."""

    source_ts: str = "resetAutoModeOptInForDefaultOffer.ts"
    global_done_key: str = "hasResetAutoModeOptInForDefaultOffer"


def reset_auto_mode_opt_in_for_default_offer() -> None:
    if not is_env_truthy(os.environ.get("CLAUDE_CODE_TRANSCRIPT_CLASSIFIER")):
        return

    raw = load_global_config_dict()
    if raw.get(ResetAutoModeOptInSpec.global_done_key):
        return
    if get_auto_mode_enabled_state() != "enabled":
        return

    try:
        user = get_settings_for_source("userSettings") or {}
        perms = user.get("permissions") or {}
        default_mode = perms.get("defaultMode") if isinstance(perms, dict) else None
        if user.get("skipAutoPermissionPrompt") and default_mode != "auto":
            path = get_settings_file_path_for_source("userSettings")
            if path:
                merged: dict[str, Any] = dict(user)
                merged.pop("skipAutoPermissionPrompt", None)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, indent=2)
                reset_settings_cache()
            log_event("tengu_migrate_reset_auto_opt_in_for_default_offer", {})

        def _mark_done(c: dict) -> dict:
            if c.get(ResetAutoModeOptInSpec.global_done_key):
                return c
            return {**c, ResetAutoModeOptInSpec.global_done_key: True}

        save_global_config(_mark_done)
    except Exception as exc:
        log_error(Exception(f"Failed to reset auto mode opt-in: {exc}"))


# Back-compat alias
def reset_auto_mode_opt_in() -> None:
    reset_auto_mode_opt_in_for_default_offer()
