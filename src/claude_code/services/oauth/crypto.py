"""
OAuth Crypto Utilities.

Provides PKCE (Proof Key for Code Exchange) utilities for OAuth flows.
"""

from __future__ import annotations

import base64
import hashlib
import secrets


def base64_url_encode(data: bytes) -> str:
    """Encode bytes using URL-safe base64 without padding.

    Args:
        data: The bytes to encode

    Returns:
        URL-safe base64 encoded string without padding
    """
    encoded = base64.urlsafe_b64encode(data).decode("ascii")
    # Remove padding
    return encoded.rstrip("=")


def generate_code_verifier() -> str:
    """Generate a cryptographically random code verifier for PKCE.

    Returns:
        A 43-character URL-safe base64 encoded string
    """
    return base64_url_encode(secrets.token_bytes(32))


def generate_code_challenge(verifier: str) -> str:
    """Generate a code challenge from a code verifier.

    Uses SHA-256 hashing as required by PKCE S256 method.

    Args:
        verifier: The code verifier string

    Returns:
        The code challenge (SHA-256 hash, URL-safe base64 encoded)
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64_url_encode(digest)


def generate_state() -> str:
    """Generate a cryptographically random state parameter.

    Returns:
        A 43-character URL-safe base64 encoded string
    """
    return base64_url_encode(secrets.token_bytes(32))
