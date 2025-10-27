"""
Unit tests for group expansion operations.

Tests the recursive expansion, caching, and circular reference detection.
"""

import pytest
from apps.shared.services.group_expansion import (
    expand_group_recursive,
    validate_circular_reference,
    get_expansion_depth,
    get_total_expanded_count,
    get_expansion_tree,
    invalidate_expansion_cache,
    get_cache_statistics,
    GroupExpansionCache,
)


def test_simple_expansion(sample_group):
    """Test expanding a simple group with regular tags."""
    expanded = expand_group_recursive(sample_group)

    assert expanded is not None
    assert isinstance(expanded, frozenset)
    assert len(expanded) == 3
    assert 'tag-1' in expanded
    assert 'tag-2' in expanded
    assert 'tag-3' in expanded


def test_nested_expansion(nested_groups):
    """Test expanding nested groups."""
    expanded = expand_group_recursive(nested_groups['engineering'])

    assert expanded is not None
    # Should have: tag-python, tag-java, tag-react, tag-vue, tag-5
    assert len(expanded) >= 5
    assert 'tag-python' in expanded
    assert 'tag-java' in expanded
    assert 'tag-react' in expanded
    assert 'tag-vue' in expanded
    assert 'tag-5' in expanded


def test_expansion_depth(nested_groups):
    """Test getting expansion depth."""
    depth = get_expansion_depth(nested_groups['engineering'])

    assert depth >= 1  # At least 1 level deep (groups contain tags)


def test_expansion_count(nested_groups):
    """Test getting total expanded count."""
    count = get_total_expanded_count(nested_groups['engineering'])

    assert count >= 5  # At least 5 total tags


def test_expansion_tree(nested_groups):
    """Test getting expansion tree structure."""
    tree = get_expansion_tree(nested_groups['engineering'])

    assert tree is not None
    assert 'id' in tree or 'group_id' in tree  # Either format is ok
    assert 'children' in tree or 'members' in tree  # Either format is ok
    assert isinstance(tree, dict)


def test_validate_no_circular_reference(sample_group, group_workspace, group_tags):
    """Test that valid group relationships pass circular check."""
    from apps.shared.services.group_storage import create_group

    # Create another group
    other_group = create_group(
        'other-group',
        group_workspace['id'],
        group_workspace['created_by'],
        frozenset(['tag-4'])
    )

    # Check that adding other_group to sample_group is valid
    is_valid, error = validate_circular_reference(sample_group, other_group)

    assert is_valid is True
    assert error is None


def test_detect_circular_reference(group_workspace):
    """Test that circular references are detected."""
    from apps.shared.services.group_storage import create_group, add_member_to_group

    # Create group A
    group_a = create_group('group-a', group_workspace['id'], group_workspace['created_by'])

    # Create group B
    group_b = create_group('group-b', group_workspace['id'], group_workspace['created_by'])

    # Add B to A
    add_member_to_group(group_a, group_b, group_workspace['created_by'])

    # Try to add A to B (would create cycle)
    is_valid, error = validate_circular_reference(group_b, group_a)

    assert is_valid is False
    assert error is not None
    assert 'circular' in error.lower()


def test_cache_invalidation(sample_group):
    """Test that cache invalidation works."""
    # Expand once to populate cache
    expand_group_recursive(sample_group)

    # Invalidate cache
    invalidate_expansion_cache(sample_group)

    # Should still work
    expanded = expand_group_recursive(sample_group)
    assert len(expanded) == 3


def test_cache_statistics():
    """Test getting cache statistics."""
    stats = get_cache_statistics()

    assert stats is not None
    assert 'cache_size' in stats or 'total_requests' in stats


def test_expansion_cache_class():
    """Test GroupExpansionCache class."""
    cache = GroupExpansionCache(max_size=10, ttl_seconds=60)

    assert cache is not None
    assert cache.max_size == 10
    assert cache.ttl_seconds == 60


def test_empty_group_expansion(group_workspace):
    """Test expanding an empty group."""
    from apps.shared.services.group_storage import create_group

    empty_group = create_group(
        'empty-group',
        group_workspace['id'],
        group_workspace['created_by'],
        frozenset()
    )

    expanded = expand_group_recursive(empty_group)

    assert expanded is not None
    assert len(expanded) == 0


def test_deep_nesting(group_workspace, group_tags):
    """Test expansion with deeper nesting."""
    from apps.shared.services.group_storage import create_group

    # Create a 3-level hierarchy
    level1 = create_group('level-1', group_workspace['id'], group_workspace['created_by'],
                          frozenset(['tag-1', 'tag-2']))

    level2 = create_group('level-2', group_workspace['id'], group_workspace['created_by'],
                          frozenset([level1, 'tag-3']))

    level3 = create_group('level-3', group_workspace['id'], group_workspace['created_by'],
                          frozenset([level2, 'tag-4']))

    # Expand top level
    expanded = expand_group_recursive(level3)

    # Should have all 4 tags
    assert len(expanded) >= 4
    assert 'tag-1' in expanded
    assert 'tag-2' in expanded
    assert 'tag-3' in expanded
    assert 'tag-4' in expanded
