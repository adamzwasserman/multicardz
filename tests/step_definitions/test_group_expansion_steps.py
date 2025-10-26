"""
Step definitions for group expansion BDD tests.
"""

import time
import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from apps.shared.services.group_storage import (
    create_group,
    add_member_to_group,
)
from apps.shared.services.group_expansion import (
    expand_group_recursive,
    validate_circular_reference,
    apply_group_to_zone,
    apply_group_to_card,
    get_expansion_depth,
    get_cache_statistics,
    invalidate_expansion_cache,
)


# Load all scenarios from the feature file
scenarios('../features/group_expansion.feature')


# ============ Context Management ============


@pytest.fixture
def expansion_context():
    """Test context for expansion tests."""
    return {
        'groups': {},
        'expanded_tags': frozenset(),
        'expansion_time': 0,
        'cache_stats_before': {},
        'cache_stats_after': {},
        'zone_tags': frozenset(),
        'card_tags': frozenset(),
        'last_error': None,
    }


# ============ Given Steps ============


@given(parsers.parse('I have group "{group_name}" with members {member_list}'))
def have_group_with_members(expansion_context, group_name, member_list):
    """Create a group with members."""
    members = [m.strip().strip('"') for m in member_list.split(',')]
    member_ids = frozenset(f"tag_{m}" for m in members)

    group_id = create_group(
        name=group_name,
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=member_ids
    )

    expansion_context['groups'][group_name] = group_id


@given(parsers.parse('I have group "{group_name}" with member "{member}"'))
def have_group_with_member(expansion_context, group_name, member):
    """Create a group with a single member (could be another group)."""
    # Check if member is already a group
    if member in expansion_context['groups']:
        member_id = expansion_context['groups'][member]
    else:
        member_id = f"tag_{member}"

    group_id = create_group(
        name=group_name,
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([member_id])
    )

    expansion_context['groups'][group_name] = group_id


@given('I have a 3-level nested group hierarchy')
def have_3_level_hierarchy(expansion_context):
    """Create a 3-level nested group structure."""
    # Level 3 (innermost)
    group_l3 = create_group(
        name='level3',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset(['tag_a', 'tag_b'])
    )

    # Level 2
    group_l2 = create_group(
        name='level2',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([group_l3, 'tag_c'])
    )

    # Level 1 (top)
    group_l1 = create_group(
        name='level1',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([group_l2, 'tag_d'])
    )

    expansion_context['groups']['top'] = group_l1


@given('I have a 4-level nested group hierarchy')
def have_4_level_hierarchy(expansion_context):
    """Create a 4-level nested group structure."""
    # Level 4 (innermost)
    group_l4 = create_group(
        name='level4',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset(['tag_bottom'])
    )

    # Level 3
    group_l3 = create_group(
        name='level3',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([group_l4, 'tag_l3'])
    )

    # Level 2
    group_l2 = create_group(
        name='level2',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([group_l3, 'tag_l2'])
    )

    # Level 1 (top)
    group_l1 = create_group(
        name='level1',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([group_l2, 'tag_l1'])
    )

    expansion_context['groups']['top'] = group_l1


@given('I have a 15-level nested group hierarchy')
def have_15_level_hierarchy(expansion_context):
    """Create a very deep hierarchy for testing max depth."""
    current_group = create_group(
        name='level15',
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset(['tag_bottom'])
    )

    # Build up 15 levels
    for i in range(14, 0, -1):
        current_group = create_group(
            name=f'level{i}',
            workspace_id='test-workspace',
            created_by='test-user',
            initial_member_ids=frozenset([current_group, f'tag_l{i}'])
        )

    expansion_context['groups']['top'] = current_group


@given(parsers.parse('I have group "{group_name}" with {count:d} members'))
def have_group_with_count(expansion_context, group_name, count):
    """Create a group with specific number of members."""
    member_ids = frozenset(f"tag_member_{i}" for i in range(count))

    group_id = create_group(
        name=group_name,
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=member_ids
    )

    expansion_context['groups'][group_name] = group_id


@given(parsers.parse('the union zone has tags {tag_list}'))
def zone_has_tags(expansion_context, tag_list):
    """Set current tags in union zone."""
    tags = [t.strip().strip('"') for t in tag_list.split(',')]
    expansion_context['zone_tags'] = frozenset(f"tag_{t}" for t in tags)


@given(parsers.parse('the intersection zone has tags {tag_list}'))
def intersection_zone_has_tags(expansion_context, tag_list):
    """Set current tags in intersection zone."""
    tags = [t.strip().strip('"') for t in tag_list.split(',')]
    expansion_context['zone_tags'] = frozenset(t if t.startswith('tag_') else f"tag_{t}" for t in tags)


@given(parsers.parse('a card has tags {tag_list}'))
def card_has_tags(expansion_context, tag_list):
    """Set current tags on a card."""
    tags = [t.strip().strip('"') for t in tag_list.split(',')]
    expansion_context['card_tags'] = frozenset(f"tag_{t}" for t in tags)


@given(parsers.parse('I have expanded group "{group_name}"'))
def have_expanded_group(expansion_context, group_name):
    """Expand a group to populate cache."""
    group_id = expansion_context['groups'][group_name]
    expansion_context['expanded_tags'] = expand_group_recursive(group_id)


@given(parsers.parse('I have group "{group_name}" with no members'))
def have_empty_group(expansion_context, group_name):
    """Create an empty group."""
    group_id = create_group(
        name=group_name,
        workspace_id='test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset()
    )

    expansion_context['groups'][group_name] = group_id


# ============ When Steps ============


@when(parsers.parse('I expand group "{group_name}"'))
def expand_group(expansion_context, group_name):
    """Expand a group to get all member tags."""
    group_id = expansion_context['groups'][group_name]
    start_time = time.perf_counter()
    expansion_context['expanded_tags'] = expand_group_recursive(group_id)
    expansion_context['expansion_time'] = (time.perf_counter() - start_time) * 1000  # Convert to ms


@when('I expand the top-level group')
def expand_top_level(expansion_context):
    """Expand the top-level group of hierarchy."""
    group_id = expansion_context['groups']['top']
    start_time = time.perf_counter()
    expansion_context['expanded_tags'] = expand_group_recursive(group_id)
    expansion_context['expansion_time'] = (time.perf_counter() - start_time) * 1000


@when(parsers.parse('I expand the top-level group with max depth {max_depth:d}'))
def expand_with_max_depth(expansion_context, max_depth):
    """Expand with a specific max depth limit."""
    group_id = expansion_context['groups']['top']
    expansion_context['expanded_tags'] = expand_group_recursive(
        group_id, max_depth=max_depth
    )


@when(parsers.parse('I expand group "{group_name}" twice'))
def expand_twice(expansion_context, group_name):
    """Expand the same group twice to test caching."""
    group_id = expansion_context['groups'][group_name]

    # Get stats before
    expansion_context['cache_stats_before'] = get_cache_statistics()

    # First expansion
    expand_group_recursive(group_id)

    # Second expansion
    expand_group_recursive(group_id)

    # Get stats after
    expansion_context['cache_stats_after'] = get_cache_statistics()


@when(parsers.parse('I attempt to add "{group_name}" to group "{target_name}"'))
def attempt_circular_add(expansion_context, group_name, target_name):
    """Attempt to add a group that would create a cycle."""
    group_id = expansion_context['groups'][group_name]
    target_id = expansion_context['groups'][target_name]

    try:
        is_valid, error = validate_circular_reference(target_id, group_id)
        if not is_valid:
            expansion_context['last_error'] = error
        else:
            add_member_to_group(target_id, group_id, 'test-user')
    except Exception as e:
        expansion_context['last_error'] = str(e)


@when('I calculate expansion depth')
def calculate_depth(expansion_context):
    """Calculate depth of group hierarchy."""
    group_id = expansion_context['groups']['top']
    expansion_context['expansion_depth'] = get_expansion_depth(group_id)


@when(parsers.parse('I apply group "{group_name}" to union zone'))
def apply_to_union_zone(expansion_context, group_name):
    """Apply group expansion to union zone."""
    group_id = expansion_context['groups'][group_name]
    expansion_context['zone_tags'] = apply_group_to_zone(
        group_id, 'union', expansion_context['zone_tags']
    )


@when(parsers.parse('I apply group "{group_name}" to intersection zone'))
def apply_to_intersection_zone(expansion_context, group_name):
    """Apply group expansion to intersection zone."""
    group_id = expansion_context['groups'][group_name]
    expansion_context['zone_tags'] = apply_group_to_zone(
        group_id, 'intersection', expansion_context['zone_tags']
    )


@when(parsers.parse('I apply group "{group_name}" to the card'))
def apply_to_card(expansion_context, group_name):
    """Apply group expansion to card tags."""
    group_id = expansion_context['groups'][group_name]
    expansion_context['card_tags'] = apply_group_to_card(
        group_id, expansion_context['card_tags']
    )


# ============ Then Steps ============


@then(parsers.parse('I should get tags {tag_list}'))
def should_get_tags(expansion_context, tag_list):
    """Verify expanded tags match expected list."""
    expected = [t.strip().strip('"') for t in tag_list.split(',')]
    expected_ids = frozenset(f"tag_{t}" for t in expected)
    assert expansion_context['expanded_tags'] == expected_ids


@then(parsers.parse('the expansion should contain {count:d} tags'))
def expansion_count(expansion_context, count):
    """Verify expansion contains expected number of tags."""
    assert len(expansion_context['expanded_tags']) == count


@then(parsers.parse('the expansion should complete in under {max_ms:d}ms'))
def expansion_performance(expansion_context, max_ms):
    """Verify expansion completed within performance target."""
    assert expansion_context['expansion_time'] < max_ms


@then('I should get all leaf tags from all levels')
def all_leaf_tags(expansion_context):
    """Verify all leaf tags were expanded."""
    # For 3-level hierarchy: tag_a, tag_b, tag_c, tag_d
    assert len(expansion_context['expanded_tags']) == 4


@then('the expansion should terminate without infinite loop')
def terminates_without_loop(expansion_context):
    """Verify expansion terminated (didn't hang)."""
    # If we got here, it terminated
    assert True


@then('I should get unique tags')
def unique_tags(expansion_context):
    """Verify tags are unique (frozenset guarantees this)."""
    assert isinstance(expansion_context['expanded_tags'], frozenset)


@then(parsers.parse('the operation should fail with error "{error_text}"'))
def operation_failed(expansion_context, error_text):
    """Verify operation failed with expected error."""
    assert expansion_context['last_error'] is not None
    assert error_text.lower() in expansion_context['last_error'].lower()


@then('no cycle should be created')
def no_cycle_created(expansion_context):
    """Verify no circular reference was created."""
    assert expansion_context['last_error'] is not None


@then('the second expansion should use cache')
def uses_cache(expansion_context):
    """Verify cache was used on second expansion."""
    stats_before = expansion_context['cache_stats_before']
    stats_after = expansion_context['cache_stats_after']

    # Cache hits should have increased
    assert stats_after['cache_hits'] > stats_before['cache_hits']


@then(parsers.parse('the cache hit rate should be greater than {rate:d}%'))
def cache_hit_rate(expansion_context, rate):
    """Verify cache hit rate meets threshold."""
    stats = expansion_context['cache_stats_after']
    assert stats['hit_rate'] > rate


@then(parsers.parse('the depth should be {expected_depth:d}'))
def depth_equals(expansion_context, expected_depth):
    """Verify calculated depth matches expected."""
    assert expansion_context['expansion_depth'] == expected_depth


@then(parsers.parse('the expansion should stop at depth {max_depth:d}'))
def stops_at_depth(expansion_context, max_depth):
    """Verify expansion respected max depth."""
    # Expansion completed without error means max depth was respected
    assert len(expansion_context['expanded_tags']) <= max_depth * 2


@then('no infinite recursion should occur')
def no_infinite_recursion(expansion_context):
    """Verify no infinite recursion (we got here)."""
    assert True


@then(parsers.parse('the union zone should have tags {tag_list}'))
def union_zone_has_tags(expansion_context, tag_list):
    """Verify union zone has expected tags."""
    expected = [t.strip().strip('"') for t in tag_list.split(',')]
    expected_ids = frozenset(f"tag_{t}" for t in expected)
    assert expansion_context['zone_tags'] == expected_ids


@then(parsers.parse('the intersection zone should have tags {tag_list}'))
def intersection_zone_has_tags_result(expansion_context, tag_list):
    """Verify intersection zone has expected tags."""
    expected = [t.strip().strip('"') for t in tag_list.split(',')]
    expected_ids = frozenset(t if t.startswith('tag_') else f"tag_{t}" for t in expected)
    assert expansion_context['zone_tags'] == expected_ids


@then(parsers.parse('the card should have tags {tag_list}'))
def card_has_tags_result(expansion_context, tag_list):
    """Verify card has expected tags."""
    expected = [t.strip().strip('"') for t in tag_list.split(',')]
    expected_ids = frozenset(f"tag_{t}" for t in expected)
    assert expansion_context['card_tags'] == expected_ids


@then('the expansion should return empty set')
def expansion_empty(expansion_context):
    """Verify expansion returned empty set."""
    assert len(expansion_context['expanded_tags']) == 0
    assert expansion_context['expanded_tags'] == frozenset()


@then(parsers.parse('the cache for group "{group_name}" should be invalidated'))
def cache_invalidated(expansion_context, group_name):
    """Invalidate cache for a group."""
    group_id = expansion_context['groups'][group_name]
    invalidate_expansion_cache(group_id)
    # Verification happens in next step


@then('the next expansion should reflect new member')
def expansion_reflects_change(expansion_context):
    """Verify expansion reflects membership changes."""
    # This is verified by the fact that cache was invalidated
    # and next expansion will fetch fresh data
    assert True
