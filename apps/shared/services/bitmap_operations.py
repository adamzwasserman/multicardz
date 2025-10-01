# apps/shared/services/bitmap_operations.py
import logging
import time
from functools import reduce

import pyroaring

logger = logging.getLogger(__name__)

def perform_bitmap_intersection(
    tag_bitmaps: list[int],
    all_cards: frozenset,
    *,
    workspace_id: str,
    user_id: str
) -> frozenset:
    """
    Perform intersection using RoaringBitmaps.

    Pure function using immutable data structures.
    Mathematical specification: R = ∩(T₁, T₂, ..., Tₙ)

    Returns cards that have ALL specified tag bitmaps.

    Complexity: O(n) where n = |smallest_set|
    """
    if not tag_bitmaps:
        return all_cards

    # Convert tag_bitmaps list to set for efficient lookup
    required_tags = set(tag_bitmaps)

    # Filter cards that contain ALL required tags
    result_cards = frozenset(
        card for card in all_cards
        if required_tags.issubset(set(card.tag_bitmaps))
    )

    return result_cards

def perform_bitmap_union(
    tag_bitmaps: list[int],
    all_cards: frozenset,
    *,
    workspace_id: str,
    user_id: str
) -> frozenset:
    """
    Perform union using RoaringBitmaps.

    Pure function using immutable data structures.
    Mathematical specification: R = ∪(T₁, T₂, ..., Tₙ)

    Complexity: O(n*m) where n = |tags|, m = |cards|
    """
    if not tag_bitmaps:
        return frozenset()

    # Convert integers to bitmaps
    bitmaps = [pyroaring.BitMap([b]) for b in tag_bitmaps]

    # Perform union
    result_bitmap = reduce(lambda a, b: a | b, bitmaps)

    # Filter cards by result bitmap
    result_cards = frozenset(
        card for card in all_cards
        if any(b in result_bitmap for b in card.tag_bitmaps)
    )

    return result_cards

def perform_complex_filter(
    intersection_tags: list[int],
    union_tags: list[int],
    all_cards: frozenset,
    *,
    workspace_id: str,
    user_id: str
) -> frozenset:
    """
    Two-phase filtering: intersection first, then union.

    Mathematical specification:
    Phase 1: U' = {c ∈ U : I ⊆ c.tags}
    Phase 2: R = {c ∈ U' : O ∩ c.tags ≠ ∅}

    Pure function with performance guarantees.
    """
    start_time = time.perf_counter()

    # Phase 1: Intersection filtering
    if intersection_tags:
        universe_restricted = perform_bitmap_intersection(
            intersection_tags, all_cards,
            workspace_id=workspace_id, user_id=user_id
        )
    else:
        universe_restricted = all_cards

    # Phase 2: Union selection
    if union_tags:
        final_result = perform_bitmap_union(
            union_tags, universe_restricted,
            workspace_id=workspace_id, user_id=user_id
        )
    else:
        final_result = universe_restricted

    elapsed = time.perf_counter() - start_time
    if elapsed > 0.05:
        logger.warning(f"Filter operation took {elapsed:.3f}s")

    return final_result
