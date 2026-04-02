"""Bundled /lorem-ipsum skill. Migrated from: skills/bundled/loremIpsum.ts"""

from __future__ import annotations

import os
import random

from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

ONE_TOKEN_WORDS = [
    "the",
    "a",
    "is",
    "are",
    "code",
    "test",
    "data",
    "file",
    "run",
    "time",
    "and",
    "or",
    "not",
    "with",
    "for",
    "from",
    "this",
    "that",
    "user",
    "system",
    "program",
    "value",
    "text",
    "line",
    "work",
    "make",
    "use",
    "set",
    "get",
    "go",
    "see",
    "know",
    "want",
    "need",
    "good",
    "new",
    "first",
    "last",
    "long",
    "great",
    "small",
    "large",
    "high",
    "right",
    "old",
    "young",
    "same",
    "other",
    "such",
    "only",
    "very",
    "just",
    "also",
    "well",
    "here",
    "there",
    "when",
    "where",
    "how",
    "why",
    "can",
    "will",
    "would",
    "should",
    "could",
    "may",
    "must",
]


def _generate_lorem_ipsum(target_tokens: int) -> str:
    tokens = 0
    result_parts: list[str] = []
    while tokens < target_tokens:
        sentence_length = 10 + random.randint(0, 10)
        words_in_sentence = 0
        for i in range(sentence_length):
            if tokens >= target_tokens:
                break
            word = random.choice(ONE_TOKEN_WORDS)
            result_parts.append(word)
            tokens += 1
            words_in_sentence += 1
            if i == sentence_length - 1 or tokens >= target_tokens:
                result_parts.append(". ")
            else:
                result_parts.append(" ")
        if words_in_sentence > 0 and random.random() < 0.2 and tokens < target_tokens:
            result_parts.append("\n\n")
    return "".join(result_parts).strip()


def register_lorem_ipsum_skill() -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        if args.strip():
            try:
                parsed = int(args.split()[0])
            except ValueError:
                parsed = -1
            if parsed <= 0:
                return [
                    {
                        "type": "text",
                        "text": "Invalid token count. Please provide a positive number (e.g., /lorem-ipsum 10000).",
                    },
                ]
        else:
            parsed = 10000

        target_tokens = parsed
        capped = min(target_tokens, 500_000)
        body = _generate_lorem_ipsum(capped)
        if capped < target_tokens:
            return [
                {
                    "type": "text",
                    "text": f"Requested {target_tokens} tokens, but capped at 500,000 for safety.\n\n{body}",
                },
            ]
        return [{"type": "text", "text": body}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="lorem-ipsum",
            description=("Generate filler text for long context testing. Specify token count as argument. Ant-only."),
            argument_hint="[token_count]",
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
