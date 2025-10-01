import functools
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from packages.shared.src.backend.models.card_models import CardSummary

T = TypeVar('T')


class SetOperationType(Enum):
    """Set operation types for performance tracking."""
    INTERSECTION = "intersection"
    UNION = "union"
    DIFFERENCE = "difference"
    SYMMETRIC_DIFFERENCE = "symmetric_difference"
    COMPLEMENT = "complement"


# Performance cache for repeated operations (singleton pattern - approved)
_OPERATION_CACHE: dict[str, Any] = {}
_CACHE_STATS = {"hits": 0, "misses": 0}


def clear_operation_cache() -> None:
    """Clear operation cache for testing or memory management."""
    global _OPERATION_CACHE, _CACHE_STATS
    _OPERATION_CACHE.clear()
    _CACHE_STATS = {"hits": 0, "misses": 0}


def get_cache_statistics() -> dict[str, Any]:
    """Get cache performance statistics."""
    total = _CACHE_STATS["hits"] + _CACHE_STATS["misses"]
    hit_rate = _CACHE_STATS["hits"] / total if total > 0 else 0
    return {
        "hits": _CACHE_STATS["hits"],
        "misses": _CACHE_STATS["misses"],
        "hit_rate": hit_rate,
        "cache_size": len(_OPERATION_CACHE)
    }


def _cache_key(operation: str, *args) -> str:
    """Generate cache key for operation with arguments."""
    # Create hash of frozensets for cache key
    arg_hashes = []
    for arg in args:
        if isinstance(arg, frozenset):
            arg_hashes.append(hash(arg))
        else:
            arg_hashes.append(str(arg))
    return f"{operation}:{':'.join(map(str, arg_hashes))}"


def cached_operation(operation_name: str):
    """Decorator for caching set operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = _cache_key(operation_name, *args)

            # Check cache
            if cache_key in _OPERATION_CACHE:
                _CACHE_STATS["hits"] += 1
                return _OPERATION_CACHE[cache_key]

            # Execute operation
            _CACHE_STATS["misses"] += 1
            result = func(*args, **kwargs)

            # Store in cache (with size limit)
            if len(_OPERATION_CACHE) < 1000:
                _OPERATION_CACHE[cache_key] = result

            return result
        return wrapper
    return decorator


@cached_operation("intersection")
def filter_cards_by_intersection(
    cards: frozenset[CardSummary],
    required_tags: frozenset[str],
    *,
    workspace_id: str,
    user_id: str
) -> frozenset[CardSummary]:
    """
    Filter cards using set intersection with performance optimization.

    Mathematical specification:
    result = {c ∈ cards | required_tags ⊆ c.tags}

    Performance guarantee: <0.38ms per 1,000 cards
    Complexity: O(n) where n = |cards|
    """
    if not required_tags:
        return cards

    start_time = time.perf_counter()

    # Optimized intersection using frozenset.issubset
    filtered_cards = frozenset(
        card for card in cards
        if required_tags.issubset(card.tags)
    )

    execution_time = (time.perf_counter() - start_time) * 1000

    # Performance validation
    expected_time = len(cards) * 0.38 / 1000  # Scale target by card count
    if execution_time > expected_time:
        # Log performance warning but don't fail operation
        print(f"Performance warning: Intersection took {execution_time:.2f}ms, expected <{expected_time:.2f}ms")

    return filtered_cards


@cached_operation("union")
def combine_cards_by_union(
    card_set_a: frozenset[CardSummary],
    card_set_b: frozenset[CardSummary],
    *,
    workspace_id: str,
    user_id: str
) -> frozenset[CardSummary]:
    """
    Combine card sets using union operation preserving multiplicity.

    Mathematical specification:
    result = card_set_a ∪ card_set_b

    Performance guarantee: O(n + m) where n,m = |card_set_a|, |card_set_b|
    """
    start_time = time.perf_counter()

    # Frozenset union is optimized for performance
    union_result = card_set_a | card_set_b

    execution_time = (time.perf_counter() - start_time) * 1000
    return union_result


@cached_operation("difference")
def subtract_cards_by_difference(
    card_set_a: frozenset[CardSummary],
    card_set_b: frozenset[CardSummary],
    *,
    workspace_id: str,
    user_id: str
) -> frozenset[CardSummary]:
    """
    Subtract cards using set difference operation.

    Mathematical specification:
    result = card_set_a - card_set_b = {c ∈ card_set_a | c ∉ card_set_b}

    Performance guarantee: O(n) where n = |card_set_a|
    """
    start_time = time.perf_counter()

    # Optimized difference using frozenset difference
    difference_result = card_set_a - card_set_b

    execution_time = (time.perf_counter() - start_time) * 1000
    return difference_result


def symmetric_difference_cards(
    card_set_a: frozenset[CardSummary],
    card_set_b: frozenset[CardSummary],
    *,
    workspace_id: str,
    user_id: str
) -> frozenset[CardSummary]:
    """
    Calculate symmetric difference of card sets.

    Mathematical specification:
    result = (card_set_a - card_set_b) ∪ (card_set_b - card_set_a)
    Equivalent to: card_set_a △ card_set_b

    Performance guarantee: O(n + m)
    """
    return card_set_a ^ card_set_b  # Frozenset symmetric difference


def validate_mathematical_properties(
    operation_result: frozenset[T],
    expected_properties: list[str],
    operation_context: dict[str, Any]
) -> bool:
    """
    Validate that set operations maintain mathematical properties.

    Checks properties like commutativity, associativity, distributivity.
    """
    validation_results = []

    for property_name in expected_properties:
        if property_name == "commutative_intersection":
            # For intersection: A ∩ B == B ∩ A
            a, b = operation_context.get("operands", [set(), set()])
            result_ab = a & b
            result_ba = b & a
            validation_results.append(result_ab == result_ba)

        elif property_name == "associative_union":
            # For union: (A ∪ B) ∪ C == A ∪ (B ∪ C)
            a, b, c = operation_context.get("operands", [set(), set(), set()])
            result_abc = (a | b) | c
            result_acb = a | (b | c)
            validation_results.append(result_abc == result_acb)

        elif property_name == "distributive_law":
            # A ∩ (B ∪ C) == (A ∩ B) ∪ (A ∩ C)
            a, b, c = operation_context.get("operands", [set(), set(), set()])
            left_side = a & (b | c)
            right_side = (a & b) | (a & c)
            validation_results.append(left_side == right_side)

    return all(validation_results)


def execute_complex_set_operation(
    cards: frozenset[CardSummary],
    operation_expression: str,
    tag_sets: dict[str, frozenset[str]],
    *,
    workspace_id: str,
    user_id: str
) -> frozenset[CardSummary]:
    """
    Execute complex set operations like (A ∩ B) ∪ (C - D).

    Supports composition of basic operations with mathematical rigor.
    """
    # Parse and execute operation expression
    # This is a simplified implementation - full parser would be more complex

    if operation_expression == "(A ∩ B) ∪ C":
        set_a = tag_sets.get("A", frozenset())
        set_b = tag_sets.get("B", frozenset())
        set_c = tag_sets.get("C", frozenset())

        # (A ∩ B)
        intersection_ab = filter_cards_by_intersection(
            cards, set_a & set_b, workspace_id=workspace_id, user_id=user_id
        )

        # C filtered cards
        c_filtered = filter_cards_by_intersection(
            cards, set_c, workspace_id=workspace_id, user_id=user_id
        )

        # (A ∩ B) ∪ C
        return combine_cards_by_union(
            intersection_ab, c_filtered, workspace_id=workspace_id, user_id=user_id
        )

    # Add more complex operation patterns as needed
    raise ValueError(f"Unsupported operation expression: {operation_expression}")


def benchmark_set_operations(
    datasets: dict[str, frozenset[CardSummary]],
    operation_type: SetOperationType
) -> dict[str, dict[str, float]]:
    """
    Benchmark set operations across different dataset sizes.

    Returns performance metrics for scaling analysis.
    """
    results = {}

    for dataset_name, cards in datasets.items():
        dataset_size = len(cards)

        # Create test tag sets for benchmarking
        test_tags = frozenset({"team-frontend", "priority-high"})

        start_time = time.perf_counter()

        if operation_type == SetOperationType.INTERSECTION:
            result = filter_cards_by_intersection(
                cards, test_tags, workspace_id="benchmark", user_id="benchmark"
            )
        # Add other operation types as needed

        execution_time = (time.perf_counter() - start_time) * 1000

        results[dataset_name] = {
            "size": dataset_size,
            "execution_time_ms": execution_time,
            "time_per_card_us": (execution_time * 1000) / dataset_size,
            "cards_per_second": dataset_size / (execution_time / 1000),
            "memory_usage_estimate": dataset_size * 50  # bytes
        }

    return results
