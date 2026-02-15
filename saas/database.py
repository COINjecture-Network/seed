"""
Database layer for the SaaS platform.

Uses SQLite for simplicity and portability. Handles user accounts,
API keys, usage metering, and envelope storage.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from .config import config


def _hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _conn(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'pro', 'enterprise')),
                    created_at REAL NOT NULL,
                    active INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL,
                    name TEXT DEFAULT 'default',
                    created_at REAL NOT NULL,
                    last_used_at REAL,
                    active INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    api_key_id INTEGER REFERENCES api_keys(id),
                    operation TEXT NOT NULL,
                    input_bytes INTEGER DEFAULT 0,
                    output_bytes INTEGER DEFAULT 0,
                    compression_ratio REAL DEFAULT 0,
                    mode TEXT DEFAULT '',
                    timestamp REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS envelopes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    envelope_id TEXT UNIQUE NOT NULL,
                    envelope_json TEXT NOT NULL,
                    original_size INTEGER NOT NULL,
                    envelope_size INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    created_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
                CREATE INDEX IF NOT EXISTS idx_usage_log_user ON usage_log(user_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_envelopes_user ON envelopes(user_id);
                CREATE INDEX IF NOT EXISTS idx_envelopes_eid ON envelopes(envelope_id);
            """)

    # --- User Management ---

    def create_user(self, email: str, password: str, name: str = "") -> Dict[str, Any]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        now = time.time()
        with self._conn() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
                (email, password_hash, name, now),
            )
            user_id = cursor.lastrowid
        return {"id": user_id, "email": email, "name": name, "tier": "free"}

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, name, tier, active FROM users WHERE email=? AND password_hash=?",
                (email, password_hash),
            ).fetchone()
        if row and row["active"]:
            return dict(row)
        return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, name, tier, created_at, active FROM users WHERE id=?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_user_tier(self, user_id: int, tier: str) -> bool:
        with self._conn() as conn:
            conn.execute("UPDATE users SET tier=? WHERE id=?", (tier, user_id))
        return True

    # --- API Key Management ---

    def create_api_key(self, user_id: int, name: str = "default") -> Dict[str, str]:
        raw_key = config.API_KEY_PREFIX + secrets.token_hex(24)
        key_hash = _hash_api_key(raw_key)
        key_prefix = raw_key[:12] + "..."
        now = time.time()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO api_keys (user_id, key_hash, key_prefix, name, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, key_hash, key_prefix, name, now),
            )
        return {"api_key": raw_key, "prefix": key_prefix, "name": name}

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        key_hash = _hash_api_key(api_key)
        now = time.time()
        with self._conn() as conn:
            row = conn.execute(
                """SELECT ak.id as key_id, ak.user_id, ak.name as key_name,
                          u.email, u.tier, u.active
                   FROM api_keys ak JOIN users u ON ak.user_id = u.id
                   WHERE ak.key_hash=? AND ak.active=1""",
                (key_hash,),
            ).fetchone()
            if row and row["active"]:
                conn.execute(
                    "UPDATE api_keys SET last_used_at=? WHERE id=?",
                    (now, row["key_id"]),
                )
                return dict(row)
        return None

    def list_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, key_prefix, name, created_at, last_used_at, active FROM api_keys WHERE user_id=?",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        with self._conn() as conn:
            conn.execute(
                "UPDATE api_keys SET active=0 WHERE id=? AND user_id=?",
                (key_id, user_id),
            )
        return True

    # --- Usage Metering ---

    def log_usage(
        self,
        user_id: int,
        operation: str,
        input_bytes: int = 0,
        output_bytes: int = 0,
        compression_ratio: float = 0,
        mode: str = "",
        api_key_id: Optional[int] = None,
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO usage_log
                   (user_id, api_key_id, operation, input_bytes, output_bytes,
                    compression_ratio, mode, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, api_key_id, operation, input_bytes, output_bytes,
                 compression_ratio, mode, time.time()),
            )

    def get_usage_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        cutoff = time.time() - (days * 86400)
        with self._conn() as conn:
            row = conn.execute(
                """SELECT
                     COUNT(*) as total_requests,
                     COALESCE(SUM(input_bytes), 0) as total_input_bytes,
                     COALESCE(SUM(output_bytes), 0) as total_output_bytes,
                     COALESCE(AVG(compression_ratio), 0) as avg_compression_ratio
                   FROM usage_log WHERE user_id=? AND timestamp>=?""",
                (user_id, cutoff),
            ).fetchone()
        return dict(row) if row else {}

    def check_rate_limit(self, user_id: int) -> Dict[str, Any]:
        window_start = time.time() - config.RATE_LIMIT_WINDOW_SECONDS
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM usage_log WHERE user_id=? AND timestamp>=?",
                (user_id, window_start),
            ).fetchone()
        count = row["count"] if row else 0
        return {
            "requests_used": count,
            "requests_limit": config.RATE_LIMIT_REQUESTS,
            "allowed": count < config.RATE_LIMIT_REQUESTS,
        }

    def check_tier_limits(self, user_id: int) -> Dict[str, Any]:
        user = self.get_user(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}

        tier = user["tier"]
        # Get monthly usage
        monthly_cutoff = time.time() - (30 * 86400)
        with self._conn() as conn:
            row = conn.execute(
                """SELECT COUNT(*) as requests, COALESCE(SUM(input_bytes), 0) as bytes_used
                   FROM usage_log WHERE user_id=? AND timestamp>=?""",
                (user_id, monthly_cutoff),
            ).fetchone()

        requests_used = row["requests"] if row else 0
        bytes_used = row["bytes_used"] if row else 0

        limits = {
            "free": (config.FREE_TIER_MONTHLY_REQUESTS, config.FREE_TIER_MONTHLY_BYTES),
            "pro": (config.PRO_TIER_MONTHLY_REQUESTS, config.PRO_TIER_MONTHLY_BYTES),
            "enterprise": (config.ENTERPRISE_TIER_MONTHLY_REQUESTS, config.ENTERPRISE_TIER_MONTHLY_BYTES),
        }

        max_requests, max_bytes = limits.get(tier, limits["free"])

        # Enterprise has unlimited (-1)
        requests_ok = max_requests == -1 or requests_used < max_requests
        bytes_ok = max_bytes == -1 or bytes_used < max_bytes

        return {
            "tier": tier,
            "requests_used": requests_used,
            "requests_limit": max_requests,
            "bytes_used": bytes_used,
            "bytes_limit": max_bytes,
            "allowed": requests_ok and bytes_ok,
        }

    # --- Envelope Storage ---

    def store_envelope(
        self, user_id: int, envelope_id: str, envelope_json: str,
        original_size: int, envelope_size: int, mode: str,
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO envelopes
                   (user_id, envelope_id, envelope_json, original_size, envelope_size, mode, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, envelope_id, envelope_json, original_size, envelope_size, mode, time.time()),
            )

    def get_envelope(self, envelope_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM envelopes WHERE envelope_id=? AND user_id=?",
                (envelope_id, user_id),
            ).fetchone()
        return dict(row) if row else None

    def list_envelopes(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT envelope_id, original_size, envelope_size, mode, created_at
                   FROM envelopes WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_envelope(self, envelope_id: str, user_id: int) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM envelopes WHERE envelope_id=? AND user_id=?",
                (envelope_id, user_id),
            )
        return cursor.rowcount > 0
