"""
Project onboarding steps (CLAUDE.md / empty workspace).

Migrated from: projectOnboardingState.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .utils.config_utils import get_project_config_path, save_current_project_config
from .utils.cwd import get_cwd


@dataclass
class OnboardingStep:
    key: str
    text: str
    is_complete: bool
    is_completable: bool
    is_enabled: bool


def _is_dir_empty(path: Path) -> bool:
    try:
        next(path.iterdir())
    except StopIteration:
        return True
    except OSError:
        return True
    return False


def get_steps() -> list[OnboardingStep]:
    cwd = Path(get_cwd())
    has_claude_md = (cwd / "CLAUDE.md").exists()
    workspace_empty = _is_dir_empty(cwd)
    return [
        OnboardingStep(
            key="workspace",
            text="Ask Claude to create a new app or clone a repository",
            is_complete=False,
            is_completable=True,
            is_enabled=workspace_empty,
        ),
        OnboardingStep(
            key="claudemd",
            text="Run /init to create a CLAUDE.md file with instructions for Claude",
            is_complete=has_claude_md,
            is_completable=True,
            is_enabled=not workspace_empty,
        ),
    ]


def is_project_onboarding_complete() -> bool:
    return all(s.is_complete for s in get_steps() if s.is_completable and s.is_enabled)


def _read_project_json() -> dict[str, object]:
    path = get_project_config_path(get_cwd())
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def maybe_mark_project_onboarding_complete() -> None:
    if _read_project_json().get("hasCompletedProjectOnboarding"):
        return
    if is_project_onboarding_complete():
        save_current_project_config(
            lambda c: {**c, "hasCompletedProjectOnboarding": True},
        )


@lru_cache(maxsize=1)
def should_show_project_onboarding() -> bool:
    data = _read_project_json()
    if data.get("hasCompletedProjectOnboarding"):
        return False
    seen = data.get("projectOnboardingSeenCount", 0)
    if isinstance(seen, int) and seen >= 4:
        return False
    if os.environ.get("IS_DEMO"):
        return False
    return not is_project_onboarding_complete()


def increment_project_onboarding_seen_count() -> None:
    save_current_project_config(
        lambda c: {
            **c,
            "projectOnboardingSeenCount": int(c.get("projectOnboardingSeenCount", 0)) + 1,
        },
    )
