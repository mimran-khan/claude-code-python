"""
Combine settings flag, auth, and feature gate for voice mode.

Migrated from: hooks/useVoiceEnabled.ts
"""

from __future__ import annotations

from collections.abc import Callable


def compute_voice_enabled(
    *,
    user_intent_voice_enabled: bool,
    has_voice_auth: Callable[[], bool],
    is_voice_growthbook_enabled: Callable[[], bool],
) -> bool:
    return user_intent_voice_enabled and has_voice_auth() and is_voice_growthbook_enabled()
