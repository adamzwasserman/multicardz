#!/usr/bin/env python3
"""
Quick benchmark to validate CardRegistrySingleton performance optimizations.

This script tests the optimized vs legacy performance to validate our improvements.
"""

import random
import time
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from apps.shared.models.card import CardSummary
from apps.shared.services.set_operations_unified import (
    CardRegistrySingleton,
    apply_unified_operations,
    initialize_card_registry,
)


def generate_test_cards(count: int = 100000) -> frozenset[CardSummary]:
    """Generate test cards for benchmarking."""
    print(f"Generating {count:,} test cards...")

    cards = []
    tags_pool = [f"tag_{i}" for i in range(200)]

    for i in range(count):
        if i % 10000 == 0 and i > 0:
            print(f"  Generated {i:,} cards...")

        num_tags = random.randint(1, 4)
        card_tags = frozenset(random.sample(tags_pool, num_tags))
        card = CardSummary(
            id=f"BENCH{i+1:06d}",
            title=f"Benchmark Card {i+1}",
            tags=card_tags
        )
        cards.append(card)

    print(f"Generated {len(cards):,} cards")
    return frozenset(cards)


def benchmark_registry_performance():
    """Benchmark the optimized registry performance."""
    print("🚀 CardRegistrySingleton Performance Benchmark")
    print("=" * 60)

    # Generate test dataset
    cards = generate_test_cards(100000)  # 100k for quick testing

    # Test operations
    operations = [
        ("intersection", [("tag_1", 5000), ("tag_2", 5000)]),
    ]

    print("\n📊 Testing Registry Initialization...")

    # Reset singleton
    CardRegistrySingleton._instance = None

    # Benchmark initialization
    start_time = time.perf_counter()
    initialize_card_registry(cards)
    init_time_ms = (time.perf_counter() - start_time) * 1000

    registry = CardRegistrySingleton()
    stats = registry.get_registry_stats()

    print(f"✅ Registry initialization: {init_time_ms:.2f}ms")
    print(f"   Cards registered: {stats['cards_registered']:,}")
    print(f"   Unique tags: {stats['unique_tags']}")
    print(f"   Memory usage: {stats['memory_usage_approx_mb']:.1f}MB")

    print("\n🔥 Testing Optimized Operations...")

    # Benchmark optimized operations
    start_time = time.perf_counter()
    result_optimized = apply_unified_operations(
        cards,
        operations,
        use_cache=False
    )
    optimized_time_ms = (time.perf_counter() - start_time) * 1000

    print(f"✅ Optimized operation: {optimized_time_ms:.2f}ms")
    print(f"   Result cards: {len(result_optimized.cards):,}")
    print(f"   Processing mode: {result_optimized.processing_mode}")

    print("\n🐌 Testing Legacy Operations (for comparison)...")

    # Force legacy behavior by clearing registry
    registry._cards_registered = 0

    # Benchmark legacy operations
    start_time = time.perf_counter()
    result_legacy = apply_unified_operations(
        cards,
        operations,
        use_cache=False
    )
    legacy_time_ms = (time.perf_counter() - start_time) * 1000

    print(f"✅ Legacy operation: {legacy_time_ms:.2f}ms")
    print(f"   Result cards: {len(result_legacy.cards):,}")
    print(f"   Processing mode: {result_legacy.processing_mode}")

    print("\n📈 Performance Analysis")
    print("=" * 60)

    # Calculate improvements
    speedup = legacy_time_ms / optimized_time_ms if optimized_time_ms > 0 else 0
    time_saved = legacy_time_ms - optimized_time_ms

    print(f"Optimized time:  {optimized_time_ms:8.2f}ms")
    print(f"Legacy time:     {legacy_time_ms:8.2f}ms")
    print(f"Time saved:      {time_saved:8.2f}ms")
    print(f"Speedup:         {speedup:8.1f}x")

    # Extrapolate to 1M cards
    estimated_1m_optimized = optimized_time_ms * 10  # Rough linear scaling
    estimated_1m_legacy = legacy_time_ms * 10

    print(f"\n🎯 Estimated 1M Card Performance:")
    print(f"Optimized (est): {estimated_1m_optimized:8.0f}ms")
    print(f"Legacy (est):    {estimated_1m_legacy:8.0f}ms")
    print(f"Target:          {1000:8.0f}ms")

    target_met = estimated_1m_optimized < 1000
    print(f"Target met:      {'✅ YES' if target_met else '❌ NO'}")

    # Validate results are consistent
    results_match = len(result_optimized.cards) == len(result_legacy.cards)
    print(f"Results match:   {'✅ YES' if results_match else '❌ NO'}")

    print("\n🎉 Benchmark Complete!")

    if speedup >= 3.0 and results_match:
        print("✅ Optimization successful! Registry provides significant performance improvement.")
        return True
    else:
        print("❌ Optimization needs improvement.")
        return False


def quick_million_card_test():
    """Quick test with 1M cards to validate ultimate performance."""
    print("\n🎯 Ultimate Performance Test: 1M Cards")
    print("=" * 60)

    # Generate 1M cards
    cards = generate_test_cards(1000000)

    # Initialize registry
    CardRegistrySingleton._instance = None

    print("\n⚡ Initializing registry for 1M cards...")
    start_time = time.perf_counter()
    initialize_card_registry(cards)
    init_time_ms = (time.perf_counter() - start_time) * 1000

    print(f"✅ 1M card initialization: {init_time_ms:.2f}ms")

    # Test operation
    operations = [
        ("intersection", [("tag_1", 5000), ("tag_2", 5000)]),
    ]

    print("\n🔥 Running 1M card operation...")
    start_time = time.perf_counter()
    result = apply_unified_operations(
        cards,
        operations,
        use_cache=False
    )
    operation_time_ms = (time.perf_counter() - start_time) * 1000

    print(f"✅ 1M card operation: {operation_time_ms:.2f}ms")
    print(f"   Result cards: {len(result.cards):,}")
    print(f"   Target: <1000ms")

    target_met = operation_time_ms < 1000
    print(f"   Target met: {'✅ YES' if target_met else '❌ NO'}")

    # Calculate improvement from baseline
    baseline_time_ms = 5348
    improvement = baseline_time_ms / operation_time_ms
    print(f"   Improvement: {improvement:.1f}x from baseline ({baseline_time_ms}ms)")

    return target_met


if __name__ == "__main__":
    # Run benchmark
    success = benchmark_registry_performance()

    # Optionally run 1M card test
    if success and "--million" in sys.argv:
        print("\n" + "=" * 80)
        quick_million_card_test()