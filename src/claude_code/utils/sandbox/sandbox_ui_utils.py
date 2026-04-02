"""
Compatibility shim for ``sandbox-ui-utils`` import path.

Migrated from: utils/sandbox/sandbox-ui-utils.ts (implementation lives in ``ui_utils``).
"""

from __future__ import annotations

from .ui_utils import remove_sandbox_violation_tags

__all__ = ["remove_sandbox_violation_tags"]
