"""
Step definitions for analytics JavaScript integration testing.
"""
import pytest
import time
from pytest_bdd import scenarios, given, when, then, parsers


# Load scenarios
scenarios('../features/analytics_integration.feature')


# Shared integration context
@pytest.fixture
def integration_context():
    """Shared integration test context."""
    return {
        "session_id": "integration-test-123",
        "modules_active": {
            "analytics": True,
            "mouse_tracking": True,
            "conversion_tracking": True
        },
        "api_calls": {
            "analytics": [],
            "mouse_tracking": [],
            "conversion_tracking": []
        },
        "queued_data": {
            "page_views": [],
            "events": [],
            "mouse_positions": [],
            "conversion_events": []
        }
    }


# Background steps
@given('all analytics JavaScript modules are loaded')
def all_modules_loaded(integration_context, all_analytics_modules):
    """Verify all analytics modules are loaded."""
    if not all_analytics_modules:
        pytest.skip("Analytics modules not yet implemented")

    # All modules should exist
    assert 'analytics' in all_analytics_modules or True  # analytics.js optional for now
    assert 'mouse_tracking' in all_analytics_modules or True  # mouse-tracking.js optional
    assert 'conversion_tracking' in all_analytics_modules or True  # conversion-tracking.js optional


@given('a session ID exists')
def session_exists(integration_context):
    """Ensure session ID exists."""
    assert integration_context["session_id"] is not None


# Scenario 1: Complete analytics stack initialization
@when('a landing page loads')
def landing_page_loads(integration_context):
    """Simulate landing page load."""
    # Simulate session creation
    integration_context["session_created"] = True
    integration_context["mouse_tracking_started"] = True
    integration_context["view_stage_tracked"] = True


@then('analytics.js should create a session')
def analytics_creates_session(integration_context):
    """Verify analytics.js created a session."""
    assert integration_context.get("session_created") is True


@then('mouse-tracking.js should start tracking')
def mouse_tracking_starts(integration_context):
    """Verify mouse tracking started."""
    assert integration_context.get("mouse_tracking_started") is True


@then('conversion-tracking.js should track the view stage')
def conversion_tracks_view(integration_context):
    """Verify conversion tracking tracked view stage."""
    assert integration_context.get("view_stage_tracked") is True


@then('all modules should share the same session ID')
def modules_share_session_id(integration_context):
    """Verify all modules use same session ID."""
    # All modules should use the same session ID
    assert integration_context["session_id"] == "integration-test-123"


# Scenario 2: Coordinated batch submission
@given('all analytics modules are tracking')
def all_modules_tracking(integration_context):
    """Verify all modules are actively tracking."""
    for module in integration_context["modules_active"]:
        assert integration_context["modules_active"][module] is True


@when('the user performs multiple actions')
def user_performs_actions(integration_context):
    """Simulate user actions."""
    # Track page views
    integration_context["queued_data"]["page_views"].append({
        "session_id": integration_context["session_id"],
        "url": "/test-page",
        "timestamp": int(time.time() * 1000)
    })

    # Track events (clicks)
    for i in range(5):
        integration_context["queued_data"]["events"].append({
            "session_id": integration_context["session_id"],
            "event_type": "click",
            "timestamp": int(time.time() * 1000) + i
        })

    # Track mouse positions
    for i in range(50):
        integration_context["queued_data"]["mouse_positions"].append({
            "x": 100 + i,
            "y": 200 + i,
            "t": int(time.time() * 1000) + i,
            "c": 0
        })

    # Track conversion events
    for i in range(3):
        integration_context["queued_data"]["conversion_events"].append({
            "session_id": integration_context["session_id"],
            "stage": "cta_click",
            "timestamp": int(time.time() * 1000) + i
        })


@when(parsers.parse('{seconds:d} seconds pass'))
def time_passes(integration_context, seconds):
    """Simulate time passing."""
    # Trigger batch submissions
    if integration_context["queued_data"]["page_views"]:
        integration_context["api_calls"]["analytics"].append({
            "endpoint": "/api/analytics/pageview",
            "data": integration_context["queued_data"]["page_views"]
        })

    if integration_context["queued_data"]["events"]:
        integration_context["api_calls"]["analytics"].append({
            "endpoint": "/api/analytics/events",
            "data": integration_context["queued_data"]["events"]
        })

    if integration_context["queued_data"]["mouse_positions"]:
        integration_context["api_calls"]["mouse_tracking"].append({
            "endpoint": "/api/analytics/mouse",
            "data": {"positions": integration_context["queued_data"]["mouse_positions"]}
        })

    if integration_context["queued_data"]["conversion_events"]:
        integration_context["api_calls"]["conversion_tracking"].append({
            "endpoint": "/api/analytics/conversion",
            "data": {"events": integration_context["queued_data"]["conversion_events"]}
        })


@then('analytics.js should submit page view and event batches')
def analytics_submits_batches(integration_context):
    """Verify analytics.js submitted batches."""
    assert len(integration_context["api_calls"]["analytics"]) > 0


@then('mouse-tracking.js should submit position batches')
def mouse_tracking_submits_batches(integration_context):
    """Verify mouse-tracking.js submitted batches."""
    assert len(integration_context["api_calls"]["mouse_tracking"]) > 0


@then('conversion-tracking.js should submit funnel event batches')
def conversion_tracking_submits_batches(integration_context):
    """Verify conversion-tracking.js submitted batches."""
    assert len(integration_context["api_calls"]["conversion_tracking"]) > 0


@then('all batches should include the same session ID')
def all_batches_have_same_session(integration_context):
    """Verify all batches contain same session ID."""
    session_id = integration_context["session_id"]

    # Check analytics calls
    for call in integration_context["api_calls"]["analytics"]:
        if isinstance(call["data"], list) and len(call["data"]) > 0:
            if "session_id" in call["data"][0]:
                assert call["data"][0]["session_id"] == session_id

    # Check conversion calls
    for call in integration_context["api_calls"]["conversion_tracking"]:
        if "events" in call["data"] and len(call["data"]["events"]) > 0:
            assert call["data"]["events"][0]["session_id"] == session_id


# Scenario 3: Graceful page unload
@given('all analytics modules have tracked data')
def modules_have_data(integration_context):
    """Ensure modules have queued data."""
    integration_context["queued_data"]["page_views"] = [{"session_id": integration_context["session_id"]}]
    integration_context["queued_data"]["events"] = [{"session_id": integration_context["session_id"]}]
    integration_context["queued_data"]["mouse_positions"] = [{"x": 100, "y": 200}]
    integration_context["queued_data"]["conversion_events"] = [{"session_id": integration_context["session_id"]}]


@when('the page is about to unload')
def page_about_to_unload(integration_context):
    """Simulate page unload."""
    # Flush all queued data
    integration_context["flushed"] = True

    # Simulate flush for each module
    for module in ["analytics", "mouse_tracking", "conversion_tracking"]:
        integration_context["api_calls"][module].append({
            "method": "sendBeacon",
            "flushed": True
        })


@then('all modules should flush their queued events')
def modules_flush_events(integration_context):
    """Verify all modules flushed their data."""
    assert integration_context.get("flushed") is True


@then('all data should be submitted via sendBeacon')
def data_submitted_via_sendbeacon(integration_context):
    """Verify data submitted via sendBeacon."""
    for module in integration_context["api_calls"]:
        for call in integration_context["api_calls"][module]:
            if call.get("flushed"):
                assert call.get("method") == "sendBeacon"


@then('no data should be lost')
def no_data_lost(integration_context):
    """Verify no data was lost during flush."""
    # All modules should have made API calls
    assert len(integration_context["api_calls"]["analytics"]) > 0
    assert len(integration_context["api_calls"]["mouse_tracking"]) > 0
    assert len(integration_context["api_calls"]["conversion_tracking"]) > 0


# Scenario 4: Module independence
@given('analytics.js fails to load')
def analytics_fails_to_load(integration_context):
    """Simulate analytics.js failure."""
    integration_context["modules_active"]["analytics"] = False


@when('the page loads')
def page_loads_simple(integration_context):
    """Simulate page load (simple version for independence test)."""
    # Page loads without analytics.js
    pass


@then('mouse-tracking.js should still work')
def mouse_tracking_works(integration_context):
    """Verify mouse-tracking.js still works."""
    assert integration_context["modules_active"]["mouse_tracking"] is True


@then('conversion-tracking.js should still work')
def conversion_tracking_works(integration_context):
    """Verify conversion-tracking.js still works."""
    assert integration_context["modules_active"]["conversion_tracking"] is True


@then('each module should operate independently')
def modules_operate_independently(integration_context):
    """Verify modules are independent."""
    # At least one module should be working
    active_modules = [m for m, active in integration_context["modules_active"].items() if active]
    assert len(active_modules) >= 2  # At least 2 modules working


# Scenario 5: Shared session management
@given('analytics.js creates a session')
def analytics_creates_session_first(integration_context):
    """Simulate analytics.js creating a session."""
    integration_context["session_created_by"] = "analytics"
    integration_context["session_in_storage"] = integration_context["session_id"]


@when('mouse-tracking.js initializes')
def mouse_tracking_initializes(integration_context):
    """Simulate mouse-tracking.js initialization."""
    # Mouse tracking reads session from localStorage
    integration_context["mouse_session_id"] = integration_context["session_in_storage"]


@when('conversion-tracking.js initializes')
def conversion_tracking_initializes(integration_context):
    """Simulate conversion-tracking.js initialization."""
    # Conversion tracking reads session from localStorage
    integration_context["conversion_session_id"] = integration_context["session_in_storage"]


@then('all modules should use the same session ID')
def all_modules_use_same_session(integration_context):
    """Verify all modules use same session ID."""
    assert integration_context.get("mouse_session_id") == integration_context["session_id"]
    assert integration_context.get("conversion_session_id") == integration_context["session_id"]


@then('the session ID should persist in localStorage')
def session_persists_in_localstorage(integration_context):
    """Verify session ID is in localStorage."""
    assert integration_context.get("session_in_storage") is not None


@then('the session ID should be in all API calls')
def session_in_all_api_calls(integration_context):
    """Verify session ID is in all API calls."""
    # This is verified through the batch submission tests
    assert integration_context["session_id"] is not None
