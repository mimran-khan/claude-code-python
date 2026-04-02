"""
Buddy sprite rendering.

Migrated from: buddy/sprites.ts
"""

from .types import Companion

# Simple ASCII art sprites for companions
SPECIES_SPRITES: dict[str, list[str]] = {
    "duck": [
        "  __  ",
        " (o<  ",
        " //\\  ",
        " V_/_ ",
    ],
    "cat": [
        " /\\_/\\",
        "( o.o )",
        " > ^ < ",
    ],
    "dog": [
        "  / \\__",
        " (    @\\___",
        " /         O",
        "/   (_____/ ",
    ],
    "rabbit": [
        " (\\(\\  ",
        " ( -.-)  ",
        ' o_(")(") ',
    ],
    "hamster": [
        "  _  _  ",
        " (o)(o) ",
        " (____) ",
    ],
    "owl": [
        " {o,o} ",
        " |)__) ",
        ' -"-"- ',
    ],
    "fox": [
        " /\\___/\\",
        "(  o o  )",
        " \\  Y  / ",
    ],
}


HAT_SPRITES: dict[str, str] = {
    "none": "",
    "crown": "  👑  ",
    "tophat": "  🎩  ",
    "beret": "  🧢  ",
    "cap": "  ⛑️  ",
    "wizard": "  🧙  ",
    "party": "  🎉  ",
}


RARITY_COLORS: dict[str, str] = {
    "common": "",
    "uncommon": "\033[32m",  # Green
    "rare": "\033[34m",  # Blue
    "epic": "\033[35m",  # Purple
    "legendary": "\033[33m",  # Gold
}


RESET_COLOR = "\033[0m"


def get_sprite(species: str) -> list[str]:
    """Get the sprite for a species."""
    return SPECIES_SPRITES.get(species, SPECIES_SPRITES["duck"])


def render_companion(companion: Companion, with_stats: bool = False) -> str:
    """Render a companion as ASCII art.

    Args:
        companion: The companion to render
        with_stats: Whether to include stats in output

    Returns:
        Rendered ASCII art string
    """
    lines = []

    # Add rarity color
    color = RARITY_COLORS.get(companion.rarity, "")

    # Add hat
    hat = HAT_SPRITES.get(companion.hat, "")
    if hat:
        lines.append(hat)

    # Add sprite
    sprite = get_sprite(companion.species)
    for line in sprite:
        lines.append(f"{color}{line}{RESET_COLOR}")

    # Add name and rarity
    lines.append("")
    lines.append(f"{companion.name}")
    lines.append(f"[{companion.rarity.upper()} {companion.species}]")

    # Add stats if requested
    if with_stats:
        lines.append("")
        lines.append("Stats:")
        for stat, value in companion.stats.items():
            bar = "█" * (value // 10) + "░" * (10 - value // 10)
            lines.append(f"  {stat:8s}: [{bar}] {value}")

    return "\n".join(lines)


def render_companion_compact(companion: Companion) -> str:
    """Render a compact version of the companion."""
    emoji = {
        "duck": "🦆",
        "cat": "🐱",
        "dog": "🐕",
        "rabbit": "🐰",
        "hamster": "🐹",
        "owl": "🦉",
        "fox": "🦊",
    }

    species_emoji = emoji.get(companion.species, "🐾")
    rarity_badge = companion.rarity[0].upper()

    return f"{species_emoji} {companion.name} [{rarity_badge}]"
