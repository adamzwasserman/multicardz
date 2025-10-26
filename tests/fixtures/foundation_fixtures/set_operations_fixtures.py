from typing import Any

import pytest

from packages.shared.src.backend.models.card_models import CardSummary


@pytest.fixture
def performance_test_datasets() -> dict[str, frozenset[CardSummary]]:
    """Create datasets of various sizes for performance testing."""
    datasets = {}

    for size in [1000, 5000, 10000, 50000, 100000]:
        cards = []
        for i in range(size):
            tags = frozenset({
                f"team-{i % 5}",
                f"priority-{i % 3}",
                f"sprint-{i // 100}",
                f"category-{i % 10}"
            })

            cards.append(CardSummary(
                id=f"PERF{i:06d}",
                title=f"Performance test card {i}",
                tags=tags
            ))

        datasets[f"cards_{size}"] = frozenset(cards)

    return datasets


@pytest.fixture
def complex_set_operation_scenarios() -> list[dict[str, Any]]:
    """Create scenarios for complex set operations testing."""
    return [
        {
            "name": "intersection_then_union",
            "operation": "(A ∩ B) ∪ C",
            "set_a": frozenset({"team-frontend", "priority-high"}),
            "set_b": frozenset({"sprint-23", "priority-high"}),
            "set_c": frozenset({"urgent", "bugfix"}),
            "expected_properties": ["commutative_intersection", "associative_union"]
        },
        {
            "name": "difference_then_intersection",
            "operation": "(A - B) ∩ C",
            "set_a": frozenset({"team-backend", "priority-medium", "sprint-23"}),
            "set_b": frozenset({"priority-medium"}),
            "set_c": frozenset({"team-backend", "code-review"}),
            "expected_properties": ["preserves_difference", "maintains_intersection"]
        },
        {
            "name": "symmetric_difference",
            "operation": "A △ B",
            "set_a": frozenset({"feature", "frontend", "sprint-23"}),
            "set_b": frozenset({"feature", "backend", "sprint-23"}),
            "expected_properties": ["symmetric", "exclusive_elements"]
        }
    ]


@pytest.fixture
def cache_performance_context() -> dict[str, Any]:
    """Create context for cache performance testing."""
    return {
        "cache_size": 1000,
        "repeated_operations": 10,
        "expected_cache_hit_rate": 0.7,
        "performance_improvement_target": 0.7  # 70% improvement
    }


@pytest.fixture
def mathematical_validation_cases() -> list[dict[str, Any]]:
    """Create test cases for mathematical property validation."""
    return [
        {
            "property": "commutative_intersection",
            "test": "A ∩ B == B ∩ A",
            "sets": [
                frozenset({"a", "b", "c"}),
                frozenset({"b", "c", "d"})
            ]
        },
        {
            "property": "associative_union",
            "test": "(A ∪ B) ∪ C == A ∪ (B ∪ C)",
            "sets": [
                frozenset({"a", "b"}),
                frozenset({"c", "d"}),
                frozenset({"e", "f"})
            ]
        },
        {
            "property": "distributive_law",
            "test": "A ∩ (B ∪ C) == (A ∩ B) ∪ (A ∩ C)",
            "sets": [
                frozenset({"a", "b", "c", "d"}),
                frozenset({"b", "c", "e"}),
                frozenset({"c", "d", "f"})
            ]
        }
    ]
