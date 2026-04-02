"""
Validate keybinding configuration and detect conflicts.

Migrated from: keybindings/validate.ts
"""

from __future__ import annotations

import re
from typing import Any

from ..utils.string_utils import plural
from .parser import chord_to_string, parse_chord, parse_keystroke
from .reserved_shortcuts import get_reserved_shortcuts, normalize_key_for_comparison
from .schema import KEYBINDING_CONTEXTS
from .types import KeybindingBlock, KeybindingWarning, ParsedBinding

VALID_CONTEXTS: frozenset[str] = frozenset(KEYBINDING_CONTEXTS)

# Backwards-compatible export for ``keybindings.__init__`` / older callers.
RESERVED_SHORTCUTS: frozenset[str] = frozenset(normalize_key_for_comparison(s.key) for s in get_reserved_shortcuts())

_BINDINGS_BLOCK_RE = re.compile(
    r'"bindings"\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
    re.MULTILINE,
)
_KEY_IN_BINDINGS_RE = re.compile(r'"([^"]+)"\s*:')


def _validate_keystroke(keystroke: str) -> KeybindingWarning | None:
    parts = keystroke.lower().split("+")
    for part in parts:
        trimmed = part.strip()
        if not trimmed:
            return KeybindingWarning(
                type="parse_error",
                severity="error",
                message=f'Empty key part in "{keystroke}"',
                key=keystroke,
                suggestion='Remove extra "+" characters',
            )

    parsed = parse_keystroke(keystroke)
    if (
        not parsed.key
        and not parsed.ctrl
        and not parsed.alt
        and not parsed.shift
        and not parsed.meta
        and not parsed.super_key
    ):
        return KeybindingWarning(
            type="parse_error",
            severity="error",
            message=f'Could not parse keystroke "{keystroke}"',
            key=keystroke,
        )
    return None


def _validate_block(block: Any, block_index: int) -> list[KeybindingWarning]:
    warnings: list[KeybindingWarning] = []

    if not isinstance(block, dict):
        warnings.append(
            KeybindingWarning(
                type="parse_error",
                severity="error",
                message=f"Keybinding block {block_index + 1} is not an object",
            )
        )
        return warnings

    raw_context = block.get("context")
    context_name: str | None = None
    if not isinstance(raw_context, str):
        warnings.append(
            KeybindingWarning(
                type="parse_error",
                severity="error",
                message=f'Keybinding block {block_index + 1} missing "context" field',
            )
        )
    elif raw_context not in VALID_CONTEXTS:
        warnings.append(
            KeybindingWarning(
                type="invalid_context",
                severity="error",
                message=f'Unknown context "{raw_context}"',
                context=raw_context,
                suggestion=f"Valid contexts: {', '.join(sorted(VALID_CONTEXTS))}",
            )
        )
    else:
        context_name = raw_context

    bindings = block.get("bindings")
    if not isinstance(bindings, dict):
        warnings.append(
            KeybindingWarning(
                type="parse_error",
                severity="error",
                message=f'Keybinding block {block_index + 1} missing "bindings" field',
            )
        )
        return warnings

    for key, action in bindings.items():
        key_err = _validate_keystroke(key)
        if key_err:
            key_err.context = context_name
            warnings.append(key_err)

        if action is not None and not isinstance(action, str):
            warnings.append(
                KeybindingWarning(
                    type="invalid_action",
                    severity="error",
                    message=f'Invalid action for "{key}": must be a string or null',
                    key=key,
                    context=context_name,
                )
            )
        elif isinstance(action, str) and action.startswith("command:"):
            if not re.match(r"^command:[a-zA-Z0-9:\-_]+$", action):
                warnings.append(
                    KeybindingWarning(
                        type="invalid_action",
                        severity="warning",
                        message=(
                            f'Invalid command binding "{action}" for "{key}": '
                            "command name may only contain alphanumeric characters, "
                            "colons, hyphens, and underscores"
                        ),
                        key=key,
                        context=context_name,
                        action=action,
                    )
                )
            if context_name and context_name != "Chat":
                warnings.append(
                    KeybindingWarning(
                        type="invalid_action",
                        severity="warning",
                        message=(f'Command binding "{action}" must be in "Chat" context, not "{context_name}"'),
                        key=key,
                        context=context_name,
                        action=action,
                        suggestion='Move this binding to a block with "context": "Chat"',
                    )
                )
        elif action == "voice:pushToTalk":
            chord = parse_chord(key)
            ks = chord[0] if chord else None
            if (
                ks
                and not ks.ctrl
                and not ks.alt
                and not ks.shift
                and not ks.meta
                and not ks.super_key
                and re.match(r"^[a-z]$", ks.key) is not None
            ):
                warnings.append(
                    KeybindingWarning(
                        type="invalid_action",
                        severity="warning",
                        message=(
                            f'Binding "{key}" to voice:pushToTalk prints into the input '
                            "during warmup; use space or a modifier combo like meta+k"
                        ),
                        key=key,
                        context=context_name,
                        action=action,
                    )
                )

    return warnings


def check_duplicate_keys_in_json(json_string: str) -> list[KeybindingWarning]:
    """Detect duplicate JSON keys within each ``bindings`` object (parse would keep last)."""
    warnings: list[KeybindingWarning] = []
    for m in _BINDINGS_BLOCK_RE.finditer(json_string):
        block_content = m.group(1) or ""
        text_before = json_string[: m.start()]
        ctx_m = re.search(r'"context"\s*:\s*"([^"]+)"[^{]*$', text_before)
        context = ctx_m.group(1) if ctx_m else "unknown"
        keys_by_name: dict[str, int] = {}
        for km in _KEY_IN_BINDINGS_RE.finditer(block_content):
            k = km.group(1)
            if not k:
                continue
            keys_by_name[k] = keys_by_name.get(k, 0) + 1
            if keys_by_name[k] == 2:
                warnings.append(
                    KeybindingWarning(
                        type="duplicate",
                        severity="warning",
                        message=f'Duplicate key "{k}" in {context} bindings',
                        key=k,
                        context=context,
                        suggestion=(
                            "This key appears multiple times in the same context. "
                            "JSON uses the last value; earlier values are ignored."
                        ),
                    )
                )
    return warnings


def validate_user_config(user_blocks: Any) -> list[KeybindingWarning]:
    if not isinstance(user_blocks, list):
        return [
            KeybindingWarning(
                type="parse_error",
                severity="error",
                message="keybindings.json must contain an array",
                suggestion="Wrap your bindings in [ ]",
            )
        ]
    out: list[KeybindingWarning] = []
    for i, block in enumerate(user_blocks):
        out.extend(_validate_block(block, i))
    return out


def _ts_action_conflict(stored: str, action: str | None) -> bool:
    """Match TypeScript ``existingAction !== action`` (null vs ``'null'`` string)."""
    if action is None:
        return True
    return stored != action


def check_duplicates(blocks: list[KeybindingBlock]) -> list[KeybindingWarning]:
    warnings: list[KeybindingWarning] = []
    seen_by_context: dict[str, dict[str, str]] = {}

    for block in blocks:
        ctx_map = seen_by_context.setdefault(block.context, {})
        for key, action in block.bindings.items():
            normalized = normalize_key_for_comparison(key)
            stored = ctx_map.get(normalized)
            action_label = "null (unbind)" if action is None else str(action)
            if stored is not None and _ts_action_conflict(stored, action):
                warnings.append(
                    KeybindingWarning(
                        type="duplicate",
                        severity="warning",
                        message=f'Duplicate binding "{key}" in {block.context} context',
                        key=key,
                        context=block.context,
                        action=action_label,
                        suggestion=(f'Previously bound to "{stored}". Only the last binding will be used.'),
                    )
                )
            ctx_map[normalized] = action if action is not None else "null"

    return warnings


def check_reserved_shortcuts(bindings: list[ParsedBinding]) -> list[KeybindingWarning]:
    warnings: list[KeybindingWarning] = []
    reserved = get_reserved_shortcuts()
    for binding in bindings:
        key_display = chord_to_string(binding.chord)
        normalized = normalize_key_for_comparison(key_display)
        for res in reserved:
            if normalize_key_for_comparison(res.key) == normalized:
                warnings.append(
                    KeybindingWarning(
                        type="reserved",
                        severity=res.severity,
                        message=f'"{key_display}" may not work: {res.reason}',
                        key=key_display,
                        context=binding.context,
                        action=binding.action,
                    )
                )
    return warnings


def _user_bindings_for_validation(user_blocks: list[KeybindingBlock]) -> list[ParsedBinding]:
    from .parser import parse_bindings

    return parse_bindings(user_blocks)


def validate_bindings(
    user_blocks: Any,
    _parsed_bindings: list[ParsedBinding],
) -> list[KeybindingWarning]:
    warnings: list[KeybindingWarning] = []
    warnings.extend(validate_user_config(user_blocks))

    if isinstance(user_blocks, list) and all(_is_keybinding_block_obj(b) for b in user_blocks):
        blocks_typed = [KeybindingBlock(context=str(b["context"]), bindings=dict(b["bindings"])) for b in user_blocks]
        warnings.extend(check_duplicates(blocks_typed))
        warnings.extend(check_reserved_shortcuts(_user_bindings_for_validation(blocks_typed)))

    seen: set[str] = set()
    out: list[KeybindingWarning] = []
    for w in warnings:
        k = f"{w.type}:{w.key}:{w.context}"
        if k in seen:
            continue
        seen.add(k)
        out.append(w)
    return out


def _is_keybinding_block_obj(obj: Any) -> bool:
    return isinstance(obj, dict) and isinstance(obj.get("context"), str) and isinstance(obj.get("bindings"), dict)


def format_warning(warning: KeybindingWarning) -> str:
    icon = "✗" if warning.severity == "error" else "⚠"
    msg = f"{icon} Keybinding {warning.severity}: {warning.message}"
    if warning.suggestion:
        msg += f"\n  {warning.suggestion}"
    return msg


def format_warnings(warnings: list[KeybindingWarning]) -> str:
    if not warnings:
        return ""
    errors = [w for w in warnings if w.severity == "error"]
    warns = [w for w in warnings if w.severity == "warning"]
    lines: list[str] = []
    if errors:
        lines.append(f"Found {len(errors)} keybinding {plural(len(errors), 'error')}:")
        lines.extend(format_warning(e) for e in errors)
    if warns:
        if lines:
            lines.append("")
        lines.append(f"Found {len(warns)} keybinding {plural(len(warns), 'warning')}:")
        lines.extend(format_warning(w) for w in warns)
    return "\n".join(lines)


def is_valid_shortcut(shortcut: str) -> tuple[bool, str | None]:
    """Lightweight shortcut string check (non-reserved)."""
    if not shortcut:
        return False, "Shortcut cannot be empty"
    chord = parse_chord(shortcut)
    if not chord:
        return False, "Invalid shortcut format"
    for ks in chord:
        if not ks.key and not any((ks.ctrl, ks.alt, ks.shift, ks.meta, ks.super_key)):
            return False, "Each keystroke must have a key"
    return True, None


_SIMPLE_RESERVED = (
    "ctrl+c",
    "ctrl+z",
    "ctrl+d",
    "ctrl+\\",
    "ctrl+s",
    "ctrl+q",
)


def validate_keybinding(
    action: str,
    shortcut: str,
    *,
    allow_reserved: bool = False,
) -> tuple[bool, str | None]:
    """Validate a single action + shortcut pair."""
    if not action:
        return False, "Action name is required"
    ok, err = is_valid_shortcut(shortcut)
    if not ok:
        return False, err
    if not allow_reserved and normalize_key_for_comparison(shortcut) in {
        normalize_key_for_comparison(x) for x in _SIMPLE_RESERVED
    }:
        return False, f"Shortcut '{shortcut}' may be reserved"
    return True, None
