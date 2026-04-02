"""
Notification Service Implementation.

Sends notifications through various channels.
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

NotificationChannel = Literal[
    "auto",
    "iterm2",
    "iterm2_with_bell",
    "kitty",
    "ghostty",
    "terminal_bell",
    "notifications_disabled",
]


@dataclass
class NotificationOptions:
    """Notification options."""

    message: str
    title: str = "Claude Code"
    notification_type: str = "info"


# Terminal type detection
def get_terminal_type() -> str:
    """Get the current terminal type.

    Returns:
        Terminal identifier
    """
    term_program = os.getenv("TERM_PROGRAM", "")

    if term_program == "Apple_Terminal":
        return "Apple_Terminal"
    elif term_program == "iTerm.app":
        return "iTerm.app"
    elif "kitty" in os.getenv("TERM", "").lower():
        return "kitty"
    elif os.getenv("GHOSTTY_BIN_DIR"):
        return "ghostty"

    return "unknown"


def get_available_channels() -> list[NotificationChannel]:
    """Get available notification channels.

    Returns:
        List of available channels
    """
    channels: list[NotificationChannel] = ["auto", "terminal_bell", "notifications_disabled"]

    terminal = get_terminal_type()

    if terminal == "iTerm.app":
        channels.extend(["iterm2", "iterm2_with_bell"])
    elif terminal == "kitty":
        channels.append("kitty")
    elif terminal == "ghostty":
        channels.append("ghostty")

    return channels


async def send_notification(
    opts: NotificationOptions,
    *,
    channel: NotificationChannel = "auto",
    terminal_bell_fn: Callable[[], None] | None = None,
) -> str:
    """Send a notification.

    Args:
        opts: Notification options
        channel: Notification channel to use
        terminal_bell_fn: Optional function to ring terminal bell

    Returns:
        The method used to send the notification
    """
    if channel == "notifications_disabled":
        return "disabled"

    if channel == "auto":
        return await _send_auto(opts, terminal_bell_fn)

    if channel == "terminal_bell":
        if terminal_bell_fn:
            terminal_bell_fn()
        else:
            print("\a", end="", flush=True)
        return "terminal_bell"

    if channel in ("iterm2", "iterm2_with_bell"):
        _send_iterm2(opts)
        if channel == "iterm2_with_bell":
            print("\a", end="", flush=True)
        return channel

    if channel == "kitty":
        _send_kitty(opts)
        return "kitty"

    if channel == "ghostty":
        _send_ghostty(opts)
        return "ghostty"

    return "none"


async def _send_auto(
    opts: NotificationOptions,
    terminal_bell_fn: Callable[[], None] | None = None,
) -> str:
    """Send notification using auto-detection.

    Args:
        opts: Notification options
        terminal_bell_fn: Optional bell function

    Returns:
        Method used
    """
    terminal = get_terminal_type()

    if terminal == "iTerm.app":
        _send_iterm2(opts)
        return "iterm2"

    if terminal == "kitty":
        _send_kitty(opts)
        return "kitty"

    if terminal == "ghostty":
        _send_ghostty(opts)
        return "ghostty"

    if terminal == "Apple_Terminal":
        # Fall back to bell
        if terminal_bell_fn:
            terminal_bell_fn()
        else:
            print("\a", end="", flush=True)
        return "terminal_bell"

    return "no_method_available"


def _send_iterm2(opts: NotificationOptions) -> None:
    """Send iTerm2 notification.

    Args:
        opts: Notification options
    """
    # iTerm2 uses escape sequences for notifications
    # OSC 9; message ST
    message = opts.message.replace("\n", " ")
    print(f"\x1b]9;{message}\x07", end="", flush=True)


def _send_kitty(opts: NotificationOptions) -> None:
    """Send Kitty notification.

    Args:
        opts: Notification options
    """
    # Kitty uses a different escape sequence
    notification_id = random.randint(0, 10000)
    title = opts.title
    message = opts.message.replace("\n", " ")
    print(f"\x1b]99;i={notification_id}:d=0:p=title;{title}\x07", end="", flush=True)
    print(f"\x1b]99;i={notification_id}:d=1:p=body;{message}\x07", end="", flush=True)


def _send_ghostty(opts: NotificationOptions) -> None:
    """Send Ghostty notification.

    Args:
        opts: Notification options
    """
    # Ghostty uses OSC 777
    title = opts.title
    message = opts.message.replace("\n", " ")
    print(f"\x1b]777;notify;{title};{message}\x07", end="", flush=True)
