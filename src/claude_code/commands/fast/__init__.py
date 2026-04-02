"""Migrated from: commands/fast/index.ts"""

from __future__ import annotations

from claude_code.commands._fast_mode import FAST_MODE_MODEL_DISPLAY, is_fast_mode_enabled
from claude_code.commands._immediate import should_inference_config_command_be_immediate
from claude_code.commands.spec import CommandSpec


def _fast_description() -> str:
    return f"Toggle fast mode ({FAST_MODE_MODEL_DISPLAY} only)"


FAST_COMMAND = CommandSpec(
    type="local-jsx",
    name="fast",
    description="",
    description_fn=_fast_description,
    availability=("claude-ai", "console"),
    is_enabled=is_fast_mode_enabled,
    is_hidden_fn=lambda: not is_fast_mode_enabled(),
    argument_hint="[on|off]",
    immediate_fn=should_inference_config_command_be_immediate,
    load_symbol="claude_code.commands.fast.ui",
)

__all__ = ["FAST_COMMAND"]
