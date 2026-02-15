"""
Tests for the SaaS platform components.

Tests database operations, authentication, and API integration.
"""

import json
import os
import tempfile
import time

import pytest

from saas.database import Database
from saas.auth import create_jwt, verify_jwt
from saas.config import Config


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    db_path = str(tmp_path / "test.db")
    return Database(db_path)


class TestDatabase:
    """Test database operations."""

    def test_create_user(self, db):
        user = db.create_user("test@example.com", "password123", "Test User")
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"
        assert user["tier"] == "free"

    def test_duplicate_email_raises(self, db):
        db.create_user("test@example.com", "pass1")
        with pytest.raises(Exception):
            db.create_user("test@example.com", "pass2")

    def test_authenticate_user(self, db):
        db.create_user("auth@test.com", "secret")
        user = db.authenticate_user("auth@test.com", "secret")
        assert user is not None
        assert user["email"] == "auth@test.com"

    def test_authenticate_wrong_password(self, db):
        db.create_user("auth@test.com", "secret")
        user = db.authenticate_user("auth@test.com", "wrong")
        assert user is None

    def test_get_user(self, db):
        created = db.create_user("get@test.com", "pass")
        user = db.get_user(created["id"])
        assert user is not None
        assert user["email"] == "get@test.com"

    def test_update_tier(self, db):
        created = db.create_user("tier@test.com", "pass")
        db.update_user_tier(created["id"], "pro")
        user = db.get_user(created["id"])
        assert user["tier"] == "pro"


class TestApiKeys:
    """Test API key management."""

    def test_create_api_key(self, db):
        user = db.create_user("key@test.com", "pass")
        key_info = db.create_api_key(user["id"], "test-key")
        assert key_info["api_key"].startswith("gseed_")
        assert key_info["name"] == "test-key"

    def test_validate_api_key(self, db):
        user = db.create_user("val@test.com", "pass")
        key_info = db.create_api_key(user["id"])
        result = db.validate_api_key(key_info["api_key"])
        assert result is not None
        assert result["email"] == "val@test.com"

    def test_invalid_api_key(self, db):
        result = db.validate_api_key("gseed_invalid_key")
        assert result is None

    def test_revoke_api_key(self, db):
        user = db.create_user("revoke@test.com", "pass")
        key_info = db.create_api_key(user["id"])
        keys = db.list_api_keys(user["id"])
        db.revoke_api_key(keys[0]["id"], user["id"])
        result = db.validate_api_key(key_info["api_key"])
        assert result is None

    def test_list_api_keys(self, db):
        user = db.create_user("list@test.com", "pass")
        db.create_api_key(user["id"], "key1")
        db.create_api_key(user["id"], "key2")
        keys = db.list_api_keys(user["id"])
        assert len(keys) == 2


class TestUsageMetering:
    """Test usage logging and metering."""

    def test_log_usage(self, db):
        user = db.create_user("usage@test.com", "pass")
        db.log_usage(user["id"], "encode", input_bytes=1000, output_bytes=50, compression_ratio=20.0)
        summary = db.get_usage_summary(user["id"])
        assert summary["total_requests"] == 1
        assert summary["total_input_bytes"] == 1000

    def test_rate_limit_check(self, db):
        user = db.create_user("rate@test.com", "pass")
        result = db.check_rate_limit(user["id"])
        assert result["allowed"] is True
        assert result["requests_used"] == 0

    def test_tier_limits(self, db):
        user = db.create_user("limits@test.com", "pass")
        result = db.check_tier_limits(user["id"])
        assert result["allowed"] is True
        assert result["tier"] == "free"


class TestEnvelopeStorage:
    """Test envelope persistence."""

    def test_store_and_retrieve(self, db):
        user = db.create_user("env@test.com", "pass")
        envelope_json = json.dumps({"mode": "stream", "seed_id": "golden_ratio"})
        db.store_envelope(user["id"], "env-123", envelope_json, 1000, 60, "stream")
        stored = db.get_envelope("env-123", user["id"])
        assert stored is not None
        assert stored["envelope_id"] == "env-123"
        assert stored["original_size"] == 1000

    def test_list_envelopes(self, db):
        user = db.create_user("envlist@test.com", "pass")
        for i in range(3):
            db.store_envelope(user["id"], f"env-{i}", "{}", 100, 10, "stream")
        envelopes = db.list_envelopes(user["id"])
        assert len(envelopes) == 3

    def test_delete_envelope(self, db):
        user = db.create_user("envdel@test.com", "pass")
        db.store_envelope(user["id"], "del-1", "{}", 100, 10, "stream")
        assert db.delete_envelope("del-1", user["id"]) is True
        assert db.get_envelope("del-1", user["id"]) is None


class TestJWT:
    """Test JWT authentication."""

    def test_create_and_verify(self):
        payload = {"user_id": 1, "email": "jwt@test.com"}
        token = create_jwt(payload)
        verified = verify_jwt(token)
        assert verified is not None
        assert verified["user_id"] == 1
        assert verified["email"] == "jwt@test.com"

    def test_invalid_token(self):
        result = verify_jwt("invalid.token.here")
        assert result is None

    def test_tampered_token(self):
        token = create_jwt({"user_id": 1})
        # Tamper with the payload
        parts = token.split(".")
        parts[1] = parts[1][::-1]  # Reverse payload
        tampered = ".".join(parts)
        result = verify_jwt(tampered)
        assert result is None

    def test_expired_token(self):
        from saas.auth import _b64_encode
        import hashlib
        import hmac

        header = '{"alg":"HS256","typ":"JWT"}'
        payload = json.dumps({"user_id": 1, "iat": 1000000, "exp": 1000001})
        header_b64 = _b64_encode(header.encode())
        payload_b64 = _b64_encode(payload.encode())
        message = f"{header_b64}.{payload_b64}"
        sig = hmac.new(
            Config.JWT_SECRET.encode(), message.encode(), hashlib.sha256
        ).digest()
        sig_b64 = _b64_encode(sig)
        token = f"{message}.{sig_b64}"
        result = verify_jwt(token)
        assert result is None  # Expired
