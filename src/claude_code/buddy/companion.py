"""
Companion generation.

Migrated from: buddy/companion.ts
"""

import hashlib

from .types import (
    EYES,
    HATS,
    RARITIES,
    RARITY_WEIGHTS,
    SPECIES,
    STAT_NAMES,
    Companion,
    Rarity,
)


def mulberry32(seed: int) -> callable:
    """Mulberry32 PRNG - tiny seeded random generator."""
    a = seed & 0xFFFFFFFF

    def rng() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | t))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng


def hash_string(s: str) -> int:
    """Hash a string to an integer."""
    h = hashlib.md5(s.encode()).hexdigest()
    return int(h[:8], 16)


def pick(rng: callable, items: tuple) -> str:
    """Pick a random item from a tuple."""
    return items[int(rng() * len(items))]


def roll_rarity(rng: callable) -> Rarity:
    """Roll for a rarity level."""
    total = sum(RARITY_WEIGHTS.values())
    roll = rng() * total

    for rarity in RARITIES:
        roll -= RARITY_WEIGHTS[rarity]
        if roll < 0:
            return rarity

    return "common"


RARITY_FLOOR: dict[str, int] = {
    "common": 5,
    "uncommon": 15,
    "rare": 25,
    "epic": 35,
    "legendary": 50,
}


def roll_stats(rng: callable, rarity: Rarity) -> dict[str, int]:
    """Roll stats for a companion.

    One peak stat, one dump stat, rest scattered.
    Rarity bumps the floor.
    """
    floor = RARITY_FLOOR[rarity]
    peak = pick(rng, STAT_NAMES)

    dump = pick(rng, STAT_NAMES)
    while dump == peak:
        dump = pick(rng, STAT_NAMES)

    stats: dict[str, int] = {}
    for name in STAT_NAMES:
        if name == peak:
            stats[name] = min(100, floor + 50 + int(rng() * 30))
        elif name == dump:
            stats[name] = max(1, floor - 10 + int(rng() * 15))
        else:
            stats[name] = floor + int(rng() * 40)

    return stats


def generate_name(rng: callable, species: str) -> str:
    """Generate a name for a companion."""
    prefixes = ("Sir", "Lord", "Lady", "Captain", "Professor", "Dr.", "Count", "Baron")
    suffixes = ("the Bold", "the Wise", "the Quick", "III", "Jr.", "the Great")

    base_names = {
        "duck": ("Quackers", "Waddles", "Ducky", "Mallard", "Drake"),
        "cat": ("Whiskers", "Mittens", "Shadow", "Luna", "Felix"),
        "dog": ("Buddy", "Max", "Spot", "Rex", "Fido"),
        "rabbit": ("Hopper", "Bunny", "Thumper", "Cotton", "Clover"),
        "hamster": ("Hammy", "Squeaky", "Nibbles", "Peanut", "Cheeks"),
        "owl": ("Hoot", "Owlbert", "Athena", "Sage", "Wisdom"),
        "fox": ("Foxy", "Rusty", "Swift", "Copper", "Ember"),
    }

    names = base_names.get(species, ("Buddy",))
    name = pick(rng, names)

    if rng() > 0.7:
        name = f"{pick(rng, prefixes)} {name}"
    if rng() > 0.8:
        name = f"{name} {pick(rng, suffixes)}"

    return name


def generate_companion(seed: str) -> Companion:
    """Generate a companion from a seed string."""
    rng = mulberry32(hash_string(seed))

    species = pick(rng, SPECIES)
    hat = pick(rng, HATS)
    eyes = pick(rng, EYES)
    rarity = roll_rarity(rng)
    stats = roll_stats(rng, rarity)
    name = generate_name(rng, species)

    return Companion(
        species=species,
        hat=hat,
        eyes=eyes,
        rarity=rarity,
        name=name,
        stats=stats,
    )


def get_companion_for_user(user_id: str | None = None) -> Companion:
    """Get or generate a companion for a user.

    Uses user ID as seed for consistent generation.
    """
    if user_id is None:
        import uuid

        user_id = str(uuid.uuid4())

    return generate_companion(user_id)
