"""GitHub PR comments (moved-to-plugin style prompt)."""

from .command import PrCommentsCommand
from .moved_plugin import (
    MovedToPluginConfig,
    get_prompt_while_marketplace_is_private,
)

__all__ = [
    "MovedToPluginConfig",
    "PrCommentsCommand",
    "get_prompt_while_marketplace_is_private",
]
