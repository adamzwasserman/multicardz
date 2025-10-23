"""Step definitions for analytics session API tests."""
from pytest_bdd import scenarios, given, when, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime, UTC
import pytest

# Link feature file
scenarios('../features/session_api.feature')


@given('the FastAPI application is running', target_fixture='client')
def fastapi_running(test_client):
    """FastAPI application test client."""
    return test_client


@given('an analytics session already exists', target_fixture='existing_session')
def existing_session(test_client, db_connection):
    """Create an existing session in the database."""
    session_id = str(uuid4())
    session_data = {
        'session_id': session_id,
        'referrer_url': 'https://google.com',
        'user_agent': 'TestAgent/1.0',
        'viewport_width': 1920,
        'viewport_height': 1080
    }

    # Create session via API
    response = test_client.post('/api/analytics/session', json=session_data)
    assert response.status_code == 201

    return session_id


@when('I POST to "/api/analytics/session" with session data', target_fixture='response')
def post_session_data(client):
    """POST session data to API."""
    session_data = {
        'session_id': str(uuid4()),
        'referrer_url': 'https://google.com/search?q=trello',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'viewport_width': 1920,
        'viewport_height': 1080,
        'timestamp': int(datetime.now(UTC).timestamp() * 1000)
    }
    
    return client.post('/api/analytics/session', json=session_data)


@when('I POST to "/api/analytics/session" with UTM parameters', target_fixture='response')
def post_session_with_utm(client):
    """POST session data with UTM parameters."""
    session_data = {
        'session_id': str(uuid4()),
        'referrer_url': 'https://google.com',
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'trello-refugees',
        'utm_term': 'trello alternative',
        'utm_content': 'ad1',
        'user_agent': 'Mozilla/5.0',
        'viewport_width': 1920,
        'viewport_height': 1080
    }
    
    return client.post('/api/analytics/session', json=session_data)


@when('I POST to "/api/analytics/session" with the same session_id', target_fixture='response')
def post_duplicate_session(test_client, existing_session):
    """POST duplicate session."""
    session_data = {
        'session_id': existing_session,
        'referrer_url': 'https://bing.com',
        'user_agent': 'TestAgent/1.0',
        'viewport_width': 1920,
        'viewport_height': 1080
    }

    return test_client.post('/api/analytics/session', json=session_data)


@when(parsers.parse('I POST to "/api/analytics/session" with referrer "{referrer_url}"'), target_fixture='response')
def post_session_with_referrer(client, referrer_url):
    """POST session with specific referrer."""
    session_data = {
        'session_id': str(uuid4()),
        'referrer_url': referrer_url,
        'user_agent': 'Mozilla/5.0',
        'viewport_width': 1920,
        'viewport_height': 1080
    }
    
    return client.post('/api/analytics/session', json=session_data)


@when('I POST to "/api/analytics/session" with invalid data', target_fixture='response')
def post_invalid_session(client):
    """POST invalid session data."""
    invalid_data = {
        # Missing required session_id
        'referrer_url': 'https://google.com',
        'user_agent': 'TestAgent'
    }
    
    return client.post('/api/analytics/session', json=invalid_data)


@then(parsers.parse('the response status should be {status_code:d}'))
def check_status_code(response, status_code):
    """Verify response status code."""
    assert response.status_code == status_code


@then('the response should contain session_id')
def check_session_id(response):
    """Verify response contains session_id."""
    data = response.json()
    assert 'session_id' in data
    assert data['session_id'] is not None


@then('the session should be stored in the database')
def check_session_stored(response, db_connection):
    """Verify session was stored in database."""
    data = response.json()
    session_id = data['session_id']

    # Query database
    result = db_connection.execute(
        text("SELECT session_id FROM analytics_sessions WHERE session_id = :session_id"),
        {"session_id": session_id}
    )
    row = result.fetchone()

    assert row is not None
    assert str(row[0]) == session_id


@then(parsers.parse('the session should have {field} "{value}"'))
def check_session_field(response, db_connection, field, value):
    """Verify session field value in database."""
    data = response.json()
    session_id = data['session_id']

    # Query database - use text() with safe field name
    result = db_connection.execute(
        text(f"SELECT {field} FROM analytics_sessions WHERE session_id = :session_id"),
        {"session_id": session_id}
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == value


@then('the last_seen timestamp should be updated')
def check_last_seen_updated(response, db_connection, existing_session):
    """Verify last_seen was updated for duplicate session."""
    # Query database
    result = db_connection.execute(
        text("SELECT last_seen FROM analytics_sessions WHERE session_id = :session_id"),
        {"session_id": existing_session}
    )
    row = result.fetchone()

    assert row is not None
    # Timestamp should be recent (within last 5 seconds)
    last_seen = row[0]
    now = datetime.now(UTC)
    diff = (now - last_seen).total_seconds()
    assert diff < 5


@then('the response should contain validation errors')
def check_validation_errors(response):
    """Verify response contains validation errors."""
    data = response.json()
    assert 'detail' in data
