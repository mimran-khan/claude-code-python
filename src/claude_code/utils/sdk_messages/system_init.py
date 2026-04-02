"""system/init message builder for SDK sessions (stub)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SystemInitInputs:
    """Inputs for building a system init payload."""

    pass


def build_system_init_message(_inputs: SystemInitInputs) -> dict[str, Any]:
    return {"type": "system_init", "version": 1}


def sdk_compat_tool_name(name: str) -> str:
    return name
