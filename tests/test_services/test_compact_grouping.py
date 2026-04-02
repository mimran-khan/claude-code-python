"""Tests for services.compact.grouping."""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.services.compact.grouping import group_messages_by_api_round


@dataclass
class _AssistantPayload:
    id: str


@dataclass
class _AssistantMsg:
    type: str
    message: _AssistantPayload


@dataclass
class _UserMsg:
    type: str
    body: str


def test_group_messages_user_then_assistant_splits_at_first_assistant() -> None:
    """First assistant message starts a new group when prior messages exist."""
    a1 = _AssistantMsg("assistant", _AssistantPayload("id-1"))
    u1 = _UserMsg("user", "hi")
    groups = group_messages_by_api_round([u1, a1])
    assert len(groups) == 2
    assert groups[0] == [u1]
    assert groups[1] == [a1]


def test_group_messages_splits_on_new_assistant_id() -> None:
    a1 = _AssistantMsg("assistant", _AssistantPayload("id-1"))
    a2 = _AssistantMsg("assistant", _AssistantPayload("id-2"))
    groups = group_messages_by_api_round([a1, a2])
    assert len(groups) == 2
    assert groups[0] == [a1]
    assert groups[1] == [a2]


def test_group_messages_empty() -> None:
    assert group_messages_by_api_round([]) == []
