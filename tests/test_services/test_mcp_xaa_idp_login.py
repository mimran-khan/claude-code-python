"""Unit tests for XAA IdP login helpers."""

from __future__ import annotations

import httpx

from claude_code.services.mcp.xaa_idp_login import discover_oidc, get_xaa_idp_settings, issuer_key


def test_issuer_key_normalizes_host_and_path() -> None:
    assert issuer_key("https://EXAMPLE.com/foo/") == "https://example.com/foo"


def test_get_xaa_idp_settings_reads_nested_dict() -> None:
    s = get_xaa_idp_settings(
        {"xaaIdp": {"issuer": "https://idp", "clientId": "cid", "callbackPort": 9}}
    )
    assert s is not None
    assert s.issuer == "https://idp"
    assert s.client_id == "cid"
    assert s.callback_port == 9


def test_discover_oidc_parses_metadata() -> None:
    body = {
        "issuer": "https://idp.example",
        "authorization_endpoint": "https://idp.example/oauth/authorize",
        "token_endpoint": "https://idp.example/oauth/token",
    }

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "idp.example"
        assert request.url.path.endswith("openid-configuration")
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(_handler)
    with httpx.Client(transport=transport) as client:
        meta = discover_oidc("https://idp.example", client)
    assert str(meta.authorization_endpoint).startswith("https://")
    assert str(meta.token_endpoint).startswith("https://")
