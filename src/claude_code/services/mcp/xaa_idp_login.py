"""
XAA IdP login: OIDC authorization_code + PKCE, cache id_token by issuer.

Migrated from: services/mcp/xaaIdpLogin.ts
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, cast
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from pydantic import AnyHttpUrl, BaseModel, ValidationError

from ...utils.env_utils import is_env_truthy
from ...utils.secure_storage.types import StorageUpdateResult
from .auth import generate_code_challenge, generate_code_verifier
from .oauth_port import build_redirect_uri, find_available_port_sync

logger = logging.getLogger(__name__)

IDP_LOGIN_TIMEOUT_S = 300.0
IDP_REQUEST_TIMEOUT_S = 30.0
ID_TOKEN_EXPIRY_BUFFER_S = 60


def is_xaa_enabled() -> bool:
    return is_env_truthy(os.environ.get("CLAUDE_CODE_ENABLE_XAA"))


@dataclass(frozen=True)
class XaaIdpSettings:
    issuer: str
    client_id: str
    callback_port: int | None = None


def get_xaa_idp_settings(settings: dict[str, Any] | None = None) -> XaaIdpSettings | None:
    """Read ``settings.xaaIdp`` when the host passes a settings dict."""
    if not settings:
        return None
    raw = settings.get("xaaIdp")
    if not isinstance(raw, dict):
        return None
    issuer = raw.get("issuer")
    cid = raw.get("clientId") or raw.get("client_id")
    if not isinstance(issuer, str) or not isinstance(cid, str):
        return None
    cb = raw.get("callbackPort") or raw.get("callback_port")
    cb_i = int(cb) if isinstance(cb, int) or (isinstance(cb, str) and cb.isdigit()) else None
    return XaaIdpSettings(issuer=issuer, client_id=cid, callback_port=cb_i)


def issuer_key(issuer: str) -> str:
    try:
        u = urlparse(issuer)
        path = u.path.rstrip("/") or ""
        host = (u.hostname or u.netloc or "").lower()
        scheme = u.scheme.lower()
        return f"{scheme}://{host}{path}"
    except Exception:
        return issuer.rstrip("/")


class OidcMetadata(BaseModel):
    issuer: str
    authorization_endpoint: AnyHttpUrl
    token_endpoint: AnyHttpUrl


def discover_oidc(idp_issuer: str, client: httpx.Client | None = None) -> OidcMetadata:
    base = idp_issuer if idp_issuer.endswith("/") else idp_issuer + "/"
    url = urljoin(base, ".well-known/openid-configuration")
    own_client = client is None
    c = client or httpx.Client(timeout=IDP_REQUEST_TIMEOUT_S)
    try:
        r = c.get(url, headers={"Accept": "application/json"})
        r.raise_for_status()
        try:
            body = r.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"XAA IdP: OIDC discovery returned non-JSON at {url}") from e
        try:
            meta = OidcMetadata.model_validate(body)
        except ValidationError as e:
            raise RuntimeError(f"XAA IdP: invalid OIDC metadata: {e}") from e
        if urlparse(str(meta.token_endpoint)).scheme != "https":
            raise RuntimeError(f"XAA IdP: refusing non-HTTPS token endpoint: {meta.token_endpoint}")
        return meta
    finally:
        if own_client:
            c.close()


def _jwt_exp(jwt: str) -> int | None:
    parts = jwt.split(".")
    if len(parts) != 3:
        return None
    try:
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad).decode("utf-8"))
        exp = payload.get("exp")
        return int(exp) if isinstance(exp, int) else None
    except Exception:
        return None


def _credential_store() -> Any:
    from ...utils.secure_storage import get_credentials_json_store

    return get_credentials_json_store()


def get_cached_idp_id_token(idp_issuer: str) -> str | None:
    storage = _credential_store()
    data = storage.read() or {}
    mcp = data.get("mcpXaaIdp") or {}
    entry = mcp.get(issuer_key(idp_issuer))
    if not isinstance(entry, dict):
        return None
    token = entry.get("idToken")
    exp = entry.get("expiresAt")
    if not isinstance(token, str) or not isinstance(exp, (int, float)):
        return None
    remaining_ms = float(exp) - time.time() * 1000
    if remaining_ms <= ID_TOKEN_EXPIRY_BUFFER_S * 1000:
        return None
    return token


def _save_idp_id_token(idp_issuer: str, id_token: str, expires_at_ms: int) -> None:
    storage = _credential_store()
    existing = storage.read() or {}
    mcp = dict(existing.get("mcpXaaIdp") or {})
    mcp[issuer_key(idp_issuer)] = {"idToken": id_token, "expiresAt": expires_at_ms}
    storage.update({**existing, "mcpXaaIdp": mcp})


def save_idp_id_token_from_jwt(idp_issuer: str, id_token: str) -> int:
    exp = _jwt_exp(id_token)
    expires_at = int(exp * 1000) if exp else int(time.time() * 1000) + 3600 * 1000
    _save_idp_id_token(idp_issuer, id_token, expires_at)
    return expires_at


def clear_idp_id_token(idp_issuer: str) -> None:
    storage = _credential_store()
    existing = storage.read() or {}
    mcp = dict(existing.get("mcpXaaIdp") or {})
    key = issuer_key(idp_issuer)
    if key not in mcp:
        return
    del mcp[key]
    storage.update({**existing, "mcpXaaIdp": mcp})


def save_idp_client_secret(
    idp_issuer: str,
    client_secret: str,
) -> StorageUpdateResult:
    storage = _credential_store()
    existing = storage.read() or {}
    cfg = dict(existing.get("mcpXaaIdpConfig") or {})
    cfg[issuer_key(idp_issuer)] = {"clientSecret": client_secret}
    return cast(StorageUpdateResult, storage.update({**existing, "mcpXaaIdpConfig": cfg}))


def get_idp_client_secret(idp_issuer: str) -> str | None:
    storage = _credential_store()
    data = storage.read() or {}
    cfg = (data.get("mcpXaaIdpConfig") or {}).get(issuer_key(idp_issuer))
    if not isinstance(cfg, dict):
        return None
    secret = cfg.get("clientSecret")
    return secret if isinstance(secret, str) else None


def clear_idp_client_secret(idp_issuer: str) -> None:
    storage = _credential_store()
    existing = storage.read() or {}
    cfg = dict(existing.get("mcpXaaIdpConfig") or {})
    key = issuer_key(idp_issuer)
    if key not in cfg:
        return
    del cfg[key]
    storage.update({**existing, "mcpXaaIdpConfig": cfg})


def _wait_for_callback(
    port: int,
    expected_state: str,
    abort_event: threading.Event | None,
    on_listening: Callable[[], None],
) -> str:
    result: dict[str, str | Exception] = {}
    server: HTTPServer | None = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            assert self.server is not None
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            q = parse_qs(parsed.query)
            err_vals = q.get("error") or []
            err = err_vals[0] if err_vals else None
            if err:
                desc_vals = q.get("error_description") or []
                desc = desc_vals[0] if desc_vals else ""
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"<html><body><h3>IdP login failed</h3><p>{html.escape(str(err))}</p>"
                    f"<p>{html.escape(str(desc))}</p></body></html>".encode()
                )
                result["err"] = RuntimeError(f"XAA IdP: {err}{' — ' + desc if desc else ''}")
                self.server.shutdown()
                return
            state_vals = q.get("state") or []
            code_vals = q.get("code") or []
            state = state_vals[0] if state_vals else None
            code = code_vals[0] if code_vals else None
            if state != expected_state:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h3>State mismatch</h3></body></html>")
                result["err"] = RuntimeError("XAA IdP: state mismatch (possible CSRF)")
                self.server.shutdown()
                return
            if not code:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h3>Missing code</h3></body></html>")
                result["err"] = RuntimeError("XAA IdP: callback missing code")
                self.server.shutdown()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            msg = "<html><body><p>IdP login complete. You may close this tab.</p></body></html>"
            self.wfile.write(msg.encode("utf-8"))
            result["code"] = code
            self.server.shutdown()

    def serve() -> None:
        nonlocal server
        try:
            server = HTTPServer(("127.0.0.1", port), Handler)
        except OSError as e:
            result["err"] = e
            return
        try:
            on_listening()
        except Exception as e:
            result["err"] = e
            server.shutdown()
            return
        server.serve_forever(poll_interval=0.2)

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    deadline = time.monotonic() + IDP_LOGIN_TIMEOUT_S
    while time.monotonic() < deadline:
        if abort_event and abort_event.is_set():
            if server:
                server.shutdown()
            raise RuntimeError("XAA IdP: login cancelled")
        if "code" in result:
            if server:
                server.server_close()
            return str(result["code"])
        if "err" in result:
            if server:
                server.server_close()
            err = result["err"]
            raise err if isinstance(err, BaseException) else RuntimeError(str(err))
        time.sleep(0.05)
    if server:
        server.shutdown()
        server.server_close()
    raise RuntimeError("XAA IdP: login timed out")


@dataclass
class IdpLoginOptions:
    idp_issuer: str
    idp_client_id: str
    idp_client_secret: str | None = None
    callback_port: int | None = None
    on_authorization_url: Callable[[str], None] | None = None
    skip_browser_open: bool = False
    abort_event: threading.Event | None = None


def acquire_idp_id_token(opts: IdpLoginOptions) -> str:
    cached = get_cached_idp_id_token(opts.idp_issuer)
    if cached:
        logger.debug("xaa_cached_id_token", extra={"issuer": opts.idp_issuer})
        return cached

    meta = discover_oidc(opts.idp_issuer)
    port = opts.callback_port if opts.callback_port is not None else find_available_port_sync()
    redirect_uri = build_redirect_uri(port)
    state = secrets.token_urlsafe(32)
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    from urllib.parse import urlencode

    auth_params = {
        "response_type": "code",
        "client_id": opts.idp_client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{meta.authorization_endpoint}?{urlencode(auth_params)}"

    def on_listen() -> None:
        if opts.on_authorization_url:
            opts.on_authorization_url(auth_url)
        if not opts.skip_browser_open:
            try:
                import webbrowser

                webbrowser.open(auth_url)
            except Exception as exc:
                logger.warning("xaa_browser_open_failed", extra={"error": str(exc)})

    code = _wait_for_callback(port, state, opts.abort_event, on_listen)

    token_data: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": opts.idp_client_id,
        "code_verifier": verifier,
    }
    if opts.idp_client_secret:
        token_data["client_secret"] = opts.idp_client_secret

    with httpx.Client(timeout=IDP_REQUEST_TIMEOUT_S) as c:
        r = c.post(
            str(meta.token_endpoint),
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        tokens = r.json()
    id_token = tokens.get("id_token")
    if not isinstance(id_token, str):
        raise RuntimeError("XAA IdP: token response missing id_token (check scope=openid)")
    exp = _jwt_exp(id_token)
    ttl_s = int(tokens.get("expires_in", 3600))
    expires_at = int(exp * 1000) if exp else int(time.time() * 1000) + ttl_s * 1000
    _save_idp_id_token(opts.idp_issuer, id_token, expires_at)
    return id_token
