"""Expand ${VAR} and ${VAR:-default} in MCP config strings.

Migrated from: services/mcp/envExpansion.ts
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass
class EnvExpansionResult:
    expanded: str
    missing_vars: list[str]


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def expand_env_vars_in_string(value: str) -> EnvExpansionResult:
    missing: list[str] = []

    def repl(match: re.Match[str]) -> str:
        var_content = match.group(1)
        if ":-" in var_content:
            name, default = var_content.split(":-", 1)
        else:
            name, default = var_content, None
        env_val = os.environ.get(name)
        if env_val is not None:
            return env_val
        if default is not None:
            return default
        missing.append(name)
        return match.group(0)

    expanded = _VAR_PATTERN.sub(repl, value)
    return EnvExpansionResult(expanded=expanded, missing_vars=missing)
