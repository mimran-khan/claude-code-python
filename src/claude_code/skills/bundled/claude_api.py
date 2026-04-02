"""Bundled /claude-api skill. Migrated from: skills/bundled/claudeApi.ts"""

from __future__ import annotations

import os
import re
from typing import Literal

from ...bootstrap.state import get_cwd_state
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

DetectedLanguage = Literal["python", "typescript", "java", "go", "ruby", "csharp", "php", "curl"]

LANGUAGE_INDICATORS: dict[DetectedLanguage, list[str]] = {
    "python": [".py", "requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
    "typescript": [".ts", ".tsx", "tsconfig.json", "package.json"],
    "java": [".java", "pom.xml", "build.gradle"],
    "go": [".go", "go.mod"],
    "ruby": [".rb", "Gemfile"],
    "csharp": [".cs", ".csproj"],
    "php": [".php", "composer.json"],
    "curl": [],
}


def _detect_language() -> DetectedLanguage | None:
    cwd = get_cwd_state() or os.getcwd()
    try:
        entries = os.listdir(cwd)
    except OSError:
        return None
    for lang, indicators in LANGUAGE_INDICATORS.items():
        if not indicators:
            continue
        for indicator in indicators:
            if indicator.startswith("."):
                if any(e.endswith(indicator) for e in entries):
                    return lang
            elif indicator in entries:
                return lang
    return None


def _process_content(md: str, model_vars: dict[str, str]) -> str:
    out = md
    prev = None
    while prev != out:
        prev = out
        out = re.sub(r"<!--[\s\S]*?-->\n?", "", out)

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return model_vars.get(key, m.group(0))

    return re.sub(r"\{\{(\w+)\}\}", repl, out)


def _build_prompt(lang: DetectedLanguage | None, args: str) -> str:
    from . import claude_api_content as content

    clean = _process_content(content.SKILL_PROMPT, content.SKILL_MODEL_VARS)
    idx = clean.find("## Reading Guide")
    base = clean[:idx].rstrip() if idx != -1 else clean
    parts: list[str] = [base]
    lang_label = lang or "unknown"
    if content.SKILL_FILES:
        paths = [p for p in content.SKILL_FILES if lang is None or p.startswith(f"{lang}/") or p.startswith("shared/")]
        if lang is None:
            paths = list(content.SKILL_FILES.keys())
        docs = "\n\n".join(
            f'<doc path="{p}">\n{_process_content(content.SKILL_FILES[p], content.SKILL_MODEL_VARS).strip()}\n</doc>'
            for p in sorted(paths)
            if p in content.SKILL_FILES
        )
        parts.append(f"## Reference ({lang_label})\n\nIncluded documentation:\n\n{docs}")
    else:
        parts.append(
            "## Reference\n\nNo bundled language docs in this build. "
            "Use WebFetch against https://docs.anthropic.com for API details.",
        )
    wf = clean.find("## When to Use WebFetch")
    if wf != -1:
        parts.append(clean[wf:].rstrip())
    if args.strip():
        parts.append(f"## User Request\n\n{args}")
    return "\n\n".join(parts)


def register_claude_api_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        lang = _detect_language()
        text = _build_prompt(lang, args)
        return [{"type": "text", "text": text}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="claude-api",
            description=(
                "Build apps with the Claude API or Anthropic SDK. "
                "Use when the user works with anthropic SDKs or Agent SDK."
            ),
            allowed_tools=["Read", "Grep", "Glob", "WebFetch"],
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
