"""Migrated from: commands/statusline.tsx"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

STATUSLINE_COMMAND = CommandSpec(
    type="prompt",
    name="statusline",
    description="Set up Claude Code's status line UI",
    content_length=0,
    progress_message="setting up statusLine",
    allowed_tools=(
        "Agent",
        "Read(~/**)",
        "Edit(~/.claude/settings.json)",
    ),
    supports_non_interactive=False,
    load_symbol="claude_code.commands.statusline.prompt_builder",
)

__all__ = ["STATUSLINE_COMMAND"]
