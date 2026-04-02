"""HTTP client for environments / work API (ported from bridge/bridgeApi.ts)."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, TypedDict, cast

import httpx

from claude_code.bridge.debug_utils import debug_body, extract_error_detail
from claude_code.bridge.types import (
    BRIDGE_LOGIN_INSTRUCTION,
    BridgeConfig,
    PermissionResponseEvent,
    WorkResponse,
)

BETA_HEADER = "environments-2025-11-01"
_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_bridge_id(id: str, label: str) -> str:
    if not id or not _SAFE_ID.match(id):
        raise ValueError(f"Invalid {label}: contains unsafe characters")
    return id


class BridgeFatalError(Exception):
    def __init__(self, message: str, status: int, error_type: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.error_type = error_type


class BridgeApiDeps(TypedDict, total=False):
    base_url: str
    get_access_token: Callable[[], str | None]
    runner_version: str
    on_debug: Callable[[str], None]
    on_auth401: Callable[[str], Any]
    get_trusted_device_token: Callable[[], str | None]


def is_expired_error_type(error_type: str | None) -> bool:
    if not error_type:
        return False
    return "expired" in error_type or "lifetime" in error_type


def is_suppressible403(err: BridgeFatalError) -> bool:
    if err.status != 403:
        return False
    m = str(err)
    return "external_poll_sessions" in m or "environments:manage" in m


def _error_type(data: Any) -> str | None:
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and isinstance(err.get("type"), str):
            return err["type"]
    return None


def _handle_error_status(status: int, data: Any, context: str) -> None:
    if status in (200, 204):
        return
    detail = extract_error_detail(data)
    et = _error_type(data)
    if status == 401:
        raise BridgeFatalError(
            f"{context}: Authentication failed (401){f': {detail}' if detail else ''}. {BRIDGE_LOGIN_INSTRUCTION}",
            401,
            et,
        )
    if status == 403:
        msg = (
            "Remote Control session has expired. Please restart with `claude remote-control` or /remote-control."
            if is_expired_error_type(et)
            else (
                f"{context}: Access denied (403){f': {detail}' if detail else ''}. Check your organization permissions."
            )
        )
        raise BridgeFatalError(msg, 403, et)
    if status == 404:
        msg404 = f"{context}: Not found (404). Remote Control may not be available for this organization."
        raise BridgeFatalError(detail or msg404, 404, et)
    if status == 410:
        raise BridgeFatalError(
            detail
            or "Remote Control session has expired. Please restart with `claude remote-control` or /remote-control.",
            410,
            et or "environment_expired",
        )
    if status == 429:
        raise RuntimeError(f"{context}: Rate limited (429). Polling too frequently.")
    raise RuntimeError(f"{context}: Failed with status {status}{f': {detail}' if detail else ''}")


def create_bridge_api_client(deps: BridgeApiDeps) -> Any:
    base_url = deps["base_url"].rstrip("/")
    get_token = deps["get_access_token"]
    runner_version = deps.get("runner_version", "")
    on_debug = deps.get("on_debug")
    on_auth401 = deps.get("on_auth401")
    get_device = deps.get("get_trusted_device_token")
    consecutive_empty = 0
    empty_poll_log_interval = 100

    def debug(msg: str) -> None:
        if on_debug:
            on_debug(msg)

    def hdr(access_token: str) -> dict[str, str]:
        h: dict[str, str] = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": BETA_HEADER,
            "x-environment-runner-version": runner_version,
        }
        if get_device:
            dt = get_device()
            if dt:
                h["X-Trusted-Device-Token"] = dt
        return h

    def resolve_auth() -> str:
        t = get_token()
        if not t:
            raise RuntimeError(BRIDGE_LOGIN_INSTRUCTION)
        return t

    class _Client:
        async def _retry(
            self,
            fn: Callable[[httpx.AsyncClient, str], Any],
            ctx: str,
        ) -> httpx.Response:
            token = resolve_auth()
            async with httpx.AsyncClient() as client:
                response = await fn(client, token)
            if response.status_code != 401 or not on_auth401:
                if response.status_code == 401:
                    debug(f"[bridge:api] {ctx}: 401 received, no refresh handler")
                return response
            debug(f"[bridge:api] {ctx}: 401 received, attempting token refresh")
            refreshed = await on_auth401(token)  # type: ignore[misc]
            if refreshed:
                nt = resolve_auth()
                async with httpx.AsyncClient() as client:
                    return await fn(client, nt)
            return response

        async def register_bridge_environment(self, config: BridgeConfig) -> dict[str, str]:
            debug(f"[bridge:api] POST /v1/environments/bridge bridgeId={config.bridge_id}")

            async def do(c: httpx.AsyncClient, token: str) -> httpx.Response:
                body: dict[str, Any] = {
                    "machine_name": config.machine_name,
                    "directory": config.dir,
                    "branch": config.branch,
                    "git_repo_url": config.git_repo_url,
                    "max_sessions": config.max_sessions,
                    "metadata": {"worker_type": config.worker_type},
                }
                if config.reuse_environment_id:
                    body["environment_id"] = config.reuse_environment_id
                return await c.post(
                    f"{base_url}/v1/environments/bridge",
                    json=body,
                    headers=hdr(token),
                    timeout=15.0,
                )

            r = await self._retry(do, "Registration")
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "Registration")
            data = cast(dict[str, str], r.json())
            debug(f"[bridge:api] <<< {debug_body(data)}")
            return data

        async def poll_for_work(
            self,
            environment_id: str,
            environment_secret: str,
            signal: Any = None,
            reclaim_older_than_ms: int | None = None,
        ) -> WorkResponse | None:
            nonlocal consecutive_empty
            validate_bridge_id(environment_id, "environmentId")
            prev = consecutive_empty
            consecutive_empty = 0
            params = {}
            if reclaim_older_than_ms is not None:
                params["reclaim_older_than_ms"] = reclaim_older_than_ms
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{base_url}/v1/environments/{environment_id}/work/poll",
                    headers=hdr(environment_secret),
                    params=params or None,
                    timeout=10.0,
                )
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "Poll")
            if r.status_code == 204 or not (r.content and str(r.content).strip()):
                consecutive_empty = prev + 1
                if consecutive_empty == 1 or consecutive_empty % empty_poll_log_interval == 0:
                    debug(
                        f"[bridge:api] GET .../work/poll -> {r.status_code} "
                        f"(no work, {consecutive_empty} consecutive empty polls)"
                    )
                return None
            if dj is None or dj == "":
                consecutive_empty = prev + 1
                return None
            consecutive_empty = 0
            return cast(WorkResponse, dj)

        async def acknowledge_work(self, environment_id: str, work_id: str, session_token: str) -> None:
            validate_bridge_id(environment_id, "environmentId")
            validate_bridge_id(work_id, "workId")
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{base_url}/v1/environments/{environment_id}/work/{work_id}/ack",
                    json={},
                    headers=hdr(session_token),
                    timeout=10.0,
                )
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "Acknowledge")

        async def stop_work(self, environment_id: str, work_id: str, force: bool) -> None:
            validate_bridge_id(environment_id, "environmentId")
            validate_bridge_id(work_id, "workId")

            async def do(c: httpx.AsyncClient, token: str) -> httpx.Response:
                return await c.post(
                    f"{base_url}/v1/environments/{environment_id}/work/{work_id}/stop",
                    json={"force": force},
                    headers=hdr(token),
                    timeout=10.0,
                )

            r = await self._retry(do, "StopWork")
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "StopWork")

        async def deregister_environment(self, environment_id: str) -> None:
            validate_bridge_id(environment_id, "environmentId")

            async def do(c: httpx.AsyncClient, token: str) -> httpx.Response:
                return await c.delete(
                    f"{base_url}/v1/environments/bridge/{environment_id}",
                    headers=hdr(token),
                    timeout=10.0,
                )

            r = await self._retry(do, "Deregister")
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "Deregister")

        async def archive_session(self, session_id: str) -> None:
            validate_bridge_id(session_id, "sessionId")

            async def do(c: httpx.AsyncClient, token: str) -> httpx.Response:
                return await c.post(
                    f"{base_url}/v1/sessions/{session_id}/archive",
                    json={},
                    headers=hdr(token),
                    timeout=10.0,
                )

            r = await self._retry(do, "ArchiveSession")
            if r.status_code == 409:
                return
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "ArchiveSession")

        async def reconnect_session(self, environment_id: str, session_id: str) -> None:
            validate_bridge_id(environment_id, "environmentId")
            validate_bridge_id(session_id, "sessionId")

            async def do(c: httpx.AsyncClient, token: str) -> httpx.Response:
                return await c.post(
                    f"{base_url}/v1/environments/{environment_id}/bridge/reconnect",
                    json={"session_id": session_id},
                    headers=hdr(token),
                    timeout=10.0,
                )

            r = await self._retry(do, "ReconnectSession")
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "ReconnectSession")

        async def heartbeat_work(self, environment_id: str, work_id: str, session_token: str) -> dict[str, Any]:
            validate_bridge_id(environment_id, "environmentId")
            validate_bridge_id(work_id, "workId")
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{base_url}/v1/environments/{environment_id}/work/{work_id}/heartbeat",
                    json={},
                    headers=hdr(session_token),
                    timeout=10.0,
                )
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "Heartbeat")
            return cast(dict[str, Any], r.json())

        async def send_permission_response_event(
            self,
            session_id: str,
            event: PermissionResponseEvent,
            session_token: str,
        ) -> None:
            validate_bridge_id(session_id, "sessionId")
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{base_url}/v1/sessions/{session_id}/events",
                    json={"events": [event]},
                    headers=hdr(session_token),
                    timeout=10.0,
                )
            try:
                dj = r.json()
            except Exception:
                dj = None
            _handle_error_status(r.status_code, dj, "SendPermissionResponseEvent")

    return _Client()
