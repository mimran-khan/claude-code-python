"""
Random word slugs for plan IDs (adjective-verb-noun).

Migrated from: utils/words.ts
"""

from __future__ import annotations

import secrets

from .words_data import ADJECTIVES, NOUNS, VERBS


def _random_int(max_n: int) -> int:
    if max_n <= 0:
        return 0
    return secrets.randbelow(max_n)


def _pick_random(seq: tuple[str, ...]) -> str:
    return seq[_random_int(len(seq))]


def generate_word_slug() -> str:
    """Return ``adjective-verb-noun`` (e.g. ``gleaming-brewing-phoenix``)."""
    return f"{_pick_random(ADJECTIVES)}-{_pick_random(VERBS)}-{_pick_random(NOUNS)}"


def generate_short_word_slug() -> str:
    """Return ``adjective-noun``."""
    return f"{_pick_random(ADJECTIVES)}-{_pick_random(NOUNS)}"
