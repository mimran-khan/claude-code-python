"""
Text input type definitions.

This module defines types for text input components used in the terminal UI.
These types support features like vim mode, autocomplete, and paste handling.

Migrated from: types/textInputTypes.ts (388 lines)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

if TYPE_CHECKING:
    pass


# ============================================================================
# Inline Ghost Text
# ============================================================================


@dataclass(frozen=True)
class InlineGhostText:
    """Inline ghost text for mid-input command autocomplete."""

    text: str  # The ghost text to display (e.g., "mit" for /commit)
    full_command: str  # The full command name (e.g., "commit")
    insert_position: int  # Position in the input where ghost text appears


# ============================================================================
# Image Dimensions
# ============================================================================


@dataclass(frozen=True)
class ImageDimensions:
    """Dimensions of an image."""

    width: int
    height: int


# ============================================================================
# Text Highlight
# ============================================================================


@dataclass(frozen=True)
class TextHighlight:
    """A text highlight for search results or other highlighting."""

    start: int
    end: int
    style: str = "highlight"


# ============================================================================
# Key Type
# ============================================================================


@dataclass
class Key:
    """Represents a key press event."""

    name: str = ""
    ctrl: bool = False
    meta: bool = False
    shift: bool = False
    sequence: str = ""


# ============================================================================
# Base Text Input Props
# ============================================================================


@dataclass
class BaseTextInputProps:
    """Base props for text input components."""

    value: str
    columns: int
    cursor_offset: int
    on_change: Callable[[str], None] | None = None
    on_change_cursor_offset: Callable[[int], None] | None = None
    on_history_up: Callable[[], None] | None = None
    on_history_down: Callable[[], None] | None = None
    placeholder: str | None = None
    multiline: bool = True
    focus: bool = True
    mask: str | None = None
    show_cursor: bool = True
    highlight_pasted_text: bool = False
    on_submit: Callable[[str], None] | None = None
    on_exit: Callable[[], None] | None = None
    on_exit_message: Callable[[bool, str | None], None] | None = None
    on_history_reset: Callable[[], None] | None = None
    on_clear_input: Callable[[], None] | None = None
    max_visible_lines: int | None = None
    on_image_paste: (
        Callable[
            [str, str | None, str | None, ImageDimensions | None, str | None],
            None,
        ]
        | None
    ) = None
    on_paste: Callable[[str], None] | None = None
    on_is_pasting_change: Callable[[bool], None] | None = None
    disable_cursor_movement_for_up_down_keys: bool = False
    disable_escape_double_press: bool = False
    argument_hint: str | None = None
    on_undo: Callable[[], None] | None = None
    dim_color: bool = False
    highlights: list[TextHighlight] | None = None
    placeholder_element: Any | None = None  # React node equivalent
    inline_ghost_text: InlineGhostText | None = None
    input_filter: Callable[[str, Key], str] | None = None


# ============================================================================
# Vim Mode
# ============================================================================

VimMode = Literal["INSERT", "NORMAL"]


@dataclass
class VimTextInputProps(BaseTextInputProps):
    """Extended props for VimTextInput."""

    initial_mode: VimMode = "INSERT"
    on_mode_change: Callable[[VimMode], None] | None = None


# ============================================================================
# Input State Types
# ============================================================================


@dataclass
class PasteState:
    """State for handling paste operations."""

    chunks: list[str] = field(default_factory=list)
    timeout_id: Any | None = None  # Timer handle


@dataclass
class BaseInputState:
    """Common properties for input hook results."""

    on_input: Callable[[str, Key], None] | None = None
    rendered_value: str = ""
    offset: int = 0
    set_offset: Callable[[int], None] | None = None
    cursor_line: int = 0  # 0-indexed within rendered text
    cursor_column: int = 0  # Display-width within current line
    viewport_char_offset: int = 0  # Where viewport starts
    viewport_char_end: int = 0  # Where viewport ends
    is_pasting: bool = False
    paste_state: PasteState | None = None


@dataclass
class TextInputState(BaseInputState):
    """State for text input."""

    pass


@dataclass
class VimInputState(BaseInputState):
    """State for vim input with mode."""

    mode: VimMode = "INSERT"
    set_mode: Callable[[VimMode], None] | None = None


# ============================================================================
# Prompt Input Mode
# ============================================================================

PromptInputMode = Literal[
    "bash",
    "prompt",
    "orphaned-permission",
    "task-notification",
]

EditablePromptInputMode = Literal["bash", "prompt", "orphaned-permission"]


# ============================================================================
# Queue Priority
# ============================================================================

QueuePriority = Literal["now", "next", "later"]
"""
Queue priority levels. Same semantics in both normal and proactive mode.

- `now`   — Interrupt and send immediately. Aborts any in-flight tool call.
- `next`  — Mid-turn drain. Let the current tool call finish, then send.
- `later` — End-of-turn drain. Wait for the current turn to finish.
"""


# ============================================================================
# Pasted Content
# ============================================================================


@dataclass
class ImagePastedContent:
    """An image that was pasted."""

    type: Literal["image"] = "image"
    id: int = 0
    content: str = ""  # Base64 encoded
    media_type: str = "image/png"
    filename: str | None = None
    dimensions: ImageDimensions | None = None
    source_path: str | None = None


@dataclass
class TextPastedContent:
    """Text that was pasted."""

    type: Literal["text"] = "text"
    id: int = 0
    content: str = ""


PastedContent = ImagePastedContent | TextPastedContent


def is_valid_image_paste(c: PastedContent) -> bool:
    """
    Type guard for image PastedContent with non-empty data.

    Empty-content images (e.g. from a 0-byte file drag) yield empty base64
    strings that the API rejects with `image cannot be empty`.
    """
    return isinstance(c, ImagePastedContent) and len(c.content) > 0


def get_image_paste_ids(
    pasted_contents: dict[int, PastedContent] | None,
) -> list[int] | None:
    """Extract image paste IDs from a QueuedCommand's pasted_contents."""
    if not pasted_contents:
        return None
    ids = [c.id for c in pasted_contents.values() if is_valid_image_paste(c)]
    return ids if ids else None


# ============================================================================
# Permission Result (minimal type for circular dependency avoidance)
# ============================================================================


@dataclass
class PermissionResultRef:
    """Reference to a permission result (avoids circular import)."""

    behavior: Literal["allow", "deny", "ask", "passthrough"] = "ask"


# ============================================================================
# Orphaned Permission
# ============================================================================


@dataclass
class OrphanedPermission:
    """An orphaned permission request."""

    permission_result: PermissionResultRef | None = None
    assistant_message: Any | None = None  # AssistantMessage


# ============================================================================
# Message Origin
# ============================================================================

MessageOrigin = Literal[
    "keyboard",
    "bridge",
    "ccr",
    "proactive",
    "teammate",
    "resource",
    "mcp",
    "channel",
]


# ============================================================================
# Queued Command
# ============================================================================


@dataclass
class QueuedCommand:
    """A command queued for execution."""

    value: str | list[dict[str, Any]]
    mode: PromptInputMode
    priority: QueuePriority | None = None
    uuid: str | None = None
    orphaned_permission: OrphanedPermission | None = None
    pasted_contents: dict[int, PastedContent] | None = None
    pre_expansion_value: str | None = None
    skip_slash_commands: bool = False
    bridge_origin: bool = False
    is_meta: bool = False
    origin: MessageOrigin | None = None
    workload: str | None = None
    agent_id: str | None = None  # AgentId
