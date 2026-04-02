"""
Voice input stub (desktop integrations live in TypeScript UI layer).

Migrated from: services/voice.ts — placeholder for Python CLI/SDK.
See also: ``voice_stream_stt`` (``services/voiceStreamSTT.ts`` wire protocol stub).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoiceSessionConfig:
    """Configuration for a future voice session."""

    enabled: bool = False
    language: str = "en"


async def start_voice_session(_config: VoiceSessionConfig | None = None) -> None:
    """No-op until native voice pipeline is ported."""
    return


async def stop_voice_session() -> None:
    return
