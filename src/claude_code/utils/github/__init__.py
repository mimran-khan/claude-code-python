"""
GitHub utilities.

Migrated from: utils/github/*.ts
"""

from .auth import (
    GhAuthStatus,
    get_gh_auth_status,
    is_gh_authenticated,
    is_gh_installed,
)

__all__ = [
    "GhAuthStatus",
    "get_gh_auth_status",
    "is_gh_authenticated",
    "is_gh_installed",
]
