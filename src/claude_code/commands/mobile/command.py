"""
Mobile QR / pairing command (stub).

Migrated from: commands/mobile/index.ts (see also :data:`~claude_code.commands.mobile.MOBILE_COMMAND`).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass(frozen=True)
class MobileMetadata:
    name: str = "mobile"
    description: str = "Show QR code for mobile app pairing (stub)."
    command_type: str = "local"


mobile_metadata = MobileMetadata()


class MobileCommand(Command):
    @property
    def name(self) -> str:
        return mobile_metadata.name

    @property
    def description(self) -> str:
        return mobile_metadata.description

    async def execute(self, context: CommandContext) -> CommandResult:
        _ = context
        return CommandResult(
            success=True,
            message="Mobile pairing is not wired in the Python port yet.",
        )
