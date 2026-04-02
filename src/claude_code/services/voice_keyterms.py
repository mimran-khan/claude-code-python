"""
Voice STT keyterm hints for voice_stream (Deepgram keyword boosting).

Migrated from: services/voiceKeyterms.ts (consumed by hooks/useVoice.ts).
Canonical location under ``services``; event_handlers re-exports for hook wiring.
"""

from __future__ import annotations

import re
from pathlib import Path

from claude_code.bootstrap.state import get_project_root
from claude_code.utils.git import get_branch

GLOBAL_VOICE_KEYTERMS: frozenset[str] = frozenset(
    {
        "MCP",
        "symlink",
        "grep",
        "regex",
        "localhost",
        "codebase",
        "TypeScript",
        "JSON",
        "OAuth",
        "webhook",
        "gRPC",
        "dotfiles",
        "subagent",
        "worktree",
    }
)

MAX_VOICE_KEYTERMS = 50

_CAMEL_SPLIT = re.compile(r"([a-z])([A-Z])")
_SPLIT_TOKENS = re.compile(r"[-_./\s]+")


def split_identifier(name: str) -> list[str]:
    """
    Split camelCase / kebab-case / paths into words; drop tokens of length <= 2
    or > 20 (matches TypeScript voiceKeyterms.ts).
    """
    spaced = _CAMEL_SPLIT.sub(r"\1 \2", name)
    out: list[str] = []
    for raw in _SPLIT_TOKENS.split(spaced):
        w = raw.strip()
        if 2 < len(w) <= 20:
            out.append(w)
    return out


def _file_name_words(file_path: str) -> list[str]:
    stem = Path(file_path).name
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    return split_identifier(stem)


async def get_voice_keyterms(recent_files: set[str] | None = None) -> list[str]:
    """
    Build keyterms for voice_stream: globals plus project basename, git branch
    words, and recent file name fragments.
    """
    terms: set[str] = set(GLOBAL_VOICE_KEYTERMS)

    project_root = ""
    try:
        project_root = get_project_root()
    except Exception:
        project_root = ""

    if project_root:
        name = Path(project_root).name
        if 2 < len(name) <= 50:
            terms.add(name)

    try:
        branch = await get_branch(project_root or None)
        if branch:
            for word in split_identifier(branch):
                terms.add(word)
    except Exception:
        pass

    if recent_files:
        for file_path in recent_files:
            if len(terms) >= MAX_VOICE_KEYTERMS:
                break
            for word in _file_name_words(file_path):
                terms.add(word)

    ordered = sorted(terms)
    return ordered[:MAX_VOICE_KEYTERMS]
