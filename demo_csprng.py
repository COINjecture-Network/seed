#!/usr/bin/env python3
"""
Demonstration of the Cryptographically Secure Pseudorandom Number Generator (CSPRNG)

This script showcases the main features and usage patterns of the CSPRNG module.
"""

from csprng import CSPRNG
import threading


def demo_secure_mode():
    """Demonstrate secure (non-deterministic) mode."""
    print("=" * 70)
    print("DEMO 1: Secure Mode (Cryptographically Secure)")
    print("=" * 70)
    
    rng = CSPRNG()
    print(f"Is deterministic: {rng.is_deterministic()}")
    print()
    
    print("Random Integers:")
    print(f"  Dice roll (1-6): {rng.random_int(1, 6)}")
    print(f"  Random port (49152-65535): {rng.random_int(49152, 65535)}")
    print(f"  Random byte (0-255): {rng.random_int(0, 255)}")
    print()
    
    print("Random Floats:")
    for i in range(5):
        print(f"  Float {i+1}: {rng.random_float():.15f}")
    print()
    
    print("Random Bytes:")
    print(f"  16 bytes (hex): {rng.random_bytes(16).hex()}")
    print(f"  32 bytes (hex): {rng.random_bytes(32).hex()}")
    print()


def demo_deterministic_mode():
    """Demonstrate deterministic mode for reproducibility."""
    print("=" * 70)
    print("DEMO 2: Deterministic Mode (Reproducible, NOT Cryptographically Secure)")
    print("=" * 70)
    
    seed = b"demo_seed_12345"
    
    print(f"Creating two generators with same seed: {seed}")
    rng1 = CSPRNG(seed=seed)
    rng2 = CSPRNG(seed=seed)
    print()
    
    print("Generator 1 - 10 random integers (0-100):")
    values1 = [rng1.random_int(0, 100) for _ in range(10)]
    print(f"  {values1}")
    print()
    
    print("Generator 2 - 10 random integers (0-100):")
    values2 = [rng2.random_int(0, 100) for _ in range(10)]
    print(f"  {values2}")
    print()
    
    if values1 == values2:
        print("✓ Both generators produced IDENTICAL sequences!")
    else:
        print("✗ Generators produced different sequences (unexpected)")
    print()


def demo_static_methods():
    """Demonstrate static convenience methods."""
    print("=" * 70)
    print("DEMO 3: Static Methods (One-off Generation)")
    print("=" * 70)
    
    print("Generate single values without creating a generator instance:")
    print()
    
    print("Random Integers:")
    for i in range(5):
        value = CSPRNG.secure_random_int(1, 100)
        print(f"  Value {i+1}: {value}")
    print()
    
    print("Random Bytes:")
    token = CSPRNG.secure_random_bytes(32)
    print(f"  32-byte token: {token.hex()}")
    print()


def demo_thread_safety():
    """Demonstrate thread-safe operation."""
    print("=" * 70)
    print("DEMO 4: Thread Safety")
    print("=" * 70)
    
    rng = CSPRNG()
    results = []
    lock = threading.Lock()
    errors = []
    
    def worker(worker_id, count):
        """Worker function to generate random numbers."""
        try:
            for _ in range(count):
                value = rng.random_int(1, 100)
                with lock:
                    results.append((worker_id, value))
        except Exception as e:
            errors.append((worker_id, e))
    
    # Create 10 threads, each generating 100 random numbers
    num_threads = 10
    nums_per_thread = 100
    
    print(f"Creating {num_threads} threads, each generating {nums_per_thread} random integers...")
    
    threads = [
        threading.Thread(target=worker, args=(i, nums_per_thread))
        for i in range(num_threads)
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    print()
    print(f"Total values generated: {len(results)}")
    print(f"Expected: {num_threads * nums_per_thread}")
    print(f"Errors encountered: {len(errors)}")
    
    if len(results) == num_threads * nums_per_thread and len(errors) == 0:
        print("✓ Thread-safe operation verified!")
    else:
        print("✗ Thread safety issue detected")
    
    # Verify all values are in valid range
    all_valid = all(1 <= value <= 100 for _, value in results)
    print(f"All values in valid range [1, 100]: {all_valid}")
    print()


def demo_distribution():
    """Demonstrate uniform distribution."""
    print("=" * 70)
    print("DEMO 5: Uniform Distribution")
    print("=" * 70)
    
    rng = CSPRNG()
    
    # Generate many samples for integer distribution
    num_samples = 10000
    print(f"Generating {num_samples} random integers in range [0, 9]...")
    samples = [rng.random_int(0, 9) for _ in range(num_samples)]
    
    # Count occurrences
    from collections import Counter
    counter = Counter(samples)
    
    print()
    print("Distribution (each should be ~1000):")
    for value in range(10):
        count = counter[value]
        bar = "█" * (count // 20)  # Scale for display
        print(f"  {value}: {count:4d} {bar}")
    print()
    
    # Check uniformity
    expected = num_samples / 10
    max_deviation = max(abs(counter[i] - expected) for i in range(10))
    deviation_percent = (max_deviation / expected) * 100
    
    print(f"Maximum deviation from expected: {max_deviation:.1f} ({deviation_percent:.1f}%)")
    
    if deviation_percent < 20:
        print("✓ Distribution appears uniform!")
    else:
        print("✗ Distribution may not be uniform (but this can happen randomly)")
    print()


def main():
    """Run all demonstrations."""
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  Cryptographically Secure Pseudorandom Number Generator (CSPRNG)  ║")
    print("║                        Demonstration Script                        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    demo_secure_mode()
    demo_deterministic_mode()
    demo_static_methods()
    demo_thread_safety()
    demo_distribution()
    
    print("=" * 70)
    print("All demonstrations completed successfully!")
    print("=" * 70)
    print()
    print("For more information, see CSPRNG_README.md")
    print()


if __name__ == "__main__":
    main()
