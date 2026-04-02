"""
Voice STT language normalization + PCM level meter.

Migrated from: hooks/useVoice.ts (language map + computeLevel only).
"""

from __future__ import annotations

import math
from typing import Final

DEFAULT_STT_LANGUAGE = "en"

LANGUAGE_NAME_TO_CODE: Final[dict[str, str]] = {
    "english": "en",
    "spanish": "es",
    "español": "es",
    "espanol": "es",
    "french": "fr",
    "français": "fr",
    "francais": "fr",
    "japanese": "ja",
    "日本語": "ja",
    "german": "de",
    "deutsch": "de",
    "portuguese": "pt",
    "português": "pt",
    "portugues": "pt",
    "italian": "it",
    "italiano": "it",
    "korean": "ko",
    "한국어": "ko",
    "hindi": "hi",
    "russian": "ru",
    "polish": "pl",
    "turkish": "tr",
    "dutch": "nl",
    "ukrainian": "uk",
    "greek": "el",
    "czech": "cs",
    "danish": "da",
    "swedish": "sv",
    "norwegian": "no",
}

SUPPORTED_LANGUAGE_CODES: Final[set[str]] = {
    "en",
    "es",
    "fr",
    "ja",
    "de",
    "pt",
    "it",
    "ko",
    "hi",
    "id",
    "ru",
    "pl",
    "tr",
    "nl",
    "uk",
    "el",
    "cs",
    "da",
    "sv",
    "no",
}

RELEASE_TIMEOUT_MS = 200
REPEAT_FALLBACK_MS = 600
FIRST_PRESS_FALLBACK_MS = 2000
FOCUS_SILENCE_TIMEOUT_MS = 5000
AUDIO_LEVEL_BARS = 16


def normalize_language_for_stt(language: str | None) -> tuple[str, str | None]:
    if not language:
        return DEFAULT_STT_LANGUAGE, None
    lower = language.lower().strip()
    if not lower:
        return DEFAULT_STT_LANGUAGE, None
    if lower in SUPPORTED_LANGUAGE_CODES:
        return lower, None
    from_name = LANGUAGE_NAME_TO_CODE.get(lower)
    if from_name:
        return from_name, None
    base = lower.split("-", 1)[0]
    if base in SUPPORTED_LANGUAGE_CODES:
        return base, None
    return DEFAULT_STT_LANGUAGE, language


def compute_level(chunk: bytes) -> float:
    """RMS of 16-bit LE PCM → sqrt-scaled 0..1 (TS parity)."""
    samples = len(chunk) >> 1
    if samples == 0:
        return 0.0
    sum_sq = 0.0
    for i in range(0, len(chunk) - 1, 2):
        sample = int.from_bytes(chunk[i : i + 2], "little", signed=True)
        sum_sq += float(sample * sample)
    rms = math.sqrt(sum_sq / samples)
    normalized = min(rms / 2000.0, 1.0)
    return math.sqrt(normalized)
