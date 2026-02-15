"""
GoldenSeed Compression SaaS - FastAPI Application

REST API for universal encoding/decoding using deterministic seed-based
stream generation. Provides extreme compression by transmitting seed
envelopes instead of raw data.

API Endpoints:
    POST /api/v1/encode    - Encode/compress data into a seed envelope
    POST /api/v1/decode    - Decode/decompress data from a seed envelope
    POST /api/v1/stream    - Generate a stream reference envelope
    GET  /api/v1/envelopes - List stored envelopes
    GET  /api/v1/envelopes/{id} - Retrieve a stored envelope
    POST /api/v1/auth/register - Register a new account
    POST /api/v1/auth/login    - Login and get JWT token
    POST /api/v1/auth/api-keys - Create an API key
    GET  /api/v1/usage         - Get usage statistics
    GET  /api/v1/health        - Health check
    GET  /                     - Web dashboard
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
import time
from typing import Optional, Dict, Any, List

# Add the src directory to path so we can import gq
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from gq.codec import (
    SeedEnvelope,
    encode,
    decode,
    encode_stream_reference,
    compression_stats,
    SEED_REGISTRY,
)

from .config import config
from .database import Database
from .auth import create_jwt, verify_jwt

# ---------------------------------------------------------------------------
# Lightweight ASGI framework (no external dependency required)
# Falls back to a built-in micro-framework if FastAPI is not installed.
# ---------------------------------------------------------------------------

try:
    from fastapi import FastAPI, Request, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# ---------------------------------------------------------------------------
# Pydantic Models (or plain dicts when FastAPI is absent)
# ---------------------------------------------------------------------------

if HAS_FASTAPI:

    class RegisterRequest(BaseModel):
        email: str
        password: str
        name: str = ""

    class LoginRequest(BaseModel):
        email: str
        password: str

    class EncodeRequest(BaseModel):
        data_base64: str = Field(..., description="Base64-encoded data to compress")
        seed_id: str = Field("golden_ratio", description="Seed identifier")
        scan_depth: int = Field(1000, description="Stream scan depth for match detection")
        store: bool = Field(True, description="Store envelope for later retrieval")

    class DecodeRequest(BaseModel):
        envelope: Optional[Dict[str, Any]] = Field(None, description="Envelope JSON object")
        envelope_id: Optional[str] = Field(None, description="Stored envelope ID to decode")

    class StreamRefRequest(BaseModel):
        seed_id: str = Field("golden_ratio", description="Seed identifier")
        offset: int = Field(0, description="Stream byte offset")
        length: int = Field(1024, description="Number of bytes")
        store: bool = Field(True, description="Store envelope for later retrieval")

    class ApiKeyRequest(BaseModel):
        name: str = "default"

# ---------------------------------------------------------------------------
# Database singleton
# ---------------------------------------------------------------------------

db = Database()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> "FastAPI":
    """Create and configure the FastAPI application."""

    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required. Install with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="GoldenSeed Compression SaaS",
        description=(
            "Universal encoding/decoding service using deterministic seed-based "
            "stream generation. Compress data to tiny seed envelopes and decompress "
            "anywhere without bandwidth."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Auth Dependency ---

    async def get_current_user(
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None),
    ) -> Dict[str, Any]:
        """Authenticate via JWT Bearer token or API key."""

        # Try API key first
        if x_api_key:
            user_info = db.validate_api_key(x_api_key)
            if user_info:
                return user_info
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Try JWT Bearer
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            payload = verify_jwt(token)
            if payload:
                user = db.get_user(payload.get("user_id"))
                if user:
                    return user
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        raise HTTPException(
            status_code=401,
            detail="Authentication required. Use 'Authorization: Bearer <token>' or 'X-API-Key: <key>'",
        )

    async def check_limits(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Check rate limits and tier limits."""
        rate = db.check_rate_limit(user["id"])
        if not rate["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. {rate['requests_used']}/{rate['requests_limit']} requests in window.",
            )
        tier = db.check_tier_limits(user["id"])
        if not tier["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly {tier['tier']} tier limit reached. Upgrade at /dashboard.",
            )
        return user

    # --- Health & Info ---

    @app.get("/api/v1/health")
    async def health():
        return {
            "status": "healthy",
            "service": "GoldenSeed Compression SaaS",
            "version": "1.0.0",
            "available_seeds": list(SEED_REGISTRY.keys()),
        }

    @app.get("/api/v1/seeds")
    async def list_seeds():
        """List available seed identifiers and their properties."""
        return {
            "seeds": {
                name: {
                    "hex_prefix": hex_val[:16] + "...",
                    "hex_length": len(hex_val),
                }
                for name, hex_val in SEED_REGISTRY.items()
            }
        }

    # --- Auth Endpoints ---

    @app.post("/api/v1/auth/register")
    async def register(req: RegisterRequest):
        """Register a new user account."""
        try:
            user = db.create_user(req.email, req.password, req.name)
            key_info = db.create_api_key(user["id"], "default")
            token = create_jwt({"user_id": user["id"], "email": user["email"]})
            return {
                "user": user,
                "token": token,
                "api_key": key_info["api_key"],
                "message": "Account created. Save your API key - it won't be shown again.",
            }
        except Exception as e:
            if "UNIQUE" in str(e):
                raise HTTPException(status_code=409, detail="Email already registered")
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/auth/login")
    async def login(req: LoginRequest):
        """Login and receive a JWT token."""
        user = db.authenticate_user(req.email, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_jwt({"user_id": user["id"], "email": user["email"]})
        return {"token": token, "user": user}

    @app.post("/api/v1/auth/api-keys")
    async def create_api_key(req: ApiKeyRequest, user: Dict = Depends(get_current_user)):
        """Create a new API key."""
        key_info = db.create_api_key(user["id"], req.name)
        return {
            "api_key": key_info["api_key"],
            "name": key_info["name"],
            "message": "Save this key - it won't be shown again.",
        }

    @app.get("/api/v1/auth/api-keys")
    async def list_api_keys(user: Dict = Depends(get_current_user)):
        """List all API keys (shows prefix only)."""
        return {"api_keys": db.list_api_keys(user["id"])}

    @app.delete("/api/v1/auth/api-keys/{key_id}")
    async def revoke_api_key(key_id: int, user: Dict = Depends(get_current_user)):
        """Revoke an API key."""
        db.revoke_api_key(key_id, user["id"])
        return {"message": "API key revoked"}

    # --- Core Compression Endpoints ---

    @app.post("/api/v1/encode")
    async def encode_data(req: EncodeRequest, user: Dict = Depends(check_limits)):
        """
        Encode (compress) data into a seed envelope.

        Send base64-encoded data, receive a compact seed envelope that can
        reconstruct the original data. The envelope is dramatically smaller
        than the original data.
        """
        try:
            data = base64.b64decode(req.data_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        if len(data) > config.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Data exceeds maximum size of {config.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB",
            )

        envelope = encode(data, seed_id=req.seed_id, scan_depth=req.scan_depth)
        stats = compression_stats(data, envelope)
        envelope_dict = envelope.to_dict()

        # Store if requested
        envelope_id = None
        if req.store:
            envelope_id = secrets.token_hex(16)
            db.store_envelope(
                user_id=user["id"],
                envelope_id=envelope_id,
                envelope_json=json.dumps(envelope_dict),
                original_size=len(data),
                envelope_size=envelope.envelope_size,
                mode=envelope.mode,
            )

        # Log usage
        db.log_usage(
            user_id=user["id"],
            operation="encode",
            input_bytes=len(data),
            output_bytes=envelope.envelope_size,
            compression_ratio=stats["compression_ratio"],
            mode=envelope.mode,
        )

        return {
            "envelope_id": envelope_id,
            "envelope": envelope_dict,
            "stats": stats,
        }

    @app.post("/api/v1/decode")
    async def decode_data(req: DecodeRequest, user: Dict = Depends(check_limits)):
        """
        Decode (decompress) data from a seed envelope.

        Provide either an envelope object or an envelope_id of a previously
        stored envelope. Returns the reconstructed original data as base64.
        """
        if req.envelope_id:
            stored = db.get_envelope(req.envelope_id, user["id"])
            if not stored:
                raise HTTPException(status_code=404, detail="Envelope not found")
            envelope = SeedEnvelope.from_dict(json.loads(stored["envelope_json"]))
        elif req.envelope:
            envelope = SeedEnvelope.from_dict(req.envelope)
        else:
            raise HTTPException(
                status_code=400, detail="Provide either 'envelope' or 'envelope_id'"
            )

        try:
            data = decode(envelope)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Log usage
        db.log_usage(
            user_id=user["id"],
            operation="decode",
            input_bytes=envelope.envelope_size,
            output_bytes=len(data),
            mode=envelope.mode,
        )

        return {
            "data_base64": base64.b64encode(data).decode(),
            "size_bytes": len(data),
            "checksum": hashlib.sha256(data).hexdigest(),
        }

    @app.post("/api/v1/stream")
    async def create_stream_reference(req: StreamRefRequest, user: Dict = Depends(check_limits)):
        """
        Create a stream reference envelope.

        This is the most efficient compression mode - reference any segment
        of the deterministic stream with a tiny envelope, regardless of how
        much data it represents.

        Example: A 1 GB stream segment is represented by ~60 bytes.
        """
        if req.length > config.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Requested length too large")

        envelope = encode_stream_reference(
            seed_id=req.seed_id, offset=req.offset, length=req.length,
        )
        stats = {
            "original_size_bytes": req.length,
            "envelope_size_bytes": envelope.envelope_size,
            "compression_ratio": round(req.length / envelope.envelope_size, 2),
            "mode": "stream",
        }

        envelope_dict = envelope.to_dict()
        envelope_id = None
        if req.store:
            envelope_id = secrets.token_hex(16)
            db.store_envelope(
                user_id=user["id"],
                envelope_id=envelope_id,
                envelope_json=json.dumps(envelope_dict),
                original_size=req.length,
                envelope_size=envelope.envelope_size,
                mode="stream",
            )

        db.log_usage(
            user_id=user["id"],
            operation="stream_ref",
            input_bytes=0,
            output_bytes=envelope.envelope_size,
            mode="stream",
        )

        return {
            "envelope_id": envelope_id,
            "envelope": envelope_dict,
            "stats": stats,
        }

    # --- Envelope Management ---

    @app.get("/api/v1/envelopes")
    async def list_envelopes(
        limit: int = 50, offset: int = 0, user: Dict = Depends(get_current_user),
    ):
        """List stored envelopes."""
        envelopes = db.list_envelopes(user["id"], limit=limit, offset=offset)
        return {"envelopes": envelopes, "count": len(envelopes)}

    @app.get("/api/v1/envelopes/{envelope_id}")
    async def get_envelope(envelope_id: str, user: Dict = Depends(get_current_user)):
        """Retrieve a stored envelope."""
        stored = db.get_envelope(envelope_id, user["id"])
        if not stored:
            raise HTTPException(status_code=404, detail="Envelope not found")
        return {
            "envelope_id": stored["envelope_id"],
            "envelope": json.loads(stored["envelope_json"]),
            "original_size": stored["original_size"],
            "envelope_size": stored["envelope_size"],
            "mode": stored["mode"],
            "created_at": stored["created_at"],
        }

    @app.delete("/api/v1/envelopes/{envelope_id}")
    async def delete_envelope(envelope_id: str, user: Dict = Depends(get_current_user)):
        """Delete a stored envelope."""
        deleted = db.delete_envelope(envelope_id, user["id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Envelope not found")
        return {"message": "Envelope deleted"}

    # --- Usage & Account ---

    @app.get("/api/v1/usage")
    async def get_usage(days: int = 30, user: Dict = Depends(get_current_user)):
        """Get usage statistics."""
        summary = db.get_usage_summary(user["id"], days=days)
        tier_info = db.check_tier_limits(user["id"])
        return {"usage": summary, "tier": tier_info}

    @app.get("/api/v1/account")
    async def get_account(user: Dict = Depends(get_current_user)):
        """Get account details."""
        full_user = db.get_user(user["id"])
        tier_info = db.check_tier_limits(user["id"])
        return {"account": full_user, "tier_info": tier_info}

    # --- Web Dashboard ---

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the web dashboard."""
        template_path = os.path.join(
            os.path.dirname(__file__), "templates", "dashboard.html"
        )
        try:
            with open(template_path) as f:
                return f.read()
        except FileNotFoundError:
            return HTMLResponse(
                "<h1>GoldenSeed Compression SaaS</h1>"
                "<p>Dashboard template not found. API available at /api/docs</p>",
                status_code=200,
            )

    return app


# --- Entry point ---

app = create_app() if HAS_FASTAPI else None


def run():
    """Run the SaaS server."""
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is required. Install with: pip install uvicorn")
        sys.exit(1)

    if app is None:
        print("FastAPI is required. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    print(f"Starting GoldenSeed Compression SaaS on {config.HOST}:{config.PORT}")
    print(f"API docs: http://{config.HOST}:{config.PORT}/api/docs")
    print(f"Dashboard: http://{config.HOST}:{config.PORT}/")
    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    run()
