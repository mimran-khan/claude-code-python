"""
File index and ripgrep-backed prompt suggestions.

Migrated from: hooks/fileSuggestions.ts

Full indexing lives in native TS; Python exposes timing constants and
entry-point names for parity with the hook pipeline.
"""

from __future__ import annotations

# hooks/fileSuggestions.ts — yieldToEventLoop chunk
CHUNK_MS = 16

# Subdir names scanned for markdown prompts (TS: CLAUDE_CONFIG_DIRECTORIES)
CLAUDE_CONFIG_SUBDIRS = (
    "commands",
    "skills",
    "agents",
    "hooks",
)
