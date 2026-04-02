"""
Notification service.

Provides functions for sending notifications to users.

Migrated from: services/notifier.ts (157 lines)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol


@dataclass
class NotificationOptions:
    """Options for a notification."""

    message: str
    title: str | None = None
    notification_type: str = ""


class TerminalNotification(Protocol):
    """Protocol for terminal notification methods."""

    def notify_iterm2(self, opts: NotificationOptions) -> None:
        """Send an iTerm2 notification."""
        ...

    def notify_bell(self) -> None:
        """Send a terminal bell."""
        ...

    def notify_kitty(
        self,
        opts: NotificationOptions,
        *,
        title: str,
        id: int,
    ) -> None:
        """Send a Kitty notification."""
        ...

    def notify_ghostty(
        self,
        opts: NotificationOptions,
        *,
        title: str,
    ) -> None:
        """Send a Ghostty notification."""
        ...


DEFAULT_TITLE = "Claude Code"


async def send_notification(
    notif: NotificationOptions,
    terminal: TerminalNotification,
    preferred_channel: str = "auto",
) -> str:
    """
    Send a notification.

    Args:
        notif: The notification options.
        terminal: The terminal notification handler.
        preferred_channel: The preferred notification channel.

    Returns:
        The method used to send the notification.
    """
    return await _send_to_channel(preferred_channel, notif, terminal)


async def _send_to_channel(
    channel: str,
    opts: NotificationOptions,
    terminal: TerminalNotification,
) -> str:
    """Send notification to the specified channel."""
    title = opts.title or DEFAULT_TITLE

    try:
        if channel == "auto":
            return await _send_auto(opts, terminal)
        elif channel == "iterm2":
            terminal.notify_iterm2(opts)
            return "iterm2"
        elif channel == "iterm2_with_bell":
            terminal.notify_iterm2(opts)
            terminal.notify_bell()
            return "iterm2_with_bell"
        elif channel == "kitty":
            terminal.notify_kitty(opts, title=title, id=_generate_kitty_id())
            return "kitty"
        elif channel == "ghostty":
            terminal.notify_ghostty(opts, title=title)
            return "ghostty"
        elif channel == "terminal_bell":
            terminal.notify_bell()
            return "terminal_bell"
        elif channel == "notifications_disabled":
            return "disabled"
        else:
            return "none"
    except Exception:
        return "error"


async def _send_auto(
    opts: NotificationOptions,
    terminal: TerminalNotification,
) -> str:
    """Auto-detect and send to the best available channel."""
    import os

    title = opts.title or DEFAULT_TITLE
    term = os.environ.get("TERM_PROGRAM", "")

    if term == "Apple_Terminal":
        terminal.notify_bell()
        return "terminal_bell"
    elif term == "iTerm.app":
        terminal.notify_iterm2(opts)
        return "iterm2"
    elif term == "kitty":
        terminal.notify_kitty(opts, title=title, id=_generate_kitty_id())
        return "kitty"
    elif term == "ghostty":
        terminal.notify_ghostty(opts, title=title)
        return "ghostty"
    else:
        return "no_method_available"


def _generate_kitty_id() -> int:
    """Generate a random Kitty notification ID."""
    return random.randint(0, 9999)
