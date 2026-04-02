"""Migrated from: commands/doctor/index.ts"""

from __future__ import annotations

import os

from claude_code.commands.spec import CommandSpec


def _doctor_enabled() -> bool:
    return os.environ.get("DISABLE_DOCTOR_COMMAND", "").lower() not in ("1", "true", "yes")


DOCTOR_COMMAND = CommandSpec(
    type="local-jsx",
    name="doctor",
    description="Diagnose and verify your Claude Code installation and settings",
    is_enabled=_doctor_enabled,
    load_symbol="claude_code.commands.doctor.ui",
)

__all__ = ["DOCTOR_COMMAND"]
