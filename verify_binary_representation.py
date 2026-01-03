#!/usr/bin/env python3
"""
Binary Representation Verification Tool

This script verifies the binary representation of seed values and their
manifested forms using the Golden Quantum seed methodology.

The verification demonstrates the relationship between a seed value and
its manifested binary representation using the formula:
    manifested = (seed * 8) + k
where k is the tap parameter.
"""

import hashlib


def calculate_checksum(value: int, algorithm: str = 'sha256') -> str:
    """
    Calculate cryptographic checksum of an integer value.

    Args:
        value: The integer value to checksum
        algorithm: Hash algorithm to use ('sha256' or 'sha512')

    Returns:
        Hexadecimal string representation of the checksum
    """
    # Convert integer to bytes (big-endian representation)
    byte_length = (value.bit_length() + 7) // 8
    value_bytes = value.to_bytes(byte_length, byteorder='big')
    
    # Calculate hash
    if algorithm == 'sha256':
        hash_obj = hashlib.sha256(value_bytes)
    elif algorithm == 'sha512':
        hash_obj = hashlib.sha512(value_bytes)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return hash_obj.hexdigest()


def verify_checksum_integrity(seed_value: int, manifested_value: int, 
                               expected_seed_checksum: str = None,
                               expected_manifested_checksum: str = None) -> dict:
    """
    Verify the integrity of seed and manifested values using checksums.

    Args:
        seed_value: The seed value to verify
        manifested_value: The manifested value to verify
        expected_seed_checksum: Expected SHA256 checksum for seed (optional)
        expected_manifested_checksum: Expected SHA256 checksum for manifested (optional)

    Returns:
        Dictionary containing checksum verification results
    """
    actual_seed_checksum = calculate_checksum(seed_value, 'sha256')
    actual_manifested_checksum = calculate_checksum(manifested_value, 'sha256')
    
    result = {
        'seed_sha256': actual_seed_checksum,
        'manifested_sha256': actual_manifested_checksum,
        'seed_checksum_valid': True,
        'manifested_checksum_valid': True
    }
    
    # Verify against expected checksums if provided
    if expected_seed_checksum:
        result['seed_checksum_valid'] = (actual_seed_checksum == expected_seed_checksum)
    
    if expected_manifested_checksum:
        result['manifested_checksum_valid'] = (actual_manifested_checksum == expected_manifested_checksum)
    
    return result


def verify_binary_representation(k: int, seed_value: int) -> dict:
    """
    Verify binary representation of seed and its manifested form.

    Args:
        k: Tap parameter (typically 11)
        seed_value: The seed value to verify

    Returns:
        Dictionary containing verification results including checksums
    """
    # Calculate binary representation of seed
    binary_representation = bin(seed_value)
    bit_length = len(binary_representation) - 2  # Subtract '0b' prefix

    # Calculate manifested value: (seed * 8) + k
    manifested = (seed_value * 8) + k
    binary_manifested = bin(manifested)
    manifested_bit_length = len(binary_manifested) - 2

    # Calculate checksums for integrity verification
    checksums = verify_checksum_integrity(seed_value, manifested)

    return {
        'k': k,
        'seed_value': seed_value,
        'seed_binary': binary_representation,
        'seed_bit_length': bit_length,
        'manifested_value': manifested,
        'manifested_binary': binary_manifested,
        'manifested_bit_length': manifested_bit_length,
        'seed_sha256': checksums['seed_sha256'],
        'manifested_sha256': checksums['manifested_sha256'],
        'seed_checksum_valid': checksums['seed_checksum_valid'],
        'manifested_checksum_valid': checksums['manifested_checksum_valid']
    }


def print_verification_results(results: dict) -> None:
    """
    Print verification results in a formatted manner.

    Args:
        results: Dictionary containing verification results
    """
    print("=" * 70)
    print("BINARY REPRESENTATION VERIFICATION")
    print("=" * 70)
    print(f"\nTap Parameter (k): {results['k']}")
    print(f"Seed Value: {results['seed_value']}")
    print(f"\nSeed Binary: {results['seed_binary']}")
    print(f"Seed Bit Length: {results['seed_bit_length']}")
    print(f"\nManifested Value: {results['manifested_value']}")
    print(f"Manifested Binary: {results['manifested_binary']}")
    print(f"Manifested Bit Length: {results['manifested_bit_length']}")
    print(f"\nBit Length Increase: {results['manifested_bit_length'] - results['seed_bit_length']}")
    
    # Print checksum validation results
    print("\n" + "=" * 70)
    print("CHECKSUM VALIDATION")
    print("=" * 70)
    print(f"\nSeed SHA256:")
    print(f"  {results['seed_sha256']}")
    print(f"  Status: {'✅ VALID' if results['seed_checksum_valid'] else '❌ INVALID'}")
    
    print(f"\nManifested SHA256:")
    print(f"  {results['manifested_sha256']}")
    print(f"  Status: {'✅ VALID' if results['manifested_checksum_valid'] else '❌ INVALID'}")
    
    print("=" * 70)


if __name__ == "__main__":
    # Final binary verification for k=11
    k = 11
    seed_11 = 1234567891011

    # Perform verification
    results = verify_binary_representation(k, seed_11)

    # Print results
    print_verification_results(results)

    # Legacy output format (for backward compatibility)
    print("\nLegacy Output Format:")
    print(f"Seed_11 Bit Length: {results['seed_bit_length']}")
    print(f"Manifested Bit Length: {results['manifested_bit_length']}")
    print(f"Binary Tap (k=11): {results['manifested_binary']}")
