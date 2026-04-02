"""
Buddy type definitions.

Migrated from: buddy/types.ts
"""

from dataclasses import dataclass
from typing import Literal

# Species types
SPECIES = ("duck", "cat", "dog", "rabbit", "hamster", "owl", "fox")

# Hat types
HATS = ("none", "crown", "tophat", "beret", "cap", "wizard", "party")

# Eye types
EYES = ("normal", "happy", "sleepy", "excited", "wink", "cool", "hearts")

# Rarity levels
RARITIES = ("common", "uncommon", "rare", "epic", "legendary")
Rarity = Literal["common", "uncommon", "rare", "epic", "legendary"]

# Rarity weights for generation
RARITY_WEIGHTS: dict[str, float] = {
    "common": 50,
    "uncommon": 30,
    "rare": 15,
    "epic": 4,
    "legendary": 1,
}

# Stat names
STAT_NAMES = ("strength", "speed", "wit", "charm", "luck")
StatName = Literal["strength", "speed", "wit", "charm", "luck"]


@dataclass
class CompanionBones:
    """Base companion structure without stats."""

    species: str
    hat: str
    eyes: str
    rarity: Rarity
    name: str


@dataclass
class Companion(CompanionBones):
    """Full companion with stats."""

    stats: dict[str, int]
    level: int = 1
    xp: int = 0

    def total_stats(self) -> int:
        """Get total of all stats."""
        return sum(self.stats.values())

    def highest_stat(self) -> tuple[str, int]:
        """Get the highest stat name and value."""
        best = max(self.stats.items(), key=lambda x: x[1])
        return best

    def is_legendary(self) -> bool:
        """Check if companion is legendary rarity."""
        return self.rarity == "legendary"
