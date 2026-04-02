"""
Native binary installer (XDG layout, locks, downloads).

Public API mirrors ``utils/nativeInstaller/index.ts``.
"""

from __future__ import annotations

from .installer import (
    InstallLatestResult,
    SetupMessage,
    check_install,
    cleanup_npm_installations,
    cleanup_old_versions,
    cleanup_shell_aliases,
    install_latest,
    lock_current_version,
    remove_installed_symlink,
)

__all__ = [
    "InstallLatestResult",
    "SetupMessage",
    "check_install",
    "cleanup_npm_installations",
    "cleanup_old_versions",
    "cleanup_shell_aliases",
    "install_latest",
    "lock_current_version",
    "remove_installed_symlink",
]
