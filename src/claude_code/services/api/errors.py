"""
API error handling.

Error types, parsing, and classification.

Migrated from: services/api/errors.ts (1208 lines)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

# Constants
API_ERROR_MESSAGE_PREFIX = "API Error"
PROMPT_TOO_LONG_ERROR_MESSAGE = "Prompt is too long"


# Error types
APIErrorType = Literal[
    "authentication",
    "rate_limit",
    "overloaded",
    "prompt_too_long",
    "media_size",
    "invalid_request",
    "server_error",
    "connection",
    "timeout",
    "unknown",
]


@dataclass
class APIErrorInfo:
    """Parsed API error information."""

    error_type: APIErrorType
    message: str
    status_code: int | None = None
    raw_error: str | None = None
    retry_after: float | None = None
    actual_tokens: int | None = None
    limit_tokens: int | None = None


def starts_with_api_error_prefix(text: str) -> bool:
    """Check if text starts with API error prefix."""
    return text.startswith(API_ERROR_MESSAGE_PREFIX) or text.startswith(
        f"Please run /login · {API_ERROR_MESSAGE_PREFIX}"
    )


def is_prompt_too_long_message(msg: dict[str, Any]) -> bool:
    """
    Check if message is a prompt-too-long error.

    Args:
        msg: Assistant message dict

    Returns:
        True if prompt too long error
    """
    if not msg.get("isApiErrorMessage"):
        return False

    content = msg.get("message", {}).get("content", [])
    if not isinstance(content, list):
        return False

    return any(
        block.get("type") == "text" and block.get("text", "").startswith(PROMPT_TOO_LONG_ERROR_MESSAGE)
        for block in content
    )


def parse_prompt_too_long_token_counts(raw_message: str) -> tuple[int | None, int | None]:
    """
    Parse token counts from prompt-too-long error.

    Args:
        raw_message: Raw API error message

    Returns:
        Tuple of (actual_tokens, limit_tokens) or (None, None)
    """
    match = re.search(
        r"prompt is too long[^0-9]*(\d+)\s*tokens?\s*>\s*(\d+)",
        raw_message,
        re.IGNORECASE,
    )

    if match:
        return int(match.group(1)), int(match.group(2))

    return None, None


def get_prompt_too_long_token_gap(msg: dict[str, Any]) -> int | None:
    """
    Get token gap from prompt-too-long error.

    Args:
        msg: Assistant message dict

    Returns:
        Number of tokens over limit, or None
    """
    if not is_prompt_too_long_message(msg):
        return None

    error_details = msg.get("errorDetails")
    if not error_details:
        return None

    actual, limit = parse_prompt_too_long_token_counts(error_details)

    if actual is None or limit is None:
        return None

    gap = actual - limit
    return gap if gap > 0 else None


def is_media_size_error(raw: str) -> bool:
    """
    Check if error is a media size rejection.

    Args:
        raw: Raw error message

    Returns:
        True if media size error
    """
    return (
        ("image exceeds" in raw and "maximum" in raw)
        or ("image dimensions exceed" in raw and "many-image" in raw)
        or bool(re.search(r"maximum of \d+ PDF pages", raw))
    )


def is_media_size_error_message(msg: dict[str, Any]) -> bool:
    """
    Check if message is a media size error.

    Args:
        msg: Assistant message dict

    Returns:
        True if media size error
    """
    if not msg.get("isApiErrorMessage"):
        return False

    error_details = msg.get("errorDetails")
    if not error_details:
        return False

    return is_media_size_error(error_details)


def classify_api_error(
    error: Exception,
    status_code: int | None = None,
) -> APIErrorInfo:
    """
    Classify an API error.

    Args:
        error: The exception
        status_code: Optional HTTP status code

    Returns:
        APIErrorInfo with classification
    """
    message = str(error)
    raw_error = message

    # Check for authentication errors
    if status_code == 401 or "invalid_api_key" in message.lower():
        return APIErrorInfo(
            error_type="authentication",
            message="Invalid API key. Please check your ANTHROPIC_API_KEY.",
            status_code=status_code,
            raw_error=raw_error,
        )

    # Check for rate limits
    if status_code == 429 or "rate_limit" in message.lower():
        retry_after = _extract_retry_after(message)
        return APIErrorInfo(
            error_type="rate_limit",
            message="Rate limited. Please wait and try again.",
            status_code=status_code,
            raw_error=raw_error,
            retry_after=retry_after,
        )

    # Check for overloaded
    if status_code == 529 or "overloaded" in message.lower():
        return APIErrorInfo(
            error_type="overloaded",
            message="API is overloaded. Please try again later.",
            status_code=status_code,
            raw_error=raw_error,
        )

    # Check for prompt too long
    if "prompt is too long" in message.lower():
        actual, limit = parse_prompt_too_long_token_counts(message)
        return APIErrorInfo(
            error_type="prompt_too_long",
            message=PROMPT_TOO_LONG_ERROR_MESSAGE,
            status_code=status_code,
            raw_error=raw_error,
            actual_tokens=actual,
            limit_tokens=limit,
        )

    # Check for media size errors
    if is_media_size_error(message):
        return APIErrorInfo(
            error_type="media_size",
            message="Media exceeds size limits.",
            status_code=status_code,
            raw_error=raw_error,
        )

    # Check for server errors
    if status_code and 500 <= status_code < 600:
        return APIErrorInfo(
            error_type="server_error",
            message="Server error. Please try again.",
            status_code=status_code,
            raw_error=raw_error,
        )

    # Check for connection errors
    if "connection" in message.lower() or "timeout" in message.lower():
        error_type: APIErrorType = "timeout" if "timeout" in message.lower() else "connection"
        return APIErrorInfo(
            error_type=error_type,
            message=f"Connection error: {message}",
            status_code=status_code,
            raw_error=raw_error,
        )

    # Unknown error
    return APIErrorInfo(
        error_type="unknown",
        message=f"API error: {message}",
        status_code=status_code,
        raw_error=raw_error,
    )


def _extract_retry_after(message: str) -> float | None:
    """Extract retry-after value from error message."""
    match = re.search(r"retry.?after[:\s]+(\d+(?:\.\d+)?)", message, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def get_assistant_message_from_error(
    error: Exception,
    model: str = "",
) -> dict[str, Any]:
    """
    Create an assistant error message from an exception.

    Args:
        error: The exception
        model: Model that was being used

    Returns:
        Assistant message dict
    """
    error_info = classify_api_error(error)

    return {
        "type": "assistant",
        "isApiErrorMessage": True,
        "errorDetails": error_info.raw_error,
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": f"{API_ERROR_MESSAGE_PREFIX}: {error_info.message}",
                }
            ],
        },
        "model": model,
    }


def format_api_error(error: Exception) -> str:
    """
    Format an API error for display.

    Args:
        error: The exception

    Returns:
        Formatted error string
    """
    error_info = classify_api_error(error)
    return f"{API_ERROR_MESSAGE_PREFIX}: {error_info.message}"


def is_retryable_error(error_info: APIErrorInfo) -> bool:
    """
    Check if an error is retryable.

    Args:
        error_info: The error info

    Returns:
        True if retryable
    """
    retryable_types: list[APIErrorType] = [
        "rate_limit",
        "overloaded",
        "server_error",
        "connection",
        "timeout",
    ]
    return error_info.error_type in retryable_types
