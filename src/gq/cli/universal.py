"""
Golden Stream Generator CLI

Command-line interface for the deterministic stream generator.

⚠️ NOT FOR CRYPTOGRAPHY: This generates deterministic pseudo-random streams
for procedural generation, testing, and simulations only.

Usage:
    gq-universal                     # Generate 10 streams (default)
    gq-universal -n 100              # Generate 100 streams
    gq-universal -n 50 -o streams.txt  # Save to file
    gq-universal --json              # Output in JSON format
    gq-universal --verify-only       # Verify seed only
"""

from ..stream_generator import main

if __name__ == "__main__":
    main()
