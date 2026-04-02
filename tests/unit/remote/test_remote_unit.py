"""Unit tests for ``claude_code.remote`` package."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.remote import message_adapter
from claude_code.remote.permission_bridge import PendingPermission, RemotePermissionBridge
from claude_code.remote.session import (
    RemotePermissionResponseAllow,
    RemotePermissionResponseDeny,
    RemoteSessionConfig,
    RemoteSessionManager,
)
from claude_code.remote.types import RemoteSession
from claude_code.remote.websocket import SessionsWebSocket


def test_remote_session_dataclass_defaults() -> None:
    rs = RemoteSession()
    assert rs.state == "ready"


def test_adapt_sdk_message_assistant() -> None:
    out = message_adapter.adapt_sdk_message({"type": "assistant", "content": [], "model": "m"})
    assert out["type"] == "assistant_message"


def test_adapt_sdk_message_user_and_tool_result() -> None:
    u = message_adapter.adapt_sdk_message({"type": "user", "content": [1]})
    assert u["type"] == "user_message"
    t = message_adapter.adapt_sdk_message({"type": "tool_result", "tool_use_id": "x", "content": "c"})
    assert t["type"] == "tool_result"


def test_adapt_sdk_message_progress() -> None:
    p = message_adapter.adapt_sdk_message({"type": "progress", "tool_name": "bash", "progress": 0.5})
    assert p["type"] == "progress"


def test_adapt_sdk_message_unknown_passthrough() -> None:
    raw = {"type": "custom", "x": 1}
    assert message_adapter.adapt_sdk_message(raw) == raw


def test_adapt_remote_message_shapes() -> None:
    a = message_adapter.adapt_remote_message({"type": "assistant_message", "content": [], "model": "m"})
    assert a["type"] == "assistant"
    u = message_adapter.adapt_remote_message({"type": "user_message", "content": []})
    assert u["type"] == "user"
    tr = message_adapter.adapt_remote_message(
        {"type": "tool_result", "tool_use_id": "z", "content": "c", "is_error": True}
    )
    assert tr["type"] == "tool_result"


def test_adapt_remote_unknown_passthrough() -> None:
    raw = {"type": "x"}
    assert message_adapter.adapt_remote_message(raw) == raw


def test_extract_content_blocks_string_and_list() -> None:
    assert message_adapter.extract_content_blocks({"content": "hi"}) == [{"type": "text", "text": "hi"}]
    assert message_adapter.extract_content_blocks({"content": [{"type": "text", "text": "a"}]}) == [
        {"type": "text", "text": "a"}
    ]
    assert message_adapter.extract_content_blocks({}) == []


def test_get_tool_uses_filters() -> None:
    msg = {"content": [{"type": "tool_use", "id": 1}, {"type": "text", "text": "t"}]}
    assert len(message_adapter.get_tool_uses(msg)) == 1


def test_get_text_content_joins() -> None:
    msg = {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}
    assert message_adapter.get_text_content(msg) == "a\nb"


@pytest.mark.asyncio
async def test_remote_session_manager_connect_disconnect_callbacks() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o")
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    await mgr.connect()
    assert mgr.is_connected is True
    cb.on_connected.assert_called_once()
    await mgr.disconnect()
    assert mgr.is_connected is False


@pytest.mark.asyncio
async def test_send_permission_response_allow_and_deny() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o")
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    await mgr.connect()
    await mgr.send_permission_response("r1", RemotePermissionResponseAllow(updated_input={"k": "v"}))
    await mgr.send_permission_response("r2", RemotePermissionResponseDeny(message="no"))
    await mgr.disconnect()


@pytest.mark.asyncio
async def test_send_interrupt_viewer_only_noop() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o", viewer_only=True)
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    await mgr.connect()
    await mgr.send_interrupt()
    await mgr.disconnect()


@pytest.mark.asyncio
async def test_send_user_input() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o")
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    await mgr.connect()
    await mgr.send_user_input("hello")
    await mgr.disconnect()


@pytest.mark.asyncio
async def test_send_event_when_disconnected_no_crash() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o")
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    await mgr._send_event({"type": "x"})


@pytest.mark.asyncio
async def test_attempt_reconnect_with_instant_sleep() -> None:
    cb = MagicMock()
    cfg = RemoteSessionConfig(session_id="s1", get_access_token=lambda: "t", org_uuid="o")
    mgr = RemoteSessionManager(config=cfg, callbacks=cb)
    mgr._should_reconnect = True
    mgr._connected = False
    with patch("claude_code.remote.session.asyncio.sleep", new_callable=AsyncMock):
        await mgr._attempt_reconnect()
    assert mgr.is_connected is True


@pytest.mark.asyncio
async def test_permission_bridge_approve_flow() -> None:
    bridge = RemotePermissionBridge()

    async def handler(p: PendingPermission) -> None:
        bridge.approve(p.request_id, {"a": 1})

    bridge.set_handler(handler)
    resp = await bridge.handle_permission_request("rid", "tool", {"x": 1})
    assert isinstance(resp, RemotePermissionResponseAllow)
    assert resp.updated_input == {"a": 1}


@pytest.mark.asyncio
async def test_permission_bridge_deny_flow() -> None:
    bridge = RemotePermissionBridge()

    async def handler(p: PendingPermission) -> None:
        bridge.deny(p.request_id, "nope")

    bridge.set_handler(handler)
    resp = await bridge.handle_permission_request("rid2", "tool", {})
    assert isinstance(resp, RemotePermissionResponseDeny)
    assert resp.message == "nope"


def test_permission_bridge_approve_unknown_returns_false() -> None:
    bridge = RemotePermissionBridge()
    assert bridge.approve("missing") is False


def test_permission_bridge_manual_approve_updates_input() -> None:
    bridge = RemotePermissionBridge()
    resolved: list[object] = []

    def resolve(r: object) -> None:
        resolved.append(r)

    pending = PendingPermission(
        request_id="id1",
        tool_name="t",
        tool_input={"k": 2},
        context={},
        resolve=resolve,
    )
    bridge._pending["id1"] = pending
    assert bridge.approve("id1", {"z": 3}) is True
    assert isinstance(resolved[0], RemotePermissionResponseAllow)
    assert resolved[0].updated_input == {"z": 3}


def test_permission_bridge_deny_manual() -> None:
    bridge = RemotePermissionBridge()
    resolved: list[object] = []

    def resolve(r: object) -> None:
        resolved.append(r)

    pending = PendingPermission("id2", "t", {}, {}, resolve)
    bridge._pending["id2"] = pending
    assert bridge.deny("id2", "blocked") is True
    assert isinstance(resolved[0], RemotePermissionResponseDeny)


def test_permission_bridge_get_pending_and_clear() -> None:
    bridge = RemotePermissionBridge()

    def resolve(_r: object) -> None:
        pass

    p = PendingPermission("x", "t", {}, {}, resolve)
    bridge._pending["x"] = p
    assert bridge.get_pending("x") is p
    assert "x" in bridge.get_all_pending()
    bridge.clear_all()
    assert bridge.get_all_pending() == {}


@pytest.mark.asyncio
async def test_sessions_websocket_connect_disconnect() -> None:
    cb = MagicMock()
    ws = SessionsWebSocket(url="wss://x", callbacks=cb)
    await ws.connect()
    assert ws.is_connected is True
    cb.on_open.assert_called_once()
    await ws.disconnect()
    assert ws.is_connected is False
    cb.on_close.assert_called_once()


@pytest.mark.asyncio
async def test_sessions_websocket_send_queues_when_disconnected() -> None:
    cb = MagicMock()
    ws = SessionsWebSocket(url="wss://x", callbacks=cb)
    await ws.send({"type": "a"})
    assert len(ws._message_queue) == 1


@pytest.mark.asyncio
async def test_sessions_websocket_send_when_connected() -> None:
    cb = MagicMock()
    ws = SessionsWebSocket(url="wss://x", callbacks=cb)
    await ws.connect()
    await ws.send({"type": "b"})
    await ws.disconnect()
