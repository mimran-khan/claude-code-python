"""
Doctor command.

Check system health.

Migrated from: commands/doctor/index.ts
"""

from __future__ import annotations

import os
import shutil

from ..base import Command, CommandContext, CommandResult


class DoctorCommand(Command):
    """Check system health and dependencies."""

    @property
    def name(self) -> str:
        return "doctor"

    @property
    def description(self) -> str:
        return "Check system health and dependencies"

    async def execute(self, context: CommandContext) -> CommandResult:
        """Run health checks."""
        checks = []

        # Check Python version
        import sys

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append(
            {
                "name": "Python version",
                "status": "ok" if sys.version_info >= (3, 11) else "warn",
                "value": python_version,
                "message": "Python 3.11+ recommended" if sys.version_info < (3, 11) else None,
            }
        )

        # Check git
        git_path = shutil.which("git")
        checks.append(
            {
                "name": "Git",
                "status": "ok" if git_path else "error",
                "value": git_path or "Not found",
            }
        )

        # Check ripgrep
        rg_path = shutil.which("rg")
        checks.append(
            {
                "name": "Ripgrep",
                "status": "ok" if rg_path else "warn",
                "value": rg_path or "Not found",
                "message": "Install ripgrep for better search performance" if not rg_path else None,
            }
        )

        # Check API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        checks.append(
            {
                "name": "API Key",
                "status": "ok" if api_key else "error",
                "value": "Set" if api_key else "Not set",
                "message": "Set ANTHROPIC_API_KEY environment variable" if not api_key else None,
            }
        )

        all_ok = all(c["status"] == "ok" for c in checks)

        return CommandResult(
            success=all_ok,
            output={"checks": checks},
            message="All checks passed!" if all_ok else "Some issues found.",
        )
