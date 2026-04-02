"""
Vim-mode prompt input transitions.

Migrated from: hooks/useVimInput.ts

Delegates to :mod:`claude_code.vim` when that package mirrors ``vim/transitions.ts``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VimInputDriverPlaceholder:
    mode: str = "INSERT"
