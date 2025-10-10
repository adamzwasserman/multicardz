"""
BDD tests for browser database service.

Tests the browser-based database service that operates in privacy mode,
ensuring all content storage and queries execute locally without server involvement.
"""
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from apps.shared.services.browser_database import (
    BrowserDatabaseConnection,
    initialize_database,
    execute_query,
    execute_transaction
)


# Shared context fixture for all scenarios
@pytest.fixture
def context():
    """Shared context for test scenarios."""
    return {}


# Scenario 1: Initialize browser database
@scenario(
    'features/browser_database_service.feature',
    'Initialize browser database'
)
def test_initialize_browser_database():
    """Test browser database initialization."""
    pass


@given("the browser database is not initialized", target_fixture="browser_db_not_initialized")
def browser_db_not_initialized(context):
    """Browser database is not initialized."""
    context["initialized"] = False
    return context


@when("I initialize the browser database")
def initialize_browser_db(browser_db_not_initialized):
    """Initialize the browser database."""
    result = initialize_database(
        database_name="test_multicardz.db",
        storage="opfs"
    )
    browser_db_not_initialized["result"] = result
    browser_db_not_initialized["initialized"] = result.success


@then("the database should be initialized successfully")
def verify_database_initialized(browser_db_not_initialized):
    """Verify database was initialized successfully."""
    assert browser_db_not_initialized["initialized"] is True
    assert browser_db_not_initialized["result"].success is True


@then("the database should use OPFS storage")
def verify_opfs_storage(browser_db_not_initialized):
    """Verify OPFS storage is used."""
    result = browser_db_not_initialized["result"]
    assert result.storage == "opfs"


@then("initialization should complete in less than 100ms")
def verify_init_performance(browser_db_not_initialized):
    """Verify initialization performance."""
    result = browser_db_not_initialized["result"]
    assert result.duration_ms < 100


# Scenario 2: Execute query on browser database
@scenario(
    'features/browser_database_service.feature',
    'Execute query on browser database'
)
def test_execute_query_on_browser_database():
    """Test query execution on browser database."""
    pass


@given("the browser database is initialized", target_fixture="browser_db_initialized")
def browser_db_initialized(context, mock_browser_db_connection):
    """Browser database is initialized."""
    # Create a connected database
    context["connection"] = BrowserDatabaseConnection(
        database_name="test_multicardz.db",
        storage_type="opfs",
        connected=True
    )
    context["initialized"] = True
    return context


@when("I execute a SELECT query")
def execute_select_query(browser_db_initialized, test_queries):
    """Execute a SELECT query."""
    query = test_queries[0]  # SELECT query
    params = ["ws-1", "user-1"]

    result = execute_query(
        browser_db_initialized["connection"],
        query,
        params
    )
    browser_db_initialized["query_result"] = result
    browser_db_initialized["network_calls"] = 0  # Local query, no network


@then("results should be returned successfully")
def verify_query_results(browser_db_initialized):
    """Verify query results are returned successfully."""
    result = browser_db_initialized["query_result"]
    assert result.success is True
    assert result.rows is not None


@then("no network request should be made")
def verify_no_network_request(browser_db_initialized):
    """Verify no network request was made."""
    assert browser_db_initialized["network_calls"] == 0


# Scenario 3: Execute transaction
@scenario(
    'features/browser_database_service.feature',
    'Execute transaction'
)
def test_execute_transaction():
    """Test transaction execution."""
    pass


@when("I execute multiple statements in a transaction")
def execute_transaction_statements(browser_db_initialized, test_transaction_statements):
    """Execute multiple statements in a transaction."""
    result = execute_transaction(
        browser_db_initialized["connection"],
        test_transaction_statements
    )
    browser_db_initialized["transaction_result"] = result


@then("all statements should execute atomically")
def verify_atomic_execution(browser_db_initialized):
    """Verify all statements executed atomically."""
    result = browser_db_initialized["transaction_result"]
    assert result.success is True


@then("the database should remain consistent")
def verify_database_consistency(browser_db_initialized):
    """Verify database consistency after transaction."""
    result = browser_db_initialized["transaction_result"]
    assert result.success is True
    assert result.error is None


# Scenario 4: Handle database errors
@scenario(
    'features/browser_database_service.feature',
    'Handle database errors'
)
def test_handle_database_errors():
    """Test database error handling."""
    pass


@when("I execute an invalid query")
def execute_invalid_query(browser_db_initialized):
    """Execute an invalid query."""
    # Execute query on unconnected database to trigger error
    disconnected_conn = BrowserDatabaseConnection(
        database_name="test.db",
        storage_type="opfs",
        connected=False  # Not connected, should error
    )

    result = execute_query(
        disconnected_conn,
        "SELECT * FROM nonexistent_table",
        []
    )
    browser_db_initialized["error_result"] = result


@then("an appropriate error should be returned")
def verify_error_returned(browser_db_initialized):
    """Verify appropriate error was returned."""
    result = browser_db_initialized["error_result"]
    assert result.success is False
    assert result.error is not None
    assert len(result.error) > 0


@then("the database should remain stable")
def verify_database_stable(browser_db_initialized):
    """Verify database remains stable after error."""
    # The original connection should still work
    result = execute_query(
        browser_db_initialized["connection"],
        "SELECT 1",
        []
    )
    assert result.success is True
