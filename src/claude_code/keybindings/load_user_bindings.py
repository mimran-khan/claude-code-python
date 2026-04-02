"""
Load and merge user ``keybindings.json`` with defaults.

Migrated from: keybindings/loadUserBindings.ts (file watcher omitted; use reload API).
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..utils.config_utils import get_claude_config_dir
from .default_bindings import get_default_binding_blocks
from .parser import parse_bindings
from .types import KeybindingBlock, KeybindingsLoadResult, ParsedBinding
from .validation import check_duplicate_keys_in_json, validate_bindings

# Optional telemetry hook: set to a callable(action, context, fallback, reason)
_fallback_logger: Callable[[str, str, str, str], None] | None = None


def set_keybinding_fallback_logger(
    fn: Callable[[str, str, str, str], None] | None,
) -> None:
    """Register a callback for shortcut display fallbacks (analytics parity)."""
    global _fallback_logger
    _fallback_logger = fn


def log_keybinding_fallback(
    action: str,
    context: str,
    fallback: str,
    reason: str,
) -> None:
    """Invoke the optional fallback logger if registered."""
    if _fallback_logger is not None:
        _fallback_logger(action, context, fallback, reason)


def is_keybinding_customization_enabled() -> bool:
    """
    Whether user keybindings.json is honored.

    TypeScript gates on GrowthBook; Python defaults to enabled, disable with
    ``CLAUDE_CODE_KEYBINDING_CUSTOMIZATION=0``.
    """
    v = os.environ.get("CLAUDE_CODE_KEYBINDING_CUSTOMIZATION", "1").lower()
    return v not in ("0", "false", "no", "off")


def get_keybindings_path() -> str:
    """Path to ``~/.claude/keybindings.json`` (or ``CLAUDE_CONFIG_DIR``)."""
    return str(Path(get_claude_config_dir()) / "keybindings.json")


def _default_parsed() -> list[ParsedBinding]:
    return parse_bindings(get_default_binding_blocks())


def _is_keybinding_block(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    return isinstance(obj.get("context"), str) and isinstance(obj.get("bindings"), dict)


def _is_keybinding_block_array(arr: Any) -> bool:
    return isinstance(arr, list) and all(_is_keybinding_block(x) for x in arr)


def _blocks_from_json(parsed: Any) -> tuple[list[KeybindingBlock] | None, str | None]:
    """Return user blocks or (None, error hint)."""
    if not isinstance(parsed, dict) or "bindings" not in parsed:
        return None, 'keybindings.json must have a "bindings" array'
    raw_blocks = parsed["bindings"]
    if not _is_keybinding_block_array(raw_blocks):
        if not isinstance(raw_blocks, list):
            return None, '"bindings" must be an array'
        return None, "keybindings.json contains invalid block structure"
    blocks: list[KeybindingBlock] = []
    for b in raw_blocks:
        blocks.append(
            KeybindingBlock(
                context=str(b["context"]),
                bindings={str(k): v for k, v in b["bindings"].items()},
            )
        )
    return blocks, None


_cached_bindings: list[ParsedBinding] | None = None
_cached_warnings: list[Any] = []


def load_keybindings() -> KeybindingsLoadResult:
    """Load merged bindings (async API shape; implementation is synchronous I/O)."""
    global _cached_bindings, _cached_warnings
    defaults = _default_parsed()

    if not is_keybinding_customization_enabled():
        _cached_bindings = defaults
        _cached_warnings = []
        return KeybindingsLoadResult(bindings=defaults, warnings=[])

    path = get_keybindings_path()
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        _cached_bindings = defaults
        _cached_warnings = []
        return KeybindingsLoadResult(bindings=defaults, warnings=[])
    except OSError as e:
        _cached_bindings = defaults
        w = validation_warning_parse(f"Failed to read keybindings.json: {e}")
        _cached_warnings = [w]
        return KeybindingsLoadResult(bindings=defaults, warnings=[w])

    try:
        parsed: Any = json.loads(content)
    except json.JSONDecodeError as e:
        _cached_bindings = defaults
        w = validation_warning_parse(f"Failed to parse keybindings.json: {e}")
        _cached_warnings = [w]
        return KeybindingsLoadResult(bindings=defaults, warnings=[w])

    user_blocks, err = _blocks_from_json(parsed)
    if user_blocks is None:
        _cached_bindings = defaults
        w = validation_warning_parse(
            err or "invalid format",
            suggestion='Use format: { "bindings": [ ... ] }',
        )
        _cached_warnings = [w]
        return KeybindingsLoadResult(bindings=defaults, warnings=[w])

    user_parsed = parse_bindings(user_blocks)
    merged = [*defaults, *user_parsed]

    dup = check_duplicate_keys_in_json(content)
    val = validate_bindings(user_blocks, merged)
    warnings = [*dup, *val]
    _cached_bindings = merged
    _cached_warnings = warnings
    return KeybindingsLoadResult(bindings=merged, warnings=warnings)


def validation_warning_parse(message: str, suggestion: str | None = None):
    from .types import KeybindingWarning

    return KeybindingWarning(
        type="parse_error",
        severity="error",
        message=message,
        suggestion=suggestion,
    )


def load_keybindings_sync() -> list[ParsedBinding]:
    """Return merged bindings, using cache after first successful load."""
    global _cached_bindings
    if _cached_bindings is not None:
        return _cached_bindings
    return load_keybindings().bindings


def load_keybindings_sync_with_warnings() -> KeybindingsLoadResult:
    if _cached_bindings is None:
        load_keybindings()
    return KeybindingsLoadResult(bindings=_cached_bindings or [], warnings=list(_cached_warnings))


def get_cached_keybinding_warnings() -> list:
    return list(_cached_warnings)


def reset_keybinding_loader_for_testing() -> None:
    global _cached_bindings, _cached_warnings
    _cached_bindings = None
    _cached_warnings = []


async def initialize_keybinding_watcher() -> None:
    """Placeholder: TypeScript uses chokidar; call ``load_keybindings()`` to refresh."""
    return None


def dispose_keybinding_watcher() -> None:
    """No-op (no background watcher in Python port)."""
    return None
