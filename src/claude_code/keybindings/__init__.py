"""
Keybindings: parse, merge, validate, and resolve keyboard shortcuts.

Migrated from: ``keybindings/*.ts`` (backend logic; React hooks are stubs).

Submodules mirroring TypeScript filenames: :mod:`match`, :mod:`validate`,
:mod:`shortcut_format`, :mod:`use_keybinding`, :mod:`use_shortcut_display`.
"""

from __future__ import annotations

from .default_bindings import DEFAULT_BINDING_BLOCKS, get_default_binding_blocks
from .features import feature, set_features_for_testing
from .load_user_bindings import (
    dispose_keybinding_watcher,
    get_cached_keybinding_warnings,
    get_keybindings_path,
    initialize_keybinding_watcher,
    is_keybinding_customization_enabled,
    load_keybindings,
    load_keybindings_sync,
    load_keybindings_sync_with_warnings,
    log_keybinding_fallback,
    reset_keybinding_loader_for_testing,
    set_keybinding_fallback_logger,
)
from .match import (
    KeyEventLike,
    get_key_name,
    keystroke_matches_binding,
    matches_binding,
    matches_keystroke,
    modifiers_match,
)
from .parser import (
    Chord,
    chord_equals,
    chord_to_display_string,
    chord_to_string,
    format_chord,
    format_keystroke,
    keystroke_equals,
    keystroke_to_display_string,
    keystroke_to_string,
    parse_bindings,
    parse_chord,
    parse_keystroke,
)
from .platform import get_platform, supports_terminal_vt_mode, to_display_platform
from .reserved_shortcuts import (
    MACOS_RESERVED,
    NON_REBINDABLE,
    TERMINAL_RESERVED,
    get_reserved_shortcuts,
    normalize_key_for_comparison,
)
from .resolver import (
    KeybindingResolver,
    chord_exactly_matches,
    chord_prefix_matches,
    get_binding_display_text,
    match_keystroke,
    resolve_key,
    resolve_key_with_chord_state,
)
from .schema import (
    COMMAND_BINDING_PATTERN,
    KEYBINDING_ACTIONS,
    KEYBINDING_CONTEXT_DESCRIPTIONS,
    KEYBINDING_CONTEXTS,
)
from .shortcut_display import get_shortcut_display, reset_shortcut_display_fallback_log
from .template import generate_keybindings_template
from .types import (
    ChordResolveResult,
    KeybindingBlock,
    KeybindingsLoadResult,
    KeybindingWarning,
    ParsedBinding,
    ParsedKeystroke,
    ReservedShortcut,
    ResolveResult,
)
from .validation import (
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

# Back-compat: parsed default bindings (merged list, not raw blocks)
DEFAULT_BINDINGS = parse_bindings(DEFAULT_BINDING_BLOCKS)

# Back-compat: alias used by older port code
load_user_bindings = load_keybindings_sync
Keybinding = ParsedBinding


def get_binding_for_action(
    action: str,
    bindings: list[ParsedBinding] | None = None,
) -> ParsedBinding | None:
    """First binding in list order whose action equals ``action``."""
    seq = bindings if bindings is not None else load_keybindings_sync()
    for b in seq:
        if b.action == action:
            return b
    return None


resolve_keybinding = resolve_key

keystrokes_equal = keystroke_equals

RESERVED_SHORTCUTS = frozenset(normalize_key_for_comparison(r.key) for r in get_reserved_shortcuts())

__all__ = [
    "Chord",
    "ChordResolveResult",
    "COMMAND_BINDING_PATTERN",
    "DEFAULT_BINDING_BLOCKS",
    "DEFAULT_BINDINGS",
    "Keybinding",
    "KeybindingBlock",
    "KeybindingResolver",
    "KeybindingWarning",
    "KeybindingsLoadResult",
    "KeyEventLike",
    "KEYBINDING_ACTIONS",
    "KEYBINDING_CONTEXTS",
    "KEYBINDING_CONTEXT_DESCRIPTIONS",
    "MACOS_RESERVED",
    "NON_REBINDABLE",
    "ParsedBinding",
    "ParsedKeystroke",
    "RESERVED_SHORTCUTS",
    "ResolveResult",
    "ReservedShortcut",
    "TERMINAL_RESERVED",
    "check_duplicate_keys_in_json",
    "check_duplicates",
    "check_reserved_shortcuts",
    "chord_equals",
    "chord_exactly_matches",
    "chord_prefix_matches",
    "chord_to_display_string",
    "chord_to_string",
    "dispose_keybinding_watcher",
    "feature",
    "format_chord",
    "format_keystroke",
    "format_warning",
    "format_warnings",
    "generate_keybindings_template",
    "get_binding_display_text",
    "get_binding_for_action",
    "get_cached_keybinding_warnings",
    "get_default_binding_blocks",
    "get_key_name",
    "get_keybindings_path",
    "get_platform",
    "get_reserved_shortcuts",
    "get_shortcut_display",
    "initialize_keybinding_watcher",
    "is_keybinding_customization_enabled",
    "is_valid_shortcut",
    "keystroke_equals",
    "keystrokes_equal",
    "keystroke_to_display_string",
    "keystroke_to_string",
    "keystroke_matches_binding",
    "load_keybindings",
    "load_keybindings_sync",
    "load_keybindings_sync_with_warnings",
    "load_user_bindings",
    "log_keybinding_fallback",
    "match_keystroke",
    "matches_binding",
    "matches_keystroke",
    "modifiers_match",
    "normalize_key_for_comparison",
    "parse_bindings",
    "parse_chord",
    "parse_keystroke",
    "reset_keybinding_loader_for_testing",
    "reset_shortcut_display_fallback_log",
    "resolve_key",
    "resolve_key_with_chord_state",
    "resolve_keybinding",
    "set_features_for_testing",
    "set_keybinding_fallback_logger",
    "supports_terminal_vt_mode",
    "to_display_platform",
    "validate_bindings",
    "validate_keybinding",
    "validate_user_config",
]
