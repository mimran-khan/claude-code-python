"""Pure logic tests for grove helpers."""

from __future__ import annotations

from claude_code.services.api.grove import (
    AccountSettings,
    ApiResult,
    GroveConfig,
    calculate_should_show_grove,
)


def test_calculate_should_show_grove_hides_when_user_chose() -> None:
    settings = ApiResult(
        True,
        AccountSettings(grove_enabled=True, grove_notice_viewed_at=None),
    )
    config = ApiResult(
        True,
        GroveConfig(
            grove_enabled=True,
            domain_excluded=False,
            notice_is_grace_period=True,
            notice_reminder_frequency=None,
        ),
    )
    assert calculate_should_show_grove(settings, config, False) is False


def test_calculate_should_show_grove_api_failure() -> None:
    settings = ApiResult(False, None)
    config = ApiResult(True, GroveConfig(True, False, True, None))
    assert calculate_should_show_grove(settings, config, False) is False
