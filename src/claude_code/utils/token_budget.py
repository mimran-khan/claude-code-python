"""
Natural-language token budget hints (+500k, use 2M tokens).

Migrated from: utils/tokenBudget.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHORTHAND_START_RE = re.compile(r"^\s*\+(\d+(?:\.\d+)?)\s*(k|m|b)\b", re.I)
_SHORTHAND_END_RE = re.compile(r"\s\+(\d+(?:\.\d+)?)\s*(k|m|b)\s*[.!?]?\s*$", re.I)
_VERBOSE_RE = re.compile(r"\b(?:use|spend)\s+(\d+(?:\.\d+)?)\s*(k|m|b)\s*tokens?\b", re.I)
_VERBOSE_RE_G = re.compile(_VERBOSE_RE.pattern, re.I)

_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def _parse_budget_match(value: str, suffix: str) -> float:
    return float(value) * _MULTIPLIERS[suffix.lower()]


def parse_token_budget(text: str) -> float | None:
    m = _SHORTHAND_START_RE.search(text)
    if m:
        return _parse_budget_match(m.group(1), m.group(2))
    m = _SHORTHAND_END_RE.search(text)
    if m:
        return _parse_budget_match(m.group(1), m.group(2))
    m = _VERBOSE_RE.search(text)
    if m:
        return _parse_budget_match(m.group(1), m.group(2))
    return None


@dataclass(frozen=True, slots=True)
class TokenBudgetSpan:
    start: int
    end: int


def find_token_budget_positions(text: str) -> list[TokenBudgetSpan]:
    positions: list[TokenBudgetSpan] = []
    start_match = _SHORTHAND_START_RE.search(text)
    if start_match:
        offset = start_match.start() + len(start_match.group(0)) - len(start_match.group(0).lstrip())
        positions.append(TokenBudgetSpan(start=offset, end=start_match.end()))
    end_match = _SHORTHAND_END_RE.search(text)
    if end_match:
        end_start = end_match.start() + 1
        already = any(p.start <= end_start < p.end for p in positions)
        if not already:
            positions.append(TokenBudgetSpan(start=end_start, end=end_match.end()))
    for m in _VERBOSE_RE_G.finditer(text):
        positions.append(TokenBudgetSpan(start=m.start(), end=m.end()))
    return positions


def get_budget_continuation_message(pct: int, turn_tokens: int, budget: int) -> str:
    def fmt(n: int) -> str:
        return f"{n:,}"

    return f"Stopped at {pct}% of token target ({fmt(turn_tokens)} / {fmt(budget)}). Keep working — do not summarize."
