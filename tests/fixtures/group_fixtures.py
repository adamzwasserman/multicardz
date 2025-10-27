"""
Group tags test fixtures.

Provides database stub and fixtures for testing group tags functionality.
"""

import pytest
from tests.fixtures.database_stub import get_connection, reset_test_database, close_test_database


@pytest.fixture(scope="function", autouse=True)
def setup_database_stub(monkeypatch):
    """
    Automatically monkey-patch database connection for all tests.

    This replaces the real database connection with an in-memory test database.
    """
    # Reset database for clean state
    reset_test_database()

    # Monkey-patch the get_connection calls in group_storage
    import apps.shared.services.group_storage as group_storage_module
    monkeypatch.setattr(group_storage_module, "get_connection", get_connection)

    yield

    # Cleanup after test
    close_test_database()


@pytest.fixture
def group_workspace():
    """Sample workspace for group testing."""
    return {
        'id': 'workspace-test-123',
        'name': 'Test Workspace',
        'created_by': 'user-test-456'
    }


@pytest.fixture
def group_tags(group_workspace):
    """Sample tags for group testing."""
    conn = get_connection()

    tags = [
        ('tag-1', group_workspace['id'], 'frontend'),
        ('tag-2', group_workspace['id'], 'backend'),
        ('tag-3', group_workspace['id'], 'api'),
        ('tag-4', group_workspace['id'], 'database'),
        ('tag-5', group_workspace['id'], 'devops'),
        ('tag-python', group_workspace['id'], 'python'),
        ('tag-java', group_workspace['id'], 'java'),
        ('tag-react', group_workspace['id'], 'react'),
        ('tag-vue', group_workspace['id'], 'vue'),
    ]

    for tag_id, workspace_id, name in tags:
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, workspace_id, name) VALUES (?, ?, ?)",
            (tag_id, workspace_id, name)
        )
    conn.commit()

    return tags


@pytest.fixture
def sample_group(group_workspace, group_tags):
    """Sample group for testing."""
    from apps.shared.services.group_storage import create_group

    group_id = create_group(
        name='engineering',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=frozenset(['tag-1', 'tag-2', 'tag-3'])
    )

    return group_id


@pytest.fixture
def nested_groups(group_workspace, group_tags):
    """Create nested groups for testing."""
    from apps.shared.services.group_storage import create_group

    # Create backend group
    backend_id = create_group(
        name='backend',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=frozenset(['tag-python', 'tag-java'])
    )

    # Create frontend group
    frontend_id = create_group(
        name='frontend',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=frozenset(['tag-react', 'tag-vue'])
    )

    # Create engineering group containing both
    engineering_id = create_group(
        name='engineering-full',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=frozenset([backend_id, frontend_id, 'tag-5'])
    )

    return {
        'backend': backend_id,
        'frontend': frontend_id,
        'engineering': engineering_id
    }
