"""
Deep link handling.

URL protocol registration and parsing.

Migrated from: utils/deepLink/*.ts (6 files)
"""

from .handler import (
    handle_deep_link,
    register_protocol_handler,
)
from .launcher import (
    get_terminal_preference,
    launch_terminal_with_deep_link,
)
from .parser import (
    DEEP_LINK_PROTOCOL,
    DeepLinkAction,
    is_deep_link,
    parse_deep_link,
)

__all__ = [
    # Parser
    "DEEP_LINK_PROTOCOL",
    "DeepLinkAction",
    "parse_deep_link",
    "is_deep_link",
    # Handler
    "handle_deep_link",
    "register_protocol_handler",
    # Launcher
    "launch_terminal_with_deep_link",
    "get_terminal_preference",
]
