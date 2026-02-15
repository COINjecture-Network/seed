"""
GoldenSeed Compression SDK Client

Python client for the GoldenSeed Compression SaaS API.

Usage:
    from saas.sdk import SeedClient

    client = SeedClient("https://your-host.com", api_key="gseed_your_key")

    # Encode data
    result = client.encode(b"Hello, World!" * 1000)
    print(f"Compressed to {result['stats']['compression_ratio']}:1")

    # Decode data
    data = client.decode(envelope=result['envelope'])
    print(f"Decoded {len(data)} bytes")

    # Stream reference (extreme compression)
    ref = client.stream_ref(offset=0, length=1_000_000_000)  # 1GB
    print(f"1GB referenced in {ref['stats']['envelope_size_bytes']} bytes")
"""

from __future__ import annotations

import base64
import json
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class SeedClientError(Exception):
    """Raised when an API call fails."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class SeedClient:
    """
    Python SDK client for the GoldenSeed Compression SaaS.

    Supports authentication via API key or JWT token.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token = token

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        elif self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}/api/v1{path}"
        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            detail = json.loads(e.read()).get("detail", str(e))
            raise SeedClientError(e.code, detail)

    # --- Auth ---

    def register(self, email: str, password: str, name: str = "") -> Dict:
        """Register a new account. Returns user info, token, and API key."""
        result = self._request("POST", "/auth/register", {
            "email": email, "password": password, "name": name,
        })
        self.token = result.get("token")
        if result.get("api_key"):
            self.api_key = result["api_key"]
        return result

    def login(self, email: str, password: str) -> Dict:
        """Login and store the JWT token."""
        result = self._request("POST", "/auth/login", {
            "email": email, "password": password,
        })
        self.token = result.get("token")
        return result

    def create_api_key(self, name: str = "default") -> Dict:
        """Create a new API key."""
        return self._request("POST", "/auth/api-keys", {"name": name})

    # --- Core Operations ---

    def encode(
        self,
        data: bytes,
        seed_id: str = "golden_ratio",
        scan_depth: int = 1000,
        store: bool = True,
    ) -> Dict:
        """
        Encode (compress) data into a seed envelope.

        Args:
            data: Raw bytes to compress
            seed_id: Seed identifier (golden_ratio, pi, e, sqrt2)
            scan_depth: How deep to scan for stream matches
            store: Whether to store the envelope server-side

        Returns:
            Dict with envelope, envelope_id, and stats
        """
        return self._request("POST", "/encode", {
            "data_base64": base64.b64encode(data).decode(),
            "seed_id": seed_id,
            "scan_depth": scan_depth,
            "store": store,
        })

    def decode(
        self,
        envelope: Optional[Dict] = None,
        envelope_id: Optional[str] = None,
    ) -> bytes:
        """
        Decode (decompress) data from a seed envelope.

        Args:
            envelope: Envelope dict (from encode result)
            envelope_id: ID of a stored envelope

        Returns:
            Reconstructed original data as bytes
        """
        body = {}
        if envelope:
            body["envelope"] = envelope
        if envelope_id:
            body["envelope_id"] = envelope_id
        result = self._request("POST", "/decode", body)
        return base64.b64decode(result["data_base64"])

    def stream_ref(
        self,
        seed_id: str = "golden_ratio",
        offset: int = 0,
        length: int = 1024,
        store: bool = True,
    ) -> Dict:
        """
        Create a stream reference envelope.

        This is extreme compression - reference any amount of deterministic
        stream data with a tiny envelope.

        Args:
            seed_id: Seed identifier
            offset: Byte offset into the stream
            length: Number of bytes to reference
            store: Whether to store the envelope

        Returns:
            Dict with envelope and stats
        """
        return self._request("POST", "/stream", {
            "seed_id": seed_id,
            "offset": offset,
            "length": length,
            "store": store,
        })

    # --- Envelope Management ---

    def list_envelopes(self, limit: int = 50, offset: int = 0) -> Dict:
        """List stored envelopes."""
        return self._request("GET", f"/envelopes?limit={limit}&offset={offset}")

    def get_envelope(self, envelope_id: str) -> Dict:
        """Retrieve a stored envelope."""
        return self._request("GET", f"/envelopes/{envelope_id}")

    def delete_envelope(self, envelope_id: str) -> Dict:
        """Delete a stored envelope."""
        return self._request("DELETE", f"/envelopes/{envelope_id}")

    # --- Account ---

    def usage(self, days: int = 30) -> Dict:
        """Get usage statistics."""
        return self._request("GET", f"/usage?days={days}")

    def account(self) -> Dict:
        """Get account details."""
        return self._request("GET", "/account")

    def health(self) -> Dict:
        """Check service health (no auth required)."""
        url = f"{self.base_url}/api/v1/health"
        req = Request(url)
        with urlopen(req) as resp:
            return json.loads(resp.read())
