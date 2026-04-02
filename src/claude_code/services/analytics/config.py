"""
Analytics configuration.

Common logic for determining when analytics should be disabled.

Migrated from: services/analytics/config.ts (39 lines)
"""

from __future__ import annotations

import os

from ...utils.env_utils import is_env_truthy


def is_analytics_disabled() -> bool:
    """
    Check if analytics operations should be disabled.

    Analytics is disabled in the following cases:
    - Test environment (PYTEST_CURRENT_TEST set or NODE_ENV === 'test')
    - Third-party cloud providers (Bedrock/Vertex/Foundry)
    - Privacy level is no-telemetry or essential-traffic
    """
    # Test environment
    if os.getenv("NODE_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST"):
        return True

    # Third-party providers
    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_BEDROCK")):
        return True
    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_VERTEX")):
        return True
    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_FOUNDRY")):
        return True

    # Privacy level check (stub - would need full privacy level impl)
    return bool(is_telemetry_disabled())


def is_telemetry_disabled() -> bool:
    """
    Check if telemetry is disabled via privacy settings.

    This is a stub - full implementation would check privacy level settings.
    """
    # Check for explicit disable
    return bool(is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_TELEMETRY")))


def is_feedback_survey_disabled() -> bool:
    """
    Check if the feedback survey should be suppressed.

    Unlike is_analytics_disabled(), this does NOT block on 3P providers.
    The survey is a local UI prompt with no transcript data.
    """
    if os.getenv("NODE_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST"):
        return True

    return is_telemetry_disabled()
