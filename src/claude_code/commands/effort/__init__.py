"""Migrated from: commands/effort/index.ts"""

from __future__ import annotations

from claude_code.commands._immediate import should_inference_config_command_be_immediate
from claude_code.commands.spec import CommandSpec

EFFORT_COMMAND = CommandSpec(
    type="local-jsx",
    name="effort",
    description="Set effort level for model usage",
    argument_hint="[low|medium|high|max|auto]",
    immediate_fn=should_inference_config_command_be_immediate,
    load_symbol="claude_code.commands.effort.ui",
)

__all__ = ["EFFORT_COMMAND"]
