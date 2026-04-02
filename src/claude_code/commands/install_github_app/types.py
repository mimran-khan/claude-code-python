"""
Migrated from: commands/install-github-app/types.ts (Workflow union).
"""

from __future__ import annotations

from typing import Literal

Workflow = Literal["claude", "claude-review"]

GITHUB_ACTION_SETUP_DOCS_URL = "https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md"
