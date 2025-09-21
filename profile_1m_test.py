#!/usr/bin/env python3
import time
import random
from apps.shared.models.card_models import CardSummary
from apps.shared.services.set_operations_unified import apply_unified_operations

# Generate 100k cards for quick profiling
cards = []
tags_pool = [f"tag_{i}" for i in range(200)]

for i in range(100000):
    num_tags = random.randint(1, 4)
    card_tags = frozenset(random.sample(tags_pool, num_tags))
    card = CardSummary(
        id=f"PROF{i+1:06d}", 
        title=f"Profile Card {i+1}", 
        tags=card_tags
    )
    cards.append(card)

cards_set = frozenset(cards)
print(f"Generated {len(cards_set):,} cards")

# Test intersection operation
operations = [
    ("intersection", [("tag_1", 5000), ("tag_2", 5000)]),
]

print("\nTiming breakdown:")
start = time.perf_counter()

# Call with profiling
result = apply_unified_operations(
    cards_set,
    operations,
    use_cache=False
)

total_time = (time.perf_counter() - start) * 1000
print(f"Total time: {total_time:.2f}ms")
print(f"Result cards: {len(result.cards)}")
print(f"Processing mode: {result.processing_mode}")
print(f"Bitmap build time: {result.bitmap_build_time_ms:.2f}ms")
print(f"Cache hit: {result.cache_hit}")
