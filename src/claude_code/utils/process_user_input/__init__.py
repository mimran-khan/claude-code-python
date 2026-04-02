"""
Process user input (slash/bash/text) — mirrors ``utils/processUserInput/``.

Implementation lives in :mod:`claude_code.utils.process_input`; this package
exposes the same entry points under the TypeScript directory name.
"""

from __future__ import annotations

from ..process_input.process_input import (
    ProcessUserInputBaseResult,
    ProcessUserInputContext,
    process_user_input,
)
from ..process_input.process_text import process_text_prompt

__all__ = [
    "ProcessUserInputBaseResult",
    "ProcessUserInputContext",
    "process_text_prompt",
    "process_user_input",
]
