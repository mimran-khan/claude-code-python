"""
TS path parity for ``utils/sandbox/sandbox-adapter.ts``.

Canonical implementation: :mod:`claude_code.utils.sandbox.adapter`.
"""

from __future__ import annotations

from claude_code.utils.sandbox.adapter import (
    BASH_TOOL_NAME,
    convert_to_sandbox_runtime_config,
    permission_rule_extract_prefix,
    permission_rule_value_from_string,
    resolve_path_pattern_for_sandbox,
    resolve_sandbox_filesystem_path,
    should_allow_managed_sandbox_domains_only,
)

__all__ = [
    "BASH_TOOL_NAME",
    "convert_to_sandbox_runtime_config",
    "permission_rule_extract_prefix",
    "permission_rule_value_from_string",
    "resolve_path_pattern_for_sandbox",
    "resolve_sandbox_filesystem_path",
    "should_allow_managed_sandbox_domains_only",
]
