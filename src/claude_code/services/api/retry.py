"""
API retry logic.

Retry handling for transient errors.

Migrated from: services/api/withRetry.ts
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from .errors import APIErrorInfo, classify_api_error, is_retryable_error

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1

    # Error-specific overrides
    rate_limit_multiplier: float = 2.0
    overload_multiplier: float = 1.5


def get_retry_delay(
    attempt: int,
    config: RetryConfig,
    error_info: APIErrorInfo | None = None,
) -> float:
    """
    Calculate retry delay with exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        error_info: Optional error info for type-specific delays

    Returns:
        Delay in seconds
    """
    # Base exponential backoff
    delay = config.initial_delay * (config.exponential_base**attempt)

    # Apply error-specific multipliers
    if error_info:
        if error_info.error_type == "rate_limit":
            delay *= config.rate_limit_multiplier
            # Use retry-after if provided
            if error_info.retry_after:
                delay = max(delay, error_info.retry_after)

        elif error_info.error_type == "overloaded":
            delay *= config.overload_multiplier

    # Apply jitter
    jitter_range = delay * config.jitter
    delay += random.uniform(-jitter_range, jitter_range)

    # Cap at max delay
    delay = min(delay, config.max_delay)

    return max(0.1, delay)


def should_retry(
    error: Exception,
    attempt: int,
    config: RetryConfig,
) -> bool:
    """
    Determine if a request should be retried.

    Args:
        error: The exception that occurred
        attempt: Current attempt number
        config: Retry configuration

    Returns:
        True if should retry
    """
    if attempt >= config.max_retries:
        return False

    error_info = classify_api_error(error)
    return is_retryable_error(error_info)


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> T:
    """
    Execute a function with retry logic.

    Args:
        fn: Async function to execute
        config: Retry configuration
        on_retry: Optional callback when retrying (attempt, error, delay)

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    if config is None:
        config = RetryConfig()

    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return await fn()

        except Exception as e:
            last_error = e

            if not should_retry(e, attempt, config):
                raise

            error_info = classify_api_error(e)
            delay = get_retry_delay(attempt, config, error_info)

            if on_retry:
                on_retry(attempt, e, delay)

            await asyncio.sleep(delay)

    # Should not reach here, but raise last error if we do
    if last_error:
        raise last_error

    raise RuntimeError("Retry exhausted without error")


async def with_timeout(
    fn: Callable[[], Awaitable[T]],
    timeout: float,
) -> T:
    """
    Execute a function with timeout.

    Args:
        fn: Async function to execute
        timeout: Timeout in seconds

    Returns:
        Function result

    Raises:
        asyncio.TimeoutError if timeout exceeded
    """
    return await asyncio.wait_for(fn(), timeout=timeout)


class RetryState:
    """Track retry state across requests."""

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.attempts = 0
        self.total_delay = 0.0
        self.last_error: Exception | None = None

    def record_attempt(self, error: Exception | None = None):
        """Record an attempt."""
        self.attempts += 1
        self.last_error = error

    def record_delay(self, delay: float):
        """Record delay time."""
        self.total_delay += delay

    def should_continue(self) -> bool:
        """Check if should continue retrying."""
        if self.last_error is None:
            return False
        return should_retry(self.last_error, self.attempts - 1, self.config)

    def get_next_delay(self) -> float:
        """Get delay for next retry."""
        if self.last_error is None:
            return 0.0
        error_info = classify_api_error(self.last_error)
        return get_retry_delay(self.attempts - 1, self.config, error_info)

    def reset(self):
        """Reset state."""
        self.attempts = 0
        self.total_delay = 0.0
        self.last_error = None
