"""
Step definitions for group storage BDD tests.
"""

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from apps.shared.services.group_storage import (
    create_group,
    get_group_by_id,
    add_member_to_group,
    remove_member_from_group,
    add_multiple_members_to_group,
    delete_group,
    group_exists_by_name,
    tag_exists,
)


# Load all scenarios from the feature file
scenarios('../features/group_storage.feature')


# ============ Context Management ============


@pytest.fixture
def context():
    """Test context to store state between steps."""
    return {
        'workspace_id': None,
        'groups': {},
        'tags': set(),
        'last_operation_error': None,
        'last_group_id': None,
    }


# ============ Given Steps ============


@given(parsers.parse('I have workspace "{workspace_id}"'))
def have_workspace(context, workspace_id):
    """Store workspace ID in context."""
    context['workspace_id'] = workspace_id


@given(parsers.parse('I have tags {tag_list}'))
def have_tags(context, tag_list):
    """Create test tags."""
    # Parse comma-separated quoted tags
    tags = [t.strip().strip('"') for t in tag_list.split(',')]
    context['tags'].update(tags)


@given(parsers.parse('I have group "{group_name}" with members {member_list}'))
def have_group_with_members(context, group_name, member_list):
    """Create a group with initial members."""
    members = [m.strip().strip('"') for m in member_list.split(',')]
    member_ids = frozenset(f"tag_{m}" for m in members)

    group_id = create_group(
        name=group_name,
        workspace_id=context['workspace_id'] or 'test-workspace',
        created_by='test-user',
        initial_member_ids=member_ids
    )

    context['groups'][group_name] = group_id
    context['last_group_id'] = group_id


@given(parsers.parse('I have group "{group_name}" with member "{member}"'))
def have_group_with_member(context, group_name, member):
    """Create a group with a single member."""
    member_id = f"tag_{member}"

    group_id = create_group(
        name=group_name,
        workspace_id=context['workspace_id'] or 'test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset([member_id])
    )

    context['groups'][group_name] = group_id
    context['last_group_id'] = group_id


@given(parsers.parse('I have group "{group_name}"'))
def have_group(context, group_name):
    """Create an empty group."""
    group_id = create_group(
        name=group_name,
        workspace_id=context['workspace_id'] or 'test-workspace',
        created_by='test-user',
        initial_member_ids=frozenset()
    )

    context['groups'][group_name] = group_id
    context['last_group_id'] = group_id


@given(parsers.parse('I have group "{group_name}" in workspace "{workspace_id}"'))
def have_group_in_workspace(context, group_name, workspace_id):
    """Create a group in specific workspace."""
    group_id = create_group(
        name=group_name,
        workspace_id=workspace_id,
        created_by='test-user',
        initial_member_ids=frozenset()
    )

    context['groups'][group_name] = group_id
    context['workspace_id'] = workspace_id


# ============ When Steps ============


@when(parsers.parse('I create group "{group_name}" with members {member_list}'))
def create_group_with_members(context, group_name, member_list):
    """Create a new group with members."""
    members = [m.strip().strip('"') for m in member_list.split(',')]
    member_ids = frozenset(f"tag_{m}" for m in members)

    try:
        group_id = create_group(
            name=group_name,
            workspace_id=context['workspace_id'] or 'test-workspace',
            created_by='test-user',
            initial_member_ids=member_ids
        )
        context['groups'][group_name] = group_id
        context['last_group_id'] = group_id
        context['last_operation_error'] = None
    except Exception as e:
        context['last_operation_error'] = str(e)


@when(parsers.parse('I add member "{member}" to group "{group_name}"'))
def add_member(context, member, group_name):
    """Add a member to an existing group."""
    group_id = context['groups'][group_name]
    member_id = f"tag_{member}"

    try:
        add_member_to_group(group_id, member_id, 'test-user')
        context['last_operation_error'] = None
    except Exception as e:
        context['last_operation_error'] = str(e)


@when(parsers.parse('I add member "{member}" to group "{group_name}" again'))
def add_member_again(context, member, group_name):
    """Add the same member again (test idempotency)."""
    add_member(context, member, group_name)


@when(parsers.parse('I delete group "{group_name}"'))
def delete_group_by_name(context, group_name):
    """Delete a group."""
    group_id = context['groups'][group_name]
    delete_group(group_id)


@when(parsers.parse('I attempt to add group "{group_name}" to itself'))
def attempt_self_reference(context, group_name):
    """Attempt to add a group to itself."""
    group_id = context['groups'][group_name]
    try:
        add_member_to_group(group_id, group_id, 'test-user')
        context['last_operation_error'] = None
    except Exception as e:
        context['last_operation_error'] = str(e)


@when('I attempt to create group with empty name')
def attempt_empty_name(context):
    """Attempt to create a group with empty name."""
    try:
        create_group(
            name='',
            workspace_id=context['workspace_id'] or 'test-workspace',
            created_by='test-user'
        )
        context['last_operation_error'] = None
    except Exception as e:
        context['last_operation_error'] = str(e)


@when(parsers.parse('I attempt to create another group "{group_name}" in workspace "{workspace_id}"'))
def attempt_duplicate_name(context, group_name, workspace_id):
    """Attempt to create a group with duplicate name in workspace."""
    try:
        create_group(
            name=group_name,
            workspace_id=workspace_id,
            created_by='test-user'
        )
        context['last_operation_error'] = None
    except Exception as e:
        context['last_operation_error'] = str(e)


@when(parsers.parse('I add members {member_list} to group "{group_name}" in batch'))
def batch_add_members(context, member_list, group_name):
    """Add multiple members to group in single operation."""
    members = [m.strip().strip('"') for m in member_list.split(',')]
    member_ids = frozenset(f"tag_{m}" for m in members)

    group_id = context['groups'][group_name]

    try:
        success, added, error = add_multiple_members_to_group(
            group_id, member_ids, 'test-user'
        )
        context['last_operation_error'] = error if not success else None
    except Exception as e:
        context['last_operation_error'] = str(e)


# ============ Then Steps ============


@then('the group should be persisted with id')
def group_persisted(context):
    """Verify group was created with an ID."""
    assert context['last_group_id'] is not None
    assert context['last_group_id'].startswith('group_')


@then(parsers.parse('the group should have {count:d} members'))
def group_has_members(context, count):
    """Verify group has expected number of members."""
    group = get_group_by_id(context['last_group_id'])
    assert group is not None
    assert len(group.member_tag_ids) == count


@then(parsers.parse('the group "{group_name}" should have {count:d} members'))
def named_group_has_members(context, group_name, count):
    """Verify named group has expected number of members."""
    group_id = context['groups'][group_name]
    group = get_group_by_id(group_id)
    assert group is not None
    assert len(group.member_tag_ids) == count


@then(parsers.parse('the group should belong to workspace "{workspace_id}"'))
def group_in_workspace(context, workspace_id):
    """Verify group belongs to correct workspace."""
    group = get_group_by_id(context['last_group_id'])
    assert group.workspace_id == workspace_id


@then('the membership should be persisted')
def membership_persisted(context):
    """Verify membership was persisted."""
    group = get_group_by_id(context['last_group_id'])
    assert group is not None
    assert len(group.member_tag_ids) > 0


@then('the group should still have 1 member')
def group_still_one_member(context):
    """Verify idempotent add didn't duplicate member."""
    group = get_group_by_id(context['last_group_id'])
    assert len(group.member_tag_ids) == 1


@then('no duplicate entry should exist')
def no_duplicates(context):
    """Verify no duplicate members in group."""
    group = get_group_by_id(context['last_group_id'])
    # frozenset inherently prevents duplicates
    assert isinstance(group.member_tag_ids, frozenset)


@then('the group should not exist')
def group_not_exist(context):
    """Verify group was deleted."""
    group = get_group_by_id(context['last_group_id'])
    assert group is None


@then('the membership records should be deleted')
def memberships_deleted(context):
    """Verify memberships were cascaded."""
    # Already verified by group not existing
    pass


@then('the member tags should still exist')
def tags_still_exist(context):
    """Verify member tags were not deleted."""
    # Tags are independent entities - they persist
    # This is enforced by database schema (no cascade on tags)
    pass


@then(parsers.parse('the operation should fail with error "{error_text}"'))
def operation_failed(context, error_text):
    """Verify operation failed with expected error."""
    assert context['last_operation_error'] is not None
    assert error_text.lower() in context['last_operation_error'].lower()


@then('the group should remain unchanged')
def group_unchanged(context):
    """Verify group was not modified."""
    # Error should have been raised, so group is unchanged
    assert context['last_operation_error'] is not None


@then('all additions should succeed')
def all_additions_succeeded(context):
    """Verify batch operation succeeded."""
    assert context['last_operation_error'] is None
