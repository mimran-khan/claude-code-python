"""
MCP (Model Context Protocol) service.

Client, configuration, and management for MCP servers.

Migrated from: services/mcp/*.ts (22 files)
"""

from .auth import (
    AuthorizationServerMetadata,
    OAuthClientInfo,
    OAuthFlowManager,
    OAuthState,
    OAuthTokens,
    build_authorization_url,
    discover_oauth_metadata,
    exchange_code_for_tokens,
    generate_code_challenge,
    generate_code_verifier,
    generate_state,
    get_oauth_flow_manager,
    refresh_tokens,
)
from .channel_allowlist import (
    ChannelAllowlistEntry,
    get_channel_allowlist,
    is_channel_allowlisted,
    is_channels_enabled,
)
from .client import (
    MCPClient,
    McpClient,
    connect_to_server,
    create_mcp_client,
)
from .config import (
    add_mcp_server,
    get_mcp_servers,
    remove_mcp_server,
    validate_mcp_config,
)
from .env_expansion import EnvExpansionResult, expand_env_vars_in_string
from .headers_helper import HeadersHelperConfig, get_mcp_headers_from_helper
from .in_process_transport import InProcessTransport, create_linked_transports
from .normalization import (
    is_valid_mcp_name,
    normalize_name_for_mcp,
    parse_tool_name,
    sanitize_tool_name,
)
from .oauth_port import build_redirect_uri, find_available_port, find_available_port_sync
from .official_registry import is_official_mcp_url, prefetch_official_mcp_urls
from .string_utils import (
    McpInfoFromString,
    build_mcp_tool_name,
    get_mcp_display_name,
    get_mcp_prefix,
    get_tool_name_for_permission_check,
    mcp_info_from_string,
)
from .types import (
    ConfigScope,
    McpConnection,
    McpHTTPServerConfig,
    McpResource,
    McpSdkServerConfig,
    McpServerCapabilities,
    McpServerConfig,
    McpSSEServerConfig,
    McpStdioServerConfig,
    McpTool,
    McpWebSocketServerConfig,
    Transport,
    parse_server_config,
)
from .utils import (
    extract_server_name_from_url,
    format_mcp_error,
    get_logging_safe_mcp_base_url,
    is_mcp_server_url,
    truncate_mcp_output,
)

__all__ = [
    # Types
    "ConfigScope",
    "Transport",
    "McpServerConfig",
    "McpStdioServerConfig",
    "McpSSEServerConfig",
    "McpHTTPServerConfig",
    "McpWebSocketServerConfig",
    "McpSdkServerConfig",
    "McpConnection",
    "McpTool",
    "McpResource",
    "McpServerCapabilities",
    "parse_server_config",
    # Client
    "McpClient",
    "MCPClient",
    "create_mcp_client",
    "connect_to_server",
    # Config
    "get_mcp_servers",
    "add_mcp_server",
    "remove_mcp_server",
    "validate_mcp_config",
    # Auth
    "OAuthTokens",
    "OAuthClientInfo",
    "AuthorizationServerMetadata",
    "OAuthState",
    "OAuthFlowManager",
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_state",
    "discover_oauth_metadata",
    "exchange_code_for_tokens",
    "refresh_tokens",
    "build_authorization_url",
    "get_oauth_flow_manager",
    # Normalization
    "normalize_name_for_mcp",
    "is_valid_mcp_name",
    "sanitize_tool_name",
    "parse_tool_name",
    # Utils
    "get_logging_safe_mcp_base_url",
    "extract_server_name_from_url",
    "format_mcp_error",
    "is_mcp_server_url",
    "truncate_mcp_output",
    # String utils
    "McpInfoFromString",
    "build_mcp_tool_name",
    "get_mcp_display_name",
    "get_mcp_prefix",
    "get_tool_name_for_permission_check",
    "mcp_info_from_string",
    "EnvExpansionResult",
    "expand_env_vars_in_string",
    "build_redirect_uri",
    "find_available_port",
    "find_available_port_sync",
    "ChannelAllowlistEntry",
    "get_channel_allowlist",
    "is_channel_allowlisted",
    "is_channels_enabled",
    "HeadersHelperConfig",
    "get_mcp_headers_from_helper",
    "InProcessTransport",
    "create_linked_transports",
    "is_official_mcp_url",
    "prefetch_official_mcp_urls",
]
