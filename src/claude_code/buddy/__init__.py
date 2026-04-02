"""
Buddy companion system.

Migrated from: buddy/*.ts
"""

from .companion import (
    generate_companion,
    get_companion_for_user,
)
from .sprites import (
    get_sprite,
    render_companion,
)
from .types import (
    EYES,
    HATS,
    RARITIES,
    RARITY_WEIGHTS,
    SPECIES,
    STAT_NAMES,
    Companion,
    CompanionBones,
    Rarity,
    StatName,
)

__all__ = [
    # Types
    "Companion",
    "CompanionBones",
    "Rarity",
    "StatName",
    "SPECIES",
    "HATS",
    "EYES",
    "RARITIES",
    "RARITY_WEIGHTS",
    "STAT_NAMES",
    # Generation
    "generate_companion",
    "get_companion_for_user",
    # Sprites
    "get_sprite",
    "render_companion",
]
