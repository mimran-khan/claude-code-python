"""
Permission System.

This module handles permission checking and management for tool execution.
"""

from .checker import (
    PermissionChecker,
    check_permission,
    get_permission_rules,
)
from .types import (
    PermissionBehavior,
    PermissionContext,
    PermissionDecision,
    PermissionMode,
    PermissionResult,
    PermissionRule,
    PermissionRuleSource,
)

__all__ = [
    # Types
    "PermissionBehavior",
    "PermissionMode",
    "PermissionDecision",
    "PermissionResult",
    "PermissionRule",
    "PermissionRuleSource",
    "PermissionContext",
    # Checker
    "PermissionChecker",
    "check_permission",
    "get_permission_rules",
]
