"""Tests for protobuf-shaped generated event types (types/generated mirror)."""

from __future__ import annotations

from datetime import datetime, timezone

from claude_code.types.generated import (
    ClaudeCodeInternalEvent,
    GrowthbookExperimentEvent,
    PublicApiAuth,
    Timestamp,
    claude_code_internal_event_from_json,
    claude_code_internal_event_to_json,
    growthbook_experiment_event_from_json,
    growthbook_experiment_event_to_json,
    public_api_auth_from_json,
    public_api_auth_to_json,
    timestamp_from_json,
    timestamp_to_datetime,
    timestamp_to_json,
)


def test_timestamp_round_trip() -> None:
    t = Timestamp(seconds=1_700_000_000, nanos=500_000_000)
    dt = timestamp_to_datetime(t)
    assert dt.tzinfo == timezone.utc
    raw = timestamp_to_json(t)
    assert raw["seconds"] == 1_700_000_000
    assert raw["nanos"] == 500_000_000
    assert timestamp_from_json(raw) == t


def test_public_api_auth_json() -> None:
    auth = PublicApiAuth(account_id=42, organization_uuid="o", account_uuid="a")
    d = public_api_auth_to_json(auth)
    assert d == {"account_id": 42, "organization_uuid": "o", "account_uuid": "a"}
    assert public_api_auth_from_json(d) == auth


def test_growthbook_experiment_round_trip() -> None:
    ts = datetime(2024, 1, 15, 1, 30, 15, 10000, tzinfo=timezone.utc)
    ev = GrowthbookExperimentEvent(
        event_id="e1",
        timestamp=ts,
        experiment_id="exp",
        variation_id=1,
        environment="production",
        auth=PublicApiAuth(account_id=1, organization_uuid="", account_uuid=""),
    )
    d = growthbook_experiment_event_to_json(ev)
    back = growthbook_experiment_event_from_json(d)
    assert back.event_id == ev.event_id
    assert back.experiment_id == ev.experiment_id
    assert back.variation_id == ev.variation_id
    assert back.environment == ev.environment
    assert back.timestamp is not None
    assert back.auth is not None
    assert back.auth.account_id == 1


def test_claude_code_internal_event_nested_env() -> None:
    payload = {
        "event_name": "tengu_test",
        "session_id": "s1",
        "env": {
            "platform": "linux",
            "is_ci": True,
            "tags": ["a", "b"],
            "github_actions_metadata": {
                "actor_id": "123",
            },
        },
        "slack": {
            "slack_team_id": "T1",
            "is_enterprise_install": False,
        },
    }
    ev = claude_code_internal_event_from_json(payload)
    assert isinstance(ev, ClaudeCodeInternalEvent)
    assert ev.event_name == "tengu_test"
    assert ev.env is not None
    assert ev.env.platform == "linux"
    assert ev.env.is_ci is True
    assert ev.env.tags == ["a", "b"]
    assert ev.env.github_actions_metadata is not None
    assert ev.env.github_actions_metadata.actor_id == "123"
    assert ev.slack is not None
    assert ev.slack.slack_team_id == "T1"
    out = claude_code_internal_event_to_json(ev)
    assert out["event_name"] == "tengu_test"
    assert out["env"]["platform"] == "linux"
    assert out["env"]["tags"] == ["a", "b"]
