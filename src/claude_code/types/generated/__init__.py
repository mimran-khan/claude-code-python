"""
Generated event and protobuf-shaped types (Python dataclass mirrors of ts_proto output).

Source TypeScript:
- types/generated/google/protobuf/timestamp.ts
- types/generated/events_mono/common/v1/auth.ts
- types/generated/events_mono/growthbook/v1/growthbook_experiment_event.ts
- types/generated/events_mono/claude_code/v1/claude_code_internal_event.ts
"""

from __future__ import annotations

from .events_mono.claude_code.v1.claude_code_internal_event import (
    ClaudeCodeInternalEvent,
    EnvironmentMetadata,
    GitHubActionsMetadata,
    SlackContext,
    claude_code_internal_event_from_json,
    claude_code_internal_event_to_json,
)
from .events_mono.common.v1.auth import (
    PublicApiAuth,
    public_api_auth_from_json,
    public_api_auth_to_json,
)
from .events_mono.growthbook.v1.growthbook_experiment_event import (
    GrowthbookExperimentEvent,
    growthbook_experiment_event_from_json,
    growthbook_experiment_event_to_json,
)
from .google.protobuf.timestamp import (
    Timestamp,
    datetime_to_iso_z,
    datetime_to_timestamp,
    parse_flexible_timestamp,
    timestamp_from_json,
    timestamp_to_datetime,
    timestamp_to_json,
)

__all__ = [
    "ClaudeCodeInternalEvent",
    "EnvironmentMetadata",
    "GitHubActionsMetadata",
    "GrowthbookExperimentEvent",
    "PublicApiAuth",
    "SlackContext",
    "Timestamp",
    "claude_code_internal_event_from_json",
    "claude_code_internal_event_to_json",
    "datetime_to_iso_z",
    "datetime_to_timestamp",
    "growthbook_experiment_event_from_json",
    "growthbook_experiment_event_to_json",
    "parse_flexible_timestamp",
    "public_api_auth_from_json",
    "public_api_auth_to_json",
    "timestamp_from_json",
    "timestamp_to_datetime",
    "timestamp_to_json",
]
