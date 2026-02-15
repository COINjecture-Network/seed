"""
SaaS Configuration

All settings with sensible defaults. Override via environment variables.
"""

import os
import secrets


class Config:
    # Server
    HOST: str = os.getenv("SEED_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SEED_PORT", "8000"))
    DEBUG: bool = os.getenv("SEED_DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv("SEED_DATABASE_URL", "sqlite:///seed_saas.db")
    DATABASE_PATH: str = os.getenv("SEED_DATABASE_PATH", "seed_saas.db")

    # Authentication
    JWT_SECRET: str = os.getenv("SEED_JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = int(os.getenv("SEED_JWT_EXPIRATION_HOURS", "24"))
    API_KEY_PREFIX: str = "gseed_"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("SEED_RATE_LIMIT", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("SEED_RATE_LIMIT_WINDOW", "60"))

    # Compression
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("SEED_MAX_UPLOAD_MB", "100")) * 1024 * 1024
    DEFAULT_SCAN_DEPTH: int = int(os.getenv("SEED_SCAN_DEPTH", "1000"))

    # Free tier limits
    FREE_TIER_MONTHLY_BYTES: int = 100 * 1024 * 1024  # 100 MB
    FREE_TIER_MONTHLY_REQUESTS: int = 1000

    # Pro tier limits
    PRO_TIER_MONTHLY_BYTES: int = 10 * 1024 * 1024 * 1024  # 10 GB
    PRO_TIER_MONTHLY_REQUESTS: int = 100_000

    # Enterprise tier - unlimited (controlled by custom agreement)
    ENTERPRISE_TIER_MONTHLY_BYTES: int = -1  # unlimited
    ENTERPRISE_TIER_MONTHLY_REQUESTS: int = -1  # unlimited


config = Config()
