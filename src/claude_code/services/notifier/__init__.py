"""
Notification Service.

Sends notifications to the user via various channels.
"""

from .notifier import (
    NotificationChannel,
    NotificationOptions,
    get_available_channels,
    send_notification,
)

__all__ = [
    "NotificationOptions",
    "NotificationChannel",
    "send_notification",
    "get_available_channels",
]
