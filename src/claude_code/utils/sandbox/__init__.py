"""Sandbox integration. Migrated from: utils/sandbox/*"""

from .adapter import (
    SandboxManager,
    SandboxManagerStub,
    add_to_excluded_commands,
    convert_to_sandbox_runtime_config,
    resolve_path_pattern_for_sandbox,
    resolve_sandbox_filesystem_path,
    should_allow_managed_sandbox_domains_only,
)
from .ui_utils import remove_sandbox_violation_tags

__all__ = [
    "SandboxManager",
    "SandboxManagerStub",
    "add_to_excluded_commands",
    "convert_to_sandbox_runtime_config",
    "remove_sandbox_violation_tags",
    "resolve_path_pattern_for_sandbox",
    "resolve_sandbox_filesystem_path",
    "should_allow_managed_sandbox_domains_only",
]
