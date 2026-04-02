"""
API request/response logging.

Logging for API interactions.

Migrated from: services/api/logging.ts (789 lines)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

# Known gateway types
KnownGateway = Literal[
    "litellm",
    "helicone",
    "portkey",
    "cloudflare-ai-gateway",
    "kong",
    "braintrust",
    "databricks",
]


# Gateway fingerprints for detection
GATEWAY_FINGERPRINTS: dict[str, list[str]] = {
    "litellm": ["x-litellm-"],
    "helicone": ["helicone-"],
    "portkey": ["x-portkey-"],
}


@dataclass
class RequestUsage:
    """Usage statistics from an API request."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


EMPTY_USAGE = RequestUsage()


@dataclass
class RequestMetrics:
    """Metrics for an API request."""

    model: str
    usage: RequestUsage
    duration_ms: float
    stop_reason: str | None = None
    request_id: str | None = None
    gateway: str | None = None


def detect_gateway(headers: dict[str, str]) -> str | None:
    """
    Detect AI gateway from response headers.

    Args:
        headers: Response headers

    Returns:
        Gateway name or None
    """
    headers_lower = {k.lower(): v for k, v in headers.items()}

    for gateway, prefixes in GATEWAY_FINGERPRINTS.items():
        for prefix in prefixes:
            if any(h.startswith(prefix) for h in headers_lower):
                return gateway

    return None


def log_api_request(
    model: str,
    messages_count: int,
    tools_count: int = 0,
    system_prompt_length: int = 0,
) -> None:
    """
    Log an outgoing API request.

    Args:
        model: Model being used
        messages_count: Number of messages
        tools_count: Number of tools
        system_prompt_length: Length of system prompt
    """
    from ...utils.log import log_for_debugging

    log_for_debugging(
        f"[API:request] model={model} messages={messages_count} tools={tools_count} system_len={system_prompt_length}"
    )


def log_api_response(
    metrics: RequestMetrics,
    error: Exception | None = None,
) -> None:
    """
    Log an API response.

    Args:
        metrics: Request metrics
        error: Optional error that occurred
    """
    from ...utils.log import log_for_debugging

    if error:
        log_for_debugging(f"[API:error] model={metrics.model} duration={metrics.duration_ms:.0f}ms error={error}")
    else:
        log_for_debugging(
            f"[API:response] model={metrics.model} "
            f"in={metrics.usage.input_tokens} out={metrics.usage.output_tokens} "
            f"duration={metrics.duration_ms:.0f}ms stop={metrics.stop_reason}"
        )


def calculate_cost(
    usage: RequestUsage,
    model: str,
) -> float:
    """
    Calculate cost for a request.

    Args:
        usage: Token usage
        model: Model used

    Returns:
        Cost in USD
    """
    # Cost per million tokens (approximate)
    model_lower = model.lower()

    if "opus" in model_lower:
        input_cost = 15.0
        output_cost = 75.0
    elif "sonnet" in model_lower:
        input_cost = 3.0
        output_cost = 15.0
    elif "haiku" in model_lower:
        input_cost = 0.25
        output_cost = 1.25
    else:
        # Default to Sonnet pricing
        input_cost = 3.0
        output_cost = 15.0

    input_tokens = usage.input_tokens / 1_000_000
    output_tokens = usage.output_tokens / 1_000_000

    # Cache reads are 90% cheaper
    cache_read_tokens = usage.cache_read_input_tokens / 1_000_000
    cache_creation_tokens = usage.cache_creation_input_tokens / 1_000_000

    cost = (
        input_tokens * input_cost
        + output_tokens * output_cost
        + cache_read_tokens * input_cost * 0.1
        + cache_creation_tokens * input_cost * 1.25
    )

    return cost


class RequestLogger:
    """Logger for tracking API requests across a session."""

    def __init__(self):
        self._requests: list[RequestMetrics] = []
        self._total_cost: float = 0.0
        self._session_start: float = time.time()

    def log_request(self, metrics: RequestMetrics) -> None:
        """Log a completed request."""
        self._requests.append(metrics)
        self._total_cost += calculate_cost(metrics.usage, metrics.model)

    @property
    def request_count(self) -> int:
        """Total number of requests."""
        return len(self._requests)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return sum(r.usage.total_tokens for r in self._requests)

    @property
    def total_cost(self) -> float:
        """Total cost in USD."""
        return self._total_cost

    @property
    def total_duration_ms(self) -> float:
        """Total API time in milliseconds."""
        return sum(r.duration_ms for r in self._requests)

    def get_summary(self) -> dict[str, Any]:
        """Get session summary."""
        return {
            "requests": self.request_count,
            "tokens": self.total_tokens,
            "cost_usd": round(self.total_cost, 4),
            "duration_ms": round(self.total_duration_ms, 0),
        }


# Global request logger
_request_logger: RequestLogger | None = None


def get_request_logger() -> RequestLogger:
    """Get the global request logger."""
    global _request_logger
    if _request_logger is None:
        _request_logger = RequestLogger()
    return _request_logger
