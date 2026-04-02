"""
Voice mode module.

Provides voice input/output capabilities for Claude Code.

Migrated from: voice/*.ts
"""

from .enabled import (
    has_voice_auth,
    is_voice_growthbook_enabled,
    is_voice_mode_enabled,
)

__all__ = [
    "is_voice_growthbook_enabled",
    "has_voice_auth",
    "is_voice_mode_enabled",
]
