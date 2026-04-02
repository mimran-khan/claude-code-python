"""
Migrated from: commands/sandbox-toggle/index.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult


@dataclass
class SandboxStatusSnapshot:
    """Inputs for dynamic /sandbox description (mirrors SandboxManager calls)."""

    sandboxing_enabled: bool = False
    auto_allow_bash_if_sandboxed: bool = False
    unsandboxed_commands_allowed: bool = False
    settings_locked_by_policy: bool = False
    dependencies_ok: bool = True
    supported_platform: bool = True
    platform_in_enabled_list: bool = True


def sandbox_description(status: SandboxStatusSnapshot | None = None) -> str:
    s = status or SandboxStatusSnapshot()
    icon = "⚠" if not s.dependencies_ok else ("✓" if s.sandboxing_enabled else "○")
    status_text = "sandbox disabled"
    if s.sandboxing_enabled:
        status_text = "sandbox enabled (auto-allow)" if s.auto_allow_bash_if_sandboxed else "sandbox enabled"
        status_text += ", fallback allowed" if s.unsandboxed_commands_allowed else ""
    if s.settings_locked_by_policy:
        status_text += " (managed)"
    return f"{icon} {status_text} (⏎ to configure)"


def sandbox_hidden(status: SandboxStatusSnapshot | None = None) -> bool:
    s = status or SandboxStatusSnapshot()
    return not s.supported_platform or not s.platform_in_enabled_list


class SandboxCommand(Command):
    def __init__(self, status: SandboxStatusSnapshot | None = None) -> None:
        self._status = status

    @property
    def name(self) -> str:
        return "sandbox"

    @property
    def description(self) -> str:
        return sandbox_description(self._status)

    @property
    def hidden(self) -> bool:
        return sandbox_hidden(self._status)

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            output={
                "action": "load_jsx",
                "module": "sandbox-toggle",
                "immediate": True,
                "args": context.args,
            },
        )
