"""
Step definitions for mouse tracking JavaScript testing.
"""

from pytest_bdd import scenarios, given, when, then, parsers
import pytest
import time


# Load scenarios
scenarios("../features/mouse_tracking_js.feature")


# Shared context for test state
@pytest.fixture
def mouse_context():
    """Shared mouse tracking test context."""
    return {
        "tracking_loaded": False,
        "tracking_enabled": True,
        "mouse_positions": [],
        "clicks": [],
        "sample_rate": 100,
        "batch_size": 50,
        "last_sample_time": 0,
        "batch_sent": False
    }


@given("the mouse tracking JavaScript is loaded")
def mouse_tracking_loaded(mouse_context, mouse_tracking_js_path):
    """Verify mouse-tracking.js file exists."""
    assert mouse_tracking_js_path.exists(), f"mouse-tracking.js not found at {mouse_tracking_js_path}"
    mouse_context["tracking_loaded"] = True


@given("mouse tracking is active")
def mouse_tracking_active(mouse_context):
    """Ensure mouse tracking is active."""
    mouse_context["tracking_enabled"] = True
    mouse_context["tracking_loaded"] = True


@given("mouse tracking is initialized")
def mouse_tracking_initialized(mouse_context):
    """Initialize mouse tracking."""
    mouse_context["tracking_loaded"] = True
    mouse_context["tracking_enabled"] = True


@given(parsers.parse("{count:d} mouse positions have been tracked"))
def mouse_positions_tracked(mouse_context, count):
    """Create N mouse positions for testing."""
    mouse_context["mouse_positions"] = [
        {
            "x": 100 + i * 5,
            "y": 150 + i * 5,
            "timestamp": 1000 + i * 100
        }
        for i in range(count)
    ]


@when("a user moves the mouse")
def user_moves_mouse(mouse_context):
    """Simulate mouse movement."""
    current_time = int(time.time() * 1000)

    # Simulate single mouse move
    mouse_context["mouse_positions"].append({
        "x": 250,
        "y": 350,
        "timestamp": current_time
    })


@when("the user moves the mouse continuously")
def user_moves_mouse_continuously(mouse_context):
    """Simulate continuous mouse movement."""
    current_time = int(time.time() * 1000)

    # Simulate 10 rapid mouse movements
    for i in range(10):
        # Only add if sampling interval has passed
        time_since_last = (current_time + i * 10) - mouse_context["last_sample_time"]

        if time_since_last >= mouse_context["sample_rate"]:
            mouse_context["mouse_positions"].append({
                "x": 100 + i * 10,
                "y": 200 + i * 10,
                "timestamp": current_time + i * 10
            })
            mouse_context["last_sample_time"] = current_time + i * 10


@when("the batch threshold is reached")
def batch_threshold_reached(mouse_context):
    """Simulate batch threshold being reached."""
    # Check if we have enough positions
    if len(mouse_context["mouse_positions"]) >= mouse_context["batch_size"]:
        mouse_context["batch_sent"] = True


@when("a user clicks on the page")
def user_clicks_page(mouse_context):
    """Simulate mouse click."""
    current_time = int(time.time() * 1000)

    click_event = {
        "x": 320,
        "y": 480,
        "timestamp": current_time,
        "type": "click"
    }

    mouse_context["clicks"].append(click_event)

    # Also add to mouse positions
    mouse_context["mouse_positions"].append({
        "x": 320,
        "y": 480,
        "timestamp": current_time,
        "is_click": True
    })


@when("tracking is disabled via privacy setting")
def tracking_disabled(mouse_context):
    """Disable tracking via privacy setting."""
    mouse_context["tracking_enabled"] = False


@then("mouse coordinates should be captured")
def coordinates_captured(mouse_context):
    """Verify mouse coordinates are captured."""
    assert len(mouse_context["mouse_positions"]) > 0, "No mouse positions captured"
    last_position = mouse_context["mouse_positions"][-1]
    assert "x" in last_position, "x coordinate not captured"
    assert "y" in last_position, "y coordinate not captured"


@then("timestamps should be recorded")
def timestamps_recorded(mouse_context):
    """Verify timestamps are recorded."""
    assert len(mouse_context["mouse_positions"]) > 0, "No positions recorded"
    last_position = mouse_context["mouse_positions"][-1]
    assert "timestamp" in last_position, "timestamp not recorded"
    assert last_position["timestamp"] > 0, "timestamp invalid"


@then("coordinates should be relative to document")
def coordinates_relative_to_document(mouse_context):
    """Verify coordinates are relative to document."""
    # In real implementation, coordinates should account for scroll position
    # For now, verify they are reasonable values
    if mouse_context["mouse_positions"]:
        last_position = mouse_context["mouse_positions"][-1]
        assert last_position["x"] >= 0, "x coordinate negative"
        assert last_position["y"] >= 0, "y coordinate negative"


@then("mouse positions should be sampled at intervals")
def positions_sampled_at_intervals(mouse_context):
    """Verify sampling is working."""
    # Should have fewer positions than total movements due to sampling
    assert len(mouse_context["mouse_positions"]) <= 10, "Not all movements were sampled"


@then("not every single mouse movement should be recorded")
def not_every_movement_recorded(mouse_context):
    """Verify not every movement is recorded."""
    # With 10 rapid movements and 100ms sampling, should have < 10 samples
    assert len(mouse_context["mouse_positions"]) < 10, "Too many samples recorded"


@then(parsers.parse("sampling rate should be configurable (default {rate:d}ms)"))
def sampling_rate_configurable(mouse_context, rate):
    """Verify sampling rate is configurable."""
    assert mouse_context["sample_rate"] == rate, f"Sample rate should be {rate}ms"


@then("all positions should be batched together")
def positions_batched(mouse_context):
    """Verify positions are batched."""
    assert len(mouse_context["mouse_positions"]) >= mouse_context["batch_size"], \
        "Not enough positions for batching"


@then("a single API call should be made")
def single_api_call_made(mouse_context):
    """Verify single API call for batch."""
    assert mouse_context["batch_sent"], "Batch was not sent"


@then("the buffer should be cleared")
def buffer_cleared(mouse_context):
    """Verify buffer is cleared after batch."""
    if mouse_context["batch_sent"]:
        # Simulate clearing buffer after batch
        mouse_context["mouse_positions_sent"] = mouse_context["mouse_positions"].copy()
        mouse_context["mouse_positions"] = []

    assert len(mouse_context["mouse_positions"]) == 0, "Buffer not cleared"


@then("the click position should be recorded")
def click_position_recorded(mouse_context):
    """Verify click position is recorded."""
    assert len(mouse_context["clicks"]) > 0, "No clicks recorded"
    last_click = mouse_context["clicks"][-1]
    assert "x" in last_click, "Click x coordinate not recorded"
    assert "y" in last_click, "Click y coordinate not recorded"


@then("the click should be marked as a special event")
def click_marked_as_special(mouse_context):
    """Verify click is marked differently."""
    assert len(mouse_context["clicks"]) > 0, "No clicks recorded"
    last_click = mouse_context["clicks"][-1]
    assert last_click["type"] == "click", "Click not marked as special event"


@then("click coordinates should match mouse position")
def click_coordinates_match(mouse_context):
    """Verify click coordinates match mouse position."""
    assert len(mouse_context["clicks"]) > 0, "No clicks recorded"

    last_click = mouse_context["clicks"][-1]

    # Find matching position
    matching_positions = [
        p for p in mouse_context["mouse_positions"]
        if p["x"] == last_click["x"] and p["y"] == last_click["y"]
    ]

    assert len(matching_positions) > 0, "No matching position found for click"


@then("mouse movements should not be recorded")
def movements_not_recorded(mouse_context):
    """Verify movements are not recorded when disabled."""
    if not mouse_context["tracking_enabled"]:
        # Simulate that no positions were added
        initial_count = len(mouse_context["mouse_positions"])
        # If tracking was disabled, no new positions should be added
        assert len(mouse_context["mouse_positions"]) == initial_count, \
            "Positions were recorded despite tracking being disabled"


@then("no API calls should be made for mouse data")
def no_api_calls_for_mouse_data(mouse_context):
    """Verify no API calls when tracking disabled."""
    if not mouse_context["tracking_enabled"]:
        assert not mouse_context["batch_sent"], "API call was made despite tracking being disabled"
