# Cryptographically Secure Pseudorandom Number Generator (CSPRNG)

A Python implementation of a cryptographically secure pseudorandom number generator that follows best practices for secure random number generation.

## Features

- **Secure by Default**: Uses `os.urandom` for cryptographically secure entropy
- **Thread-Safe**: All operations are protected by threading locks
- **Uniform Distribution**: Implements rejection sampling to ensure uniform distribution without modulo bias
- **Deterministic Mode**: Optional seeding for reproducible outputs (testing/non-cryptographic use)
- **Well-Tested**: Comprehensive test suite covering all functionality
- **Well-Documented**: Extensive docstrings and comments explaining design decisions

## Usage

### Secure Random Number Generation (Recommended)

```python
from csprng import CSPRNG

# Create a secure generator
rng = CSPRNG()

# Generate random integers
dice_roll = rng.random_int(1, 6)
port_number = rng.random_int(49152, 65535)

# Generate random floats [0.0, 1.0)
probability = rng.random_float()

# Generate random bytes
token = rng.random_bytes(32)
```

### Deterministic Mode (Testing/Reproducibility Only)

⚠️ **WARNING**: Deterministic mode is NOT cryptographically secure and should only be used for testing or non-security-critical applications.

```python
from csprng import CSPRNG

# Create a deterministic generator with a seed
rng = CSPRNG(seed=b"my_test_seed")

# Will produce the same sequence every time with the same seed
values = [rng.random_int(1, 100) for _ in range(10)]

# Check if generator is deterministic
assert rng.is_deterministic() == True
```

### Static Methods (One-off Generation)

```python
from csprng import CSPRNG

# Generate a single random integer without creating a generator instance
random_number = CSPRNG.secure_random_int(0, 100)

# Generate random bytes without creating a generator instance
random_token = CSPRNG.secure_random_bytes(32)
```

## API Reference

### Class: `CSPRNG`

#### `__init__(seed: Optional[Union[bytes, int]] = None)`

Initialize the CSPRNG.

- **Parameters:**
  - `seed` (optional): Seed for deterministic mode. Can be bytes or int. If None, uses secure entropy.
- **Raises:**
  - `ValueError`: If seed is invalid type or empty.

#### `random_bytes(length: int) -> bytes`

Generate cryptographically secure random bytes.

- **Parameters:**
  - `length`: Number of bytes to generate (must be positive)
- **Returns:** Random bytes of specified length
- **Raises:**
  - `ValueError`: If length is not positive

#### `random_int(a: int, b: int) -> int`

Generate a uniformly distributed random integer in range [a, b].

- **Parameters:**
  - `a`: Lower bound (inclusive)
  - `b`: Upper bound (inclusive)
- **Returns:** Random integer in range [a, b]
- **Raises:**
  - `ValueError`: If a > b

#### `random_float() -> float`

Generate a uniformly distributed random float in range [0.0, 1.0).

- **Returns:** Random float in range [0.0, 1.0)

#### `is_deterministic() -> bool`

Check if the generator is operating in deterministic mode.

- **Returns:** True if using custom seed, False if secure

#### `secure_random_int(a: int, b: int) -> int` (static)

Generate a single secure random integer using Python's `secrets` module.

- **Parameters:**
  - `a`: Lower bound (inclusive)
  - `b`: Upper bound (inclusive)
- **Returns:** Secure random integer in range [a, b]
- **Raises:**
  - `ValueError`: If a > b

#### `secure_random_bytes(length: int) -> bytes` (static)

Generate secure random bytes using Python's `secrets` module.

- **Parameters:**
  - `length`: Number of bytes to generate
- **Returns:** Secure random bytes
- **Raises:**
  - `ValueError`: If length is not positive

## Design and Implementation

### Entropy Sources

- **Secure Mode**: Uses `os.urandom(64)` which provides cryptographically secure random bytes from the operating system:
  - Linux: `/dev/urandom` (getrandom() syscall when available)
  - Windows: CryptGenRandom
  - macOS: `/dev/urandom` (backed by Yarrow PRNG)

- **Deterministic Mode**: Uses SHA-512 to expand user-provided seed to 64 bytes

### State Evolution

The internal state is evolved using SHA-512 hashing:

- **Secure Mode**: Mixes new entropy with current state using XOR, then hashes with SHA-512. This provides forward secrecy - even if the state is compromised, past outputs cannot be reconstructed.

- **Deterministic Mode**: Hashes the current state with SHA-512 to produce the next state.

### Uniform Distribution

The `random_int` method uses rejection sampling to ensure uniform distribution without modulo bias. This is critical for security-sensitive applications.

### Thread Safety

All state-modifying operations are protected by a threading lock (`threading.Lock`), ensuring safe concurrent access from multiple threads.

### Precision

The `random_float` method uses 53 bits of randomness to provide full double-precision float uniformity in the range [0.0, 1.0).

## Testing

Run the comprehensive test suite:

```bash
python3 -m unittest test_csprng -v
```

The test suite includes:
- Initialization tests (secure and deterministic)
- Random byte generation tests
- Random integer generation tests (including distribution tests)
- Random float generation tests (including distribution tests)
- Thread safety tests
- Static method tests
- Error handling tests

## Security Considerations

1. **Use Secure Mode for Cryptography**: Never use deterministic mode for cryptographic applications, key generation, or security-sensitive operations.

2. **Seed Security**: If using deterministic mode, ensure seeds are never predictable or reused across different contexts.

3. **Forward Secrecy**: In secure mode, the implementation provides forward secrecy by continuously mixing new entropy into the state.

4. **No Modulo Bias**: The implementation uses rejection sampling to avoid modulo bias in integer generation.

5. **Platform Security**: The security of the secure mode depends on the underlying OS's random number generator (`os.urandom`). Ensure your operating system is up-to-date.

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## License

This implementation is part of the seed repository and follows the same license as the main codebase.
