"""
Vim Mode State Machine Types.

This file defines the complete state machine for vim input handling.

State Diagram:
                              VimState
  ┌──────────────────────────────┬──────────────────────────────────────┐
  │  INSERT                      │  NORMAL                              │
  │  (tracks insertedText)       │  (CommandState machine)              │
  │                              │                                      │
  │                              │  idle ──┬─[d/c/y]──► operator        │
  │                              │         ├─[1-9]────► count           │
  │                              │         ├─[fFtT]───► find            │
  │                              │         ├─[g]──────► g               │
  │                              │         ├─[r]──────► replace         │
  │                              │         └─[><]─────► indent          │
  │                              │                                      │
  │                              │  operator ─┬─[motion]──► execute     │
  │                              │            ├─[0-9]────► operatorCount│
  │                              │            ├─[ia]─────► operatorTextObj
  │                              │            └─[fFtT]───► operatorFind │
  └──────────────────────────────┴──────────────────────────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# Core Types
Operator = Literal["delete", "change", "yank"]
FindType = Literal["f", "F", "t", "T"]
TextObjScope = Literal["inner", "around"]


# State Machine Types


@dataclass
class InsertState:
    """INSERT mode state."""

    mode: Literal["INSERT"] = "INSERT"
    inserted_text: str = ""


@dataclass
class IdleCommandState:
    """Idle state - waiting for first keystroke."""

    type: Literal["idle"] = "idle"


@dataclass
class CountCommandState:
    """Accumulating count digits."""

    type: Literal["count"] = "count"
    digits: str = ""


@dataclass
class OperatorCommandState:
    """Operator entered, waiting for motion."""

    type: Literal["operator"] = "operator"
    op: Operator = "delete"
    count: int = 1


@dataclass
class OperatorCountCommandState:
    """Operator with count being entered."""

    type: Literal["operatorCount"] = "operatorCount"
    op: Operator = "delete"
    count: int = 1
    digits: str = ""


@dataclass
class OperatorFindCommandState:
    """Operator with find motion pending."""

    type: Literal["operatorFind"] = "operatorFind"
    op: Operator = "delete"
    count: int = 1
    find: FindType = "f"


@dataclass
class OperatorTextObjCommandState:
    """Operator with text object pending."""

    type: Literal["operatorTextObj"] = "operatorTextObj"
    op: Operator = "delete"
    count: int = 1
    scope: TextObjScope = "inner"


@dataclass
class FindCommandState:
    """Find motion pending character."""

    type: Literal["find"] = "find"
    find: FindType = "f"
    count: int = 1


@dataclass
class GCommandState:
    """g prefix entered."""

    type: Literal["g"] = "g"
    count: int = 1


@dataclass
class OperatorGCommandState:
    """Operator with g prefix."""

    type: Literal["operatorG"] = "operatorG"
    op: Operator = "delete"
    count: int = 1


@dataclass
class ReplaceCommandState:
    """Replace command pending character."""

    type: Literal["replace"] = "replace"
    count: int = 1


@dataclass
class IndentCommandState:
    """Indent command."""

    type: Literal["indent"] = "indent"
    dir: Literal[">", "<"] = ">"
    count: int = 1


CommandState = (
    IdleCommandState
    | CountCommandState
    | OperatorCommandState
    | OperatorCountCommandState
    | OperatorFindCommandState
    | OperatorTextObjCommandState
    | FindCommandState
    | GCommandState
    | OperatorGCommandState
    | ReplaceCommandState
    | IndentCommandState
)


@dataclass
class NormalState:
    """NORMAL mode state."""

    mode: Literal["NORMAL"] = "NORMAL"
    command: CommandState = field(default_factory=IdleCommandState)


VimState = InsertState | NormalState


# Recorded changes for dot-repeat


@dataclass
class InsertChange:
    """Insert text change."""

    type: Literal["insert"] = "insert"
    text: str = ""


@dataclass
class OperatorChange:
    """Operator with motion change."""

    type: Literal["operator"] = "operator"
    op: Operator = "delete"
    motion: str = ""
    count: int = 1


@dataclass
class OperatorTextObjChange:
    """Operator with text object change."""

    type: Literal["operatorTextObj"] = "operatorTextObj"
    op: Operator = "delete"
    obj_type: str = ""
    scope: TextObjScope = "inner"
    count: int = 1


@dataclass
class OperatorFindChange:
    """Operator with find motion change."""

    type: Literal["operatorFind"] = "operatorFind"
    op: Operator = "delete"
    find: FindType = "f"
    char: str = ""
    count: int = 1


@dataclass
class ReplaceChange:
    """Replace character change."""

    type: Literal["replace"] = "replace"
    char: str = ""
    count: int = 1


@dataclass
class XChange:
    """Delete character change."""

    type: Literal["x"] = "x"
    count: int = 1


@dataclass
class ToggleCaseChange:
    """Toggle case change."""

    type: Literal["toggleCase"] = "toggleCase"
    count: int = 1


@dataclass
class IndentChange:
    """Indent change."""

    type: Literal["indent"] = "indent"
    dir: Literal[">", "<"] = ">"
    count: int = 1


@dataclass
class OpenLineChange:
    """Open line change."""

    type: Literal["openLine"] = "openLine"
    direction: Literal["above", "below"] = "below"


@dataclass
class JoinChange:
    """Join lines change."""

    type: Literal["join"] = "join"
    count: int = 1


RecordedChange = (
    InsertChange
    | OperatorChange
    | OperatorTextObjChange
    | OperatorFindChange
    | ReplaceChange
    | XChange
    | ToggleCaseChange
    | IndentChange
    | OpenLineChange
    | JoinChange
)


@dataclass
class LastFind:
    """Last find motion."""

    type: FindType
    char: str


@dataclass
class PersistentState:
    """Persistent state that survives across commands."""

    last_change: RecordedChange | None = None
    last_find: LastFind | None = None
    register: str = ""
    register_is_linewise: bool = False


# Key Groups
OPERATORS = {
    "d": "delete",
    "c": "change",
    "y": "yank",
}

SIMPLE_MOTIONS = frozenset(
    [
        "h",
        "l",
        "j",
        "k",  # Basic movement
        "w",
        "b",
        "e",
        "W",
        "B",
        "E",  # Word motions
        "0",
        "^",
        "$",  # Line positions
    ]
)

FIND_KEYS = frozenset(["f", "F", "t", "T"])

TEXT_OBJ_SCOPES = {
    "i": "inner",
    "a": "around",
}

TEXT_OBJ_TYPES = frozenset(
    [
        "w",
        "W",  # Word/WORD
        '"',
        "'",
        "`",  # Quotes
        "(",
        ")",
        "b",  # Parens
        "[",
        "]",  # Brackets
        "{",
        "}",
        "B",  # Braces
        "<",
        ">",  # Angle brackets
    ]
)

MAX_VIM_COUNT = 10000


# State Factories


def create_initial_vim_state() -> VimState:
    """Create the initial vim state."""
    return InsertState(inserted_text="")


def create_initial_persistent_state() -> PersistentState:
    """Create the initial persistent state."""
    return PersistentState()


def is_operator_key(key: str) -> bool:
    """Check if key is an operator."""
    return key in OPERATORS


def is_text_obj_scope_key(key: str) -> bool:
    """Check if key is a text object scope."""
    return key in TEXT_OBJ_SCOPES
