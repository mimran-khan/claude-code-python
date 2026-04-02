"""
Init command.

Initialize Claude Code in a project.

Migrated from: commands/init.ts
"""

from __future__ import annotations

import os

from ..base import Command, CommandContext, CommandResult


class InitCommand(Command):
    """Initialize Claude Code in a project."""

    @property
    def name(self) -> str:
        return "init"

    @property
    def description(self) -> str:
        return "Initialize Claude Code in current project"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Initialize project."""
        cwd = context.cwd

        # Check for existing CLAUDE.md
        claude_md_path = os.path.join(cwd, "CLAUDE.md")
        if os.path.exists(claude_md_path):
            return CommandResult(
                success=False,
                error="CLAUDE.md already exists in this directory.",
            )

        # Check for existing .claude directory
        claude_dir = os.path.join(cwd, ".claude")
        if os.path.exists(claude_dir):
            return CommandResult(
                success=False,
                error=".claude directory already exists.",
            )

        # Create CLAUDE.md template
        template = """# Project Memory

## Project Overview
<!-- Describe your project here -->

## Important Files
<!-- List key files and their purposes -->

## Conventions
<!-- Document project conventions and patterns -->

## Instructions
<!-- Specific instructions for Claude -->
"""

        try:
            with open(claude_md_path, "w") as f:
                f.write(template)

            return CommandResult(
                success=True,
                message=f"Created CLAUDE.md in {cwd}",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create CLAUDE.md: {e}",
            )
