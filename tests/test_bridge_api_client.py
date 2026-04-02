"""Unit tests for claude_code.bridge.bridge_api."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.bridge.bridge_api import (
    BridgeFatalError,
    _handle_error_status,
    create_bridge_api_client,
    is_expired_error_type,
    is_suppressible403,
    validate_bridge_id,
)
from claude_code.bridge.types import BridgeConfig


def test_validate_bridge_id_accepts_safe_token() -> None:
    assert validate_bridge_id("ab-CD_12", "id") == "ab-CD_12"


def test_validate_bridge_id_rejects_empty() -> None:
    with pytest.raises(ValueError, match="Invalid"):
        validate_bridge_id("", "envId")


def test_validate_bridge_id_rejects_unsafe_characters() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        validate_bridge_id("env/../x", "envId")


def test_is_expired_error_type_detects_substrings() -> None:
    assert is_expired_error_type("token_expired") is True
    assert is_expired_error_type("lifetime_exceeded") is True
    assert is_expired_error_type(None) is False
    assert is_expired_error_type("other") is False


def test_is_suppressible403_only_for_specific_messages() -> None:
    e1 = BridgeFatalError("external_poll_sessions denied", 403)
    assert is_suppressible403(e1) is True
    e2 = BridgeFatalError("environments:manage missing", 403)
    assert is_suppressible403(e2) is True
    e3 = BridgeFatalError("nope", 403)
    assert is_suppressible403(e3) is False
    e4 = BridgeFatalError("external_poll_sessions", 404)
    assert is_suppressible403(e4) is False


def test_handle_error_status_no_op_for_200() -> None:
    _handle_error_status(200, {}, "ctx")


def test_handle_error_status_401_raises_bridge_fatal() -> None:
    with pytest.raises(BridgeFatalError) as ei:
        _handle_error_status(401, {"error": {"type": "auth"}}, "Login")
    assert ei.value.status == 401


def test_handle_error_status_403_expired_message() -> None:
    with pytest.raises(BridgeFatalError) as ei:
        _handle_error_status(
            403,
            {"error": {"type": "session_expired"}},
            "X",
        )
    assert ei.value.status == 403
    assert "expired" in str(ei.value).lower() or "restart" in str(ei.value).lower()


def test_handle_error_status_404_raises() -> None:
    with pytest.raises(BridgeFatalError) as ei:
        _handle_error_status(404, {}, "Ctx")
    assert ei.value.status == 404


def test_handle_error_status_410_raises() -> None:
    with pytest.raises(BridgeFatalError) as ei:
        _handle_error_status(410, {}, "Ctx")
    assert ei.value.status == 410


def test_handle_error_status_429_runtime() -> None:
    with pytest.raises(RuntimeError, match="429"):
        _handle_error_status(429, {}, "Poll")


def test_handle_error_status_generic_runtime() -> None:
    with pytest.raises(RuntimeError, match="500"):
        _handle_error_status(500, {}, "Op")


def _bridge_config() -> BridgeConfig:
    return BridgeConfig(
        dir="/tmp",
        machine_name="m",
        branch="main",
        git_repo_url=None,
        max_sessions=1,
        spawn_mode="single-session",
        verbose=False,
        sandbox=False,
        bridge_id="bridge_1",
        worker_type="claude_code",
        environment_id="env_unused",
        api_base_url="https://x",
        session_ingress_url="https://y",
    )


@pytest.mark.asyncio
async def test_register_bridge_environment_success() -> None:
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={"environment_id": "e1", "secret": "s"})

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=None)

    deps = {
        "base_url": "https://api.test",
        "get_access_token": lambda: "tok",
        "runner_version": "1.0",
    }
    api = create_bridge_api_client(deps)

    with patch("claude_code.bridge.bridge_api.httpx.AsyncClient", return_value=cm):
        out = await api.register_bridge_environment(_bridge_config())

    assert out["environment_id"] == "e1"
    mock_client.post.assert_awaited()


@pytest.mark.asyncio
async def test_resolve_auth_raises_without_token() -> None:
    deps = {"base_url": "https://api.test", "get_access_token": lambda: None}
    api = create_bridge_api_client(deps)
    with pytest.raises(RuntimeError, match="login"):
        await api.register_bridge_environment(_bridge_config())


@pytest.mark.asyncio
async def test_poll_for_work_validates_environment_id() -> None:
    deps = {"base_url": "https://api.test", "get_access_token": lambda: "t"}
    api = create_bridge_api_client(deps)
    with pytest.raises(ValueError, match="environmentId"):
        await api.poll_for_work("../bad", "secret")
