"""
API error utilities.

Migrated from: services/api/errorUtils.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# SSL/TLS error codes from OpenSSL (Node/Bun); see OpenSSL X509_STORE_CTX docs.
SSL_ERROR_CODES: frozenset[str] = frozenset(
    {
        "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
        "UNABLE_TO_GET_ISSUER_CERT",
        "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
        "CERT_SIGNATURE_FAILURE",
        "CERT_NOT_YET_VALID",
        "CERT_HAS_EXPIRED",
        "CERT_REVOKED",
        "CERT_REJECTED",
        "CERT_UNTRUSTED",
        "DEPTH_ZERO_SELF_SIGNED_CERT",
        "SELF_SIGNED_CERT_IN_CHAIN",
        "CERT_CHAIN_TOO_LONG",
        "PATH_LENGTH_EXCEEDED",
        "ERR_TLS_CERT_ALTNAME_INVALID",
        "HOSTNAME_MISMATCH",
        "ERR_TLS_HANDSHAKE_TIMEOUT",
        "ERR_SSL_WRONG_VERSION_NUMBER",
        "ERR_SSL_DECRYPTION_FAILED_OR_BAD_RECORD_MAC",
    }
)


@dataclass(frozen=True)
class ConnectionErrorDetails:
    code: str
    message: str
    is_ssl_error: bool


def extract_connection_error_details(
    error: BaseException | None,
) -> ConnectionErrorDetails | None:
    """
    Walk the ``__cause__`` / ``__context__`` chain for a root error ``code``.
    """
    if error is None:
        return None

    current: BaseException | None = error
    depth = 0
    visited: set[int] = set()

    while current is not None and depth < 5:
        cid = id(current)
        if cid in visited:
            break
        visited.add(cid)

        code = getattr(current, "code", None)
        if isinstance(code, str):
            return ConnectionErrorDetails(
                code=code,
                message=str(current),
                is_ssl_error=code in SSL_ERROR_CODES,
            )

        nxt = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
        if nxt is current:
            break
        current = nxt if isinstance(nxt, BaseException) else None
        depth += 1

    return None


def get_ssl_error_hint(error: BaseException | None) -> str | None:
    details = extract_connection_error_details(error)
    if not details or not details.is_ssl_error:
        return None
    return (
        f"SSL certificate error ({details.code}). If you are behind a corporate "
        "proxy or TLS-intercepting firewall, set NODE_EXTRA_CA_CERTS to your CA "
        "bundle path, or ask IT to allowlist *.anthropic.com. Run /doctor for details."
    )


def _sanitize_message_html(message: str) -> str:
    if "<!DOCTYPE html" in message or "<html" in message:
        title_match = re.search(r"<title>([^<]+)</title>", message, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return ""
    return message


def sanitize_api_error(api_error: Any) -> str:
    """Strip HTML (e.g. Cloudflare pages) from API error messages."""
    message = getattr(api_error, "message", None)
    if message is None and isinstance(api_error, dict):
        message = api_error.get("message")
    if message is None:
        return ""
    if not isinstance(message, str):
        return str(message)
    return _sanitize_message_html(message)


def _has_nested_error(value: Any) -> bool:
    return isinstance(value, dict) and "error" in value and isinstance(value.get("error"), dict)


def _extract_nested_error_message(api_error: Any) -> str | None:
    if not _has_nested_error(api_error):
        return None
    nested = api_error["error"]
    err_inner = nested.get("error")
    if isinstance(err_inner, dict):
        dm = err_inner.get("message")
        if isinstance(dm, str) and dm:
            s = _sanitize_message_html(dm)
            if s:
                return s
    msg = nested.get("message")
    if isinstance(msg, str) and msg:
        s = _sanitize_message_html(msg)
        if s:
            return s
    return None


def format_api_error(error: Any) -> str:
    """Format an SDK-style API error for display."""
    base_exc = error if isinstance(error, BaseException) else None
    connection_details = extract_connection_error_details(base_exc)

    if connection_details:
        code = connection_details.code
        is_ssl = connection_details.is_ssl_error
        if code == "ETIMEDOUT":
            return "Request timed out. Check your internet connection and proxy settings"
        if is_ssl:
            if code in (
                "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
                "UNABLE_TO_GET_ISSUER_CERT",
                "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
            ):
                return (
                    "Unable to connect to API: SSL certificate verification failed. "
                    "Check your proxy or corporate SSL certificates"
                )
            if code == "CERT_HAS_EXPIRED":
                return "Unable to connect to API: SSL certificate has expired"
            if code == "CERT_REVOKED":
                return "Unable to connect to API: SSL certificate has been revoked"
            if code in ("DEPTH_ZERO_SELF_SIGNED_CERT", "SELF_SIGNED_CERT_IN_CHAIN"):
                return (
                    "Unable to connect to API: Self-signed certificate detected. "
                    "Check your proxy or corporate SSL certificates"
                )
            if code in ("ERR_TLS_CERT_ALTNAME_INVALID", "HOSTNAME_MISMATCH"):
                return "Unable to connect to API: SSL certificate hostname mismatch"
            if code == "CERT_NOT_YET_VALID":
                return "Unable to connect to API: SSL certificate is not yet valid"
            return f"Unable to connect to API: SSL error ({code})"

    msg = error.get("message") if isinstance(error, dict) else getattr(error, "message", None)
    if msg == "Connection error.":
        if connection_details and connection_details.code:
            return f"Unable to connect to API ({connection_details.code})"
        return "Unable to connect to API. Check your internet connection"

    if not msg:
        nested = _extract_nested_error_message(error)
        status = error.get("status") if isinstance(error, dict) else getattr(error, "status", None)
        return nested or f"API error (status {status if status is not None else 'unknown'})"

    if not isinstance(msg, str):
        msg = str(msg)

    sanitized = sanitize_api_error(error)
    if sanitized != msg and len(sanitized) > 0:
        return sanitized
    return msg


def is_transient_error(error: Exception) -> bool:
    """True if the error is likely to succeed on retry."""
    message = str(error).lower()
    transient_patterns = [
        "timeout",
        "temporarily unavailable",
        "service unavailable",
        "too many requests",
        "rate limit",
        "overloaded",
        "connection reset",
        "connection refused",
        "network",
    ]
    return any(p in message for p in transient_patterns)


def get_error_code(error: Exception) -> int | None:
    """HTTP status from exception if available."""
    if hasattr(error, "status_code"):
        val = error.status_code
        if isinstance(val, int):
            return val
    if hasattr(error, "status"):
        val = error.status
        if isinstance(val, int):
            return val
    message = str(error)
    match = re.search(r"\b(4\d\d|5\d\d)\b", message)
    if match:
        return int(match.group(1))
    return None
