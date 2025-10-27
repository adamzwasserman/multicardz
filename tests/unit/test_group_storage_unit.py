"""
Unit tests for group storage operations.

Tests the core CRUD operations for group tags with database stub.
"""

import pytest
from apps.shared.services.group_storage import (
    create_group,
    get_group_by_id,
    add_member_to_group,
    remove_member_from_group,
    delete_group,
    get_groups_by_workspace,
    get_group_statistics,
)


def test_create_group(group_workspace):
    """Test creating a new group."""
    group_id = create_group(
        name='test-group',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=frozenset()
    )

    assert group_id is not None
    assert group_id.startswith('group_')


def test_get_group_by_id(sample_group, group_workspace):
    """Test retrieving a group by ID."""
    group = get_group_by_id(sample_group)

    assert group is not None
    assert group.id == sample_group
    assert group.name == 'engineering'
    assert group.workspace_id == group_workspace['id']
    assert len(group.member_tag_ids) == 3


def test_add_member_to_group(sample_group, group_workspace, group_tags):
    """Test adding a member to a group."""
    success = add_member_to_group(
        sample_group,
        'tag-4',
        group_workspace['created_by']
    )

    assert success is True

    group = get_group_by_id(sample_group)
    assert 'tag-4' in group.member_tag_ids
    assert len(group.member_tag_ids) == 4


def test_add_member_idempotent(sample_group, group_workspace):
    """Test that adding same member twice is idempotent."""
    # Add once
    add_member_to_group(sample_group, 'tag-4', group_workspace['created_by'])

    # Add again
    success = add_member_to_group(sample_group, 'tag-4', group_workspace['created_by'])

    assert success is True

    group = get_group_by_id(sample_group)
    assert len(group.member_tag_ids) == 4  # Still 4, not 5


def test_prevent_self_reference(sample_group, group_workspace):
    """Test that group cannot be added to itself."""
    with pytest.raises(ValueError, match="Cannot add group to itself"):
        add_member_to_group(sample_group, sample_group, group_workspace['created_by'])


def test_remove_member_from_group(sample_group):
    """Test removing a member from a group."""
    success = remove_member_from_group(sample_group, 'tag-1')

    assert success is True

    group = get_group_by_id(sample_group)
    assert 'tag-1' not in group.member_tag_ids
    assert len(group.member_tag_ids) == 2


def test_delete_group(sample_group):
    """Test deleting a group."""
    success = delete_group(sample_group)

    assert success is True

    group = get_group_by_id(sample_group)
    assert group is None


def test_get_groups_by_workspace(group_workspace):
    """Test getting all groups in a workspace."""
    # Create multiple groups
    group1 = create_group('group1', group_workspace['id'], group_workspace['created_by'])
    group2 = create_group('group2', group_workspace['id'], group_workspace['created_by'])

    groups = get_groups_by_workspace(group_workspace['id'])

    assert len(groups) >= 2
    group_ids = {g.id for g in groups}
    assert group1 in group_ids
    assert group2 in group_ids


def test_get_group_statistics(sample_group):
    """Test getting group statistics."""
    stats = get_group_statistics(sample_group)

    assert stats is not None
    assert stats['total_members'] == 3
    assert stats['regular_tags'] == 3
    assert stats['nested_groups'] == 0
    assert 'created_at' in stats
    assert 'created_by' in stats


def test_nested_group_statistics(nested_groups):
    """Test statistics for nested groups."""
    eng_stats = get_group_statistics(nested_groups['engineering'])

    assert eng_stats['total_members'] == 3  # 2 groups + 1 tag
    assert eng_stats['regular_tags'] == 1  # tag-5
    assert eng_stats['nested_groups'] == 2  # backend + frontend
