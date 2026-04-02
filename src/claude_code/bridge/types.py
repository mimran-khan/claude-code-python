"""Bridge protocol types (ported from bridge/types.ts)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypedDict

# --- Constants ---

DEFAULT_SESSION_TIMEOUT_MS = 24 * 60 * 60 * 1000

BRIDGE_LOGIN_INSTRUCTION = (
    "Remote Control is only available with claude.ai subscriptions. "
    "Please use `/login` to sign in with your claude.ai account."
)

BRIDGE_LOGIN_ERROR = "Error: You must be logged in to use Remote Control.\n\n" + BRIDGE_LOGIN_INSTRUCTION

REMOTE_CONTROL_DISCONNECTED_MSG = "Remote Control disconnected."

# --- Work / session protocol ---


class WorkData(TypedDict):
    type: Literal["session", "healthcheck"]
    id: str


class WorkResponse(TypedDict, total=False):
    id: str
    type: Literal["work"]
    environment_id: str
    state: str
    data: WorkData
    secret: str
    created_at: str


class WorkSourceGitInfo(TypedDict, total=False):
    type: str
    repo: str
    ref: str | None
    token: str | None


class WorkSourceItem(TypedDict, total=False):
    type: str
    git_info: WorkSourceGitInfo | None


@dataclass
class WorkSecret:
    version: int
    session_ingress_token: str
    api_base_url: str
    sources: list[dict[str, Any]]
    auth: list[dict[str, Any]]
    claude_code_args: dict[str, str] | None = None
    mcp_config: Any | None = None
    environment_variables: dict[str, str] | None = None
    use_code_sessions: bool | None = None


SessionDoneStatus = Literal["completed", "failed", "interrupted"]
SessionActivityType = Literal["tool_start", "text", "result", "error"]


@dataclass
class SessionActivity:
    type: SessionActivityType
    summary: str
    timestamp: int


SpawnMode = Literal["single-session", "worktree", "same-dir"]
BridgeWorkerType = Literal["claude_code", "claude_code_assistant"]


@dataclass
class BridgeConfig:
    dir: str
    machine_name: str
    branch: str
    git_repo_url: str | None
    max_sessions: int
    spawn_mode: SpawnMode
    verbose: bool
    sandbox: bool
    bridge_id: str
    worker_type: str
    environment_id: str
    api_base_url: str
    session_ingress_url: str
    reuse_environment_id: str | None = None
    debug_file: str | None = None
    session_timeout_ms: int | None = None


class PermissionResponseSuccess(TypedDict):
    subtype: Literal["success"]
    request_id: str
    response: dict[str, Any]


class PermissionResponseEvent(TypedDict):
    type: Literal["control_response"]
    response: PermissionResponseSuccess


class BridgeApiClient(Protocol):
    async def register_bridge_environment(self, config: BridgeConfig) -> dict[str, str]: ...

    async def poll_for_work(
        self,
        environment_id: str,
        environment_secret: str,
        signal: Any | None = None,
        reclaim_older_than_ms: int | None = None,
    ) -> WorkResponse | None: ...

    async def acknowledge_work(self, environment_id: str, work_id: str, session_token: str) -> None: ...

    async def stop_work(self, environment_id: str, work_id: str, force: bool) -> None: ...

    async def deregister_environment(self, environment_id: str) -> None: ...

    async def send_permission_response_event(
        self,
        session_id: str,
        event: PermissionResponseEvent,
        session_token: str,
    ) -> None: ...

    async def archive_session(self, session_id: str) -> None: ...

    async def reconnect_session(self, environment_id: str, session_id: str) -> None: ...

    async def heartbeat_work(self, environment_id: str, work_id: str, session_token: str) -> dict[str, Any]: ...


@dataclass
class SessionHandle:
    session_id: str
    done: Any  # asyncio.Future or Task for SessionDoneStatus
    activities: list[SessionActivity] = field(default_factory=list)
    current_activity: SessionActivity | None = None
    access_token: str = ""
    last_stderr: list[str] = field(default_factory=list)
    # Optional OS process (e.g. asyncio.subprocess.Process) wired by session spawner
    _process: Any | None = field(default=None, repr=False)
    _stdin_writer: Any | None = field(default=None, repr=False)

    def kill(self) -> None:
        proc = self._process
        if proc is None:
            return
        with contextlib.suppress(ProcessLookupError, OSError):
            proc.terminate()

    def force_kill(self) -> None:
        proc = self._process
        if proc is None:
            return
        with contextlib.suppress(ProcessLookupError, OSError):
            proc.kill()

    def write_stdin(self, data: str) -> None:
        writer = self._stdin_writer
        if writer is None:
            return
        try:
            payload = data.encode("utf-8") if isinstance(data, str) else data
            writer.write(payload)
            drain = getattr(writer, "drain", None)
            if callable(drain):
                fut = drain()
                if hasattr(fut, "__await__"):
                    # Async drain cannot be awaited from sync API; best-effort only.
                    pass
        except (OSError, BrokenPipeError, TypeError, ValueError, AttributeError):
            pass

    def update_access_token(self, token: str) -> None:
        self.access_token = token


@dataclass
class SessionSpawnOpts:
    session_id: str
    sdk_url: str
    access_token: str
    use_ccr_v2: bool = False
    worker_epoch: int | None = None
    on_first_user_message: Callable[[str], None] | None = None


class SessionSpawner(Protocol):
    def spawn(self, opts: SessionSpawnOpts, dir: str) -> SessionHandle: ...


class BridgeLogger(Protocol):
    def print_banner(self, config: BridgeConfig, environment_id: str) -> None: ...
    def log_session_start(self, session_id: str, prompt: str) -> None: ...
    def log_session_complete(self, session_id: str, duration_ms: int) -> None: ...
    def log_session_failed(self, session_id: str, error: str) -> None: ...
    def log_status(self, message: str) -> None: ...
    def log_verbose(self, message: str) -> None: ...
    def log_error(self, message: str) -> None: ...
    def log_reconnected(self, disconnected_ms: int) -> None: ...
    def update_idle_status(self) -> None: ...
    def update_reconnecting_status(self, delay_str: str, elapsed_str: str) -> None: ...
    def update_session_status(
        self,
        session_id: str,
        elapsed: str,
        activity: SessionActivity,
        trail: list[str],
    ) -> None: ...
    def clear_status(self) -> None: ...
    def set_repo_info(self, repo_name: str, branch: str) -> None: ...
    def set_debug_log_path(self, path: str) -> None: ...
    def set_attached(self, session_id: str) -> None: ...
    def update_failed_status(self, error: str) -> None: ...
    def toggle_qr(self) -> None: ...
    def update_session_count(self, active: int, max_sessions: int, mode: SpawnMode) -> None: ...
    def set_spawn_mode_display(self, mode: Literal["same-dir", "worktree"] | None) -> None: ...
    def add_session(self, session_id: str, url: str) -> None: ...
    def update_session_activity(self, session_id: str, activity: SessionActivity) -> None: ...
    def set_session_title(self, session_id: str, title: str) -> None: ...
    def remove_session(self, session_id: str) -> None: ...
    def refresh_display(self) -> None: ...
