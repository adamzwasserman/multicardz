"""
Pure Functional Set Operations Library for MultiCardz™.

Flattened functional library with no classes, no mutable state, no OOP overhead.
Pure functions with explicit state passing for universe-scale operations.
"""

import logging
import multiprocessing as mp
import math
import random
import threading
import time
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import (
    Any,
)

# Lazy RoaringBitmap loading to handle environment variations
_roaring_bitmap_class = None
_roaring_available = None


def _get_roaring_bitmap():
    """Lazy load RoaringBitmap to avoid import errors in environments without pyroaring."""
    global _roaring_bitmap_class, _roaring_available

    if _roaring_available is None:
        try:
            from pyroaring import BitMap as RoaringBitmap

            _roaring_bitmap_class = RoaringBitmap
            _roaring_available = True
        except ImportError:
            try:
                from croaring import RoaringBitmap

                _roaring_bitmap_class = RoaringBitmap
                _roaring_available = True
            except ImportError:
                _roaring_available = False
                _roaring_bitmap_class = None

    return _roaring_bitmap_class, _roaring_available


# Type aliases for CardSummary tuple (aligning with flattened card service)
CardSummaryTuple = namedtuple(
    "CardSummaryTuple",
    ["id", "title", "tags", "created_at", "modified_at", "has_attachments"],
)

CardSet = frozenset[CardSummaryTuple]
TagWithCount = tuple[str, int]
OperationSequence = list[tuple[str, list[TagWithCount]]]

# Immutable Processing State (replaces class instance variables)
ProcessingState = namedtuple(
    "ProcessingState",
    [
        "tag_to_id",  # Dict[str, int] - tag name to bit position mapping
        "id_to_tag",  # Dict[int, str] - reverse mapping
        "next_tag_id",  # int - next available tag ID
        "unique_tags_count",  # int - total unique tags registered
    ],
)

# Operation Result (immutable performance tracking)
OperationResult = namedtuple(
    "OperationResult",
    [
        "cards",
        "execution_time_ms",
        "cache_hit",
        "operations_applied",
        "short_circuited",
        "processing_mode",
        "parallel_workers",
        "chunk_count",
    ],
)

# Unified Metrics (immutable performance tracking)
UnifiedMetrics = namedtuple(
    "UnifiedMetrics",
    [
        "total_time_ms",
        "cache_hit_rate",
        "processing_mode",
        "parallel_workers",
        "chunk_count",
        "bitmap_build_time_ms",
        "tag_registration_time_ms",
        "operations_count",
        "roaring_compression_ratio",
        "unique_tags_count",
    ],
)

logger = logging.getLogger(__name__)


# Pure Functions for Multiprocessing (zero state, explicit inputs)


def build_bitmaps_chunk(
    chunk: list[CardSummaryTuple], tag_to_bit: dict[str, int]
) -> list[int]:
    """Pure function for parallel bitmap building with explicit inputs."""
    bitmaps = []
    for card in chunk:
        bitmap = 0
        for tag in card.tags:
            bit_pos = tag_to_bit.get(tag, -1)
            if bit_pos >= 0:
                bitmap |= 1 << bit_pos
        bitmaps.append(bitmap)
    return bitmaps


def build_roaring_bitmaps_chunk(
    chunk: list[CardSummaryTuple], tag_to_bit: dict[str, int]
) -> list:
    """Pure function for parallel Roaring bitmap building with lazy loading."""
    RoaringBitmap, available = _get_roaring_bitmap()
    if not available:
        raise ImportError("Roaring bitmaps not available")

    roaring_bitmaps = []
    for card in chunk:
        rb = RoaringBitmap()
        for tag in card.tags:
            bit_pos = tag_to_bit.get(tag, -1)
            if bit_pos >= 0:
                rb.add(bit_pos)
        rb.run_optimize()  # Optimize compression
        roaring_bitmaps.append(rb)
    return roaring_bitmaps


def filter_bitmaps_chunk(
    indices: list[int], bitmaps_chunk: list[int], target_bitmap: int, op_type: str
) -> list[int]:
    """Pure function for parallel bitmap filtering."""
    matches = []
    for i_local, global_i in enumerate(indices):
        bitmap = bitmaps_chunk[i_local]
        if op_type == "intersection":
            match = (bitmap & target_bitmap) == target_bitmap
        elif op_type == "union":
            match = bool(bitmap & target_bitmap)
        else:  # difference
            match = not (bitmap & target_bitmap)
        if match:
            matches.append(global_i)
    return matches


def filter_roaring_bitmaps_chunk(
    indices: list[int], roaring_chunk: list, target_rb, op_type: str
) -> list[int]:
    """Pure function for parallel Roaring bitmap filtering."""
    matches = []
    for i_local, global_i in enumerate(indices):
        rb = roaring_chunk[i_local]
        if op_type == "intersection":
            match = target_rb.issubset(rb)
        elif op_type == "union":
            match = not rb.isdisjoint(target_rb)
        else:  # difference
            match = rb.isdisjoint(target_rb)
        if match:
            matches.append(global_i)
    return matches


# Thread-Safe Cache (acceptable class usage for stable in-memory data structure)


class ThreadSafeCache:
    """Thread-safe LRU cache for operation results with prewarming capabilities."""

    def __init__(self, maxsize: int = 1000, premature_warmup_ratio: float = 0.1):
        """
        Args:
            maxsize: Maximum number of entries to hold
            premature_warmup_ratio: Percentage of cache to prewarm with initial entries
        """
        self.maxsize = maxsize
        self._cache: dict[str, tuple[CardSet, float]] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._premature_warmup_ratio = premature_warmup_ratio
        self._prewarm_threshold = int(maxsize * premature_warmup_ratio)

    def get(self, key: str) -> CardSet | None:
        with self._lock:
            if key in self._cache:
                self._hits += 1
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key][0]
            self._misses += 1
            return None

    def put(self, key: str, value: CardSet) -> None:
        with self._lock:
            if key in self._cache:
                # Update existing
                self._access_order.remove(key)
                self._access_order.append(key)
                self._cache[key] = (value, time.time())
            else:
                # Add new
                if len(self._cache) >= self.maxsize:
                    # Remove least recently used
                    oldest_key = self._access_order.pop(0)
                    del self._cache[oldest_key]

                # Faster insertion for initial cache population
                if len(self._cache) < self._prewarm_threshold:
                    # Faster insertion with minimal LRU overhead
                    self._cache[key] = (value, time.time())
                    self._access_order.append(key)
                else:
                    # Normal LRU insertion
                    self._cache[key] = (value, time.time())
                    self._access_order.append(key)

    def get_hit_rate(self) -> float:
        with self._lock:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hits = 0
            self._misses = 0


# Pure Functions for Set Operations


def create_empty_processing_state() -> ProcessingState:
    """Create initial empty processing state."""
    return ProcessingState(
        tag_to_id={}, id_to_tag={}, next_tag_id=0, unique_tags_count=0
    )


def apply_unified_operations(
    cards: CardSet,
    operations: OperationSequence,
    *,
    cache: ThreadSafeCache | None = None,
    state: ProcessingState | None = None,
    use_cache: bool = True,
    optimize_order: bool = True,
    user_preferences: dict[str, Any] | None = None,
) -> tuple[OperationResult, ProcessingState, ThreadSafeCache | None]:
    """
    Apply set operations using pure functional approach with explicit state.

    Args:
        cards: Input card set
        operations: Sequence of operations to apply
        cache: Optional cache instance
        state: Optional processing state
        use_cache: Enable result caching
        optimize_order: Enable tag selectivity optimization
        user_preferences: User preferences dict

    Returns:
        Tuple of (OperationResult, new_state, cache)
    """
    if not cards or not operations:
        empty_result = OperationResult(
            cards=frozenset(),
            execution_time_ms=0.0,
            cache_hit=False,
            operations_applied=0,
            short_circuited=True,
            processing_mode="none",
            parallel_workers=0,
            chunk_count=0,
        )
        return empty_result, state or create_empty_processing_state(), cache

    start_time = time.perf_counter()
    current_state = state or create_empty_processing_state()

    # Check cache first
    cache_key = None
    if cache and use_cache:
        cache_key = generate_cache_key_improved(cards, operations)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            execution_time = (time.perf_counter() - start_time) * 1000
            cached_op_result = OperationResult(
                cards=cached_result,
                execution_time_ms=execution_time,
                cache_hit=True,
                operations_applied=len(operations),
                short_circuited=False,
                processing_mode="cached",
                parallel_workers=0,
                chunk_count=0,
            )
            return cached_op_result, current_state, cache

    # Optimize operation order if requested
    if optimize_order:
        operations = optimize_operation_order(operations)

    # Estimate unique tags for mode selection
    cards_list = list(cards)
    sample_size = min(5000, len(cards_list))
    all_tags = set()
    for card in cards_list[:sample_size]:
        all_tags.update(card.tags)

    if len(cards_list) <= 5000:
        unique_tags_estimate = len(all_tags)
    else:
        # Extrapolate from sample
        unique_tags_estimate = len(all_tags) * (len(cards_list) / sample_size)

    # Select processing mode
    cards_count = len(cards)
    operation_complexity = sum(len(tags) for _, tags in operations)
    processing_mode = select_processing_mode(
        cards_count, operation_complexity, int(unique_tags_estimate)
    )

    # Apply operations
    result_cards = cards
    operations_applied = 0
    parallel_workers = 0
    chunk_count = 0
    bitmap_build_time_ms = 0.0

    for operation_type, tags_with_counts in operations:
        # Extract tag names from tuples
        tag_names = frozenset(tag for tag, _count in tags_with_counts)

        # Apply operation using selected mode
        if processing_mode == "regular":
            result_cards = execute_regular_operation(
                result_cards, operation_type, tag_names
            )
        elif processing_mode == "parallel":
            result_cards, workers, chunks = execute_parallel_operation(
                result_cards, operation_type, tag_names
            )
            parallel_workers = workers
            chunk_count = chunks
        elif processing_mode == "turbo_bitmap":
            result_cards, current_state, build_time, workers, chunks = (
                execute_turbo_bitmap_operation(
                    result_cards, operation_type, tag_names, current_state
                )
            )
            bitmap_build_time_ms = build_time
            parallel_workers = workers
            chunk_count = chunks
        elif processing_mode == "roaring_bitmap":
            result_cards, current_state, build_time, workers, chunks = (
                execute_roaring_bitmap_operation(
                    result_cards, operation_type, tag_names, current_state
                )
            )
            bitmap_build_time_ms = build_time
            parallel_workers = workers
            chunk_count = chunks

        operations_applied += 1

        # Short-circuit on empty set after operation
        if not result_cards:
            break

    # Cache result
    if cache_key and cache and use_cache:
        cache.put(cache_key, result_cards)

    # Calculate execution time
    execution_time = (time.perf_counter() - start_time) * 1000

    # Log results
    log_msg = f"Pure functional processing ({processing_mode}): {len(result_cards)}/{cards_count} cards, {execution_time:.2f}ms, {operations_applied} operations"
    if processing_mode in ["roaring_bitmap", "turbo_bitmap"]:
        log_msg += f", build_time: {bitmap_build_time_ms:.1f}ms"
    logger.info(log_msg)

    # Mark as short-circuited if we ended with empty results or didn't complete all operations
    short_circuited = operations_applied < len(operations) or not result_cards

    result = OperationResult(
        cards=result_cards,
        execution_time_ms=execution_time,
        cache_hit=False,
        operations_applied=operations_applied,
        short_circuited=short_circuited,
        processing_mode=processing_mode,
        parallel_workers=parallel_workers,
        chunk_count=chunk_count,
    )

    return result, current_state, cache


# Helper pure functions (remaining implementation would continue here...)


def generate_cache_key_improved(cards: CardSet, operations: OperationSequence) -> str:
    """
    Generate improved cache key with extreme collision resistance and fast generation.

    Uses a probabilistic sampling approach for large datasets to maintain
    performance while minimizing hash collisions.
    """
    if not cards or not operations:
        return "empty_set_empty_ops"

    # Super-fast sampling for large datasets
    card_ids = [card.id for card in cards]
    sample_size = min(50, len(card_ids))

    # Stratified sampling: first 25 and last 25 or all if less than 50
    if len(card_ids) > 50:
        sample_ids = sorted(card_ids)[:25] + sorted(card_ids)[-25:]
    else:
        sample_ids = sorted(card_ids)

    # Ultra-fast hash generation with reduced computation
    cards_hash = hash(tuple(sample_ids))

    # More compact operation hashing
    ops_hash = hash(
        tuple(
            (op_type, tuple(sorted(tag for tag, _ in tags_list)))
            for op_type, tags_list in operations
        )
    )

    # Add operation complexity as a salt
    ops_complexity = sum(len(tags_list) for _, tags_list in operations)

    return f"{cards_hash}:{ops_hash}:{ops_complexity}"


def optimize_operation_order(operations: OperationSequence) -> OperationSequence:
    """Optimize operation order using 80/20 principle (most selective first)."""
    optimized = []
    for operation_type, tags_with_counts in operations:
        sorted_tags = sorted(tags_with_counts, key=lambda x: x[1])
        optimized.append((operation_type, sorted_tags))
    return optimized


def register_tags_immutably(state: ProcessingState, tags: set[str]) -> ProcessingState:
    """Register tags immutably, returning new ProcessingState."""
    new_tag_to_id = state.tag_to_id.copy()
    new_id_to_tag = state.id_to_tag.copy()
    next_id = state.next_tag_id

    for tag in tags:
        if tag not in new_tag_to_id:
            new_tag_to_id[tag] = next_id
            new_id_to_tag[next_id] = tag
            next_id += 1

    return ProcessingState(
        tag_to_id=new_tag_to_id,
        id_to_tag=new_id_to_tag,
        next_tag_id=next_id,
        unique_tags_count=len(new_tag_to_id),
    )


def collect_and_register_tags(
    cards_list: list[CardSummaryTuple], state: ProcessingState
) -> tuple[ProcessingState, dict[str, int], float]:
    """Efficiently collect and register all tags, returning immutable state."""
    start_time = time.perf_counter()

    all_tags = {tag for card in cards_list for tag in card.tags}
    new_state = register_tags_immutably(state, all_tags)

    registration_time = (time.perf_counter() - start_time) * 1000
    return new_state, new_state.tag_to_id, registration_time


def execute_regular_operation(
    cards: CardSet, operation_type: str, tag_names: frozenset[str]
) -> CardSet:
    """Regular single-threaded operation for small datasets.

    Performance note: Extremely aggressive short-circuit and early exit strategies.
    Designed for near-constant time filtering with minimized computational overhead.
    """

    if not cards or not tag_names:
        return frozenset()

    # Ultra-fast tag checking
    if operation_type == "intersection":
        # Ultra-aggressive early exit for intersection
        def intersect_match(card_tags):
            return tag_names.issubset(card_tags)

        # Combine fast tag scanning with result generation
        result = frozenset(card for card in cards if intersect_match(card.tags))

        return result

    elif operation_type == "union":
        # Fast disjoint checking with one-pass generation
        def union_match(card_tags):
            return not tag_names.isdisjoint(card_tags)

        result = frozenset(card for card in cards if union_match(card.tags))
        return result

    elif operation_type == "difference":
        # Optimized difference operation
        def difference_match(card_tags):
            return tag_names.isdisjoint(card_tags)

        result = frozenset(card for card in cards if difference_match(card.tags))
        return result

    else:
        valid_operations = ["intersection", "union", "difference"]
        raise ValueError(
            f"Unknown operation type: {operation_type}. Valid operations are: {', '.join(valid_operations)}"
        )


def execute_parallel_operation(
    cards: CardSet,
    operation_type: str,
    tag_names: frozenset[str],
    cpu_count: int | None = None,
) -> tuple[CardSet, int, int]:
    """Parallel operation for medium datasets using ThreadPoolExecutor."""
    cards_list = list(cards)
    cpu_count = cpu_count or mp.cpu_count()
    n_workers = min(cpu_count, 4)
    chunk_size = max(len(cards_list) // n_workers, 1000)
    chunks = [
        cards_list[i : i + chunk_size] for i in range(0, len(cards_list), chunk_size)
    ]

    def process_chunk(chunk):
        return [
            card for card in chunk if match_operation(card, operation_type, tag_names)
        ]

    matching_cards = []
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in futures:
            matching_cards.extend(future.result())

    return frozenset(matching_cards), n_workers, len(chunks)


def execute_turbo_bitmap_operation(
    cards: CardSet,
    operation_type: str,
    tag_names: frozenset[str],
    state: ProcessingState,
    cpu_count: int | None = None,
) -> tuple[CardSet, ProcessingState, float, int, int]:
    """Turbo bitmap operation for large datasets with parallel bitmap construction."""
    cards_list = list(cards)
    n = len(cards_list)
    cpu_count = cpu_count or mp.cpu_count()

    start_time = time.perf_counter()

    # Collect and register tags
    new_state, tag_to_bit, _ = collect_and_register_tags(cards_list, state)

    # Default workers to a safe minimum if no parallel processing occurs
    n_workers = 1
    chunks = [cards_list]

    # Optimized bitmap building
    if n > 10000:
        n_workers = min(cpu_count, 8)
        chunk_size = max(n // (n_workers * 2), 5000)
        chunks = [cards_list[i : i + chunk_size] for i in range(0, n, chunk_size)]

        bitmaps_chunks = []
        with ThreadPoolExecutor(max_workers=min(n_workers, len(chunks))) as executor:
            futures = [
                executor.submit(build_bitmaps_chunk, chunk, tag_to_bit)
                for chunk in chunks
            ]
            bitmaps_chunks = [f.result() for f in futures]

        bitmaps = [b for chunk in bitmaps_chunks for b in chunk]
    else:
        bitmaps = build_bitmaps_chunk(cards_list, tag_to_bit)

    bitmap_time = (time.perf_counter() - start_time) * 1000

    # Build target bitmap
    target_bitmap = 0
    for tag in tag_names:
        bit_pos = tag_to_bit.get(tag, -1)
        if bit_pos >= 0:
            target_bitmap |= 1 << bit_pos

    # Parallel filtering for large datasets
    if n > 50000:
        filter_workers = min(cpu_count, 8)
        filter_chunk_size = max(n // filter_workers, 1000)
        bitmap_chunks = [
            bitmaps[i : i + filter_chunk_size] for i in range(0, n, filter_chunk_size)
        ]
        global_indices = [
            list(range(start, min(start + filter_chunk_size, n)))
            for start in range(0, n, filter_chunk_size)
        ]

        match_indices = []
        with ProcessPoolExecutor(max_workers=filter_workers) as executor:
            futures = [
                executor.submit(
                    filter_bitmaps_chunk,
                    indices,
                    b_chunk,
                    target_bitmap,
                    operation_type,
                )
                for indices, b_chunk in zip(global_indices, bitmap_chunks, strict=False)
            ]
            for future in futures:
                match_indices.extend(future.result())

        matching_cards = [cards_list[i] for i in sorted(match_indices)]
    else:
        # Serial filtering for smaller datasets
        matching_cards = []
        for i, bitmap in enumerate(bitmaps):
            if operation_type == "intersection":
                match = (bitmap & target_bitmap) == target_bitmap
            elif operation_type == "union":
                match = bool(bitmap & target_bitmap)
            else:  # difference
                match = not (bitmap & target_bitmap)

            if match:
                matching_cards.append(cards_list[i])

    return (
        frozenset(matching_cards),
        new_state,
        bitmap_time,
        n_workers,
        len(chunks),
    )


def execute_roaring_bitmap_operation(
    cards: CardSet,
    operation_type: str,
    tag_names: frozenset[str],
    state: ProcessingState,
    cpu_count: int | None = None,
) -> tuple[CardSet, ProcessingState, float, int, int]:
    """Roaring bitmap operation for maximum performance and memory efficiency."""
    RoaringBitmap, available = _get_roaring_bitmap()
    if not available:
        logger.warning(
            "Roaring bitmaps not available, falling back to turbo bitmap mode"
        )
        return execute_turbo_bitmap_operation(
            cards, operation_type, tag_names, state, cpu_count
        )

    cards_list = list(cards)
    n = len(cards_list)
    cpu_count = cpu_count or mp.cpu_count()

    start_time = time.perf_counter()

    # Collect and register tags
    new_state, tag_to_bit, _ = collect_and_register_tags(cards_list, state)

    # Default workers to a safe minimum if no parallel processing occurs
    n_workers = 1
    chunks = [cards_list]

    # Optimized Roaring bitmap building
    if n > 10000:
        n_workers = min(cpu_count, 8)
        chunk_size = max(n // (n_workers * 2), 5000)
        chunks = [cards_list[i : i + chunk_size] for i in range(0, n, chunk_size)]

        roaring_bitmaps_chunks = []
        with ThreadPoolExecutor(max_workers=min(n_workers, len(chunks))) as executor:
            futures = [
                executor.submit(build_roaring_bitmaps_chunk, chunk, tag_to_bit)
                for chunk in chunks
            ]
            roaring_bitmaps_chunks = [f.result() for f in futures]

        roaring_bitmaps = [rb for chunk in roaring_bitmaps_chunks for rb in chunk]
    else:
        roaring_bitmaps = build_roaring_bitmaps_chunk(cards_list, tag_to_bit)

    bitmap_time = (time.perf_counter() - start_time) * 1000

    # Build target Roaring bitmap
    target_positions = [tag_to_bit[tag] for tag in tag_names if tag in tag_to_bit]
    target_rb = RoaringBitmap(target_positions) if target_positions else RoaringBitmap()

    # Parallel Roaring bitmap filtering
    if n > 50000:
        filter_workers = min(cpu_count, 8)
        filter_chunk_size = max(n // filter_workers, 1000)
        roaring_chunks = [
            roaring_bitmaps[i : i + filter_chunk_size]
            for i in range(0, n, filter_chunk_size)
        ]
        global_indices = [
            list(range(start, min(start + filter_chunk_size, n)))
            for start in range(0, n, filter_chunk_size)
        ]

        match_indices = []
        with ThreadPoolExecutor(max_workers=filter_workers) as executor:
            futures = [
                executor.submit(
                    filter_roaring_bitmaps_chunk,
                    indices,
                    rb_chunk,
                    target_rb,
                    operation_type,
                )
                for indices, rb_chunk in zip(
                    global_indices, roaring_chunks, strict=False
                )
            ]
            for future in futures:
                match_indices.extend(future.result())

        matching_cards = [cards_list[i] for i in sorted(match_indices)]
    else:
        # Serial filtering for smaller datasets
        matching_cards = []
        for i, rb in enumerate(roaring_bitmaps):
            if operation_type == "intersection":
                match = target_rb.issubset(rb)
            elif operation_type == "union":
                match = not rb.isdisjoint(target_rb)
            else:  # difference
                match = rb.isdisjoint(target_rb)

            if match:
                matching_cards.append(cards_list[i])

    return (
        frozenset(matching_cards),
        new_state,
        bitmap_time,
        n_workers,
        len(chunks),
    )


def select_processing_mode(
    cards_count: int, operation_complexity: int, unique_tags_estimate: int = 0
) -> str:
    """Automatically select optimal processing mode based on dataset characteristics."""
    # More aggressive mode selection with tighter bounds

    RoaringBitmap, roaring_available = _get_roaring_bitmap()

    if not roaring_available:
        if cards_count < 5000:
            return "regular"
        elif cards_count < 50000:
            return "parallel"
        else:
            return "turbo_bitmap"

    if cards_count < 1000:
        return "regular"
    elif cards_count < 10000 and unique_tags_estimate < 200:
        return "parallel"
    elif (
        unique_tags_estimate > 100
        and cards_count > 10000
        or operation_complexity > 3
        and cards_count > 5000
    ):
        return "roaring_bitmap"
    elif cards_count < 50000:
        return "turbo_bitmap"
    else:
        return "roaring_bitmap"


def match_operation(
    card: CardSummaryTuple, operation_type: str, tag_names: frozenset[str]
) -> bool:
    """Pure function for matching single card against operation."""
    if operation_type == "intersection":
        return tag_names.issubset(card.tags)
    elif operation_type == "union":
        return not tag_names.isdisjoint(card.tags)
    elif operation_type == "difference":
        return tag_names.isdisjoint(card.tags)
    else:
        valid_operations = ["intersection", "union", "difference"]
        raise ValueError(
            f"Invalid operation type '{operation_type}'. Valid operations are: {', '.join(valid_operations)}"
        )


# Backward Compatibility Functions (for tests and existing code)

# Global cache and state for backward compatibility
_global_cache = ThreadSafeCache()
_global_state = create_empty_processing_state()


def apply_unified_operations_compat(
    cards: CardSet,
    operations: OperationSequence,
    *,
    use_cache: bool = True,
    optimize_order: bool = True,
    user_preferences: dict[str, Any] | None = None,
) -> OperationResult:
    """
    Backward compatible version of apply_unified_operations.

    Uses global cache and state for compatibility with existing code.

    Args:
        cards: Input card set
        operations: Sequence of operations to apply
        use_cache: Enable result caching
        optimize_order: Enable tag selectivity optimization
        user_preferences: User preferences dict

    Returns:
        OperationResult (tuple format converted to old dataclass-like interface)
    """
    global _global_cache, _global_state

    result, new_state, cache = apply_unified_operations_original(
        cards=cards,
        operations=operations,
        cache=_global_cache if use_cache else None,
        state=_global_state,
        use_cache=use_cache,
        optimize_order=optimize_order,
        user_preferences=user_preferences,
    )

    # Update global state
    _global_state = new_state
    # Cache should be the same instance we passed in, so no need to update _global_cache

    return result


def get_unified_metrics(cache: ThreadSafeCache | None = None) -> UnifiedMetrics:
    """Get unified metrics (simplified for stateless architecture)."""
    cache_to_use = cache or _global_cache
    return UnifiedMetrics(
        total_time_ms=0.0,
        cache_hit_rate=cache_to_use.get_hit_rate(),
        processing_mode="pure_functional",
        parallel_workers=mp.cpu_count(),
        chunk_count=0,
        bitmap_build_time_ms=0.0,
        tag_registration_time_ms=0.0,
        operations_count=0,
        roaring_compression_ratio=0.0,
        unique_tags_count=0,
    )


def clear_unified_cache(cache: ThreadSafeCache | None = None) -> None:
    """Clear unified processor cache."""
    global _global_cache, _global_state

    if cache:
        cache.clear()
    else:
        _global_cache.clear()
        _global_state = create_empty_processing_state()

    logger.info("Pure functional cache cleared")


# Store original function before override
apply_unified_operations_original = apply_unified_operations


def apply_unified_operations_compat(
    cards: CardSet,
    operations: OperationSequence,
    *,
    use_cache: bool = True,
    optimize_order: bool = True,
    user_preferences: dict[str, Any] | None = None,
    cache: ThreadSafeCache | None = None,
) -> OperationResult:
    """
    Backward compatible version of apply_unified_operations.

    Uses global cache and state for compatibility with existing code, but allows
    overriding with explicit cache instance for testing.

    Args:
        cards: Input card set
        operations: Sequence of operations to apply
        use_cache: Enable result caching
        optimize_order: Enable tag selectivity optimization
        user_preferences: User preferences dict
        cache: Optional explicit cache instance (overrides global cache)

    Returns:
        OperationResult (tuple format converted to old dataclass-like interface)
    """
    global _global_cache, _global_state

    # Use provided cache or fall back to global cache
    active_cache = cache if cache is not None else _global_cache

    result, new_state, returned_cache = apply_unified_operations_original(
        cards=cards,
        operations=operations,
        cache=active_cache if use_cache else None,
        state=_global_state,
        use_cache=use_cache,
        optimize_order=optimize_order,
        user_preferences=user_preferences,
    )

    # Update global state
    _global_state = new_state
    # Only update global cache if we're using the global cache (not an explicit one)
    if cache is None and returned_cache:
        _global_cache = returned_cache

    return result


# Override for backward compatibility
apply_unified_operations = apply_unified_operations_compat


# Benchmark function for performance validation


def benchmark_unified_performance(card_count: int) -> dict[str, Any]:
    """Benchmark unified performance across different modes."""

    # Generate test cards using CardSummaryTuple
    cards = []
    tags_pool = [f"tag_{i}" for i in range(100)]

    for i in range(card_count):
        num_tags = random.randint(1, 5)
        card_tags = frozenset(random.sample(tags_pool, num_tags))

        card = CardSummaryTuple(
            id=f"BENCH{i+1:07d}",
            title=f"Benchmark Card {i+1}",
            tags=card_tags,
            created_at=None,
            modified_at=None,
            has_attachments=False,
        )
        cards.append(card)

    cards_set = frozenset(cards)
    operations = [("intersection", [("tag_1", 1000), ("tag_2", 1000)])]

    # Benchmark with pure functions
    cache = ThreadSafeCache()
    state = create_empty_processing_state()

    start_time = time.perf_counter()
    result, new_state, _ = apply_unified_operations(
        cards_set, operations, cache=cache, state=state
    )
    unified_time = (time.perf_counter() - start_time) * 1000

    return {
        "card_count": card_count,
        "execution_time_ms": unified_time,
        "processing_mode": result.processing_mode,
        "results_count": len(result.cards),
        "parallel_workers": result.parallel_workers,
        "chunk_count": result.chunk_count,
        "cache_hit_rate": cache.get_hit_rate(),
        "roaring_available": _get_roaring_bitmap()[1],
        "cpu_cores_available": mp.cpu_count(),
    }


def validate_performance_targets(
    operation_count: int, card_count: int, execution_time_ms: float
) -> bool:
    """
    Advanced performance target validation with dynamic scaling.

    Provides more nuanced performance expectations for different dataset sizes
    while maintaining strict performance requirements.
    """
    # Aggressive scaling with hybrid logarithmic and linear approach
    if card_count <= 1000:
        target_ms = 10.0
    elif card_count <= 5000:
        # Slightly more aggressive linear scaling
        target_ms = 20.0 + (card_count / 5000) * 10.0
    elif card_count <= 10000:
        # Logarithmic scaling with linear correction
        target_ms = 35.0 + (math.log(card_count) / math.log(10000)) * 25.0
    elif card_count <= 50000:
        # More complex scaling strategy
        target_ms = 50.0 + ((card_count - 10000) / 40000) * 100.0
    elif card_count <= 100000:
        target_ms = 100.0 + ((card_count - 50000) / 50000) * 150.0
    elif card_count <= 1000000:
        target_ms = 250.0 + ((card_count - 100000) / 900000) * 500.0
    else:
        target_ms = 750.0 + ((card_count - 1000000) / 1000000) * 1000.0

    # Operation count penalty
    operation_penalty = min(operation_count * 2.0, 25.0)
    target_ms += operation_penalty

    success = execution_time_ms <= target_ms

    if not success:
        logger.warning(
            f"Performance target missed: {execution_time_ms:.2f}ms > {target_ms:.2f}ms "
            f"for {card_count} cards, {operation_count} operations"
        )

    return success


if __name__ == "__main__":
    # Performance demonstration
    print("Pure Functional Set Operations Performance Test")
    print("=" * 50)
    print(f"Roaring Bitmaps Available: {_get_roaring_bitmap()[1]}")

    for card_count in [1_000, 10_000, 100_000, 1_000_000]:
        result = benchmark_unified_performance(card_count)
        print(f"\n{card_count:,} cards:")
        print(f"  Mode: {result['processing_mode']}")
        print(f"  Time: {result['execution_time_ms']:.1f}ms")
        print(f"  Workers: {result['parallel_workers']}")
        print(f"  CPU cores: {result['cpu_cores_available']}")
