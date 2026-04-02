"""Tests for claude_code.keybindings."""

from __future__ import annotations

from claude_code.keybindings import (
    KeybindingBlock,
    KeyEventLike,
    check_duplicate_keys_in_json,
    get_binding_display_text,
    normalize_key_for_comparison,
    parse_bindings,
    parse_chord,
    resolve_key,
    resolve_key_with_chord_state,
)
from claude_code.keybindings.load_user_bindings import reset_keybinding_loader_for_testing
from claude_code.keybindings.parser import keystroke_equals, parse_keystroke
from claude_code.keybindings.resolver import chord_exactly_matches


def test_parse_chord_lone_space_is_space_key() -> None:
    chord = parse_chord(" ")
    assert len(chord) == 1
    assert chord[0].key == " "


def test_normalize_key_for_comparison_chord_steps() -> None:
    assert normalize_key_for_comparison("Ctrl+X ctrl+b") == normalize_key_for_comparison(
        "ctrl+x ctrl+b"
    )


def test_normalize_key_super_and_cmd_align_for_comparison() -> None:
    """``super`` / ``win`` normalize like ``cmd`` so bindings dedupe consistently."""
    assert normalize_key_for_comparison("super+up") == normalize_key_for_comparison("cmd+up")
    assert normalize_key_for_comparison("win+k") == normalize_key_for_comparison("command+k")


def test_resolve_key_ctrl_t_global() -> None:
    from claude_code.keybindings import DEFAULT_BINDINGS

    key = KeyEventLike(ctrl=True)
    r = resolve_key("t", key, ["Global"], DEFAULT_BINDINGS)
    assert r["type"] == "match"
    assert r["action"] == "app:toggleTodos"


def test_resolve_key_escape_meta_quirk() -> None:
    from claude_code.keybindings import DEFAULT_BINDINGS

    key = KeyEventLike(escape=True, meta=True)
    r = resolve_key("", key, ["Chat"], DEFAULT_BINDINGS)
    assert r["type"] == "match"
    assert r["action"] == "chat:cancel"


def test_chord_ctrl_x_ctrl_k() -> None:
    from claude_code.keybindings import DEFAULT_BINDINGS

    k1 = KeyEventLike(ctrl=True)
    r1 = resolve_key_with_chord_state("x", k1, ["Chat"], DEFAULT_BINDINGS, None)
    assert r1["type"] == "chord_started"
    pending = r1["pending"]
    k2 = KeyEventLike(ctrl=True)
    r2 = resolve_key_with_chord_state("k", k2, ["Chat"], DEFAULT_BINDINGS, pending)
    assert r2["type"] == "match"
    assert r2["action"] == "chat:killAgents"


def test_get_binding_display_text_last_wins() -> None:
    user = [
        KeybindingBlock(context="Global", bindings={"ctrl+t": "app:toggleTodos"}),
        KeybindingBlock(context="Global", bindings={"ctrl+y": "app:toggleTodos"}),
    ]
    merged = parse_bindings(user)
    text = get_binding_display_text("app:toggleTodos", "Global", merged)
    assert text == "ctrl+y"


def test_duplicate_keys_json_warning() -> None:
    # Python dict literals cannot express duplicate keys; use raw JSON text.
    raw = (
        '{"bindings": [{"context": "Chat", "bindings": {'
        '"enter": "chat:submit", "enter": "chat:cancel"}}]}'
    )
    w = check_duplicate_keys_in_json(raw)
    assert any(x.type == "duplicate" for x in w)


def test_keystroke_equals_alt_meta_collapsed() -> None:
    a = parse_keystroke("alt+k")
    b = parse_keystroke("meta+k")
    assert keystroke_equals(a, b)


def test_chord_exactly_matches() -> None:
    from claude_code.keybindings import ParsedBinding

    b = ParsedBinding(
        chord=parse_chord("ctrl+a"),
        action="test:action",
        context="Global",
    )
    assert chord_exactly_matches(parse_chord("ctrl+a"), b)


def teardown_module() -> None:
    reset_keybinding_loader_for_testing()
