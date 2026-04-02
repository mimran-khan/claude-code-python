"""
Resolve raw key input to keybinding actions (including chords).

Migrated from: keybindings/resolver.ts
"""

from __future__ import annotations

from typing import Any

from .ink_match import KeyEventLike, get_key_name, matches_binding
from .parser import chord_to_string, keystrokes_equal
from .types import (
    ChordResolveResult,
    ParsedBinding,
    ParsedKeystroke,
    ResolveResult,
)


def _build_keystroke(raw_input: str, key: Any) -> ParsedKeystroke | None:
    key_name = get_key_name(raw_input, key)
    if not key_name:
        return None
    escape = bool(getattr(key, "escape", False))
    effective_meta = False if escape else bool(getattr(key, "meta", False))
    return ParsedKeystroke(
        key=key_name,
        ctrl=bool(getattr(key, "ctrl", False)),
        alt=effective_meta,
        shift=bool(getattr(key, "shift", False)),
        meta=effective_meta,
        super_key=bool(getattr(key, "super", False)),
    )


def resolve_key(
    raw_input: str,
    key: Any,
    active_contexts: list[str],
    bindings: list[ParsedBinding],
) -> ResolveResult:
    """Resolve a key to an action (single-keystroke bindings only)."""
    ctx_set = set(active_contexts)
    match: ParsedBinding | None = None
    for binding in bindings:
        if len(binding.chord) != 1:
            continue
        if binding.context not in ctx_set:
            continue
        if matches_binding(raw_input, key, binding):
            match = binding
    if match is None:
        return {"type": "none"}
    if match.action is None:
        return {"type": "unbound"}
    return {"type": "match", "action": match.action}


def get_binding_display_text(
    action: str,
    context: str,
    bindings: list[ParsedBinding],
) -> str | None:
    """Human chord string for ``action`` in ``context`` (last binding wins)."""
    for b in reversed(bindings):
        if b.action == action and b.context == context:
            return chord_to_string(b.chord)
    return None


def chord_prefix_matches(prefix: list[ParsedKeystroke], binding: ParsedBinding) -> bool:
    if len(prefix) >= len(binding.chord):
        return False
    for i, pk in enumerate(prefix):
        bk = binding.chord[i]
        if not keystrokes_equal(pk, bk):
            return False
    return True


def chord_exactly_matches(chord: list[ParsedKeystroke], binding: ParsedBinding) -> bool:
    if len(chord) != len(binding.chord):
        return False
    return all(keystrokes_equal(ck, bk) for ck, bk in zip(chord, binding.chord, strict=False))


def resolve_key_with_chord_state(
    raw_input: str,
    key: Any,
    active_contexts: list[str],
    bindings: list[ParsedBinding],
    pending: list[ParsedKeystroke] | None,
) -> ChordResolveResult:
    """Resolve with multi-step chord state (Ink parity)."""
    if bool(getattr(key, "escape", False)) and pending is not None:
        return {"type": "chord_cancelled"}

    current = _build_keystroke(raw_input, key)
    if current is None:
        if pending is not None:
            return {"type": "chord_cancelled"}
        return {"type": "none"}

    test_chord = [*pending, current] if pending else [current]
    ctx_set = set(active_contexts)
    context_bindings = [b for b in bindings if b.context in ctx_set]

    chord_winners: dict[str, str | None] = {}
    for binding in context_bindings:
        if len(binding.chord) > len(test_chord) and chord_prefix_matches(test_chord, binding):
            chord_winners[chord_to_string(binding.chord)] = binding.action

    has_longer = any(a is not None for a in chord_winners.values())
    if has_longer:
        return {"type": "chord_started", "pending": test_chord}

    exact: ParsedBinding | None = None
    for binding in context_bindings:
        if chord_exactly_matches(test_chord, binding):
            exact = binding
    if exact is not None:
        if exact.action is None:
            return {"type": "unbound"}
        return {"type": "match", "action": exact.action}

    if pending is not None:
        return {"type": "chord_cancelled"}
    return {"type": "none"}


class KeybindingResolver:
    """Stateful resolver wrapping :meth:`resolve_key_with_chord_state`."""

    def __init__(self, bindings: list[ParsedBinding] | None = None) -> None:
        from .load_user_bindings import load_keybindings_sync

        self._bindings = bindings if bindings is not None else load_keybindings_sync()
        self._pending: list[ParsedKeystroke] | None = None

    @property
    def bindings(self) -> list[ParsedBinding]:
        return self._bindings

    def set_bindings(self, bindings: list[ParsedBinding]) -> None:
        self._bindings = bindings
        self._pending = None

    def resolve(
        self,
        raw_input: str,
        key: KeyEventLike | Any,
        active_contexts: list[str],
    ) -> ChordResolveResult:
        result = resolve_key_with_chord_state(
            raw_input,
            key,
            active_contexts,
            self._bindings,
            self._pending,
        )
        if result["type"] == "chord_started":
            self._pending = result["pending"]
        else:
            self._pending = None
        return result

    def reset(self) -> None:
        self._pending = None


def match_keystroke(keystroke: ParsedKeystroke, bindings: list[ParsedBinding]) -> str | None:
    """First single-keystroke match in list order (no context filter)."""
    for binding in bindings:
        if len(binding.chord) == 1 and keystrokes_equal(binding.chord[0], keystroke):
            return binding.action
    return None
