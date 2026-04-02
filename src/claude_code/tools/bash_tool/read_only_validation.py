"""
Read-only bash command validation.

Migrated from: tools/BashTool/readOnlyValidation.ts

The TypeScript module contains large per-command safe-flag tables; Python uses
:mod:`claude_code.tools.bash_tool.validation` heuristics until full parity.
"""

from __future__ import annotations

import re

from .validation import check_read_only_command


def bash_segment_appears_read_only(command_segment: str) -> bool:
    seg = command_segment.strip()
    if not seg:
        return True
    if re.search(r"[>&]\s*[^\s]", seg) and not seg.startswith("echo "):
        return False
    return check_read_only_command(seg)


def is_read_only_bash_command(command: str) -> bool:
    chunks = re.split(r"\s*(?:&&|\|\|)\s*", command)
    return all(bash_segment_appears_read_only(c) for c in chunks if c.strip())


__all__ = ["bash_segment_appears_read_only", "is_read_only_bash_command"]
