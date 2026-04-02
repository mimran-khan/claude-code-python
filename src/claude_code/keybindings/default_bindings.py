"""
Default keybinding blocks (merged with user keybindings.json).

Migrated from: keybindings/defaultBindings.ts
"""

from __future__ import annotations

from .features import feature
from .platform import get_platform, supports_terminal_vt_mode
from .types import KeybindingBlock


def _image_paste_key() -> str:
    return "alt+v" if get_platform() == "windows" else "ctrl+v"


def _mode_cycle_key() -> str:
    return "shift+tab" if supports_terminal_vt_mode() else "meta+m"


def get_default_binding_blocks() -> list[KeybindingBlock]:
    """Build default blocks; optional sections depend on :func:`features.feature`."""
    mode_cycle = _mode_cycle_key()
    image_paste = _image_paste_key()

    global_bindings: dict[str, str | None] = {
        "ctrl+c": "app:interrupt",
        "ctrl+d": "app:exit",
        "ctrl+l": "app:redraw",
        "ctrl+t": "app:toggleTodos",
        "ctrl+o": "app:toggleTranscript",
        "ctrl+shift+o": "app:toggleTeammatePreview",
        "ctrl+r": "history:search",
    }
    if feature("KAIROS") or feature("KAIROS_BRIEF"):
        global_bindings["ctrl+shift+b"] = "app:toggleBrief"
    if feature("QUICK_SEARCH"):
        global_bindings["ctrl+shift+f"] = "app:globalSearch"
        global_bindings["cmd+shift+f"] = "app:globalSearch"
        global_bindings["ctrl+shift+p"] = "app:quickOpen"
        global_bindings["cmd+shift+p"] = "app:quickOpen"
    if feature("TERMINAL_PANEL"):
        global_bindings["meta+j"] = "app:toggleTerminal"

    chat_bindings: dict[str, str | None] = {
        "escape": "chat:cancel",
        "ctrl+x ctrl+k": "chat:killAgents",
        mode_cycle: "chat:cycleMode",
        "meta+p": "chat:modelPicker",
        "meta+o": "chat:fastMode",
        "meta+t": "chat:thinkingToggle",
        "enter": "chat:submit",
        "up": "history:previous",
        "down": "history:next",
        "ctrl+_": "chat:undo",
        "ctrl+shift+-": "chat:undo",
        "ctrl+x ctrl+e": "chat:externalEditor",
        "ctrl+g": "chat:externalEditor",
        "ctrl+s": "chat:stash",
        image_paste: "chat:imagePaste",
    }
    if feature("MESSAGE_ACTIONS"):
        chat_bindings["shift+up"] = "chat:messageActions"
    if feature("VOICE_MODE"):
        chat_bindings["space"] = "voice:pushToTalk"

    blocks: list[KeybindingBlock] = [
        KeybindingBlock(context="Global", bindings=global_bindings),
        KeybindingBlock(context="Chat", bindings=chat_bindings),
        KeybindingBlock(
            context="Autocomplete",
            bindings={
                "tab": "autocomplete:accept",
                "escape": "autocomplete:dismiss",
                "up": "autocomplete:previous",
                "down": "autocomplete:next",
            },
        ),
        KeybindingBlock(
            context="Settings",
            bindings={
                "escape": "confirm:no",
                "up": "select:previous",
                "down": "select:next",
                "k": "select:previous",
                "j": "select:next",
                "ctrl+p": "select:previous",
                "ctrl+n": "select:next",
                "space": "select:accept",
                "enter": "settings:close",
                "/": "settings:search",
                "r": "settings:retry",
            },
        ),
        KeybindingBlock(
            context="Confirmation",
            bindings={
                "y": "confirm:yes",
                "n": "confirm:no",
                "enter": "confirm:yes",
                "escape": "confirm:no",
                "up": "confirm:previous",
                "down": "confirm:next",
                "tab": "confirm:nextField",
                "space": "confirm:toggle",
                "shift+tab": "confirm:cycleMode",
                "ctrl+e": "confirm:toggleExplanation",
                "ctrl+d": "permission:toggleDebug",
            },
        ),
        KeybindingBlock(
            context="Tabs",
            bindings={
                "tab": "tabs:next",
                "shift+tab": "tabs:previous",
                "right": "tabs:next",
                "left": "tabs:previous",
            },
        ),
        KeybindingBlock(
            context="Transcript",
            bindings={
                "ctrl+e": "transcript:toggleShowAll",
                "ctrl+c": "transcript:exit",
                "escape": "transcript:exit",
                "q": "transcript:exit",
            },
        ),
        KeybindingBlock(
            context="HistorySearch",
            bindings={
                "ctrl+r": "historySearch:next",
                "escape": "historySearch:accept",
                "tab": "historySearch:accept",
                "ctrl+c": "historySearch:cancel",
                "enter": "historySearch:execute",
            },
        ),
        KeybindingBlock(
            context="Task",
            bindings={"ctrl+b": "task:background"},
        ),
        KeybindingBlock(
            context="ThemePicker",
            bindings={"ctrl+t": "theme:toggleSyntaxHighlighting"},
        ),
        KeybindingBlock(
            context="Scroll",
            bindings={
                "pageup": "scroll:pageUp",
                "pagedown": "scroll:pageDown",
                "wheelup": "scroll:lineUp",
                "wheeldown": "scroll:lineDown",
                "ctrl+home": "scroll:top",
                "ctrl+end": "scroll:bottom",
                "ctrl+shift+c": "selection:copy",
                "cmd+c": "selection:copy",
            },
        ),
        KeybindingBlock(
            context="Help",
            bindings={"escape": "help:dismiss"},
        ),
        KeybindingBlock(
            context="Attachments",
            bindings={
                "right": "attachments:next",
                "left": "attachments:previous",
                "backspace": "attachments:remove",
                "delete": "attachments:remove",
                "down": "attachments:exit",
                "escape": "attachments:exit",
            },
        ),
        KeybindingBlock(
            context="Footer",
            bindings={
                "up": "footer:up",
                "ctrl+p": "footer:up",
                "down": "footer:down",
                "ctrl+n": "footer:down",
                "right": "footer:next",
                "left": "footer:previous",
                "enter": "footer:openSelected",
                "escape": "footer:clearSelection",
            },
        ),
        KeybindingBlock(
            context="MessageSelector",
            bindings={
                "up": "messageSelector:up",
                "down": "messageSelector:down",
                "k": "messageSelector:up",
                "j": "messageSelector:down",
                "ctrl+p": "messageSelector:up",
                "ctrl+n": "messageSelector:down",
                "ctrl+up": "messageSelector:top",
                "shift+up": "messageSelector:top",
                "meta+up": "messageSelector:top",
                "shift+k": "messageSelector:top",
                "ctrl+down": "messageSelector:bottom",
                "shift+down": "messageSelector:bottom",
                "meta+down": "messageSelector:bottom",
                "shift+j": "messageSelector:bottom",
                "enter": "messageSelector:select",
            },
        ),
        KeybindingBlock(
            context="DiffDialog",
            bindings={
                "escape": "diff:dismiss",
                "left": "diff:previousSource",
                "right": "diff:nextSource",
                "up": "diff:previousFile",
                "down": "diff:nextFile",
                "enter": "diff:viewDetails",
            },
        ),
        KeybindingBlock(
            context="ModelPicker",
            bindings={
                "left": "modelPicker:decreaseEffort",
                "right": "modelPicker:increaseEffort",
            },
        ),
        KeybindingBlock(
            context="Select",
            bindings={
                "up": "select:previous",
                "down": "select:next",
                "j": "select:next",
                "k": "select:previous",
                "ctrl+n": "select:next",
                "ctrl+p": "select:previous",
                "enter": "select:accept",
                "escape": "select:cancel",
            },
        ),
        KeybindingBlock(
            context="Plugin",
            bindings={
                "space": "plugin:toggle",
                "i": "plugin:install",
            },
        ),
    ]

    if feature("MESSAGE_ACTIONS"):
        blocks.insert(
            -3,
            KeybindingBlock(
                context="MessageActions",
                bindings={
                    "up": "messageActions:prev",
                    "down": "messageActions:next",
                    "k": "messageActions:prev",
                    "j": "messageActions:next",
                    "meta+up": "messageActions:top",
                    "meta+down": "messageActions:bottom",
                    "super+up": "messageActions:top",
                    "super+down": "messageActions:bottom",
                    "shift+up": "messageActions:prevUser",
                    "shift+down": "messageActions:nextUser",
                    "escape": "messageActions:escape",
                    "ctrl+c": "messageActions:ctrlc",
                    "enter": "messageActions:enter",
                    "c": "messageActions:c",
                    "p": "messageActions:p",
                },
            ),
        )

    return blocks


# Module-level cache for callers expecting a constant tuple-like API
DEFAULT_BINDING_BLOCKS: list[KeybindingBlock] = get_default_binding_blocks()
