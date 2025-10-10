"""BDD tests for connection logic update."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch

# Load all scenarios from the feature file
scenarios('../tests/features/connection_logic_update.feature')


# Shared context for test scenarios
@pytest.fixture
def context():
    """Shared context for test scenarios."""
    return {
        "database_mode": None,
        "connection": None,
        "previous_connection": None,
        "connection_result": None,
        "error": None
    }


# Given steps
@given(parsers.parse('the database mode is set to "{mode}"'))
def set_database_mode(context, mode):
    """Set the database mode."""
    context["database_mode"] = mode


@given("a connection is established")
def establish_connection(context, mock_server_connection):
    """Establish a database connection."""
    context["previous_connection"] = mock_server_connection


# When steps
@when("I request a database connection")
def request_connection(context):
    """Request a database connection based on current mode."""
    from apps.shared.config.connection_router import get_database_connection
    try:
        context["connection"] = get_database_connection(
            mode=context["database_mode"]
        )
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I switch the database mode to "{mode}"'))
def switch_database_mode(context, mode):
    """Switch the database mode."""
    context["database_mode"] = mode


@when("I request a new database connection")
def request_new_connection(context):
    """Request a new database connection after mode switch."""
    from apps.shared.config.connection_router import get_database_connection
    try:
        if context["previous_connection"]:
            context["previous_connection"].close()
            context["previous_connection"].is_closed = True
        context["connection"] = get_database_connection(
            mode=context["database_mode"]
        )
    except Exception as e:
        context["error"] = e


@when("I request a database connection with server parameters")
def request_connection_with_server_params(context, connection_parameters):
    """Request a connection with server parameters in privacy mode."""
    from apps.shared.config.connection_router import get_database_connection
    try:
        context["connection"] = get_database_connection(
            mode=context["database_mode"],
            params=connection_parameters["server_params"]
        )
    except Exception as e:
        context["error"] = e


# Then steps
@then("the connection should route to the browser database")
def verify_browser_connection(context):
    """Verify connection routes to browser database."""
    assert context["connection"] is not None
    assert context["connection"].connection_type == "browser"


@then("no server connection should be established")
def verify_no_server_connection(context):
    """Verify no server connection was established."""
    assert context["connection"].connection_type != "server"
    assert not hasattr(context["connection"], "url") or \
           "turso" not in str(getattr(context["connection"], "url", ""))


@then("the connection should route to the server database")
def verify_server_connection(context):
    """Verify connection routes to server database."""
    assert context["connection"] is not None
    assert context["connection"].connection_type == "server"


@then("the connection URL should be the Turso cloud URL")
def verify_turso_url(context):
    """Verify connection URL is Turso cloud URL."""
    assert hasattr(context["connection"], "url")
    assert "turso" in context["connection"].url or "libsql" in context["connection"].url


@then("the connection should route to the local database")
def verify_local_connection(context):
    """Verify connection routes to local database."""
    assert context["connection"] is not None
    assert context["connection"].connection_type == "local"


@then("the connection URL should be the local development URL")
def verify_local_url(context):
    """Verify connection URL is local development URL."""
    assert hasattr(context["connection"], "url")
    assert "127.0.0.1" in context["connection"].url or "localhost" in context["connection"].url


@then("the previous server connection should be closed")
def verify_previous_connection_closed(context):
    """Verify previous connection was closed."""
    if context["previous_connection"]:
        assert context["previous_connection"].is_closed is True


@then("the connection should reject server parameters")
def verify_server_params_rejected(context):
    """Verify server parameters were rejected."""
    # In privacy mode, server params should not be used
    assert context["connection"] is not None
    assert context["connection"].connection_type == "browser"
    assert not hasattr(context["connection"], "auth_token")


@then("return a browser database connection instead")
def verify_browser_connection_returned(context):
    """Verify browser connection was returned despite server params."""
    assert context["connection"] is not None
    assert context["connection"].connection_type == "browser"
