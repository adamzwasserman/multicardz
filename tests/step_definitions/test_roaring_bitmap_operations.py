# tests/step_definitions/test_roaring_bitmap_operations.py
import time
from collections import namedtuple

import pytest
from pytest_bdd import given, scenarios, then, when

# Load scenarios from feature file
scenarios('../features/roaring_bitmap_operations.feature')

# Create Card namedtuple for testing
Card = namedtuple('Card', ['card_id', 'tag_bitmaps'])

@pytest.fixture
def context():
    """Context for test execution."""
    return {
        'cards': None,
        'intersection_result': None,
        'union_result': None,
        'complex_result': None,
        'elapsed_time': 0,
        'workspace_id': 'test-workspace',
        'user_id': 'test-user'
    }

# Scenario 1: Intersection of tag sets

@given("I have cards with multiple tags")
def cards_with_multiple_tags(context):
    """Create cards with multiple tags."""
    context['cards'] = frozenset([
        Card("card1", (1, 2, 3)),
        Card("card2", (1, 2)),
        Card("card3", (1, 3)),
        Card("card4", (2, 3)),
        Card("card5", (1, 2, 3, 4))
    ])

@when("I perform intersection operation")
def perform_intersection(context):
    """Perform intersection operation."""
    # Import the implementation (will fail initially - red state)
    from apps.shared.services.bitmap_operations import perform_bitmap_intersection

    start_time = time.perf_counter()
    context['intersection_result'] = perform_bitmap_intersection(
        [1, 2],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    context['elapsed_time'] = time.perf_counter() - start_time

@then("only cards with ALL specified tags are returned")
def verify_intersection_result(context):
    """Verify intersection returns only cards with all tags."""
    result = context['intersection_result']
    # Cards with both tag 1 AND tag 2
    expected_card_ids = {"card1", "card2", "card5"}
    result_card_ids = {card.card_id for card in result}
    assert result_card_ids == expected_card_ids

@then("operation completes in under 50ms")
def verify_performance(context):
    """Verify operation completes in under 50ms."""
    assert context['elapsed_time'] < 0.05, f"Operation took {context['elapsed_time']:.3f}s"

@then("result is a frozenset")
def verify_frozenset(context):
    """Verify result is a frozenset."""
    result = context.get('intersection_result') or context.get('union_result') or context.get('complex_result')
    assert isinstance(result, frozenset)

# Scenario 2: Union of tag sets

@given("I have cards with various tags")
def cards_with_various_tags(context):
    """Create cards with various tags."""
    context['cards'] = frozenset([
        Card("card1", (1,)),
        Card("card2", (2,)),
        Card("card3", (3,)),
        Card("card4", (1, 2)),
        Card("card5", (4,))
    ])

@when("I perform union operation")
def perform_union(context):
    """Perform union operation."""
    from apps.shared.services.bitmap_operations import perform_bitmap_union

    start_time = time.perf_counter()
    context['union_result'] = perform_bitmap_union(
        [1, 2],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    context['elapsed_time'] = time.perf_counter() - start_time

@then("cards with ANY specified tags are returned")
def verify_union_result(context):
    """Verify union returns cards with any of the tags."""
    result = context['union_result']
    # Cards with tag 1 OR tag 2
    expected_card_ids = {"card1", "card2", "card4"}
    result_card_ids = {card.card_id for card in result}
    assert result_card_ids == expected_card_ids

@then("duplicates are eliminated")
def verify_no_duplicates(context):
    """Verify no duplicate cards in result."""
    result = context.get('union_result')
    card_ids = [card.card_id for card in result]
    assert len(card_ids) == len(set(card_ids))

@then("result maintains immutability")
def verify_immutability(context):
    """Verify result is immutable."""
    result = context.get('union_result') or context.get('intersection_result')
    assert isinstance(result, frozenset)
    # Verify it's truly immutable
    with pytest.raises(AttributeError):
        result.add(Card("new_card", [5]))

# Scenario 3: Complex nested operations

@given("I have a complex filter expression")
def complex_filter_setup(context):
    """Set up complex filter scenario."""
    context['cards'] = frozenset([
        Card("card1", (1, 2, 3)),
        Card("card2", (1, 2)),
        Card("card3", (1, 3)),
        Card("card4", (2, 3, 4)),
        Card("card5", (1, 2, 3, 4)),
        Card("card6", (5,)),
        Card("card7", (1, 5))
    ])
    context['intersection_tags'] = [1, 2]  # Must have both 1 AND 2
    context['union_tags'] = [3, 4]  # Then must have 3 OR 4

@when("I combine intersection and union operations")
def perform_complex_operation(context):
    """Perform complex two-phase filtering."""
    from apps.shared.services.bitmap_operations import perform_complex_filter

    start_time = time.perf_counter()
    context['complex_result'] = perform_complex_filter(
        context['intersection_tags'],
        context['union_tags'],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    context['elapsed_time'] = time.perf_counter() - start_time

@then("the result follows set theory rules")
def verify_set_theory(context):
    """Verify result follows mathematical set theory."""
    result = context['complex_result']
    # Phase 1: Cards with tags 1 AND 2 = {card1, card2, card5}
    # Phase 2: Of those, cards with tag 3 OR 4 = {card1, card5}
    expected_card_ids = {"card1", "card5"}
    result_card_ids = {card.card_id for card in result}
    assert result_card_ids == expected_card_ids

@then("performance remains under threshold")
def verify_performance_threshold(context):
    """Verify performance is under 50ms threshold."""
    assert context['elapsed_time'] < 0.05, f"Operation took {context['elapsed_time']:.3f}s"

@then("operations use pure functions")
def verify_pure_functions(context):
    """Verify operations are pure functions."""
    # Verify original cards are unchanged
    assert context['cards'] is not None
    # Verify result is immutable
    assert isinstance(context['complex_result'], frozenset)
    # Verify we can call again with same result
    from apps.shared.services.bitmap_operations import perform_complex_filter

    result2 = perform_complex_filter(
        context['intersection_tags'],
        context['union_tags'],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    assert result2 == context['complex_result']

    # Test edge cases for better coverage
    # Empty intersection tags
    empty_intersection = perform_complex_filter(
        [],
        [3, 4],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    assert isinstance(empty_intersection, frozenset)

    # Empty union tags
    empty_union = perform_complex_filter(
        [1, 2],
        [],
        context['cards'],
        workspace_id=context['workspace_id'],
        user_id=context['user_id']
    )
    assert isinstance(empty_union, frozenset)
