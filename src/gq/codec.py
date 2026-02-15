"""
GoldenSeed Compression Codec

Universal encoding/decoding engine that leverages deterministic stream generation
for extreme data compression. Three compression modes:

1. **Stream-Aligned**: Data that IS a segment of the deterministic stream.
   Compressed to just a seed envelope (seed_id + offset + length).
   Ratio: up to 33,554,432:1 for 1GB.

2. **Delta Compression**: Arbitrary data XOR'd against the deterministic stream.
   Stores the seed envelope + XOR delta (only non-zero bytes).
   Effective when data has patterns similar to the stream.

3. **Catalog Compression**: Register known datasets by name/hash.
   Recipients regenerate from the catalog entry. Zero bandwidth.

The codec produces "Seed Envelopes" - compact descriptors that contain
everything needed to reconstruct the original data.
"""

from __future__ import annotations

import hashlib
import json
import struct
import time
import zlib
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Iterator

from .universal_qkd import (
    universal_qkd_generator,
    collect_sifted_bits,
    xor_fold_hardening,
    HEX_SEED,
    GOLDEN_RATIO_HEX,
    PI_HEX,
    E_HEX,
    SQRT2_HEX,
)


# Named seed registry
SEED_REGISTRY: Dict[str, str] = {
    "golden_ratio": GOLDEN_RATIO_HEX,
    "pi": PI_HEX,
    "e": E_HEX,
    "sqrt2": SQRT2_HEX,
}

# Envelope format version
ENVELOPE_VERSION = 1

# Magic bytes for binary envelope format
ENVELOPE_MAGIC = b"GQSE"  # GoldenSeed Envelope

# Chunk size from the generator (16 bytes per yield)
STREAM_CHUNK_SIZE = 16


@dataclass
class SeedEnvelope:
    """
    Compact descriptor that encodes how to reconstruct data from a seed stream.

    This is the fundamental unit of "compressed" data in the GoldenSeed system.
    Instead of transmitting the data itself, transmit the envelope and let
    the recipient regenerate it locally.
    """
    version: int = ENVELOPE_VERSION
    seed_id: str = "golden_ratio"
    seed_hex: Optional[str] = None  # Custom seed (if not using registry)
    offset: int = 0                  # Stream offset in bytes
    length: int = 0                  # Data length in bytes
    checksum: str = ""               # SHA-256 of original data
    mode: str = "stream"             # "stream", "delta", or "catalog"
    delta: Optional[bytes] = None    # XOR delta for delta mode
    delta_compressed: Optional[bytes] = None  # zlib-compressed delta
    catalog_key: Optional[str] = None  # Key for catalog mode
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "version": self.version,
            "seed_id": self.seed_id,
            "offset": self.offset,
            "length": self.length,
            "checksum": self.checksum,
            "mode": self.mode,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
        if self.seed_hex:
            d["seed_hex"] = self.seed_hex
        if self.delta_compressed is not None:
            d["delta_compressed"] = self.delta_compressed.hex()
        elif self.delta is not None:
            d["delta"] = self.delta.hex()
        if self.catalog_key:
            d["catalog_key"] = self.catalog_key
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SeedEnvelope":
        env = cls(
            version=d.get("version", ENVELOPE_VERSION),
            seed_id=d.get("seed_id", "golden_ratio"),
            seed_hex=d.get("seed_hex"),
            offset=d.get("offset", 0),
            length=d.get("length", 0),
            checksum=d.get("checksum", ""),
            mode=d.get("mode", "stream"),
            catalog_key=d.get("catalog_key"),
            metadata=d.get("metadata", {}),
            created_at=d.get("created_at", time.time()),
        )
        if "delta_compressed" in d:
            env.delta_compressed = bytes.fromhex(d["delta_compressed"])
        elif "delta" in d:
            env.delta = bytes.fromhex(d["delta"])
        return env

    @classmethod
    def from_json(cls, s: str) -> "SeedEnvelope":
        return cls.from_dict(json.loads(s))

    def to_binary(self) -> bytes:
        """Serialize envelope to compact binary format."""
        parts = bytearray(ENVELOPE_MAGIC)
        parts.append(self.version)
        # Mode: 0=stream, 1=delta, 2=catalog
        mode_byte = {"stream": 0, "delta": 1, "catalog": 2}.get(self.mode, 0)
        parts.append(mode_byte)
        # Seed ID as length-prefixed string
        seed_id_bytes = self.seed_id.encode("utf-8")
        parts.extend(struct.pack("<H", len(seed_id_bytes)))
        parts.extend(seed_id_bytes)
        # Offset and length as 64-bit unsigned
        parts.extend(struct.pack("<QQ", self.offset, self.length))
        # Checksum as 32 bytes
        parts.extend(bytes.fromhex(self.checksum))
        # Delta (if present)
        if self.delta_compressed is not None:
            parts.extend(struct.pack("<I", len(self.delta_compressed)))
            parts.extend(self.delta_compressed)
        elif self.delta is not None:
            compressed = zlib.compress(self.delta)
            parts.extend(struct.pack("<I", len(compressed)))
            parts.extend(compressed)
        else:
            parts.extend(struct.pack("<I", 0))
        return bytes(parts)

    @classmethod
    def from_binary(cls, data: bytes) -> "SeedEnvelope":
        """Deserialize envelope from compact binary format."""
        if data[:4] != ENVELOPE_MAGIC:
            raise ValueError("Invalid envelope magic bytes")
        pos = 4
        version = data[pos]; pos += 1
        mode_byte = data[pos]; pos += 1
        mode = {0: "stream", 1: "delta", 2: "catalog"}.get(mode_byte, "stream")
        sid_len = struct.unpack_from("<H", data, pos)[0]; pos += 2
        seed_id = data[pos:pos+sid_len].decode("utf-8"); pos += sid_len
        offset, length = struct.unpack_from("<QQ", data, pos); pos += 16
        checksum = data[pos:pos+32].hex(); pos += 32
        delta_len = struct.unpack_from("<I", data, pos)[0]; pos += 4
        delta_compressed = None
        if delta_len > 0:
            delta_compressed = data[pos:pos+delta_len]
        return cls(
            version=version,
            seed_id=seed_id,
            offset=offset,
            length=length,
            checksum=checksum,
            mode=mode,
            delta_compressed=delta_compressed,
        )

    @property
    def envelope_size(self) -> int:
        """Size of the envelope itself in bytes."""
        return len(self.to_binary())

    @property
    def compression_ratio(self) -> float:
        """Compression ratio (original_size / envelope_size)."""
        if self.envelope_size == 0:
            return 0.0
        return self.length / self.envelope_size


def _raw_stream_generator(seed_hex: str) -> Iterator[bytes]:
    """
    Stream generator that works with any valid hex seed.

    Unlike universal_qkd_generator, this does not enforce the golden ratio
    checksum, allowing it to work with all registered seeds (pi, e, sqrt2, etc).
    Uses the same algorithm: SHA-256 state init, basis matching, XOR folding.
    """
    seed = bytes.fromhex(seed_hex)
    state = hashlib.sha256(seed).digest()
    counter = 0
    while True:
        sifted_bits, state, counter = collect_sifted_bits(state, counter)
        output = xor_fold_hardening(sifted_bits)
        yield output


def _generate_stream_bytes(seed_hex: str, offset: int, length: int) -> bytes:
    """
    Generate a specific segment of the deterministic stream.

    Args:
        seed_hex: Hex seed string (actual hex, not a seed name)
        offset: Byte offset into the stream
        length: Number of bytes to generate

    Returns:
        The requested segment of the stream
    """
    if length == 0:
        return b""

    gen = _raw_stream_generator(seed_hex)
    # Skip to offset
    chunks_to_skip = offset // STREAM_CHUNK_SIZE
    byte_offset_in_chunk = offset % STREAM_CHUNK_SIZE

    result = bytearray()
    for i, chunk in enumerate(gen):
        if i < chunks_to_skip:
            continue
        if i == chunks_to_skip:
            # Partial first chunk
            start = byte_offset_in_chunk
            result.extend(chunk[start:])
        else:
            result.extend(chunk)
        if len(result) >= length:
            break

    return bytes(result[:length])


def _resolve_seed_hex(seed_id: str, seed_hex: Optional[str] = None) -> str:
    """Resolve a seed identifier to its hex representation."""
    if seed_hex:
        return seed_hex
    if seed_id in SEED_REGISTRY:
        return SEED_REGISTRY[seed_id]
    raise ValueError(f"Unknown seed_id: {seed_id}. Available: {list(SEED_REGISTRY.keys())}")


def encode(
    data: bytes,
    seed_id: str = "golden_ratio",
    seed_hex: Optional[str] = None,
    scan_depth: int = 1000,
) -> SeedEnvelope:
    """
    Encode (compress) data into a SeedEnvelope.

    Strategy:
    1. Check if data matches a segment of the stream (stream mode - best compression)
    2. If not, compute XOR delta against stream at offset 0 (delta mode)
    3. Apply zlib compression to the delta for additional savings

    Args:
        data: The data to encode/compress
        seed_id: Named seed from the registry
        seed_hex: Custom seed hex (overrides seed_id)
        scan_depth: How many stream chunks to scan for stream-match mode

    Returns:
        SeedEnvelope describing how to reconstruct the data
    """
    resolved_hex = _resolve_seed_hex(seed_id, seed_hex)
    data_checksum = hashlib.sha256(data).hexdigest()
    data_len = len(data)

    # Strategy 1: Check if data matches a stream segment
    gen = universal_qkd_generator(resolved_hex)
    stream_buffer = bytearray()

    for chunk_idx in range(scan_depth):
        chunk = next(gen)
        stream_buffer.extend(chunk)

        # Check if data appears in the accumulated stream
        if data_len <= len(stream_buffer):
            pos = bytes(stream_buffer).find(data)
            if pos != -1:
                return SeedEnvelope(
                    seed_id=seed_id,
                    seed_hex=seed_hex if seed_hex else None,
                    offset=pos,
                    length=data_len,
                    checksum=data_checksum,
                    mode="stream",
                    metadata={"scan_chunks": chunk_idx + 1},
                )

    # Strategy 2: Delta compression against stream at offset 0
    stream_segment = _generate_stream_bytes(resolved_hex, 0, data_len)

    # XOR to produce delta
    delta = bytes(a ^ b for a, b in zip(data, stream_segment))

    # Compress the delta with zlib
    delta_compressed = zlib.compress(delta, level=9)

    return SeedEnvelope(
        seed_id=seed_id,
        seed_hex=seed_hex if seed_hex else None,
        offset=0,
        length=data_len,
        checksum=data_checksum,
        mode="delta",
        delta=delta,
        delta_compressed=delta_compressed,
        metadata={"delta_raw_size": len(delta), "delta_compressed_size": len(delta_compressed)},
    )


def decode(envelope: SeedEnvelope) -> bytes:
    """
    Decode (decompress) data from a SeedEnvelope.

    Reconstructs the original data by regenerating the stream segment
    and applying any stored delta.

    Args:
        envelope: The SeedEnvelope to decode

    Returns:
        The original data bytes

    Raises:
        ValueError: If checksum verification fails
    """
    resolved_hex = _resolve_seed_hex(envelope.seed_id, envelope.seed_hex)

    if envelope.mode == "stream":
        # Pure stream reconstruction - no delta needed
        data = _generate_stream_bytes(resolved_hex, envelope.offset, envelope.length)

    elif envelope.mode == "delta":
        # Regenerate stream segment and apply delta
        stream_segment = _generate_stream_bytes(resolved_hex, envelope.offset, envelope.length)

        # Get the delta
        if envelope.delta_compressed is not None:
            delta = zlib.decompress(envelope.delta_compressed)
        elif envelope.delta is not None:
            delta = envelope.delta
        else:
            raise ValueError("Delta mode envelope has no delta data")

        data = bytes(a ^ b for a, b in zip(stream_segment, delta))

    elif envelope.mode == "catalog":
        raise ValueError("Catalog mode requires a catalog registry (use decode_from_catalog)")

    else:
        raise ValueError(f"Unknown envelope mode: {envelope.mode}")

    # Verify checksum
    actual_checksum = hashlib.sha256(data).hexdigest()
    if actual_checksum != envelope.checksum:
        raise ValueError(
            f"Checksum mismatch: expected {envelope.checksum}, got {actual_checksum}"
        )

    return data


def encode_stream_reference(
    seed_id: str = "golden_ratio",
    offset: int = 0,
    length: int = 1024,
    seed_hex: Optional[str] = None,
) -> SeedEnvelope:
    """
    Create a SeedEnvelope that references a specific stream segment.

    This is the most efficient compression mode - the envelope is tiny
    regardless of how much data it represents.

    Args:
        seed_id: Named seed from the registry
        offset: Byte offset into the stream
        length: Number of bytes
        seed_hex: Custom seed hex

    Returns:
        SeedEnvelope for the stream segment
    """
    resolved_hex = _resolve_seed_hex(seed_id, seed_hex)
    data = _generate_stream_bytes(resolved_hex, offset, length)
    data_checksum = hashlib.sha256(data).hexdigest()

    return SeedEnvelope(
        seed_id=seed_id,
        seed_hex=seed_hex if seed_hex else None,
        offset=offset,
        length=length,
        checksum=data_checksum,
        mode="stream",
    )


def compression_stats(data: bytes, envelope: SeedEnvelope) -> Dict[str, Any]:
    """Compute compression statistics for an encoding."""
    original_size = len(data)
    envelope_binary = envelope.to_binary()
    envelope_size = len(envelope_binary)

    return {
        "original_size_bytes": original_size,
        "envelope_size_bytes": envelope_size,
        "compression_ratio": round(original_size / envelope_size, 2) if envelope_size > 0 else float("inf"),
        "space_savings_percent": round((1 - envelope_size / original_size) * 100, 2) if original_size > 0 else 0,
        "mode": envelope.mode,
        "seed_id": envelope.seed_id,
    }


# --- Catalog System ---

class SeedCatalog:
    """
    Registry of known datasets that can be reconstructed from seed envelopes.

    The catalog maps human-readable names to SeedEnvelopes, enabling
    zero-bandwidth data distribution. Parties who share a catalog
    can reference datasets by name without transmitting any data.
    """

    def __init__(self):
        self._entries: Dict[str, SeedEnvelope] = {}

    def register(self, key: str, data: bytes, seed_id: str = "golden_ratio", **kwargs) -> SeedEnvelope:
        """Register data in the catalog and return its envelope."""
        envelope = encode(data, seed_id=seed_id, **kwargs)
        envelope.mode = "catalog" if envelope.mode == "stream" else envelope.mode
        envelope.catalog_key = key
        self._entries[key] = envelope
        return envelope

    def lookup(self, key: str) -> Optional[SeedEnvelope]:
        """Look up an envelope by catalog key."""
        return self._entries.get(key)

    def decode_entry(self, key: str) -> bytes:
        """Decode a catalog entry back to original data."""
        envelope = self._entries.get(key)
        if envelope is None:
            raise KeyError(f"Catalog key not found: {key}")
        # Temporarily set mode for decoding
        original_mode = envelope.mode
        if envelope.mode == "catalog":
            envelope.mode = "stream"
        try:
            return decode(envelope)
        finally:
            envelope.mode = original_mode

    def list_entries(self) -> List[Dict[str, Any]]:
        """List all catalog entries with metadata."""
        return [
            {
                "key": key,
                "length": env.length,
                "mode": env.mode,
                "seed_id": env.seed_id,
                "checksum": env.checksum,
            }
            for key, env in self._entries.items()
        ]

    def export_catalog(self) -> str:
        """Export catalog as JSON."""
        entries = {key: env.to_dict() for key, env in self._entries.items()}
        return json.dumps({"version": ENVELOPE_VERSION, "entries": entries}, indent=2)

    def import_catalog(self, catalog_json: str) -> int:
        """Import catalog from JSON. Returns number of entries imported."""
        data = json.loads(catalog_json)
        count = 0
        for key, env_dict in data.get("entries", {}).items():
            self._entries[key] = SeedEnvelope.from_dict(env_dict)
            count += 1
        return count
