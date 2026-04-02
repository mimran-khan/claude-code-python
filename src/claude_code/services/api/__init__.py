"""
Claude API service.

Communication with Claude API (Anthropic, Bedrock, Vertex).

Migrated from: services/api/*.ts
"""

from . import (
    admin_requests,
    files_api,
    overage_credit_grant,
    prompt_cache_break_detection,
    referral,
    session_ingress,
)
from .bootstrap import (
    BootstrapResponse,
    ModelOption,
    fetch_bootstrap_api,
    fetch_bootstrap_data,
    get_additional_models,
)
from .claude import (
    QueryResult,
    StreamEvent,
    get_max_output_tokens_for_model,
    query_model,
    query_model_with_streaming,
)
from .client import (
    AnthropicClient,
    APIRequestError,
    ClientConfig,
    get_anthropic_client,
)
from .error_utils import (
    SSL_ERROR_CODES,
    ConnectionErrorDetails,
    extract_connection_error_details,
    format_api_error,
    get_error_code,
    get_ssl_error_hint,
    is_transient_error,
    sanitize_api_error,
)
from .errors import (
    API_ERROR_MESSAGE_PREFIX,
    PROMPT_TOO_LONG_ERROR_MESSAGE,
    APIErrorType,
    classify_api_error,
    get_assistant_message_from_error,
    get_prompt_too_long_token_gap,
    is_media_size_error,
    is_prompt_too_long_message,
    parse_prompt_too_long_token_counts,
)
from .grove import (
    AccountSettings as GroveAccountSettings,
)
from .grove import (
    ApiResult,
    GroveConfig,
    calculate_should_show_grove,
    check_grove_for_non_interactive,
    get_grove_notice_config,
    get_grove_settings,
    is_consumer_subscriber,
    is_qualified_for_grove,
    mark_grove_notice_viewed,
    update_grove_settings,
)
from .logging import (
    EMPTY_USAGE,
    RequestLogger,
    RequestMetrics,
    RequestUsage,
    calculate_cost,
    get_request_logger,
    log_api_request,
    log_api_response,
)
from .retry import (
    RetryConfig,
    get_retry_delay,
    should_retry,
    with_retry,
)
from .usage import (
    ExtraUsage,
    RateLimit,
    Utilization,
    fetch_utilization,
    format_utilization,
)

__all__ = [
    # Client
    "get_anthropic_client",
    "AnthropicClient",
    "ClientConfig",
    "APIRequestError",
    # Claude
    "query_model",
    "query_model_with_streaming",
    "get_max_output_tokens_for_model",
    "StreamEvent",
    "QueryResult",
    # Errors
    "API_ERROR_MESSAGE_PREFIX",
    "PROMPT_TOO_LONG_ERROR_MESSAGE",
    "APIErrorType",
    "is_prompt_too_long_message",
    "is_media_size_error",
    "get_prompt_too_long_token_gap",
    "parse_prompt_too_long_token_counts",
    "get_assistant_message_from_error",
    "classify_api_error",
    # Retry
    "with_retry",
    "get_retry_delay",
    "should_retry",
    "RetryConfig",
    # Bootstrap
    "fetch_bootstrap_api",
    "fetch_bootstrap_data",
    "get_additional_models",
    "BootstrapResponse",
    "ModelOption",
    # Usage
    "fetch_utilization",
    "format_utilization",
    "Utilization",
    "RateLimit",
    "ExtraUsage",
    # Logging
    "log_api_request",
    "log_api_response",
    "calculate_cost",
    "RequestUsage",
    "RequestMetrics",
    "RequestLogger",
    "get_request_logger",
    "EMPTY_USAGE",
    # Error utils
    "ConnectionErrorDetails",
    "SSL_ERROR_CODES",
    "extract_connection_error_details",
    "format_api_error",
    "get_ssl_error_hint",
    "sanitize_api_error",
    "is_transient_error",
    "get_error_code",
    # Grove
    "GroveAccountSettings",
    "GroveConfig",
    "ApiResult",
    "get_grove_settings",
    "mark_grove_notice_viewed",
    "update_grove_settings",
    "get_grove_notice_config",
    "is_qualified_for_grove",
    "calculate_should_show_grove",
    "check_grove_for_non_interactive",
    "is_consumer_subscriber",
    # Submodules (full TS parity helpers)
    "admin_requests",
    "files_api",
    "overage_credit_grant",
    "prompt_cache_break_detection",
    "referral",
    "session_ingress",
]
