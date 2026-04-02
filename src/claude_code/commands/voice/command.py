"""
Migrated from: commands/voice/index.ts
"""

from __future__ import annotations

from ..base import Command, CommandContext, CommandResult


def voice_is_enabled(growthbook_voice: bool = False) -> bool:
    return growthbook_voice


def voice_is_hidden(voice_mode_enabled: bool = True) -> bool:
    return not voice_mode_enabled


class VoiceCommand(Command):
    def __init__(
        self,
        *,
        growthbook_voice: bool = False,
        voice_mode_enabled: bool = True,
    ) -> None:
        self._growthbook_voice = growthbook_voice
        self._voice_mode_enabled = voice_mode_enabled

    @property
    def name(self) -> str:
        return "voice"

    @property
    def description(self) -> str:
        return "Toggle voice mode"

    @property
    def command_type(self):
        return "local"

    @property
    def hidden(self) -> bool:
        return voice_is_hidden(self._voice_mode_enabled)

    async def execute(self, context: CommandContext) -> CommandResult:
        _ = context
        if not voice_is_enabled(self._growthbook_voice):
            return CommandResult(success=False, message="Voice command disabled.")
        from .voice_call import call as voice_call

        result = await voice_call()
        return CommandResult(
            success=True,
            message=result.get("value", ""),
            output={"action": "voice_toggle", **result},
        )
