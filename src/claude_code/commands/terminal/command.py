"""
Migrated from: commands/terminalSetup/index.ts
"""

from __future__ import annotations

import os

from ..base import Command, CommandContext, CommandResult

NATIVE_CSIU_TERMINALS: dict[str, str] = {
    "ghostty": "Ghostty",
    "kitty": "Kitty",
    "iTerm.app": "iTerm2",
    "WezTerm": "WezTerm",
}


def native_csiu_terminals() -> dict[str, str]:
    return dict(NATIVE_CSIU_TERMINALS)


def terminal_setup_description(term_program: str | None = None) -> str:
    t = term_program or os.environ.get("TERM_PROGRAM")
    if t == "Apple_Terminal":
        return "Enable Option+Enter key binding for newlines and visual bell"
    return "Install Shift+Enter key binding for newlines"


def terminal_setup_hidden(term_program: str | None = None) -> bool:
    t = term_program or os.environ.get("TERM_PROGRAM")
    return t is not None and t in NATIVE_CSIU_TERMINALS


class TerminalSetupCommand(Command):
    def __init__(self, term_program: str | None = None) -> None:
        self._term = term_program

    @property
    def name(self) -> str:
        return "terminal-setup"

    @property
    def description(self) -> str:
        return terminal_setup_description(self._term)

    @property
    def hidden(self) -> bool:
        return terminal_setup_hidden(self._term)

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "terminalSetup"},
        )
