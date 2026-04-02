"""
LSP Types.

Type definitions for Language Server Protocol integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LspCapabilities:
    """Capabilities supported by an LSP server."""

    hover: bool = False
    completion: bool = False
    definition: bool = False
    references: bool = False
    diagnostics: bool = False
    formatting: bool = False
    code_actions: bool = False
    rename: bool = False
    document_symbols: bool = False
    workspace_symbols: bool = False


@dataclass
class LspServerConfig:
    """Configuration for an LSP server."""

    name: str
    command: list[str] = field(default_factory=list)
    language_ids: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    initialization_options: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScopedLspServerConfig:
    """LSP server config scoped to a plugin."""

    plugin_name: str
    server_name: str
    config: LspServerConfig
    enabled: bool = True
