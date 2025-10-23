"""Step definitions for FastAPI application tests."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers


scenarios('../features/fastapi_app.feature')


# Scenario: Start FastAPI application

@given('the FastAPI app is created')
def fastapi_app_created(test_client):
    """App is created via fixture."""
    assert test_client is not None


@when('I start the test client')
def start_test_client(test_client):
    """Test client is ready."""
    pass


@then('the app should be accessible')
def app_accessible(test_client):
    """App responds to requests."""
    response = test_client.get('/health')
    assert response is not None


@then('health check endpoint should return 200')
def health_check_200(test_client):
    """Health endpoint returns 200 OK."""
    response = test_client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'public-website'


# Scenario: CORS configuration

@given('the app has CORS enabled')
def cors_enabled(test_client):
    """CORS middleware is configured."""
    pass


@when('I make a request with Origin header')
def request_with_origin(test_client):
    """Make request with Origin header."""
    pytest.cors_response = test_client.get(
        '/health',
        headers={'Origin': 'https://multicardz.com'}
    )


@then('CORS headers should be present')
def cors_headers_present():
    """CORS headers in response."""
    response = pytest.cors_response
    assert 'access-control-allow-origin' in response.headers or \
           'Access-Control-Allow-Origin' in response.headers


@then('Access-Control-Allow-Origin should be set')
def cors_origin_set():
    """Access-Control-Allow-Origin header set."""
    response = pytest.cors_response
    origin = response.headers.get('access-control-allow-origin') or \
             response.headers.get('Access-Control-Allow-Origin')
    # FastAPI CORS middleware returns the requesting origin if allowed
    assert origin is not None


# Scenario: Security headers

@given('the app is running')
def app_running(test_client):
    """App is running."""
    pass


@when('I request the health endpoint')
def request_health(test_client):
    """Request health endpoint."""
    pytest.security_response = test_client.get('/health')


@then('security headers should be present')
def security_headers_present(expected_security_headers):
    """Security headers are in response."""
    response = pytest.security_response
    for header in expected_security_headers.keys():
        assert header in response.headers or header.title() in response.headers


@then('X-Frame-Options should be DENY')
def xframe_deny():
    """X-Frame-Options is DENY."""
    response = pytest.security_response
    xframe = response.headers.get('x-frame-options') or \
             response.headers.get('X-Frame-Options')
    assert xframe == 'DENY'


@then('X-Content-Type-Options should be nosniff')
def xcontent_nosniff():
    """X-Content-Type-Options is nosniff."""
    response = pytest.security_response
    xcontent = response.headers.get('x-content-type-options') or \
               response.headers.get('X-Content-Type-Options')
    assert xcontent == 'nosniff'
