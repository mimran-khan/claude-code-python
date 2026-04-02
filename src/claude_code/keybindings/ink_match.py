"""
Map terminal / Ink-style key events to parsed keystrokes and bindings.

Migrated from: keybindings/match.ts
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .parser import ParsedKeystroke
from .types import ParsedBinding


@dataclass
class KeyEventLike:
    """Subset of Ink ``Key`` used for matching."""

    ctrl: bool = False
    shift: bool = False
    meta: bool = False
    super: bool = False
    escape: bool = False
    return_: bool = False
    tab: bool = False
    backspace: bool = False
    delete: bool = False
    up_arrow: bool = False
    down_arrow: bool = False
    left_arrow: bool = False
    right_arrow: bool = False
    page_up: bool = False
    page_down: bool = False
    wheel_up: bool = False
    wheel_down: bool = False
    home: bool = False
    end: bool = False


def _coerce_key_event(key: KeyEventLike | Any) -> KeyEventLike:
    if isinstance(key, KeyEventLike):
        return key
    return KeyEventLike(
        ctrl=bool(getattr(key, "ctrl", False)),
        shift=bool(getattr(key, "shift", False)),
        meta=bool(getattr(key, "meta", False)),
        super=bool(getattr(key, "super", False)),
        escape=bool(getattr(key, "escape", False)),
        return_=bool(getattr(key, "return", False)),
        tab=bool(getattr(key, "tab", False)),
        backspace=bool(getattr(key, "backspace", False)),
        delete=bool(getattr(key, "delete", False)),
        up_arrow=bool(getattr(key, "upArrow", False)),
        down_arrow=bool(getattr(key, "downArrow", False)),
        left_arrow=bool(getattr(key, "leftArrow", False)),
        right_arrow=bool(getattr(key, "rightArrow", False)),
        page_up=bool(getattr(key, "pageUp", False)),
        page_down=bool(getattr(key, "pageDown", False)),
        wheel_up=bool(getattr(key, "wheelUp", False)),
        wheel_down=bool(getattr(key, "wheelDown", False)),
        home=bool(getattr(key, "home", False)),
        end=bool(getattr(key, "end", False)),
    )


def get_key_name(raw_input: str, key: KeyEventLike | Any) -> str | None:
    """Normalize Ink key flags + character input to internal key name."""
    k = _coerce_key_event(key)
    if k.escape:
        return "escape"
    if k.return_:
        return "enter"
    if k.tab:
        return "tab"
    if k.backspace:
        return "backspace"
    if k.delete:
        return "delete"
    if k.up_arrow:
        return "up"
    if k.down_arrow:
        return "down"
    if k.left_arrow:
        return "left"
    if k.right_arrow:
        return "right"
    if k.page_up:
        return "pageup"
    if k.page_down:
        return "pagedown"
    if k.wheel_up:
        return "wheelup"
    if k.wheel_down:
        return "wheeldown"
    if k.home:
        return "home"
    if k.end:
        return "end"
    if len(raw_input) == 1:
        return raw_input.lower()
    return None


def modifiers_match(key: KeyEventLike | Any, target: ParsedKeystroke) -> bool:
    """Compare ctrl/shift/meta/alt/super between event and parsed binding."""
    ink = _coerce_key_event(key)
    if ink.ctrl != target.ctrl:
        return False
    if ink.shift != target.shift:
        return False
    target_needs_meta = target.alt or target.meta
    if ink.meta != target_needs_meta:
        return False
    return ink.super == target.super_key


def matches_keystroke(raw_input: str, key: KeyEventLike | Any, target: ParsedKeystroke) -> bool:
    """True if terminal event satisfies a parsed keystroke (TS ``matchesKeystroke``)."""
    ink = _coerce_key_event(key)
    key_name = get_key_name(raw_input, ink)
    if key_name != target.key:
        return False
    if ink.escape:
        return modifiers_match(replace(ink, meta=False), target)
    return modifiers_match(ink, target)


def keystroke_matches_binding(
    raw_input: str,
    key: KeyEventLike | Any,
    parsed: ParsedKeystroke,
) -> bool:
    """Alias for :func:`matches_keystroke` (historical Python port name)."""
    return matches_keystroke(raw_input, key, parsed)


def matches_binding(raw_input: str, key: KeyEventLike | Any, binding: ParsedBinding) -> bool:
    """Single-keystroke bindings only (TS ``matchesBinding``)."""
    if len(binding.chord) != 1:
        return False
    return matches_keystroke(raw_input, key, binding.chord[0])
