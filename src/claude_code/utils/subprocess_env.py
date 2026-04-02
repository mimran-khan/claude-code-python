"""
Scrub sensitive environment variables from child process environments.

Migrated from: utils/subprocessEnv.ts
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping

from .env_utils import is_env_truthy

_GHA_SUBPROCESS_SCRUB: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_FOUNDRY_API_KEY",
    "ANTHROPIC_CUSTOM_HEADERS",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "OTEL_EXPORTER_OTLP_LOGS_HEADERS",
    "OTEL_EXPORTER_OTLP_METRICS_HEADERS",
    "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "AZURE_CLIENT_SECRET",
    "AZURE_CLIENT_CERTIFICATE_PATH",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_URL",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_RUNTIME_URL",
    "ALL_INPUTS",
    "OVERRIDE_GITHUB_TOKEN",
    "DEFAULT_WORKFLOW_TOKEN",
    "SSH_SIGNING_KEY",
)

_get_upstream_proxy_env: Callable[[], dict[str, str]] | None = None


def register_upstream_proxy_env_fn(fn: Callable[[], dict[str, str]]) -> None:
    """Wire CCR upstream proxy env injection (lazy init from init)."""
    global _get_upstream_proxy_env
    _get_upstream_proxy_env = fn


def subprocess_env(
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """
    Return a copy of the environment suitable for spawning subprocesses.

    When ``CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`` is truthy, strip GitHub-Actions
    secret surface from the child env. Merge upstream proxy vars when registered.
    """
    env: dict[str, str] = dict(base if base is not None else os.environ)
    proxy_env = _get_upstream_proxy_env() if _get_upstream_proxy_env else {}
    env.update(proxy_env)

    if not is_env_truthy(os.environ.get("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB")):
        return env

    for key in _GHA_SUBPROCESS_SCRUB:
        env.pop(key, None)
        env.pop(f"INPUT_{key}", None)
    return env
