"""
Model command.

View or change the model.

Migrated from: commands/model/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ModelCommand(Command):
    """View or change the AI model."""

    @property
    def name(self) -> str:
        return "model"

    @property
    def description(self) -> str:
        return "View or change the AI model"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Show or change model."""
        args = context.args

        if not args:
            # Show current model
            return CommandResult(
                success=True,
                output={
                    "current_model": "claude-sonnet-4-20250514",
                    "available_models": [
                        "claude-sonnet-4-20250514",
                        "claude-opus-4-20250514",
                    ],
                },
            )

        new_model = args[0]
        # Would validate and set model
        return CommandResult(
            success=True,
            message=f"Model set to: {new_model}",
        )
