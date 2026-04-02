"""Unit tests for ``claude_code.buddy.types`` (lightweight dataclasses)."""

from __future__ import annotations

from claude_code.buddy.types import (
    RARITY_WEIGHTS,
    SPECIES,
    Companion,
    CompanionBones,
)


def test_companion_total_stats_and_highest_stat() -> None:
    c = Companion(
        species="duck",
        hat="cap",
        eyes="happy",
        rarity="rare",
        name="Quack",
        stats={"strength": 2, "speed": 5, "wit": 3, "charm": 1, "luck": 4},
    )
    assert c.total_stats() == 15
    assert c.highest_stat() == ("speed", 5)


def test_companion_is_legendary_only_for_legendary_rarity() -> None:
    common = Companion(
        species="cat",
        hat="none",
        eyes="normal",
        rarity="common",
        name="Tabby",
        stats=dict.fromkeys(("strength", "speed", "wit", "charm", "luck"), 1),
    )
    legend = Companion(
        species="owl",
        hat="wizard",
        eyes="cool",
        rarity="legendary",
        name="Sage",
        stats=dict.fromkeys(("strength", "speed", "wit", "charm", "luck"), 10),
    )
    assert common.is_legendary() is False
    assert legend.is_legendary() is True


def test_companion_bones_is_separate_from_full_companion() -> None:
    bones = CompanionBones(
        species="fox",
        hat="beret",
        eyes="wink",
        rarity="uncommon",
        name="Rusty",
    )
    assert bones.species == "fox"


def test_constants_cover_expected_keys() -> None:
    assert "duck" in SPECIES
    assert sum(RARITY_WEIGHTS.values()) == 100
