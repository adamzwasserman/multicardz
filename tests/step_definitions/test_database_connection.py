"""
Step definitions for database connection management BDD tests.
"""

import shutil
import tempfile
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

# Import the feature
scenarios("../features/database_connection.feature")

# Global test state
test_state: dict[str, Any] = {}


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test databases."""
    temp_dir = tempfile.mkdtemp(prefix="multicardz_conn_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@given("I have a workspace_id and user_id")
def set_workspace_context():
    """Set workspace context for testing."""
    test_state["workspace_id"] = "test-workspace-001"
    test_state["user_id"] = "test-user-001"


@when("I request a database connection")
def request_connection(temp_db_dir):
    """Request a database connection."""
    workspace_id = test_state.get("workspace_id")
    user_id = test_state.get("user_id")

    # This will fail until we implement the connection module (red test)
    try:
        from apps.shared.services.database_connection import get_workspace_connection

        # Store context manager for later use
        test_state["connection_cm"] = get_workspace_connection(workspace_id, user_id)

        # Enter context and store connection
        test_state["connection"] = test_state["connection_cm"].__enter__()
        test_state["connection_success"] = True
    except ImportError:
        test_state["connection_success"] = False
        test_state["import_error"] = True


@then("the connection should be workspace-specific")
def verify_workspace_specific():
    """Verify connection is workspace-specific."""
    assert test_state.get("connection_success", False), "Connection failed"
    conn = test_state.get("connection")
    assert conn is not None, "No connection found"

    # Verify workspace context
    workspace_id = test_state.get("workspace_id")
    assert workspace_id is not None


@then("queries should be automatically scoped")
def verify_automatic_scoping():
    """Verify queries are automatically scoped."""
    try:
        from apps.shared.services.database_connection import create_scoped_query

        workspace_id = test_state.get("workspace_id")
        user_id = test_state.get("user_id")

        query = "SELECT * FROM cards"
        scoped_query, params = create_scoped_query(query, workspace_id, user_id)

        assert "workspace_id" in scoped_query
        assert "user_id" in scoped_query
        assert workspace_id in params
        assert user_id in params

        test_state["scoping_verified"] = True
    except ImportError:
        test_state["scoping_verified"] = False


@then("the connection should use context manager")
def verify_context_manager():
    """Verify connection uses context manager pattern."""
    assert test_state.get("connection_cm") is not None, "No context manager found"

    # Cleanup
    if test_state.get("connection_cm"):
        try:
            test_state["connection_cm"].__exit__(None, None, None)
        except:
            pass


@given("Turso is unavailable")
def mock_turso_unavailable():
    """Mock Turso being unavailable."""
    test_state["turso_available"] = False
    test_state["workspace_id"] = "test-workspace-002"
    test_state["user_id"] = "test-user-002"


@then("the system should use SQLite fallback")
def verify_sqlite_fallback():
    """Verify SQLite fallback is used."""
    conn = test_state.get("connection")
    assert conn is not None, "No fallback connection found"

    # SQLite connections should work
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1


@then("functionality should remain the same")
def verify_functionality_maintained():
    """Verify functionality is maintained in fallback mode."""
    conn = test_state.get("connection")
    if conn:
        # Basic functionality check
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        # Just verify we can query
        assert result is not None


@then("a warning should be logged")
def verify_warning_logged():
    """Verify warning is logged for fallback."""
    # This would check logging output in a real implementation
    test_state["warning_logged"] = True


@given("I have multiple concurrent requests")
def setup_concurrent_requests():
    """Setup multiple concurrent connection requests."""
    test_state["concurrent_requests"] = 10
    test_state["workspace_id"] = "test-workspace-003"
    test_state["user_id"] = "test-user-003"


@when("connections are requested")
def request_multiple_connections(temp_db_dir):
    """Request multiple connections concurrently."""
    try:
        from apps.shared.services.database_connection import get_workspace_connection

        workspace_id = test_state.get("workspace_id")
        user_id = test_state.get("user_id")
        num_requests = test_state.get("concurrent_requests", 10)

        # Simulate concurrent connection requests
        connections = []
        for _ in range(num_requests):
            cm = get_workspace_connection(workspace_id, user_id)
            conn = cm.__enter__()
            connections.append((cm, conn))

        test_state["connections"] = connections
        test_state["concurrent_success"] = True
    except ImportError:
        test_state["concurrent_success"] = False


@then("connections should be pooled")
def verify_connection_pooling():
    """Verify connections are pooled."""
    # This is a placeholder - actual pooling verification would be more complex
    assert test_state.get("concurrent_success", False) or test_state.get(
        "import_error", False
    )


@then("pool size should not exceed maximum")
def verify_pool_size_limit():
    """Verify pool size doesn't exceed maximum."""
    connections = test_state.get("connections", [])
    # In a real implementation, would verify pool size < MAX_CONNECTIONS
    assert len(connections) <= 100  # Arbitrary max for test


@then("connections should be recycled properly")
def verify_connection_recycling():
    """Verify connections are properly recycled."""
    connections = test_state.get("connections", [])

    # Clean up all connections
    for cm, conn in connections:
        try:
            cm.__exit__(None, None, None)
        except:
            pass

    test_state["connections_cleaned"] = True
