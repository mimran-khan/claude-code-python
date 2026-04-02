"""
Anthropic voice_stream speech-to-text (WebSocket) — desktop layer stub.

Migrated from: services/voiceStreamSTT.ts

Full WebSocket client (OAuth, proxy, TLS, transcript framing) remains in the
TypeScript UI build; Python CLI exposes constants for parity.
"""

from __future__ import annotations

from typing import Any, Literal

FinalizeSource = Literal[
    "post_closestream_endpoint",
    "no_data_timeout",
    "safety_timeout",
    "ws_close",
    "ws_already_closed",
]

FINALIZE_TIMEOUTS_MS = {"safety": 5_000, "no_data": 1_500}

VOICE_STREAM_PATH = "/api/ws/speech_to_text/voice_stream"
KEEPALIVE_INTERVAL_MS = 8_000


async def connect_voice_stream(_callbacks: Any) -> None:
    """Placeholder until native voice_stream is implemented for Python."""
    return
