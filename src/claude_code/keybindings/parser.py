"""
Parse keystroke strings and keybinding blocks.

Migrated from: keybindings/parser.ts
"""

from __future__ import annotations

from .platform import to_display_platform
from .types import Chord, DisplayPlatform, KeybindingBlock, ParsedBinding, ParsedKeystroke


def parse_keystroke(input_str: str) -> ParsedKeystroke:
    """Parse a keystroke like ``ctrl+shift+k`` into structured modifiers + key."""
    parts = input_str.split("+")
    ks = ParsedKeystroke()

    for part in parts:
        lower = part.lower()
        match lower:
            case "ctrl" | "control":
                ks.ctrl = True
            case "alt" | "opt" | "option":
                ks.alt = True
            case "shift":
                ks.shift = True
            case "meta":
                ks.meta = True
            case "cmd" | "command" | "super" | "win":
                ks.super_key = True
            case "esc":
                ks.key = "escape"
            case "return":
                ks.key = "enter"
            case "space":
                ks.key = " "
            case "↑":
                ks.key = "up"
            case "↓":
                ks.key = "down"
            case "←":
                ks.key = "left"
            case "→":
                ks.key = "right"
            case _:
                ks.key = lower

    return ks


def parse_chord(input_str: str) -> Chord:
    """Parse ``ctrl+k ctrl+s``; a lone `` `` is the space key, not a separator."""
    if input_str == " ":
        return [parse_keystroke("space")]
    return [parse_keystroke(p) for p in input_str.strip().split()]


def key_to_display_name(key: str) -> str:
    """Map internal key names to human-readable display fragments."""
    match key:
        case "escape":
            return "Esc"
        case " ":
            return "Space"
        case "tab":
            return "tab"
        case "enter":
            return "Enter"
        case "backspace":
            return "Backspace"
        case "delete":
            return "Delete"
        case "up":
            return "↑"
        case "down":
            return "↓"
        case "left":
            return "←"
        case "right":
            return "→"
        case "pageup":
            return "PageUp"
        case "pagedown":
            return "PageDown"
        case "home":
            return "Home"
        case "end":
            return "End"
        case _:
            return key


def keystroke_to_string(ks: ParsedKeystroke) -> str:
    """Canonical string for a parsed keystroke (for chord identity / display base)."""
    parts: list[str] = []
    if ks.ctrl:
        parts.append("ctrl")
    if ks.alt:
        parts.append("alt")
    if ks.shift:
        parts.append("shift")
    if ks.meta:
        parts.append("meta")
    if ks.super_key:
        parts.append("cmd")
    parts.append(key_to_display_name(ks.key))
    return "+".join(parts)


def chord_to_string(chord: Chord) -> str:
    """Join chord steps with spaces."""
    return " ".join(keystroke_to_string(ks) for ks in chord)


# Historical names from early Python port
format_keystroke = keystroke_to_string
format_chord = chord_to_string


def keystroke_to_display_string(
    ks: ParsedKeystroke,
    platform: DisplayPlatform | None = None,
) -> str:
    """Platform-appropriate display (opt vs alt, cmd vs super)."""
    plat = to_display_platform(platform)
    parts: list[str] = []
    if ks.ctrl:
        parts.append("ctrl")
    if ks.alt or ks.meta:
        parts.append("opt" if plat == "macos" else "alt")
    if ks.shift:
        parts.append("shift")
    if ks.super_key:
        parts.append("cmd" if plat == "macos" else "super")
    parts.append(key_to_display_name(ks.key))
    return "+".join(parts)


def chord_to_display_string(
    chord: Chord,
    platform: DisplayPlatform | None = None,
) -> str:
    """Display string for a full chord."""
    return " ".join(keystroke_to_display_string(ks, platform) for ks in chord)


def parse_bindings(blocks: list[KeybindingBlock]) -> list[ParsedBinding]:
    """Flatten config blocks into a list of parsed bindings (document order)."""
    out: list[ParsedBinding] = []
    for block in blocks:
        for key, action in block.bindings.items():
            out.append(
                ParsedBinding(
                    chord=parse_chord(key),
                    action=action,
                    context=block.context,
                )
            )
    return out


def keystrokes_equal(a: ParsedKeystroke, b: ParsedKeystroke) -> bool:
    """Equality for resolver/chord logic; alt/meta collapsed (terminal parity)."""
    return (
        a.key == b.key
        and a.ctrl == b.ctrl
        and a.shift == b.shift
        and (a.alt or a.meta) == (b.alt or b.meta)
        and a.super_key == b.super_key
    )


def chord_equals(a: Chord, b: Chord) -> bool:
    """Full chord equality using keystrokes_equal."""
    if len(a) != len(b):
        return False
    return all(keystrokes_equal(x, y) for x, y in zip(a, b, strict=False))


keystroke_equals = keystrokes_equal
