"""Sandbox UI helpers. Migrated from: utils/sandbox/sandbox-ui-utils.ts"""

from __future__ import annotations

import re

_TAG_RE = re.compile(r"<sandbox_violations>[\s\S]*?</sandbox_violations>")


def remove_sandbox_violation_tags(text: str) -> str:
    return _TAG_RE.sub("", text)
