"""Migrated from: commands/session/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _is_remote_mode() -> bool:
    return os.environ.get("CLAUDE_CODE_REMOTE_MODE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


SESSION_COMMAND = CommandSpec(
    type="local-jsx",
    name="session",
    description="Show remote session URL and QR code",
    aliases=("remote",),
    is_enabled=_is_remote_mode,
    is_hidden_fn=lambda: not _is_remote_mode(),
    load_symbol="claude_code.commands.session.ui",
)

__all__ = ["SESSION_COMMAND"]
