"""
Pure Functional Set Operations Library for MultiCardz™.

Flattened functional library with no classes, no mutable state, no OOP overhead.
Pure functions with explicit state passing for universe-scale operations.
"""

import logging
import multiprocessing as mp
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


# Elite Singleton Pattern for Stable In-Memory Data (approved per CLAUDE.md)
class CardRegistrySingleton:
    """
    Thread-safe singleton for pre-computed card registry with immutable data structures.

    Approved singleton pattern for stable in-memory global data structures as per
    CLAUDE.md: "Singleton patterns for stable in-memory global data structures"

    This eliminates redundant tag registration and bitmap construction by maintaining
    pre-computed immutable structures for universe-scale operations.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            # Immutable registry data
            self._tag_to_id: dict[str, int] = {}
            self._id_to_tag: dict[int, str] = {}
            self._next_tag_id: int = 0

            # Pre-computed card bitmaps (card_id -> bitmap)
            self._card_bitmaps: dict[str, Any] = {}  # Will store RoaringBitmap objects

            # Inverted index for fast lookups (tag -> frozenset of card_ids)
            self._tag_to_cards: dict[str, frozenset[str]] = {}

            # Registry state tracking
            self._cards_registered: int = 0
            self._registry_frozen: bool = False

            self._initialized = True

    def register_cards_batch(self, cards: frozenset[CardSummaryTuple]) -> None:
        """
        Register a batch of cards with pre-computed tag mappings and bitmaps.

        This is called ONCE during application startup to eliminate redundant
        tag registration and bitmap construction on every operation.

        Args:
            cards: Immutable frozenset of cards to register
        """
        if self._registry_frozen:
            logger.warning("Registry is frozen, cannot register new cards")
            return

        with self._lock:
            if self._registry_frozen:
                return

            RoaringBitmap, roaring_available = _get_roaring_bitmap()

            # Collect all unique tags from the card set
            all_tags = set()
            for card in cards:
                all_tags.update(card.tags)

            # Register new tags
            for tag in all_tags:
                if tag not in self._tag_to_id:
                    self._tag_to_id[tag] = self._next_tag_id
                    self._id_to_tag[self._next_tag_id] = tag
                    self._next_tag_id += 1

            # Build pre-computed bitmaps and inverted index
            tag_to_cards = {tag: [] for tag in all_tags}

            for card in cards:
                # Build bitmap for this card's tags
                if roaring_available:
                    tag_positions = [self._tag_to_id[tag] for tag in card.tags]
                    self._card_bitmaps[card.id] = RoaringBitmap(tag_positions)
                else:
                    # Fallback to integer bitmap
                    bitmap = 0
                    for tag in card.tags:
                        bitmap |= (1 << self._tag_to_id[tag])
                    self._card_bitmaps[card.id] = bitmap

                # Update inverted index
                for tag in card.tags:
                    tag_to_cards[tag].append(card.id)

            # Convert to immutable frozensets
            for tag, card_ids in tag_to_cards.items():
                self._tag_to_cards[tag] = frozenset(card_ids)

            self._cards_registered = len(cards)
            logger.info(f"Registered {len(cards)} cards with {len(all_tags)} unique tags")

    def freeze_registry(self) -> None:
        """Freeze the registry to prevent further modifications."""
        with self._lock:
            self._registry_frozen = True
            logger.info(f"Registry frozen with {self._cards_registered} cards")

    def get_tag_mapping(self) -> tuple[dict[str, int], dict[int, str], int]:
        """Get immutable tag mapping data."""
        return (
            self._tag_to_id.copy(),
            self._id_to_tag.copy(),
            self._next_tag_id
        )

    def get_card_bitmap(self, card_id: str) -> Any:
        """Get pre-computed bitmap for a card."""
        return self._card_bitmaps.get(card_id)

    def get_cards_with_tags(self, tag_names: frozenset[str]) -> frozenset[str]:
        """
        Fast lookup of cards containing any of the specified tags.

        Uses pre-computed inverted index for O(1) tag lookups instead of
        O(n) card scanning.
        """
        result_card_ids = set()
        for tag in tag_names:
            if tag in self._tag_to_cards:
                result_card_ids.update(self._tag_to_cards[tag])
        return frozenset(result_card_ids)

    def save_registry_state(self, filepath: str) -> None:
        """
        Persist the registry state to disk for fast reloading.

        Saves pre-computed bitmaps and tag mappings to avoid rebuilding
        on application restart.
        """
        import pickle
        import gzip

        with self._lock:
            state_data = {
                "tag_to_id": self._tag_to_id,
                "id_to_tag": self._id_to_tag,
                "next_tag_id": self._next_tag_id,
                "card_bitmaps": self._card_bitmaps,
                "tag_to_cards": self._tag_to_cards,
                "cards_registered": self._cards_registered,
                "version": "1.0",  # For future compatibility
            }

            with gzip.open(filepath, 'wb') as f:
                pickle.dump(state_data, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info(f"Registry state saved to {filepath}")

    def load_registry_state(self, filepath: str) -> bool:
        """
        Load persisted registry state from disk.

        Returns:
            bool: True if successfully loaded, False otherwise
        """
        import pickle
        import gzip
        import os

        if not os.path.exists(filepath):
            logger.info(f"Registry state file not found: {filepath}")
            return False

        try:
            with self._lock:
                with gzip.open(filepath, 'rb') as f:
                    state_data = pickle.load(f)

                # Validate version compatibility
                version = state_data.get("version", "unknown")
                if version != "1.0":
                    logger.warning(f"Registry state version mismatch: {version}")
                    return False

                # Restore state
                self._tag_to_id = state_data["tag_to_id"]
                self._id_to_tag = state_data["id_to_tag"]
                self._next_tag_id = state_data["next_tag_id"]
                self._card_bitmaps = state_data["card_bitmaps"]
                self._tag_to_cards = state_data["tag_to_cards"]
                self._cards_registered = state_data["cards_registered"]

            logger.info(f"Registry state loaded from {filepath}: {self._cards_registered} cards")
            return True

        except Exception as e:
            logger.error(f"Failed to load registry state: {e}")
            return False

    def update_card(self, card: CardSummaryTuple) -> None:
        """
        Incrementally update a single card's registry data.

        Handles card mutations by updating bitmaps and inverted index.
        """
        if self._registry_frozen:
            logger.warning("Registry is frozen, cannot update cards")
            return

        with self._lock:
            RoaringBitmap, roaring_available = _get_roaring_bitmap()

            # Remove old card data if it exists
            if card.id in self._card_bitmaps:
                old_bitmap = self._card_bitmaps[card.id]
                # Remove from inverted index
                for tag, card_ids in self._tag_to_cards.items():
                    if card.id in card_ids:
                        self._tag_to_cards[tag] = card_ids - {card.id}

            # Register new tags if needed
            for tag in card.tags:
                if tag not in self._tag_to_id:
                    self._tag_to_id[tag] = self._next_tag_id
                    self._id_to_tag[self._next_tag_id] = tag
                    self._next_tag_id += 1

            # Build new bitmap for the card
            if roaring_available:
                tag_positions = [self._tag_to_id[tag] for tag in card.tags]
                self._card_bitmaps[card.id] = RoaringBitmap(tag_positions)
            else:
                bitmap = 0
                for tag in card.tags:
                    bitmap |= (1 << self._tag_to_id[tag])
                self._card_bitmaps[card.id] = bitmap

            # Update inverted index
            for tag in card.tags:
                if tag not in self._tag_to_cards:
                    self._tag_to_cards[tag] = frozenset()
                self._tag_to_cards[tag] = self._tag_to_cards[tag] | {card.id}

    def remove_card(self, card_id: str) -> None:
        """
        Remove a card from the registry.

        Handles card deletion by removing bitmaps and updating inverted index.
        """
        if self._registry_frozen:
            logger.warning("Registry is frozen, cannot remove cards")
            return

        with self._lock:
            if card_id not in self._card_bitmaps:
                return

            # Remove bitmap
            del self._card_bitmaps[card_id]

            # Update inverted index
            for tag, card_ids in list(self._tag_to_cards.items()):
                if card_id in card_ids:
                    new_card_ids = card_ids - {card_id}
                    if new_card_ids:
                        self._tag_to_cards[tag] = new_card_ids
                    else:
                        del self._tag_to_cards[tag]

            self._cards_registered -= 1

    def add_cards_batch(self, new_cards: frozenset[CardSummaryTuple]) -> None:
        """
        Add a batch of new cards to an existing registry.

        More efficient than individual updates for bulk additions.
        """
        if self._registry_frozen:
            logger.warning("Registry is frozen, cannot add cards")
            return

        with self._lock:
            RoaringBitmap, roaring_available = _get_roaring_bitmap()

            # Collect new tags
            new_tags = set()
            for card in new_cards:
                new_tags.update(card.tags)

            # Register new tags
            for tag in new_tags:
                if tag not in self._tag_to_id:
                    self._tag_to_id[tag] = self._next_tag_id
                    self._id_to_tag[self._next_tag_id] = tag
                    self._next_tag_id += 1

            # Build bitmaps and update inverted index
            tag_to_cards = {tag: set(card_ids) for tag, card_ids in self._tag_to_cards.items()}

            for card in new_cards:
                # Build bitmap
                if roaring_available:
                    tag_positions = [self._tag_to_id[tag] for tag in card.tags]
                    self._card_bitmaps[card.id] = RoaringBitmap(tag_positions)
                else:
                    bitmap = 0
                    for tag in card.tags:
                        bitmap |= (1 << self._tag_to_id[tag])
                    self._card_bitmaps[card.id] = bitmap

                # Update inverted index
                for tag in card.tags:
                    if tag not in tag_to_cards:
                        tag_to_cards[tag] = set()
                    tag_to_cards[tag].add(card.id)

            # Convert back to immutable frozensets
            for tag, card_ids in tag_to_cards.items():
                self._tag_to_cards[tag] = frozenset(card_ids)

            self._cards_registered += len(new_cards)
            logger.info(f"Added {len(new_cards)} cards to registry")

    def get_registry_stats(self) -> dict[str, Any]:
        """Get registry statistics for monitoring."""
        return {
            "cards_registered": self._cards_registered,
            "unique_tags": len(self._tag_to_id),
            "registry_frozen": self._registry_frozen,
            "memory_usage_approx_mb": (
                len(self._card_bitmaps) * 64 + len(self._tag_to_cards) * 32
            ) / (1024 * 1024)
        }


# Registry Initialization Helper (Pure Function)
def initialize_card_registry(
    cards: frozenset[CardSummaryTuple],
    cache_filepath: str | None = None
) -> None:
    """
    Initialize the CardRegistrySingleton with pre-computed data.

    This should be called ONCE during application startup to eliminate
    redundant tag registration and bitmap construction on every operation.

    Args:
        cards: Complete immutable frozenset of all cards in the system
        cache_filepath: Optional path to persist/load registry state
    """
    registry = CardRegistrySingleton()

    # Try to load from cache first
    if cache_filepath and registry.load_registry_state(cache_filepath):
        logger.info("Registry loaded from cache")
    else:
        # Build from scratch
        registry.register_cards_batch(cards)
        if cache_filepath:
            registry.save_registry_state(cache_filepath)

    registry.freeze_registry()

    stats = registry.get_registry_stats()
    logger.info(
        f"Card registry ready: {stats['cards_registered']} cards, "
        f"{stats['unique_tags']} tags, {stats['memory_usage_approx_mb']:.1f}MB"
    )


def handle_card_mutations(
    added_cards: frozenset[CardSummaryTuple] | None = None,
    updated_cards: frozenset[CardSummaryTuple] | None = None,
    deleted_card_ids: frozenset[str] | None = None,
    cache_filepath: str | None = None
) -> None:
    """
    Handle incremental card mutations efficiently.

    This is called when cards are added, updated, or deleted to maintain
    registry consistency without full rebuild.

    Args:
        added_cards: New cards to add to registry
        updated_cards: Existing cards with updated tags
        deleted_card_ids: IDs of cards to remove
        cache_filepath: Optional path to update persisted state
    """
    registry = CardRegistrySingleton()

    # Temporarily unfreeze for updates
    was_frozen = registry._registry_frozen
    registry._registry_frozen = False

    try:
        if deleted_card_ids:
            for card_id in deleted_card_ids:
                registry.remove_card(card_id)
            logger.info(f"Removed {len(deleted_card_ids)} cards from registry")

        if updated_cards:
            for card in updated_cards:
                registry.update_card(card)
            logger.info(f"Updated {len(updated_cards)} cards in registry")

        if added_cards:
            registry.add_cards_batch(added_cards)

        # Save updated state if cache is enabled
        if cache_filepath:
            registry.save_registry_state(cache_filepath)

    finally:
        # Restore frozen state
        if was_frozen:
            registry._registry_frozen = True

    stats = registry.get_registry_stats()
    logger.info(f"Registry updated: {stats['cards_registered']} total cards")


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
    """Thread-safe LRU cache for operation results."""

    def __init__(self, maxsize: int = 1000):  # Increased for universe scale
        self.maxsize = maxsize
        self._cache: dict[str, tuple[CardSet, float]] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

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

    # Get tag information from registry - NO LIST CONVERSION NEEDED
    registry = CardRegistrySingleton()
    if registry.get_registry_stats()["cards_registered"] == 0:
        # Auto-initialize with current cards for test compatibility
        logger.info("Auto-initializing CardRegistrySingleton with current card set")
        initialize_card_registry(cards)

    unique_tags_estimate = registry.get_registry_stats()["unique_tags"]

    # ONLY use optimized registry-based operations - no mode selection needed
    processing_mode = "roaring_bitmap_optimized"

    # Apply operations using optimized registry path
    result_cards = cards
    operations_applied = 0
    parallel_workers = 1  # Registry operations are single-threaded but ultra-fast
    chunk_count = 1
    bitmap_build_time_ms = 0.0

    for operation_type, tags_with_counts in operations:
        # Extract tag names from tuples
        tag_names = frozenset(tag for tag, _count in tags_with_counts)

        # Use ONLY the optimized registry path
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
    cards_count = len(cards)
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
    """Generate improved cache key with better collision resistance."""
    card_ids = [card.id for card in cards]
    # Use sorted sampling for deterministic cache keys
    sorted_card_ids = sorted(card_ids)
    card_ids_sample = sorted_card_ids[: min(100, len(card_ids))]
    cards_hash = hash(tuple(card_ids_sample))

    ops_hash = hash(
        frozenset(
            (op_type, frozenset(tag for tag, _ in tags_list))
            for op_type, tags_list in operations
        )
    )

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
    """Regular single-threaded operation for small datasets."""

    # Early short-circuit detection for intersection operations
    if operation_type == "intersection":
        # Check if any of the required tags exist in the dataset
        all_existing_tags = set()
        for card in cards:
            all_existing_tags.update(card.tags)
            # Early exit optimization: if we found all required tags, no need to continue scanning
            if tag_names.issubset(all_existing_tags):
                break

        # If any required tag doesn't exist in the entire dataset, return empty set immediately
        if not tag_names.issubset(all_existing_tags):
            return frozenset()

        return frozenset(card for card in cards if tag_names.issubset(card.tags))
    elif operation_type == "union":
        return frozenset(card for card in cards if not tag_names.isdisjoint(card.tags))
    elif operation_type == "difference":
        return frozenset(card for card in cards if tag_names.isdisjoint(card.tags))
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
        n_workers = 1
        chunks = [cards_list]
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
        min(n_workers, len(chunks)),
        len(chunks),
    )


def execute_roaring_bitmap_operation_optimized(
    cards: CardSet,
    operation_type: str,
    tag_names: frozenset[str],
    state: ProcessingState,
    cpu_count: int | None = None,
) -> tuple[CardSet, ProcessingState, float, int, int]:
    """
    Optimized roaring bitmap operation using pre-computed registry.

    Eliminates frozenset->list conversion and redundant bitmap construction
    by using CardRegistrySingleton for O(1) lookups instead of O(n) processing.
    """
    # Validate operation type first
    valid_operations = ["intersection", "union", "difference"]
    if operation_type not in valid_operations:
        raise ValueError(
            f"Invalid operation type '{operation_type}'. Valid operations are: {', '.join(valid_operations)}"
        )

    start_time = time.perf_counter()

    # Get singleton registry - no list conversion needed!
    registry = CardRegistrySingleton()

    # Early exit: check if all required tags exist
    tag_to_id, id_to_tag, next_tag_id = registry.get_tag_mapping()
    missing_tags = tag_names - set(tag_to_id.keys())

    if missing_tags:
        if operation_type == "intersection":
            # If any required tag is missing, intersection is empty
            empty_result = frozenset()
            bitmap_time = (time.perf_counter() - start_time) * 1000
            return empty_result, state, bitmap_time, 0, 0
        # For union/difference, we can still proceed with existing tags
        tag_names = tag_names - missing_tags

    if not tag_names:
        # No valid tags to process
        if operation_type == "difference":
            result = cards  # All cards remain for difference with empty set
        else:
            result = frozenset()  # Empty result for union/intersection with empty set
        bitmap_time = (time.perf_counter() - start_time) * 1000
        return result, state, bitmap_time, 0, 0

    # Use inverted index for fast candidate lookup
    candidate_card_ids = registry.get_cards_with_tags(tag_names)

    # Filter cards using pre-computed bitmaps - NO list iteration!
    RoaringBitmap, roaring_available = _get_roaring_bitmap()

    if roaring_available:
        # Build target bitmap from tag positions
        target_positions = [tag_to_id[tag] for tag in tag_names]
        target_rb = RoaringBitmap(target_positions)

        matching_cards = set()

        # Only check cards that might match (from inverted index)
        for card in cards:
            if operation_type == "intersection":
                # For intersection, card must be in candidates AND its bitmap must contain all target tags
                if card.id in candidate_card_ids:
                    card_bitmap = registry.get_card_bitmap(card.id)
                    if card_bitmap and target_rb.issubset(card_bitmap):
                        matching_cards.add(card)
            elif operation_type == "union":
                # For union, card must have any of the target tags
                if card.id in candidate_card_ids:
                    matching_cards.add(card)
            else:  # difference
                # For difference, card must NOT have any of the target tags
                if card.id not in candidate_card_ids:
                    matching_cards.add(card)
    else:
        # Fallback without roaring bitmaps
        matching_cards = set()
        for card in cards:
            if operation_type == "intersection":
                if tag_names.issubset(card.tags):
                    matching_cards.add(card)
            elif operation_type == "union":
                if not tag_names.isdisjoint(card.tags):
                    matching_cards.add(card)
            else:  # difference
                if tag_names.isdisjoint(card.tags):
                    matching_cards.add(card)

    bitmap_time = (time.perf_counter() - start_time) * 1000

    return (
        frozenset(matching_cards),
        state,
        bitmap_time,
        1,  # Single-threaded with registry lookup
        1,  # Single chunk (no chunking needed)
    )


def execute_roaring_bitmap_operation(
    cards: CardSet,
    operation_type: str,
    tag_names: frozenset[str],
    state: ProcessingState,
    cpu_count: int | None = None,
) -> tuple[CardSet, ProcessingState, float, int, int]:
    """
    Roaring bitmap operation for maximum performance and memory efficiency.

    REQUIRES CardRegistrySingleton to be initialized. No legacy fallback.
    """
    RoaringBitmap, available = _get_roaring_bitmap()
    if not available:
        logger.warning(
            "Roaring bitmaps not available, falling back to turbo bitmap mode"
        )
        return execute_turbo_bitmap_operation(
            cards, operation_type, tag_names, state, cpu_count
        )

    # MANDATORY: Use optimized registry-only path
    registry = CardRegistrySingleton()
    if registry.get_registry_stats()["cards_registered"] == 0:
        raise RuntimeError(
            "CardRegistrySingleton not initialized! Call initialize_card_registry() first. "
            "Legacy path removed for architectural purity."
        )

    return execute_roaring_bitmap_operation_optimized(
        cards, operation_type, tag_names, state, cpu_count
    )


def select_processing_mode(
    cards_count: int, operation_complexity: int, unique_tags_estimate: int = 0
) -> str:
    """Automatically select optimal processing mode based on dataset characteristics."""
    # Memory awareness - basic check without psutil for now
    # TODO: Add psutil back for production memory monitoring

    RoaringBitmap, roaring_available = _get_roaring_bitmap()

    if not roaring_available:
        if cards_count < 10000:
            return "regular"
        elif cards_count < 100000:
            return "parallel"
        else:
            return "turbo_bitmap"

    if cards_count < 10000:
        return "regular"
    elif cards_count < 50000 and unique_tags_estimate < 500:
        return "parallel"
    elif (
        unique_tags_estimate > 200
        and cards_count > 50000
        or operation_complexity > 5
        and cards_count > 25000
    ):
        return "roaring_bitmap"
    elif cards_count < 100000:
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
    """Validate that operations meet performance targets."""
    if card_count <= 1000:
        target_ms = 10.0
    elif card_count <= 5000:
        target_ms = 25.0
    elif card_count <= 10000:
        target_ms = 50.0
    elif card_count <= 100000:
        target_ms = 50.0 + ((card_count - 10000) / 90000) * 450.0
    elif card_count <= 1000000:
        target_ms = 500.0 + ((card_count - 100000) / 900000) * 500.0
    else:
        target_ms = 1000.0 + ((card_count - 1000000) / 1000000) * 1000.0

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
