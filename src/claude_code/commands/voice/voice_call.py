"""
/voice local handler — toggle voice mode.

Migrated from: commands/voice/voice.ts
"""

from __future__ import annotations

from claude_code.utils.auth import is_anthropic_auth_enabled
from claude_code.utils.settings.change_detector import notify_settings_changed
from claude_code.utils.settings.settings import (
    get_merged_settings,
    update_settings_for_source,
)
from claude_code.voice.enabled import (
    has_voice_auth,
    is_voice_growthbook_enabled,
    is_voice_mode_enabled,
)


async def call() -> dict[str, str]:
    if not is_voice_mode_enabled():
        if not is_anthropic_auth_enabled():
            return {
                "type": "text",
                "value": "Voice mode requires a Claude.ai account. Please run /login to sign in.",
            }
        return {"type": "text", "value": "Voice mode is not available."}

    settings = get_merged_settings()
    if settings.get("voiceEnabled") is True:
        if not update_settings_for_source("userSettings", {"voiceEnabled": False}):
            return {
                "type": "text",
                "value": "Failed to update settings. Check your settings file for syntax errors.",
            }
        notify_settings_changed()
        return {"type": "text", "value": "Voice mode disabled."}

    if not has_voice_auth():
        return {
            "type": "text",
            "value": "Voice mode requires a Claude.ai account. Please run /login to sign in.",
        }

    if not is_voice_growthbook_enabled():
        return {"type": "text", "value": "Voice mode is not available."}

    # Recording / SoX / microphone parity lives in services/voice (TS). Stub success path.
    if not update_settings_for_source("userSettings", {"voiceEnabled": True}):
        return {
            "type": "text",
            "value": "Failed to update settings. Check your settings file for syntax errors.",
        }
    notify_settings_changed()
    return {
        "type": "text",
        "value": "Voice mode enabled. (Python port: wire microphone + STT checks for full parity.)",
    }


__all__ = ["call"]
