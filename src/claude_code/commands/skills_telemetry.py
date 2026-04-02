"""
Hook for telemetry skill listing (override via ``set_skill_commands_provider``).

Wiring: assign ``get_skill_tool_commands_for_telemetry`` when command discovery exists.
"""

from __future__ import annotations

from typing import Any


async def get_skill_tool_commands_for_telemetry(_cwd: str) -> list[Any]:
    """Default no-op until skill discovery is connected."""
    return []
