"""
Bridge and remote control (REPL bridge, headless bridge, sessions).

Handles connectivity between a local Claude Code instance and remote
infrastructure: session creation, polling, SDK-style messaging, JWT/trusted
device flows, and environment-specific bridge modes (including env-less bridge).

This package is large by design; import specific submodules (e.g.
``bridge.repl_bridge``) when possible rather than the full barrel export.

Ported from TypeScript ``bridge/``.
"""

from __future__ import annotations

from claude_code.bridge.bridge_api import (
    BridgeApiDeps,
    BridgeFatalError,
    create_bridge_api_client,
    is_expired_error_type,
    is_suppressible403,
    validate_bridge_id,
)
from claude_code.bridge.bridge_config import (
    get_bridge_access_token,
    get_bridge_base_url,
    get_bridge_base_url_override,
    get_bridge_token_override,
)
from claude_code.bridge.bridge_debug import (
    clear_bridge_debug_handle,
    get_bridge_debug_handle,
    inject_bridge_fault,
    register_bridge_debug_handle,
    wrap_api_for_fault_injection,
)
from claude_code.bridge.bridge_enabled import (
    check_bridge_min_version,
    get_bridge_disabled_reason,
    is_bridge_enabled,
    is_bridge_enabled_blocking,
    is_cse_shim_enabled,
    is_env_less_bridge_enabled,
)
from claude_code.bridge.bridge_main import (
    BackoffConfig,
    BridgeHeadlessPermanentError,
    ParsedArgs,
    bridge_main,
    is_connection_error,
    is_server_error,
    parse_args,
    run_bridge_headless,
    run_bridge_loop,
)
from claude_code.bridge.bridge_messaging import (
    OUTBOUND_ONLY_ERROR,
    BoundedUUIDSet,
    ServerControlRequestHandlers,
    extract_title_text,
    handle_ingress_message,
    handle_server_control_request,
    is_eligible_bridge_message,
    is_sdk_control_request,
    is_sdk_control_response,
    is_sdk_message,
    make_result_message,
)
from claude_code.bridge.bridge_permission_callbacks import (
    BridgePermissionResponse,
    is_bridge_permission_response,
)
from claude_code.bridge.bridge_pointer import (
    BRIDGE_POINTER_TTL_MS,
    BridgePointer,
    clear_bridge_pointer,
    get_bridge_pointer_path,
    read_bridge_pointer,
    read_bridge_pointer_across_worktrees,
    write_bridge_pointer,
)
from claude_code.bridge.bridge_status_util import (
    FAILED_FOOTER_TEXT,
    SHIMMER_INTERVAL_MS,
    TOOL_DISPLAY_EXPIRY_MS,
    abbreviate_activity,
    build_active_footer_text,
    build_bridge_connect_url,
    build_bridge_session_url,
    build_idle_footer_text,
    compute_glimmer_index,
    compute_shimmer_segments,
    format_duration,
    get_bridge_status,
    timestamp,
    truncate_prompt,
    wrap_with_osc8_link,
)
from claude_code.bridge.bridge_ui import create_bridge_logger
from claude_code.bridge.capacity_wake import CapacitySignal, CapacityWake, create_capacity_wake
from claude_code.bridge.code_session_api import (
    RemoteCredentials,
    create_code_session,
    fetch_remote_credentials,
)
from claude_code.bridge.create_session import (
    SessionEvent,
    archive_bridge_session,
    create_bridge_session,
    get_bridge_session,
    update_bridge_session_title,
)
from claude_code.bridge.debug_utils import (
    debug_body,
    debug_truncate,
    describe_axios_error,
    error_message,
    extract_error_detail,
    extract_http_status,
    log_bridge_skip,
    redact_secrets,
)
from claude_code.bridge.env_less_bridge_config import (
    DEFAULT_ENV_LESS_BRIDGE_CONFIG,
    EnvLessBridgeConfig,
    check_env_less_bridge_min_version,
    get_env_less_bridge_config,
    should_show_app_upgrade_message,
)
from claude_code.bridge.flush_gate import FlushGate
from claude_code.bridge.inbound_attachments import (
    InboundAttachment,
    extract_inbound_attachments,
    prepend_path_refs,
    resolve_and_prepend,
    resolve_inbound_attachments,
)
from claude_code.bridge.inbound_messages import (
    extract_inbound_message_fields,
    normalize_image_blocks,
)
from claude_code.bridge.init_repl_bridge import InitBridgeOptions, init_repl_bridge
from claude_code.bridge.jwt_utils import (
    create_token_refresh_scheduler,
    decode_jwt_expiry,
    decode_jwt_payload,
)
from claude_code.bridge.poll_config import get_poll_interval_config
from claude_code.bridge.poll_config_defaults import DEFAULT_POLL_CONFIG, PollIntervalConfig
from claude_code.bridge.remote_bridge_core import EnvLessBridgeParams, init_env_less_bridge_core
from claude_code.bridge.repl_bridge import BridgeCoreParams, ReplBridgeHandle, init_bridge_core
from claude_code.bridge.repl_bridge_handle import (
    get_repl_bridge_handle,
    get_self_bridge_compat_id,
    set_repl_bridge_handle,
)
from claude_code.bridge.repl_bridge_transport import (
    ReplBridgeTransport,
    create_v1_repl_transport,
    create_v2_repl_transport,
)
from claude_code.bridge.session_id_compat import (
    set_cse_shim_gate,
    to_compat_session_id,
    to_infra_session_id,
)
from claude_code.bridge.session_runner import (
    PermissionRequest,
    SessionSpawnerDeps,
    create_session_spawner,
    extract_activities_for_testing,
    safe_filename_id,
)
from claude_code.bridge.trusted_device import (
    clear_trusted_device_token,
    clear_trusted_device_token_cache,
    enroll_trusted_device,
    get_trusted_device_token,
)
from claude_code.bridge.types import (
    BRIDGE_LOGIN_ERROR,
    BRIDGE_LOGIN_INSTRUCTION,
    DEFAULT_SESSION_TIMEOUT_MS,
    REMOTE_CONTROL_DISCONNECTED_MSG,
    BridgeConfig,
    BridgeLogger,
    PermissionResponseEvent,
    SessionActivity,
    SessionHandle,
    SessionSpawner,
    SessionSpawnOpts,
    WorkResponse,
    WorkSecret,
)
from claude_code.bridge.work_secret import (
    build_ccr_v2_sdk_url,
    build_sdk_url,
    decode_work_secret,
    register_worker,
    same_session_id,
)

__all__ = [
    "BRIDGE_LOGIN_ERROR",
    "BRIDGE_LOGIN_INSTRUCTION",
    "BRIDGE_POINTER_TTL_MS",
    "DEFAULT_ENV_LESS_BRIDGE_CONFIG",
    "DEFAULT_POLL_CONFIG",
    "DEFAULT_SESSION_TIMEOUT_MS",
    "FAILED_FOOTER_TEXT",
    "InitBridgeOptions",
    "OUTBOUND_ONLY_ERROR",
    "BackoffConfig",
    "BoundedUUIDSet",
    "BridgeHeadlessPermanentError",
    "ParsedArgs",
    "PollIntervalConfig",
    "REMOTE_CONTROL_DISCONNECTED_MSG",
    "SHIMMER_INTERVAL_MS",
    "TOOL_DISPLAY_EXPIRY_MS",
    "BridgeApiDeps",
    "BridgeConfig",
    "BridgeCoreParams",
    "BridgeFatalError",
    "BridgeLogger",
    "BridgePermissionResponse",
    "BridgePointer",
    "CapacitySignal",
    "CapacityWake",
    "EnvLessBridgeConfig",
    "EnvLessBridgeParams",
    "FlushGate",
    "InboundAttachment",
    "PermissionRequest",
    "PermissionResponseEvent",
    "RemoteCredentials",
    "ReplBridgeHandle",
    "ReplBridgeTransport",
    "ServerControlRequestHandlers",
    "SessionActivity",
    "SessionEvent",
    "SessionHandle",
    "SessionSpawnOpts",
    "SessionSpawner",
    "SessionSpawnerDeps",
    "WorkResponse",
    "WorkSecret",
    "abbreviate_activity",
    "archive_bridge_session",
    "bridge_main",
    "build_active_footer_text",
    "build_bridge_connect_url",
    "build_bridge_session_url",
    "build_ccr_v2_sdk_url",
    "build_idle_footer_text",
    "build_sdk_url",
    "check_bridge_min_version",
    "check_env_less_bridge_min_version",
    "clear_bridge_debug_handle",
    "clear_bridge_pointer",
    "clear_trusted_device_token",
    "clear_trusted_device_token_cache",
    "compute_glimmer_index",
    "compute_shimmer_segments",
    "create_bridge_api_client",
    "create_bridge_logger",
    "create_bridge_session",
    "create_code_session",
    "create_session_spawner",
    "create_token_refresh_scheduler",
    "create_v1_repl_transport",
    "create_v2_repl_transport",
    "create_capacity_wake",
    "decode_jwt_expiry",
    "decode_jwt_payload",
    "decode_work_secret",
    "debug_body",
    "debug_truncate",
    "describe_axios_error",
    "enroll_trusted_device",
    "error_message",
    "extract_activities_for_testing",
    "extract_error_detail",
    "extract_http_status",
    "extract_inbound_attachments",
    "extract_inbound_message_fields",
    "extract_title_text",
    "fetch_remote_credentials",
    "format_duration",
    "get_bridge_access_token",
    "get_bridge_base_url",
    "get_bridge_base_url_override",
    "get_bridge_debug_handle",
    "get_bridge_disabled_reason",
    "get_bridge_pointer_path",
    "get_bridge_session",
    "get_bridge_status",
    "get_bridge_token_override",
    "get_env_less_bridge_config",
    "get_poll_interval_config",
    "get_repl_bridge_handle",
    "get_self_bridge_compat_id",
    "get_trusted_device_token",
    "handle_ingress_message",
    "handle_server_control_request",
    "init_bridge_core",
    "init_env_less_bridge_core",
    "init_repl_bridge",
    "inject_bridge_fault",
    "is_bridge_enabled",
    "is_bridge_enabled_blocking",
    "is_bridge_permission_response",
    "is_cse_shim_enabled",
    "is_connection_error",
    "is_eligible_bridge_message",
    "is_env_less_bridge_enabled",
    "is_expired_error_type",
    "is_sdk_control_request",
    "is_sdk_control_response",
    "is_sdk_message",
    "is_server_error",
    "is_suppressible403",
    "log_bridge_skip",
    "make_result_message",
    "normalize_image_blocks",
    "parse_args",
    "prepend_path_refs",
    "read_bridge_pointer",
    "read_bridge_pointer_across_worktrees",
    "redact_secrets",
    "register_bridge_debug_handle",
    "register_worker",
    "resolve_and_prepend",
    "resolve_inbound_attachments",
    "run_bridge_headless",
    "run_bridge_loop",
    "safe_filename_id",
    "same_session_id",
    "set_cse_shim_gate",
    "set_repl_bridge_handle",
    "should_show_app_upgrade_message",
    "timestamp",
    "to_compat_session_id",
    "to_infra_session_id",
    "truncate_prompt",
    "update_bridge_session_title",
    "validate_bridge_id",
    "wrap_api_for_fault_injection",
    "wrap_with_osc8_link",
    "write_bridge_pointer",
]
