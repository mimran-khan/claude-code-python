"""
Memory types.

Migrated from: utils/memory/types.ts
"""

import os
from typing import Literal

# Base memory types
_BASE_MEMORY_TYPES = ("User", "Project", "Local", "Managed", "AutoMem")

# Check if team memory feature is enabled
_TEAM_MEM_ENABLED = os.environ.get("TEAMMEM", "").lower() in ("1", "true")

# All memory type values
MEMORY_TYPE_VALUES: tuple[str, ...] = _BASE_MEMORY_TYPES + ("TeamMem",) if _TEAM_MEM_ENABLED else _BASE_MEMORY_TYPES

# Memory type literal
MemoryType = Literal["User", "Project", "Local", "Managed", "AutoMem", "TeamMem"]


def is_valid_memory_type(value: str) -> bool:
    """Check if a value is a valid memory type."""
    return value in MEMORY_TYPE_VALUES


def get_memory_priority(memory_type: MemoryType) -> int:
    """Get priority order for a memory type.

    Lower number = higher priority.
    """
    priorities = {
        "User": 1,
        "Project": 2,
        "Local": 3,
        "TeamMem": 4,
        "Managed": 5,
        "AutoMem": 6,
    }
    return priorities.get(memory_type, 99)
