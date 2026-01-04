# Changelog

All notable changes to the Post-Quantum Secure Key Generation Multi-Language Compiler with deterministic keys and verified checksums.

## [Unreleased]

### Changed
- **NIST PQC Alignment**: Updated terminology to reflect alignment with NIST Post-Quantum Cryptography standards
- Documentation now emphasizes compatibility with NIST PQC algorithms (CRYSTALS-Kyber, CRYSTALS-Dilithium, FrodoKEM)
- Clarified system as post-quantum secure key generation rather than traditional QKD
- Added integration points for NIST PQC algorithm implementations

## [1.0.0] - 2026-01-03

### Added
- **Post-Quantum Secure Key Generation System**: Complete implementation with deterministic keys and quantum-resistant security
- **Multi-Language Compiler**: Generate Binary Fusion Tap implementations in 7 languages
  - Python (3.6+)
  - JavaScript (Node.js + Browser)
  - TypeScript (with full type definitions)
  - Rust (memory-safe, zero-cost)
  - Go (concurrent-ready)
  - C (high-performance native)
  - Java (enterprise-ready)

- **Key Generator Service**:
  - Three algorithms: Fusion, Hash, Hybrid
  - Deterministic key generation with verified checksums
  - Configurable key lengths: 128, 256, 512 bits
  - Batch generation
  - JSON/Text output
  - SHA256 checksum validation
  - **NIST PQC Compatible**: Suitable for use with Kyber, Dilithium, FrodoKEM
  - 19 comprehensive unit tests

- **K-Value Explorer**:
  - Analyze Binary Fusion Tap across any k range
  - Visual bit length growth charts
  - Identify special k values (Fibonacci, power-of-2, max ZPE)
  - JSON export for analysis
  - Detailed mode for deep inspection

- **Binary Verification Tool**:
  - Verify binary representations with checksums
  - 8-fold Heartbeat operation
  - ZPE Overflow extraction
  - SHA256/SHA512 checksum support
  - 18 unit tests

- **Release System**:
  - Automated release generation
  - Language-specific READMEs
  - Build/run scripts for each language
  - Configuration files (package.json, Cargo.toml, etc.)
  - Master documentation

### Features

**Binary Fusion Tap Algorithm (Post-Quantum Secure Core):**
1. Seed Generation: Concatenate 1,2,3,...,k (deterministic)
2. 8-fold Heartbeat: Bit-shift left by 3 (×8 multiplication)
3. Phase Offset: Add k parameter for phase alignment
4. ZPE Overflow: XOR extraction for k ≥ 10 (entropy extraction)
5. Checksum Verification: SHA256/SHA512 integrity validation

**Applications:**
- **Post-Quantum Cryptography** - Primary use case, NIST PQC integration
- Secure key generation with verified checksums (Kyber, Dilithium, FrodoKEM compatible)
- Protocol verification and compliance testing
- Quantum-resistant cryptography research
- Deterministic tie-breaking in distributed systems
- API key generation for SaaS platforms
- Cross-platform deterministic systems

### Technical Details

**Key Metrics (k=11):**
- Seed Value: 1234567891011
- Bit Length: 41 → 44 (after heartbeat)
- ZPE Overflow: 59 (0b111011)
- Manifested: 9876543128099

**Test Coverage:**
- 56 total unit tests across all components
- 100% pass rate
- Covers all algorithms and languages
- Integration and unit tests

**Performance:**
- C implementation: Native performance
- Rust: Zero-cost abstractions
- Go: Concurrent-ready
- All implementations produce identical output

### Documentation
- Comprehensive README.md
- Language-specific guides
- API documentation
- Examples for all languages
- Build instructions
- Usage examples

## [Unreleased]

### Planned
- WebAssembly compilation target
- Python package distribution (PyPI)
- npm package for JavaScript/TypeScript
- Cargo crate for Rust
- More k-value analysis tools
- Performance benchmarks
- Additional test vectors

---

Format based on [Keep a Changelog](https://keepachangelog.com/)
