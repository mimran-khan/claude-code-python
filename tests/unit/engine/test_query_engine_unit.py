"""Unit tests for ``claude_code.engine.query_engine`` helpers and lightweight API surface."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from claude_code.core.tool import get_empty_tool_permission_context
from claude_code.engine import query_engine as qe


def _minimal_config(**kwargs):
    defaults = dict(
        cwd="/tmp",
        tools=[],
        commands=[],
        mcp_clients=[],
        agents=[],
        can_use_tool=lambda *_a, **_k: {"allowed": True},
        get_app_state=lambda: qe.AppState(tool_permission_context=get_empty_tool_permission_context()),
        set_app_state=lambda _u: None,
    )
    defaults.update(kwargs)
    return qe.QueryEngineConfig(**defaults)


def test_get_main_loop_model_respects_env() -> None:
    with patch.dict("os.environ", {"CLAUDE_CODE_MODEL": "custom-model"}):
        assert qe._get_main_loop_model() == "custom-model"


def test_get_main_loop_model_default() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert qe._get_main_loop_model() == "claude-sonnet-4-20250514"


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("true", True),
        ("1", True),
        ("adaptive", True),
        ("TRUE", True),
        ("false", False),
        ("0", False),
        ("", False),
    ],
)
def test_should_enable_thinking_by_default_parametrized(env_value: str, expected: bool) -> None:
    with patch.dict("os.environ", {"CLAUDE_CODE_THINKING": env_value}):
        assert qe._should_enable_thinking_by_default() is expected


def test_should_enable_thinking_false_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_THINKING", raising=False)
    assert qe._should_enable_thinking_by_default() is False


def test_is_local_command_message_positive() -> None:
    msg = SimpleNamespace(type="system", subtype="local_command")
    assert qe._is_local_command_message(msg) is True


def test_is_local_command_message_negative() -> None:
    assert qe._is_local_command_message(SimpleNamespace(type="user")) is False
    assert qe._is_local_command_message(object()) is False


def test_create_abort_controller_abort_sets_flag() -> None:
    ctrl = qe._create_abort_controller()
    assert ctrl.aborted is False
    ctrl.abort("test")
    assert ctrl.aborted is True
    assert ctrl.reason == "test"


def test_query_engine_get_messages_and_set_model() -> None:
    engine = qe.QueryEngine(_minimal_config())
    assert engine.get_messages() == []
    engine.set_model("new-model")
    assert engine.config.user_specified_model == "new-model"


def test_query_engine_interrupt_calls_abort() -> None:
    mock_ctrl = MagicMock()
    engine = qe.QueryEngine(_minimal_config(abort_controller=mock_ctrl))
    engine.interrupt()
    mock_ctrl.abort.assert_called_once()


def test_extract_result_text_from_string_content() -> None:
    # QueryEngine expects wire-shaped user rows with a ``message`` dict (see submit_message pipeline).
    last = SimpleNamespace(message={"role": "user", "content": "hello"})
    engine = qe.QueryEngine(_minimal_config(initial_messages=[last]))
    assert engine._extract_result_text() == "hello"


def test_extract_result_text_from_text_blocks() -> None:
    content = [{"type": "text", "text": "block"}]
    last = SimpleNamespace(message={"role": "user", "content": content})
    engine = qe.QueryEngine(_minimal_config(initial_messages=[last]))
    assert engine._extract_result_text() == "block"


def test_extract_result_text_empty_messages() -> None:
    engine = qe.QueryEngine(_minimal_config())
    assert engine._extract_result_text() == ""
