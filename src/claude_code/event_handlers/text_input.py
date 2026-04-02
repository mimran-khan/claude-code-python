"""
Multiline prompt input (modifiers, history, notifications).

Migrated from: hooks/useTextInput.ts

Full parity belongs in the TUI layer (prompt-toolkit / textual). Import
downstream helpers from :mod:`claude_code.commands.keybindings` as they land.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextInputDriverPlaceholder:
    """Marker type until TextInputState is ported."""

    value: str
