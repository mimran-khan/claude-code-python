"""
Resume command.

Resume a previous session.

Migrated from: commands/resume/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


class ResumeCommand(Command):
    """Resume a previous session."""

    @property
    def name(self) -> str:
        return "resume"

    @property
    def description(self) -> str:
        return "Resume a previous session"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Resume a session."""
        args = context.args

        if not args:
            # List available sessions
            return CommandResult(
                success=True,
                output={
                    "sessions": [],
                    "message": "No recent sessions available.",
                },
            )

        session_id = args[0]
        # Would load and resume session
        return CommandResult(
            success=True,
            message=f"Resuming session: {session_id}",
            output={"action": "resumeSession", "sessionId": session_id},
        )
