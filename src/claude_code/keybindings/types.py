"""
Keybinding domain types.

Migrated from: keybindings/types.ts (inferred from usage across the module).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

# Context names used in keybindings.json and resolver
KeybindingContextName = Literal[
    "Global",
    "Chat",
    "Autocomplete",
    "Confirmation",
    "Help",
    "Transcript",
    "HistorySearch",
    "Task",
    "ThemePicker",
    "Settings",
    "Tabs",
    "Attachments",
    "Footer",
    "MessageSelector",
    "DiffDialog",
    "ModelPicker",
    "Select",
    "Plugin",
    "Scroll",
    "MessageActions",
]

DisplayPlatform = Literal["macos", "windows", "linux", "wsl", "unknown"]


@dataclass
class ParsedKeystroke:
    """Single step of a chord after parsing a keystroke string."""

    key: str = ""
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    meta: bool = False
    super_key: bool = False  # cmd / super / win (TS: super)


Chord = list[ParsedKeystroke]


@dataclass
class ParsedBinding:
    """Flattened binding: chord sequence, action, UI context."""

    chord: Chord
    action: str | None
    context: str


@dataclass
class KeybindingBlock:
    """One block in keybindings.json: context + keystroke -> action map."""

    context: str
    bindings: dict[str, str | None]


class ResolveResultMatch(TypedDict):
    type: Literal["match"]
    action: str


class ResolveResultNone(TypedDict):
    type: Literal["none"]


class ResolveResultUnbound(TypedDict):
    type: Literal["unbound"]


ResolveResult = ResolveResultMatch | ResolveResultNone | ResolveResultUnbound


class ChordResolveResultMatch(TypedDict):
    type: Literal["match"]
    action: str


class ChordResolveResultNone(TypedDict):
    type: Literal["none"]


class ChordResolveResultUnbound(TypedDict):
    type: Literal["unbound"]


class ChordResolveResultStarted(TypedDict):
    type: Literal["chord_started"]
    pending: list[ParsedKeystroke]


class ChordResolveResultCancelled(TypedDict):
    type: Literal["chord_cancelled"]


ChordResolveResult = (
    ChordResolveResultMatch
    | ChordResolveResultNone
    | ChordResolveResultUnbound
    | ChordResolveResultStarted
    | ChordResolveResultCancelled
)


@dataclass
class KeybindingWarning:
    """Validation or doctor warning for keybinding configuration."""

    type: Literal[
        "parse_error",
        "duplicate",
        "reserved",
        "invalid_context",
        "invalid_action",
    ]
    severity: Literal["error", "warning"]
    message: str
    key: str | None = None
    context: str | None = None
    action: str | None = None
    suggestion: str | None = None


@dataclass
class KeybindingsLoadResult:
    """Result of loading and merging default + user keybindings."""

    bindings: list[ParsedBinding]
    warnings: list[KeybindingWarning]


@dataclass
class ReservedShortcut:
    """Shortcut that is reserved by OS/terminal or non-rebindable in-app."""

    key: str
    reason: str
    severity: Literal["error", "warning"]
