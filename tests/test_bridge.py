"""Tests for bridge session ID compatibility helpers."""

from __future__ import annotations

import pytest

from claude_code.bridge import session_id_compat as sic


@pytest.fixture(autouse=True)
def reset_cse_gate() -> None:
    sic._is_cse_shim_enabled = None  # noqa: SLF001
    yield
    sic._is_cse_shim_enabled = None  # noqa: SLF001


def test_to_compat_session_id_no_cse_prefix_unchanged() -> None:
    assert sic.to_compat_session_id("plain") == "plain"


def test_to_compat_session_id_shim_disabled_leaves_cse() -> None:
    sic.set_cse_shim_gate(lambda: False)
    assert sic.to_compat_session_id("cse_abc") == "cse_abc"


def test_to_compat_session_id_shim_enabled_rewrites() -> None:
    sic.set_cse_shim_gate(lambda: True)
    assert sic.to_compat_session_id("cse_xyz123") == "session_xyz123"


def test_to_infra_session_id() -> None:
    assert sic.to_infra_session_id("other") == "other"
    assert sic.to_infra_session_id("session_qq") == "cse_qq"
