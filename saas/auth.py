"""
Authentication module for the SaaS platform.

Handles JWT token generation/validation and API key authentication.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import base64
from typing import Optional, Dict, Any

from .config import config


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_jwt(payload: Dict[str, Any]) -> str:
    """Create a JWT token with the given payload."""
    header = {"alg": config.JWT_ALGORITHM, "typ": "JWT"}

    payload = {
        **payload,
        "iat": int(time.time()),
        "exp": int(time.time()) + config.JWT_EXPIRATION_HOURS * 3600,
    }

    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())

    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        config.JWT_SECRET.encode(), message.encode(), hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(signature)

    return f"{message}.{sig_b64}"


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return the payload if valid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            config.JWT_SECRET.encode(), message.encode(), hashlib.sha256
        ).digest()
        actual_sig = _b64_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        payload = json.loads(_b64_decode(payload_b64))

        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None

        return payload

    except Exception:
        return None
