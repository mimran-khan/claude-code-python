"""
Services for Claude Code.

This package contains service modules for API communication,
token estimation, rate limiting, and other backend services.
"""

# Import submodules
from . import (
    agent_summary,
    analytics,
    api,
    auth,
    bedrock,
    claude_ai,
    compact,
    docker,
    lsp,
    magic_docs,
    mcp,
    plugins,
    policy_limits,
    prompt_suggestion,
    remote_managed_settings,
    session_memory,
    settings_sync,
    team_memory_sync,
    tips,
    tool_use_summary,
)
from .away_summary import generate_away_summary
from .diagnostics import (
    Diagnostic,
    DiagnosticFile,
    DiagnosticTrackingService,
    diagnostic_tracker,
)
from .limits import (
    ClaudeAILimits,
    RateLimitType,
    get_current_limits,
    is_rate_limited,
    update_limits,
)
from .notifier import NotificationOptions, send_notification

# Re-export from submodules
from .oauth import (
    OAuthService,
    generate_code_challenge,
    generate_code_verifier,
    generate_state,
)
from .rate_limit_messages import (
    get_rate_limit_error_message,
    get_rate_limit_message,
    is_rate_limit_error_message,
)
from .token_estimation import (
    rough_token_count_estimation as estimate_tokens,
)
from .token_estimation import (
    rough_token_count_estimation_for_content as count_tokens,
)

__all__ = [
    # Token estimation
    "estimate_tokens",
    "count_tokens",
    # Rate limit messages
    "get_rate_limit_message",
    "get_rate_limit_error_message",
    "is_rate_limit_error_message",
    # Notifications
    "send_notification",
    "NotificationOptions",
    # OAuth
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_state",
    "OAuthService",
    "generate_away_summary",
    # Diagnostics
    "Diagnostic",
    "DiagnosticFile",
    "DiagnosticTrackingService",
    "diagnostic_tracker",
    # Limits
    "ClaudeAILimits",
    "RateLimitType",
    "get_current_limits",
    "update_limits",
    "is_rate_limited",
    # Submodules
    "analytics",
    "plugins",
    "mcp",
    "compact",
    "api",
    "lsp",
    "session_memory",
    "tips",
    "agent_summary",
    "magic_docs",
    "prompt_suggestion",
    "bedrock",
    "auth",
    "claude_ai",
    "docker",
    "policy_limits",
    "remote_managed_settings",
    "settings_sync",
    "team_memory_sync",
    "tool_use_summary",
]
