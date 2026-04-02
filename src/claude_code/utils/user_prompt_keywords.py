"""
Heuristic keyword matchers for user prompts (sentiment / continuation).

Migrated from: utils/userPromptKeywords.ts
"""

from __future__ import annotations

import re

_NEGATIVE_PATTERN = re.compile(
    r"\b(wtf|wth|ffs|omfg|shit(ty|tiest)?|dumbass|horrible|awful|"
    r"piss(ed|ing)? off|piece of (shit|crap|junk)|what the (fuck|hell)|"
    r"fucking? (broken|useless|terrible|awful|horrible)|fuck you|"
    r"screw (this|you)|so frustrating|this sucks|damn it)\b",
    re.IGNORECASE,
)

_KEEP_GOING_PATTERN = re.compile(r"\b(keep going|go on)\b", re.IGNORECASE)


def matches_negative_keyword(input_text: str) -> bool:
    return bool(_NEGATIVE_PATTERN.search(input_text.lower()))


def matches_keep_going_keyword(input_text: str) -> bool:
    lower = input_text.lower().strip()
    if lower == "continue":
        return True
    return bool(_KEEP_GOING_PATTERN.search(lower))
