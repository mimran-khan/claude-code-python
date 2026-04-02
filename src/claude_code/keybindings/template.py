"""
Generate a starter ``keybindings.json`` document.

Migrated from: keybindings/template.ts
"""

from __future__ import annotations

import json

from .default_bindings import get_default_binding_blocks
from .reserved_shortcuts import NON_REBINDABLE, normalize_key_for_comparison
from .types import KeybindingBlock


def _filter_reserved_shortcuts(blocks: list[KeybindingBlock]) -> list[KeybindingBlock]:
    reserved = {normalize_key_for_comparison(r.key) for r in NON_REBINDABLE}
    out: list[KeybindingBlock] = []
    for block in blocks:
        filtered = {k: v for k, v in block.bindings.items() if normalize_key_for_comparison(k) not in reserved}
        if filtered:
            out.append(KeybindingBlock(context=block.context, bindings=filtered))
    return out


def generate_keybindings_template() -> str:
    """JSON text with defaults (excluding non-rebindable shortcuts)."""
    bindings = _filter_reserved_shortcuts(get_default_binding_blocks())
    config = {
        "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
        "$docs": "https://code.claude.com/docs/en/keybindings",
        "bindings": [{"context": b.context, "bindings": b.bindings} for b in bindings],
    }
    return json.dumps(config, indent=2) + "\n"
