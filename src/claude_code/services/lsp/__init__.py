"""
LSP (Language Server Protocol) service.

Client and server management for LSP.

Migrated from: services/lsp/*.ts (7 files)
"""

from .client import (
    LSPClient,
    ServerCapabilities,
    create_lsp_client,
)
from .diagnostics import (
    Diagnostic,
    DiagnosticRegistry,
    DiagnosticSeverity,
    get_diagnostics_for_file,
)
from .manager import (
    LSPServerManager,
    get_lsp_manager,
    start_lsp_server,
    stop_lsp_server,
)
from .passive_feedback import (
    PublishDiagnosticsParams,
    format_diagnostics_for_attachment,
    map_lsp_severity,
)

__all__ = [
    # Client
    "LSPClient",
    "create_lsp_client",
    "ServerCapabilities",
    # Manager
    "LSPServerManager",
    "get_lsp_manager",
    "start_lsp_server",
    "stop_lsp_server",
    # Diagnostics
    "Diagnostic",
    "DiagnosticSeverity",
    "DiagnosticRegistry",
    "get_diagnostics_for_file",
    "PublishDiagnosticsParams",
    "format_diagnostics_for_attachment",
    "map_lsp_severity",
]
