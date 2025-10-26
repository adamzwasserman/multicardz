#!/usr/bin/env python3
"""Definitive cache debugging - exact test replication"""

import os
import random
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/Users/adam/dev/multicardz")
os.chdir("/Users/adam/dev/multicardz")

# Check what model is used in the performance test
import subprocess

from apps.shared.services.set_operations_unified import (
    ThreadSafeCache,
    apply_unified_operations,
    clear_unified_cache,
    generate_cache_key_improved,
)

result = subprocess.run(
    [
        "grep",
        "-n",
        "CardSummary",
        "/Users/adam/dev/multicardz/tests/test_set_operations_performance.py",
    ],
    capture_output=True,
    text=True,
)
print("CardSummary import in test:", result.stdout.strip())

# Import CardSummary from correct location
from apps.shared.models.card import CardSummary

print("Using apps.shared.models.card.CardSummary")


def generate_test_cards(count: int):
    """Exact copy of performance test card generation."""
    tags_pool = [
        "urgent",
        "bug",
        "feature",
        "backend",
        "frontend",
        "api",
        "database",
        "ui",
        "high",
        "medium",
        "low",
        "assigned",
        "review",
        "testing",
        "documentation",
        "performance",
        "security",
        "refactor",
        "enhancement",
        "critical",
    ]

    # Use fixed base time to ensure consistent timestamps
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    cards = []
    for i in range(count):
        # Realistic tag distribution: 1-5 tags per card
        num_tags = random.randint(1, 5)
        card_tags = frozenset(random.sample(tags_pool, num_tags))

        card = CardSummary(
            id=f"CARD{i+1:04d}",
            title=f"Test Card {i+1}",
            tags=card_tags,
            created_at=base_time - timedelta(days=random.randint(0, 365)),
            modified_at=base_time - timedelta(hours=random.randint(0, 24)),
        )
        cards.append(card)

    return frozenset(cards)


# Set random seed for reproducible results
random.seed(42)

print("=== DEFINITIVE CACHE EFFECTIVENESS DEBUG ===")

# Clear cache like the test does
clear_unified_cache()

# Generate cards ONCE (exactly like the test)
cards = generate_test_cards(1000)

operations = [
    ("intersection", [("urgent", 45), ("bug", 67)]),
    ("union", [("high", 89), ("medium", 123)]),
]

# Create explicit cache instance (exactly like the test)
cache = ThreadSafeCache()

print("Initial cache state:")
print(f"  Cache size: {len(cache._cache)}")
print(f"  Cache hits: {cache._hits}")
print(f"  Cache misses: {cache._misses}")

# Set random seed right before cache key generation to ensure consistency
random.seed(42)
cache_key1 = generate_cache_key_improved(cards, operations)
print(f"Cache key: {cache_key1}")

print("\n=== FIRST EXECUTION (should be cache miss) ===")
# Reset seed again for consistent cache key in apply_unified_operations
random.seed(42)
start_time = time.perf_counter()
result1 = apply_unified_operations(cards, operations, use_cache=True, cache=cache)
first_time = (time.perf_counter() - start_time) * 1000

print("Result 1:")
print(f"  cache_hit: {result1.cache_hit}")
print(f"  cards: {len(result1.cards)}")
print(f"  operations_applied: {result1.operations_applied}")
print(f"  short_circuited: {result1.short_circuited}")
print(f"  processing_mode: {result1.processing_mode}")
print(f"  execution_time: {first_time:.3f}ms")

print("Cache state after 1st execution:")
print(f"  Cache size: {len(cache._cache)}")
print(f"  Cache hits: {cache._hits}")
print(f"  Cache misses: {cache._misses}")
print(f"  Cache keys: {list(cache._cache.keys())}")

# Reset seed again for consistent cache key generation
random.seed(42)
cache_key2 = generate_cache_key_improved(cards, operations)
print(f"Cache key (2nd generation): {cache_key2}")
print(f"Keys match: {cache_key1 == cache_key2}")

print("\n=== SECOND EXECUTION (should be cache hit) ===")
# Reset seed again for consistent cache key in apply_unified_operations
random.seed(42)
start_time = time.perf_counter()
result2 = apply_unified_operations(cards, operations, use_cache=True, cache=cache)
second_time = (time.perf_counter() - start_time) * 1000

print("Result 2:")
print(f"  cache_hit: {result2.cache_hit}")
print(f"  cards: {len(result2.cards)}")
print(f"  operations_applied: {result2.operations_applied}")
print(f"  short_circuited: {result2.short_circuited}")
print(f"  processing_mode: {result2.processing_mode}")
print(f"  execution_time: {second_time:.3f}ms")

print("Cache state after 2nd execution:")
print(f"  Cache size: {len(cache._cache)}")
print(f"  Cache hits: {cache._hits}")
print(f"  Cache misses: {cache._misses}")

print("\n=== ANALYSIS ===")
print(f"Cache should hit: {cache_key1 in cache._cache}")
print(f"Results identical: {result1.cards == result2.cards}")
print(
    f"Performance improvement: {first_time:.3f}ms → {second_time:.3f}ms ({((first_time - second_time) / first_time * 100):.1f}% faster)"
)

# Check if this matches test expectations
print("\n=== TEST EXPECTATIONS ===")
print("Expected: result1.cache_hit = False, result2.cache_hit = True")
print(
    f"Actual:   result1.cache_hit = {result1.cache_hit}, result2.cache_hit = {result2.cache_hit}"
)
print(f"TEST WOULD PASS: {not result1.cache_hit and result2.cache_hit}")
