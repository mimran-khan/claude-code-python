"""Analytics service for event logging."""

from .config import is_analytics_disabled, is_feedback_survey_disabled
from .growthbook import (
    check_statsig_feature_gate_cached_may_be_stale,
    clear_feature_cache,
    get_dynamic_config_cached_may_be_stale,
    get_feature_value,
    get_feature_value_cached,
    set_feature_value,
)
from .index import (
    AnalyticsSink,
    attach_analytics_sink,
    log_event,
    log_event_async,
    reset_for_testing,
    strip_proto_fields,
)
from .metadata import enrich_metadata, get_event_metadata

__all__ = [
    "AnalyticsSink",
    "attach_analytics_sink",
    "log_event",
    "log_event_async",
    "reset_for_testing",
    "strip_proto_fields",
    "get_event_metadata",
    "enrich_metadata",
    "get_feature_value",
    "get_feature_value_cached",
    "get_dynamic_config_cached_may_be_stale",
    "check_statsig_feature_gate_cached_may_be_stale",
    "set_feature_value",
    "clear_feature_cache",
    "is_analytics_disabled",
    "is_feedback_survey_disabled",
]
