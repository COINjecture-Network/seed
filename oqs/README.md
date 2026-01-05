# Open Quantum Safe (OQS) Integration

This directory contains the integration of **Open Quantum Safe (OQS)** library into the project, providing quantum-resistant cryptographic operations using NIST-approved post-quantum algorithms.

## Overview

The OQS integration demonstrates practical implementation of post-quantum cryptography (PQC) using the **liboqs** library. This ensures that cryptographic operations in the project are resistant to attacks from both classical and quantum computers.

### Key Features

- 🔐 **Quantum-Resistant Key Exchange** - Using Kyber-768 (NIST FIPS 203 - ML-KEM)
- ✅ **NIST-Approved Algorithms** - Compliant with NIST Post-Quantum Cryptography standards
- 🧪 **Comprehensive Testing** - Automated CI/CD testing via GitHub Actions
- 📚 **Complete Documentation** - Full integration guide and examples
- 🔄 **Hybrid Approach** - Compatible with existing deterministic key generation

## Quick Start

### Prerequisites

- GCC or Clang compiler
- CMake (version 3.5 or higher)
- OpenSSL development libraries
- Make

On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y cmake gcc ninja-build libssl-dev
```

On macOS:
```bash
brew install cmake gcc openssl
```

### Building liboqs

1. **Build and install liboqs:**
   ```bash
   cd oqs
   bash build_liboqs.sh
   ```

   This script will:
   - Download liboqs v0.10.1 from GitHub
   - Configure with CMake
   - Build the library
   - Install to `oqs/liboqs-install/`

2. **Verify the installation:**
   ```bash
   ls -l liboqs-install/lib/
   ls -l liboqs-install/include/
   ```

### Building and Running the Kyber Test

1. **Build the test:**
   ```bash
   make
   ```

2. **Run the test:**
   ```bash
   make test
   ```

   Expected output:
   ```
   ==========================================
   Kyber-768 Key Exchange Test
   Post-Quantum Cryptography (NIST FIPS 203)
   ==========================================

   Algorithm: Kyber768
   NIST Security Level: 3
   Public Key Size: 1184 bytes
   Secret Key Size: 2400 bytes
   Ciphertext Size: 1088 bytes
   Shared Secret Size: 32 bytes

   Step 1: Alice generates keypair
   -----------------------------------
   ✓ Keypair generated successfully

   Step 2: Bob encapsulates shared secret
   -----------------------------------
   ✓ Encapsulation successful

   Step 3: Alice decapsulates shared secret
   -----------------------------------
   ✓ Decapsulation successful

   Step 4: Verify shared secrets match
   -----------------------------------
   ✓ SUCCESS: Both parties have the same shared secret!
   ✓ Key exchange completed successfully
   ```

## What is Kyber?

**Kyber** (now standardized as **ML-KEM** in NIST FIPS 203) is a **Key Encapsulation Mechanism (KEM)** designed to be secure against attacks by quantum computers. It's based on the **Module Learning With Errors (Module-LWE)** problem, which is believed to be hard for both classical and quantum computers to solve.

### Kyber-768 Specifications

- **Security Level**: NIST Level 3 (equivalent to AES-192)
- **Public Key Size**: 1,184 bytes
- **Secret Key Size**: 2,400 bytes
- **Ciphertext Size**: 1,088 bytes
- **Shared Secret Size**: 32 bytes (256 bits)
- **Standard**: NIST FIPS 203 (Module-Lattice-Based Key-Encapsulation Mechanism)

### How Kyber Key Exchange Works

```
Alice                                Bob
------                               -----
1. Generate keypair
   (public_key, secret_key)
   
2. Send public_key         --------->
   
                                     3. Encapsulate:
                                        Generate shared_secret
                                        Create ciphertext using public_key
   
                           <---------  4. Send ciphertext
   
5. Decapsulate:
   Recover shared_secret
   using ciphertext and secret_key
   
6. Both parties now have the same shared_secret
   Use it for symmetric encryption (AES, ChaCha20, etc.)
```

## Integration with Project

This OQS integration complements the existing **NIST PQC hybrid key generation** in the project:

### Hybrid Security Model

1. **Python Layer** (`src/gq/nist_pqc.py`):
   - Generates deterministic keys using GCP-1 protocol
   - Produces PQC-compatible seed material
   - Provides high-level API for hybrid key generation

2. **C/liboqs Layer** (`oqs/`):
   - Implements actual Kyber key exchange
   - Uses seed material from Python layer
   - Provides low-level cryptographic operations

### Example Integration

```c
// Use seed from Python hybrid key generation
uint8_t seed[32] = { /* from generate_kyber_seed() */ };

// Initialize Kyber with the seed
OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
// ... use the seed for key generation ...
```

## Project Structure

```
oqs/
├── README.md                    # This file
├── SECURITY_CHECKLIST.md        # Security best practices
├── build_liboqs.sh             # Build script for liboqs
├── kyber_test.c                # Kyber key exchange test
├── Makefile                    # Build configuration
├── build/                      # Build directory (generated)
└── liboqs-install/             # liboqs installation (generated)
    ├── include/                # Header files
    └── lib/                    # Library files
```

## Supported Algorithms

liboqs includes many NIST-approved post-quantum algorithms:

### Key Encapsulation Mechanisms (KEMs)
- **Kyber-512** (Security Level 1)
- **Kyber-768** (Security Level 3) - **Recommended**
- **Kyber-1024** (Security Level 5)

### Digital Signature Algorithms
- **Dilithium2** (Security Level 2)
- **Dilithium3** (Security Level 3)
- **Dilithium5** (Security Level 5)
- **Falcon-512** (Security Level 1)
- **Falcon-1024** (Security Level 5)
- **SPHINCS+-128f** (Security Level 1)
- **SPHINCS+-192f** (Security Level 3)
- **SPHINCS+-256f** (Security Level 5)

## Testing

### Local Testing

```bash
# Build and test
make test

# Clean build artifacts
make clean

# Show help
make help
```

### CI/CD Testing

The project includes automated testing via GitHub Actions (`.github/workflows/oqs-integration.yml`):

1. **Build liboqs** - Downloads and builds liboqs v0.10.1
2. **Build test** - Compiles the Kyber test
3. **Run test** - Executes the key exchange test
4. **Verify integration** - Tests Python NIST PQC compatibility
5. **Security checklist** - Validates security requirements

Run workflow manually:
```bash
# Via GitHub Actions web interface:
# Actions → OQS Integration Tests → Run workflow
```

## Development

### Adding New Tests

1. Create a new `.c` file in `oqs/`
2. Update `Makefile` to include the new test
3. Add test execution to `.github/workflows/oqs-integration.yml`

Example for Dilithium signature test:
```c
#include <oqs/oqs.h>

int main() {
    OQS_SIG *sig = OQS_SIG_new(OQS_SIG_alg_dilithium_3);
    // ... implement signature test ...
    OQS_SIG_free(sig);
    return 0;
}
```

### Using System liboqs

If you have liboqs installed system-wide:

```bash
make USE_SYSTEM_LIBOQS=1
```

### Custom liboqs Installation

```bash
make LIBOQS_INSTALL_DIR=/path/to/liboqs
```

## Security Considerations

### Quantum Threat Timeline

While large-scale quantum computers don't yet exist, organizations should:

1. **Start planning now** - "Store now, decrypt later" attacks are a real threat
2. **Implement hybrid approaches** - Combine classical and PQC algorithms
3. **Stay updated** - NIST standards are evolving

### Best Practices

✅ **DO:**
- Use NIST-approved algorithms (Kyber, Dilithium, SPHINCS+)
- Implement hybrid classical/PQC systems
- Use appropriate security levels for your threat model
- Keep liboqs updated to latest stable version
- Validate key exchange success before using shared secrets
- Use secure random number generators
- Follow key management best practices

❌ **DON'T:**
- Rely solely on classical cryptography for long-term security
- Use deprecated or non-standardized PQC algorithms
- Skip testing and validation
- Hardcode cryptographic keys
- Ignore side-channel attack considerations

See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) for complete security guidelines.

## Troubleshooting

### Build Issues

**Problem:** CMake not found
```bash
sudo apt-get install cmake
```

**Problem:** OpenSSL headers missing
```bash
sudo apt-get install libssl-dev
```

**Problem:** Library not found when running test
```bash
export LD_LIBRARY_PATH=$(pwd)/liboqs-install/lib:$LD_LIBRARY_PATH
```

### Runtime Issues

**Problem:** "OQS_KEM_new failed"
- Verify liboqs installation: `ls liboqs-install/lib/`
- Check LD_LIBRARY_PATH includes liboqs-install/lib
- Rebuild liboqs: `bash build_liboqs.sh`

**Problem:** Segmentation fault
- Ensure all memory allocations succeeded
- Verify correct algorithm name (case-sensitive)
- Check liboqs version compatibility

## Resources

### Official Resources
- **liboqs GitHub**: https://github.com/open-quantum-safe/liboqs
- **OQS Project**: https://openquantumsafe.org/
- **NIST PQC**: https://csrc.nist.gov/projects/post-quantum-cryptography

### NIST Standards
- **FIPS 203**: Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM / Kyber)
- **FIPS 204**: Module-Lattice-Based Digital Signature Algorithm (ML-DSA / Dilithium)
- **FIPS 205**: Stateless Hash-Based Digital Signature Algorithm (SLH-DSA / SPHINCS+)

### Related Documentation
- Main project README: `../README.md`
- NIST PQC integration: `../examples/nist_pqc_integration.md`
- Security policy: `../SECURITY.md`
- Python NIST PQC module: `../src/gq/nist_pqc.py`

## Contributing

When contributing to OQS integration:

1. Ensure all tests pass locally before submitting PR
2. Update documentation for new features
3. Follow existing code style and conventions
4. Add tests for new functionality
5. Verify CI/CD workflows pass

## License

This integration follows the same license as the main project (GPL-3.0-or-later).

The liboqs library is licensed under the MIT License.

---

**Last Updated**: January 5, 2026  
**liboqs Version**: 0.10.1  
**NIST Standards**: FIPS 203, 204, 205
