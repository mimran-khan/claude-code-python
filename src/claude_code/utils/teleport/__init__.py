"""
Teleport API utilities for remote session management.

Migrated from: utils/teleport/*.ts
"""

from .api import (
    CCR_BYOC_BETA,
    TELEPORT_RETRY_DELAYS,
    GitSource,
    KnowledgeBaseSource,
    RemoteMessageContent,
    SessionContextSource,
    SessionStatus,
    http_get_with_retry,
    http_post_with_retry,
    is_transient_network_error,
    send_event_to_remote_session,
)
from .environment_selection import (
    EnvironmentSelectionInfo,
    get_environment_selection_info,
)
from .environments import (
    Environment,
    get_available_environments,
    get_default_environment,
)
from .git_bundle import (
    create_git_bundle,
    extract_git_bundle,
)
from .poll import PollRemoteSessionResponse, poll_remote_session_events
from .remote_environments import (
    EnvironmentResource,
    create_default_cloud_environment,
    fetch_environments,
)

__all__ = [
    # API
    "CCR_BYOC_BETA",
    "TELEPORT_RETRY_DELAYS",
    "SessionStatus",
    "GitSource",
    "KnowledgeBaseSource",
    "SessionContextSource",
    "RemoteMessageContent",
    "is_transient_network_error",
    "http_get_with_retry",
    "http_post_with_retry",
    "send_event_to_remote_session",
    # Environments
    "Environment",
    "get_available_environments",
    "get_default_environment",
    # Git bundle
    "create_git_bundle",
    "extract_git_bundle",
    "PollRemoteSessionResponse",
    "poll_remote_session_events",
    "EnvironmentResource",
    "fetch_environments",
    "create_default_cloud_environment",
    "EnvironmentSelectionInfo",
    "get_environment_selection_info",
]
