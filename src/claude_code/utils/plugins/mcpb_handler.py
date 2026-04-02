"""MCPB bundle handling. Migrated from mcpbHandler.ts (stub API)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class McpbLoadSuccess:
    manifest: Any
    mcp_config: dict[str, Any]
    extracted_path: str


@dataclass
class McpbNeedsConfig:
    status: str = "needs-config"


def is_mcpb_source(path: str) -> bool:
    return path.lower().endswith(".mcpb")


async def load_mcpb_file(
    _path: str,
    _plugin_path: str,
    _plugin_id: str,
    _on_status: Callable[[str], None] | None = None,
) -> McpbLoadSuccess | McpbNeedsConfig:
    return McpbNeedsConfig()


def validate_user_config(_schema: Any, _values: dict[str, Any]) -> bool:
    return True


__all__ = [
    "McpbLoadSuccess",
    "McpbNeedsConfig",
    "is_mcpb_source",
    "load_mcpb_file",
    "validate_user_config",
]
