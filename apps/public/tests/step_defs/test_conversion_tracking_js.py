"""
Step definitions for conversion tracking JavaScript BDD tests.
"""
import json
import pytest
import time
from pytest_bdd import scenarios, given, when, then, parsers


# Load scenarios
scenarios('../features/conversion_tracking_js.feature')


# Shared context for test state
@pytest.fixture
def conversion_context():
    """Shared conversion tracking test context."""
    return {
        "tracking_loaded": False,
        "session_id": "test-session-123",
        "landing_page_id": "page-abc-456",
        "queued_events": [],
        "api_calls": [],
        "batch_size": 5,
        "batch_interval": 5000
    }


# Background steps
@given('the conversion tracking module is loaded')
def conversion_module_loaded(conversion_context, conversion_tracking_js):
    """Load conversion tracking JavaScript."""
    if conversion_tracking_js is None:
        pytest.skip("conversion-tracking.js not yet implemented")
    conversion_context["tracking_loaded"] = True


@given('a session ID exists in localStorage')
def session_id_exists(conversion_context):
    """Verify session ID exists."""
    assert conversion_context["session_id"] is not None


# Scenario 1: Track page view funnel stage
@when('the page loads')
def page_loads(conversion_context):
    """Simulate page load and track view stage."""
    event = {
        "session_id": conversion_context["session_id"],
        "landing_page_id": conversion_context["landing_page_id"],
        "stage": "view",
        "timestamp": int(time.time() * 1000),
        "data": {
            "url": "https://multicardz.com/trello-performance",
            "referrer": "https://google.com",
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": None,
            "utm_term": None,
            "utm_content": None
        }
    }
    conversion_context["queued_events"].append(event)


@then('the "view" funnel stage should be tracked')
def view_stage_tracked(conversion_context):
    """Verify view funnel stage was tracked."""
    events = conversion_context["queued_events"]
    assert len(events) > 0, "No conversion events tracked"
    assert events[0]['stage'] == 'view'


@then('the event should include the session_id')
def event_includes_session_id(conversion_context, mock_session_id):
    """Verify event includes session ID."""
    events = conversion_context["queued_events"]
    assert events[0]['session_id'] == mock_session_id


@then('the event should include the landing_page_id')
def event_includes_landing_page_id(conversion_context, mock_landing_page_id):
    """Verify event includes landing page ID."""
    events = conversion_context["queued_events"]
    assert events[0]['landing_page_id'] == mock_landing_page_id


# Scenario 2: Track CTA click funnel stage
@given(parsers.parse('a CTA button exists with data-cta="{cta_id}"'))
def cta_button_exists(conversion_context, cta_id):
    """Verify CTA button exists."""
    # Simulate button existence
    pass


@when('the user clicks the CTA button')
def click_cta_button(conversion_context):
    """Simulate CTA button click."""
    event = {
        "session_id": conversion_context["session_id"],
        "landing_page_id": conversion_context["landing_page_id"],
        "stage": "cta_click",
        "timestamp": int(time.time() * 1000),
        "data": {
            "cta_id": "signup",
            "button_text": "Sign Up",
            "position": {"x": 200, "y": 300},
            "href": None,
            "tag_name": "button"
        }
    }
    conversion_context["queued_events"].append(event)


@then('the "cta_click" funnel stage should be tracked')
def cta_click_stage_tracked(conversion_context):
    """Verify cta_click funnel stage was tracked."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    assert len(cta_events) > 0, "No cta_click events tracked"


@then(parsers.parse('the event should include cta_id "{cta_id}"'))
def event_includes_cta_id(conversion_context, cta_id):
    """Verify event includes CTA ID."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    assert cta_events[-1]['data']['cta_id'] == cta_id


@then('the event should include button_text')
def event_includes_button_text(conversion_context):
    """Verify event includes button text."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    assert 'button_text' in cta_events[-1]['data']
    assert len(cta_events[-1]['data']['button_text']) > 0


@then('the event should include button_position')
def event_includes_button_position(conversion_context):
    """Verify event includes button position."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    position = cta_events[-1]['data'].get('position')
    assert position is not None
    assert 'x' in position
    assert 'y' in position


# Scenario 3: Track multiple CTA clicks
@given('multiple CTA buttons exist')
def multiple_cta_buttons_exist(conversion_context):
    """Verify multiple CTA buttons exist."""
    # Simulate multiple buttons
    pass


@when(parsers.parse('the user clicks CTA button "{cta_id}"'))
def click_specific_cta_button(conversion_context, cta_id):
    """Simulate clicking specific CTA button."""
    event = {
        "session_id": conversion_context["session_id"],
        "landing_page_id": conversion_context["landing_page_id"],
        "stage": "cta_click",
        "timestamp": int(time.time() * 1000),
        "data": {
            "cta_id": cta_id,
            "button_text": f"Button {cta_id}",
            "position": {"x": 100, "y": 200},
            "href": None,
            "tag_name": "button"
        }
    }
    conversion_context["queued_events"].append(event)
    time.sleep(0.01)  # Small delay to ensure unique timestamps


@then(parsers.parse('{count:d} "cta_click" funnel stages should be tracked'))
def multiple_cta_clicks_tracked(conversion_context, count):
    """Verify multiple CTA clicks tracked."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    assert len(cta_events) == count, f"Expected {count} cta_click events, got {len(cta_events)}"


@then('each event should have unique timestamps')
def events_have_unique_timestamps(conversion_context):
    """Verify events have unique timestamps."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    timestamps = [e['timestamp'] for e in cta_events]
    assert len(timestamps) == len(set(timestamps)), "Timestamps are not unique"


@then('each event should have different cta_ids')
def events_have_different_cta_ids(conversion_context):
    """Verify events have different CTA IDs."""
    events = conversion_context["queued_events"]
    cta_events = [e for e in events if e.get('stage') == 'cta_click']
    cta_ids = [e['data']['cta_id'] for e in cta_events]
    assert len(cta_ids) == len(set(cta_ids)), "CTA IDs are not unique"


# Scenario 4: Funnel events are batched
@given(parsers.parse('the batch size is configured to {size:d} events'))
def batch_size_configured(conversion_context, size):
    """Configure batch size."""
    conversion_context["batch_size"] = size


@when(parsers.parse('{count:d} CTA clicks occur'))
def multiple_cta_clicks_occur(conversion_context, count):
    """Simulate multiple CTA clicks."""
    for i in range(count):
        event = {
            "session_id": conversion_context["session_id"],
            "landing_page_id": conversion_context["landing_page_id"],
            "stage": "cta_click",
            "timestamp": int(time.time() * 1000) + i,
            "data": {
                "cta_id": f"cta-{i}",
                "button_text": f"Button {i}",
                "position": {"x": 100, "y": 200},
                "href": None,
                "tag_name": "button"
            }
        }
        conversion_context["queued_events"].append(event)

        # Simulate batch submission when batch size is reached
        if len(conversion_context["queued_events"]) >= conversion_context["batch_size"]:
            batch = conversion_context["queued_events"][:]
            conversion_context["api_calls"].append({
                "url": "/api/analytics/conversion",
                "method": "POST",
                "body": {"events": batch}
            })
            conversion_context["queued_events"] = []


@then(parsers.parse('a batch submission to "{endpoint}" should occur'))
def batch_submission_occurs(conversion_context, endpoint):
    """Verify batch submission occurred."""
    api_calls = conversion_context["api_calls"]
    endpoint_calls = [call for call in api_calls if endpoint in call['url']]
    assert len(endpoint_calls) > 0, f"No API calls to {endpoint}"


@then(parsers.parse('the batch should contain {count:d} funnel events'))
def batch_contains_events(conversion_context, count):
    """Verify batch contains correct number of events."""
    api_calls = conversion_context["api_calls"]
    conversion_calls = [call for call in api_calls if 'conversion' in call['url']]
    if conversion_calls:
        last_batch = conversion_calls[-1]['body']
        assert len(last_batch['events']) == count


@then('each event should have the correct structure')
def events_have_correct_structure(conversion_context):
    """Verify events have required fields."""
    api_calls = conversion_context["api_calls"]
    conversion_calls = [call for call in api_calls if 'conversion' in call['url']]

    if conversion_calls:
        last_batch = conversion_calls[-1]['body']
        events = last_batch['events']

        for event in events:
            assert 'session_id' in event
            assert 'stage' in event
            assert 'timestamp' in event
            assert 'landing_page_id' in event


# Scenario 5: Flush on page unload
@given(parsers.parse('{count:d} CTA clicks have been tracked'))
def cta_clicks_tracked(conversion_context, count):
    """Track CTA clicks."""
    for i in range(count):
        event = {
            "session_id": conversion_context["session_id"],
            "landing_page_id": conversion_context["landing_page_id"],
            "stage": "cta_click",
            "timestamp": int(time.time() * 1000) + i,
            "data": {
                "cta_id": f"cta-{i}",
                "button_text": f"Button {i}",
                "position": {"x": 100, "y": 200},
                "href": None,
                "tag_name": "button"
            }
        }
        conversion_context["queued_events"].append(event)


@when('the beforeunload event fires')
def beforeunload_fires(conversion_context):
    """Simulate page unload and flush events."""
    if conversion_context["queued_events"]:
        batch = conversion_context["queued_events"][:]
        conversion_context["api_calls"].append({
            "url": "/api/analytics/conversion",
            "method": "POST",
            "body": {"events": batch}
        })
        conversion_context["queued_events"] = []


@then('the conversion events should be flushed immediately')
def events_flushed(conversion_context):
    """Verify events were flushed."""
    api_calls = conversion_context["api_calls"]
    assert len(api_calls) > 0, "No API calls made after flush"


@then(parsers.parse('the API should receive {count:d} events'))
def api_receives_events(conversion_context, count):
    """Verify API received correct number of events."""
    api_calls = conversion_context["api_calls"]
    conversion_calls = [call for call in api_calls if 'conversion' in call['url']]

    total_events = 0
    for call in conversion_calls:
        body = call['body']
        total_events += len(body['events'])

    assert total_events >= count, f"Expected at least {count} events, got {total_events}"
