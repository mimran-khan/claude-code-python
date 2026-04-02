"""
Cross-App Access (XAA): id_token -> ID-JAG -> MCP access_token.

Migrated from: services/mcp/xaa.ts
"""

from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlparse

import httpx
from mcp.client.auth.utils import (
    build_oauth_authorization_server_metadata_discovery_urls,
    build_protected_resource_metadata_discovery_urls,
)
from mcp.shared.auth import OAuthMetadata, ProtectedResourceMetadata
from pydantic import ValidationError

logger = logging.getLogger(__name__)

XAA_REQUEST_TIMEOUT_S = 30.0
TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
JWT_BEARER_GRANT = "urn:ietf:params:oauth:grant-type:jwt-bearer"
ID_JAG_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:id-jag"
ID_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:id_token"

_SENSITIVE_TOKEN_RE = re.compile(
    r'"(access_token|refresh_token|id_token|assertion|subject_token|client_secret)"\s*:\s*"[^"]*"',
    re.IGNORECASE,
)


def _normalize_url(url: str) -> str:
    try:
        return str(httpx.URL(url)).rstrip("/")
    except Exception:
        return url.rstrip("/")


def _coerce_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _redact_tokens(raw: Any) -> str:
    s = raw if isinstance(raw, str) else json.dumps(raw, default=str)
    return _SENSITIVE_TOKEN_RE.sub(lambda m: f'"{m.group(1)}":"[REDACTED]"', s)


class XaaTokenExchangeError(Exception):
    """IdP token-exchange failure; ``should_clear_id_token`` guides cache policy."""

    def __init__(self, message: str, should_clear_id_token: bool) -> None:
        super().__init__(message)
        self.should_clear_id_token = should_clear_id_token


@dataclass(frozen=True)
class JwtAuthGrantResult:
    jwt_auth_grant: str
    expires_in: int | None = None
    scope: str | None = None


@dataclass(frozen=True)
class XaaTokenResult:
    access_token: str
    token_type: str
    expires_in: int | None = None
    scope: str | None = None
    refresh_token: str | None = None


@dataclass(frozen=True)
class XaaResult:
    access_token: str
    token_type: str
    authorization_server_url: str
    expires_in: int | None = None
    scope: str | None = None
    refresh_token: str | None = None


def _discover_prm(server_url: str, client: httpx.Client) -> ProtectedResourceMetadata:
    last_err: str | None = None
    for url in build_protected_resource_metadata_discovery_urls(None, server_url):
        try:
            r = client.get(url, headers={"Accept": "application/json"})
        except Exception as e:
            last_err = str(e)
            continue
        if r.status_code != 200:
            continue
        try:
            prm = ProtectedResourceMetadata.model_validate_json(r.content)
        except ValidationError:
            continue
        if not prm.authorization_servers:
            last_err = "PRM missing authorization_servers"
            continue
        if _normalize_url(str(prm.resource)) != _normalize_url(server_url):
            raise RuntimeError(f"XAA: PRM resource mismatch: expected {server_url}, got {prm.resource}")
        return prm
    raise RuntimeError(f"XAA: PRM discovery failed: {last_err or 'no valid metadata'}")


def _discover_as(as_url: str, client: httpx.Client) -> OAuthMetadata:
    last_err: str | None = None
    for url in build_oauth_authorization_server_metadata_discovery_urls(as_url, as_url):
        try:
            r = client.get(url, headers={"Accept": "application/json"})
        except Exception as e:
            last_err = str(e)
            continue
        if r.status_code != 200:
            continue
        try:
            meta = OAuthMetadata.model_validate_json(r.content)
        except ValidationError:
            continue
        if not meta.issuer or not meta.token_endpoint:
            last_err = "AS metadata missing issuer or token_endpoint"
            continue
        if _normalize_url(str(meta.issuer)) != _normalize_url(as_url):
            raise RuntimeError(f"XAA: AS issuer mismatch: expected {as_url}, got {meta.issuer}")
        if urlparse(str(meta.token_endpoint)).scheme != "https":
            raise RuntimeError(f"XAA: refusing non-HTTPS token endpoint: {meta.token_endpoint}")
        return meta
    raise RuntimeError(f"XAA: AS metadata discovery failed: {last_err or as_url}")


def request_jwt_authorization_grant(
    client: httpx.Client,
    *,
    token_endpoint: str,
    audience: str,
    resource: str,
    id_token: str,
    client_id: str,
    client_secret: str | None = None,
    scope: str | None = None,
) -> JwtAuthGrantResult:
    data: dict[str, str] = {
        "grant_type": TOKEN_EXCHANGE_GRANT,
        "requested_token_type": ID_JAG_TOKEN_TYPE,
        "audience": audience,
        "resource": resource,
        "subject_token": id_token,
        "subject_token_type": ID_TOKEN_TYPE,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    if scope:
        data["scope"] = scope
    r = client.post(
        token_endpoint,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not r.is_success:
        body = _redact_tokens(r.text)[:200]
        should_clear = r.status_code < 500
        raise XaaTokenExchangeError(
            f"XAA: token exchange failed: HTTP {r.status_code}: {body}",
            should_clear,
        )
    try:
        raw = r.json()
    except json.JSONDecodeError:
        raise XaaTokenExchangeError(
            f"XAA: token exchange returned non-JSON at {token_endpoint}",
            False,
        ) from None
    access = raw.get("access_token")
    issued = raw.get("issued_token_type")
    if not isinstance(access, str):
        raise XaaTokenExchangeError(
            f"XAA: token exchange response missing access_token: {_redact_tokens(raw)}",
            True,
        )
    if issued != ID_JAG_TOKEN_TYPE:
        raise XaaTokenExchangeError(
            f"XAA: unexpected issued_token_type: {issued}",
            True,
        )
    exp = raw.get("expires_in")
    exp_i = int(exp) if exp is not None and str(exp).isdigit() else None
    sc = raw.get("scope")
    scope_s = sc if isinstance(sc, str) else None
    return JwtAuthGrantResult(jwt_auth_grant=access, expires_in=exp_i, scope=scope_s)


def exchange_jwt_auth_grant(
    client: httpx.Client,
    *,
    token_endpoint: str,
    assertion: str,
    client_id: str,
    client_secret: str,
    auth_method: str = "client_secret_basic",
    scope: str | None = None,
) -> XaaTokenResult:
    data: dict[str, str] = {
        "grant_type": JWT_BEARER_GRANT,
        "assertion": assertion,
    }
    if scope:
        data["scope"] = scope
    headers: dict[str, str] = {"Content-Type": "application/x-www-form-urlencoded"}
    if auth_method == "client_secret_basic":
        enc_id = quote(client_id, safe="")
        enc_sec = quote(client_secret, safe="")
        basic = base64.b64encode(f"{enc_id}:{enc_sec}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    else:
        data["client_id"] = client_id
        data["client_secret"] = client_secret
    r = client.post(token_endpoint, data=data, headers=headers)
    if not r.is_success:
        raise RuntimeError(f"XAA: jwt-bearer grant failed: HTTP {r.status_code}: {_redact_tokens(r.text)[:200]}")
    try:
        raw = r.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(f"XAA: jwt-bearer returned non-JSON at {token_endpoint}") from e
    at = raw.get("access_token")
    if not isinstance(at, str) or not at:
        raise RuntimeError(f"XAA: jwt-bearer response invalid: {_redact_tokens(raw)}")
    tt = raw.get("token_type")
    token_type = tt if isinstance(tt, str) else "Bearer"
    exp = raw.get("expires_in")
    exp_i = int(exp) if exp is not None and str(exp).isdigit() else None
    sc = raw.get("scope")
    rt = raw.get("refresh_token")
    return XaaTokenResult(
        access_token=at,
        token_type=token_type,
        expires_in=exp_i,
        scope=sc if isinstance(sc, str) else None,
        refresh_token=rt if isinstance(rt, str) else None,
    )


@dataclass
class XaaConfig:
    client_id: str
    client_secret: str
    idp_client_id: str
    idp_id_token: str
    idp_token_endpoint: str
    idp_client_secret: str | None = None


def perform_cross_app_access(
    server_url: str,
    config: XaaConfig,
    server_name: str = "xaa",
) -> XaaResult:
    with httpx.Client(timeout=XAA_REQUEST_TIMEOUT_S) as client:
        logger.debug("xaa_prm", extra={"server": server_name, "url": server_url})
        prm = _discover_prm(server_url, client)
        as_urls = [str(u) for u in prm.authorization_servers]
        as_errors: list[str] = []
        as_meta: OAuthMetadata | None = None
        for as_url in as_urls:
            try:
                candidate = _discover_as(as_url, client)
            except Exception as e:
                as_errors.append(f"{as_url}: {e}")
                continue
            grants = candidate.grant_types_supported
            if grants and JWT_BEARER_GRANT not in grants:
                as_errors.append(f"{as_url}: no jwt-bearer (supported: {', '.join(grants)})")
                continue
            as_meta = candidate
            break
        if as_meta is None:
            raise RuntimeError("XAA: no authorization server supports jwt-bearer. Tried: " + "; ".join(as_errors))
        methods = as_meta.token_endpoint_auth_methods_supported
        auth_method = (
            "client_secret_post"
            if methods and "client_secret_basic" not in methods and "client_secret_post" in methods
            else "client_secret_basic"
        )
        logger.debug(
            "xaa_as",
            extra={
                "server": server_name,
                "issuer": str(as_meta.issuer),
                "token_endpoint": str(as_meta.token_endpoint),
                "auth_method": auth_method,
            },
        )
        jag = request_jwt_authorization_grant(
            client,
            token_endpoint=config.idp_token_endpoint,
            audience=str(as_meta.issuer),
            resource=str(prm.resource),
            id_token=config.idp_id_token,
            client_id=config.idp_client_id,
            client_secret=config.idp_client_secret,
        )
        tokens = exchange_jwt_auth_grant(
            client,
            token_endpoint=str(as_meta.token_endpoint),
            assertion=jag.jwt_auth_grant,
            client_id=config.client_id,
            client_secret=config.client_secret,
            auth_method=auth_method,
        )
        return XaaResult(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            scope=tokens.scope,
            refresh_token=tokens.refresh_token,
            authorization_server_url=str(as_meta.issuer),
        )
