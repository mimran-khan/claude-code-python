"""Compatibility shim; full validation API in :mod:`claude_code.utils.plugins.validation`."""

from __future__ import annotations

from .validation import *  # noqa: F403  # shim: re-export full ``validation`` public API
from .validation import ValidationResult, validate_manifest
from .validation import __all__ as _validation_all


async def validate_plugin_directory(path: str) -> ValidationResult:
    """Validate a plugin or marketplace tree under ``path`` (``validateManifest``-style)."""
    return await validate_manifest(path)


__all__ = list(_validation_all) + ["validate_plugin_directory"]
