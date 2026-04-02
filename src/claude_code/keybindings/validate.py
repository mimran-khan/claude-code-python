"""
Validate ``keybindings.json`` and surface conflicts (doctor / CLI).

Migrated from: ``keybindings/validate.ts``. Implementation:
:mod:`claude_code.keybindings.validation`.
"""

from __future__ import annotations

from .validation import (
    RESERVED_SHORTCUTS,
    check_duplicate_keys_in_json,
    check_duplicates,
    check_reserved_shortcuts,
    format_warning,
    format_warnings,
    is_valid_shortcut,
    validate_bindings,
    validate_keybinding,
    validate_user_config,
)

__all__ = [
    "RESERVED_SHORTCUTS",
    "check_duplicate_keys_in_json",
    "check_duplicates",
    "check_reserved_shortcuts",
    "format_warning",
    "format_warnings",
    "is_valid_shortcut",
    "validate_bindings",
    "validate_keybinding",
    "validate_user_config",
]
