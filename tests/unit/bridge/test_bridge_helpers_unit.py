"""Unit tests for small bridge helper modules."""

from __future__ import annotations

import asyncio
import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from claude_code.bridge import bridge_status_util, jwt_utils, session_id_compat

_real_asyncio_sleep = asyncio.sleep


async def _scheduler_sleep_stub(delay: float) -> None:
    """Yield to the loop; treat all delays as instant (no wall-clock wait)."""
    _ = delay
    await _real_asyncio_sleep(0)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _make_jwt_payload_segment(payload: dict[str, object]) -> str:
    return _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def test_decode_jwt_payload_valid() -> None:
    body = _make_jwt_payload_segment({"sub": "u", "exp": 2000000000})
    token = f"hdr.{body}.sig"
    out = jwt_utils.decode_jwt_payload(token)
    assert isinstance(out, dict)
    assert out.get("sub") == "u"


def test_decode_jwt_payload_strips_sk_ant_prefix() -> None:
    body = _make_jwt_payload_segment({"exp": 1})
    token = f"sk-ant-si-hdr.{body}.sig"
    out = jwt_utils.decode_jwt_payload(token)
    assert isinstance(out, dict)


def test_decode_jwt_payload_invalid_returns_none() -> None:
    assert jwt_utils.decode_jwt_payload("not-a-jwt") is None
    assert jwt_utils.decode_jwt_payload("a.b") is None


def test_decode_jwt_expiry() -> None:
    body = _make_jwt_payload_segment({"exp": 12345})
    assert jwt_utils.decode_jwt_expiry(f"x.{body}.y") == 12345


def test_decode_jwt_expiry_missing_returns_none() -> None:
    body = _make_jwt_payload_segment({"sub": "x"})
    assert jwt_utils.decode_jwt_expiry(f"x.{body}.y") is None


@pytest.mark.asyncio
async def test_token_refresh_scheduler_invokes_on_refresh() -> None:
    with (
        patch.object(jwt_utils.asyncio, "sleep", side_effect=_scheduler_sleep_stub),
        patch.object(jwt_utils.time, "time", return_value=0),
    ):
        # exp=0 with time.time()=0 → delay_ms <= 0 → refresh runs without long sleep
        body = _make_jwt_payload_segment({"exp": 0})
        token = f"h.{body}.s"
        on_refresh = MagicMock()
        sched = jwt_utils.create_token_refresh_scheduler(
            get_access_token=lambda: "tok2",
            on_refresh=on_refresh,
            label="t",
            refresh_buffer_ms=0,
        )
        sched["schedule"]("sid", token)
        for _ in range(50):
            if on_refresh.called:
                break
            await asyncio.sleep(0)
        on_refresh.assert_called()


@pytest.mark.asyncio
async def test_token_refresh_scheduler_cancel_all_cleans() -> None:
    with (
        patch.object(jwt_utils.asyncio, "sleep", side_effect=_scheduler_sleep_stub),
        patch.object(jwt_utils.time, "time", return_value=0),
    ):
        body = _make_jwt_payload_segment({"exp": 9999999999})
        token = f"h.{body}.s"
        sched = jwt_utils.create_token_refresh_scheduler(
            get_access_token=lambda: None,
            on_refresh=lambda *_: None,
            label="t",
        )
        sched["schedule"]("sid", token)
        sched["cancel_all"]()


def test_bridge_status_util_format_duration() -> None:
    assert "s" in bridge_status_util.format_duration(30_000)
    assert "m" in bridge_status_util.format_duration(120_000)


def test_truncate_prompt_respects_width() -> None:
    assert len(bridge_status_util.truncate_prompt("abc", 2)) <= 2


def test_build_bridge_urls() -> None:
    u1 = bridge_status_util.build_bridge_connect_url("env1", "https://x.com/")
    assert "bridge=env1" in u1
    u2 = bridge_status_util.build_bridge_session_url("s1", "env1", None)
    assert "/session/s1" in u2
    assert "bridge=env1" in u2


def test_get_bridge_status_matrix() -> None:
    assert bridge_status_util.get_bridge_status(error="e", connected=False, session_active=False, reconnecting=False)[
        "color"
    ] == "error"
    st = bridge_status_util.get_bridge_status(error=None, connected=False, session_active=False, reconnecting=True)
    assert st["color"] == "warning"
    st2 = bridge_status_util.get_bridge_status(error=None, connected=True, session_active=False, reconnecting=False)
    assert st2["color"] == "success"


def test_footer_and_osc8() -> None:
    assert "http" in bridge_status_util.build_idle_footer_text("http://u")
    assert "\x1b]8;;" in bridge_status_util.wrap_with_osc8_link("t", "http://u")


def test_compute_glimmer_and_shimmer() -> None:
    idx = bridge_status_util.compute_glimmer_index(5, 10)
    assert isinstance(idx, int)
    seg = bridge_status_util.compute_shimmer_segments("hello", 2)
    assert "before" in seg and "shimmer" in seg


def test_session_id_compat_roundtrip() -> None:
    session_id_compat.set_cse_shim_gate(lambda: True)
    assert session_id_compat.to_compat_session_id("cse_abc") == "session_abc"
    assert session_id_compat.to_infra_session_id("session_abc") == "cse_abc"
    session_id_compat.set_cse_shim_gate(lambda: False)
    assert session_id_compat.to_compat_session_id("cse_x") == "cse_x"


def test_session_id_compat_no_prefix_passthrough() -> None:
    assert session_id_compat.to_compat_session_id("plain") == "plain"
    assert session_id_compat.to_infra_session_id("plain") == "plain"
