"""BDD step definitions for analytics schema tests."""

import time
from pytest_bdd import scenarios, given, when, then, parsers
from sqlalchemy import text
from uuid import uuid4


# Load scenarios from feature file
scenarios('../features/analytics_schema.feature')


# Scenario: Create analytics session

@given('the database is connected')
def database_connected(db_connection):
    """Verify database connection is active."""
    assert db_connection is not None
    # Test connection
    result = db_connection.execute(text("SELECT 1")).scalar()
    assert result == 1


@when('I create a session with session_id')
def create_session(db_connection, test_session):
    """Insert analytics session into database."""
    db_connection.execute(
        text("""
            INSERT INTO analytics_sessions
                (session_id, landing_page_id, referrer_url, referrer_domain,
                 utm_source, utm_medium, utm_campaign, user_agent, ip_address,
                 browser_fingerprint, first_seen, last_seen)
            VALUES
                (:session_id, :landing_page_id, :referrer_url, :referrer_domain,
                 :utm_source, :utm_medium, :utm_campaign, :user_agent, CAST(:ip_address AS INET),
                 :browser_fingerprint, :first_seen, :last_seen)
        """),
        test_session
    )
    db_connection.commit()


@then('the session should be retrievable')
def session_retrievable(db_connection, test_session):
    """Verify session can be queried from database."""
    result = db_connection.execute(
        text("SELECT session_id FROM analytics_sessions WHERE session_id = :session_id"),
        {'session_id': test_session['session_id']}
    ).fetchone()

    assert result is not None
    assert str(result[0]) == str(test_session['session_id'])


@then('the session should track referrer and UTM params')
def session_has_utm_params(db_connection, test_session):
    """Verify UTM parameters are stored correctly."""
    result = db_connection.execute(
        text("""
            SELECT utm_source, utm_medium, utm_campaign, referrer_domain
            FROM analytics_sessions
            WHERE session_id = :session_id
        """),
        {'session_id': test_session['session_id']}
    ).fetchone()

    assert result is not None
    assert result[0] == test_session['utm_source']
    assert result[1] == test_session['utm_medium']
    assert result[2] == test_session['utm_campaign']
    assert result[3] == test_session['referrer_domain']


# Scenario: Log page view

@given('a session exists')
def session_exists(db_connection, test_session):
    """Ensure test session exists in database."""
    create_session(db_connection, test_session)


@when('I log a page view with duration and scroll depth')
def log_page_view(db_connection, test_page_view):
    """Insert page view record."""
    result = db_connection.execute(
        text("""
            INSERT INTO analytics_page_views
                (session_id, landing_page_id, url, duration_ms,
                 scroll_depth_percent, viewport_width, viewport_height)
            VALUES
                (:session_id, :landing_page_id, :url, :duration_ms,
                 :scroll_depth_percent, :viewport_width, :viewport_height)
            RETURNING id
        """),
        test_page_view
    )
    page_view_id = result.fetchone()[0]
    test_page_view['id'] = page_view_id  # Store for later use
    db_connection.commit()


@then('the page view should be associated with the session')
def page_view_associated(db_connection, test_page_view):
    """Verify page view is linked to session."""
    result = db_connection.execute(
        text("""
            SELECT session_id FROM analytics_page_views
            WHERE session_id = :session_id
        """),
        {'session_id': test_page_view['session_id']}
    ).fetchone()

    assert result is not None
    assert str(result[0]) == str(test_page_view['session_id'])


@then('duration and scroll depth should be stored')
def duration_and_scroll_stored(db_connection, test_page_view):
    """Verify duration and scroll depth are captured."""
    result = db_connection.execute(
        text("""
            SELECT duration_ms, scroll_depth_percent
            FROM analytics_page_views
            WHERE session_id = :session_id
        """),
        {'session_id': test_page_view['session_id']}
    ).fetchone()

    assert result is not None
    assert result[0] == test_page_view['duration_ms']
    assert result[1] == test_page_view['scroll_depth_percent']


# Scenario: Track events

@given('a page view exists')
def page_view_exists(db_connection, test_session, test_page_view):
    """Ensure page view exists in database."""
    create_session(db_connection, test_session)
    log_page_view(db_connection, test_page_view)


@when('I log click events with element selectors')
def log_click_events(db_connection, test_event, test_page_view):
    """Insert analytics event using the created page_view_id."""
    # Update event to use actual page_view_id
    test_event['page_view_id'] = test_page_view['id']

    db_connection.execute(
        text("""
            INSERT INTO analytics_events
                (session_id, page_view_id, event_type, element_selector,
                 element_text, element_position_x, element_position_y, timestamp_ms)
            VALUES
                (:session_id, :page_view_id, :event_type, :element_selector,
                 :element_text, :element_position_x, :element_position_y, :timestamp_ms)
        """),
        test_event
    )
    db_connection.commit()


@then('the events should be ordered by timestamp')
def events_ordered(db_connection, test_event):
    """Verify events can be ordered by timestamp."""
    # Insert a second event with higher timestamp
    second_event = test_event.copy()
    second_event['timestamp_ms'] = test_event['timestamp_ms'] + 1000

    db_connection.execute(
        text("""
            INSERT INTO analytics_events
                (session_id, page_view_id, event_type, element_selector,
                 element_text, element_position_x, element_position_y, timestamp_ms)
            VALUES
                (:session_id, :page_view_id, :event_type, :element_selector,
                 :element_text, :element_position_x, :element_position_y, :timestamp_ms)
        """),
        second_event
    )
    db_connection.commit()

    # Query ordered by timestamp
    results = db_connection.execute(
        text("""
            SELECT timestamp_ms FROM analytics_events
            WHERE session_id = :session_id
            ORDER BY timestamp_ms ASC
        """),
        {'session_id': test_event['session_id']}
    ).fetchall()

    assert len(results) == 2
    assert results[0][0] < results[1][0]


@then('element positions should be captured')
def element_positions_captured(db_connection, test_event):
    """Verify element coordinates are stored."""
    result = db_connection.execute(
        text("""
            SELECT element_position_x, element_position_y
            FROM analytics_events
            WHERE session_id = :session_id
            AND timestamp_ms = :timestamp_ms
        """),
        {'session_id': test_event['session_id'], 'timestamp_ms': test_event['timestamp_ms']}
    ).fetchone()

    assert result is not None
    assert result[0] == test_event['element_position_x']
    assert result[1] == test_event['element_position_y']


# Scenario: Record mouse tracking data

@when('I batch insert 100 mouse coordinates')
def batch_insert_mouse_data(db_connection, test_mouse_coordinates, test_page_view):
    """Insert 100 mouse tracking points and measure performance."""
    start_time = time.time()

    for coord in test_mouse_coordinates:
        # Use the actual page_view_id from the created page view
        coord['page_view_id'] = test_page_view['id']

        db_connection.execute(
            text("""
                INSERT INTO analytics_mouse_tracking
                    (session_id, page_view_id, timestamp_ms, event_type, x, y, scroll_x, scroll_y)
                VALUES
                    (:session_id, :page_view_id, :timestamp_ms, :event_type, :x, :y, :scroll_x, :scroll_y)
            """),
            coord
        )

    db_connection.commit()

    # Store elapsed time for verification
    db_connection.info['batch_insert_time'] = (time.time() - start_time) * 1000  # ms


@then('all coordinates should be stored')
def all_coordinates_stored(db_connection, test_mouse_coordinates):
    """Verify all 100 coordinates were inserted."""
    result = db_connection.execute(
        text("""
            SELECT COUNT(*) FROM analytics_mouse_tracking
            WHERE session_id = :session_id
        """),
        {'session_id': test_mouse_coordinates[0]['session_id']}
    ).scalar()

    assert result == 100


@then('performance should be acceptable')
def performance_acceptable(db_connection):
    """Verify batch insert completed within reasonable time (< 1000ms for 100 inserts)."""
    max_time = 1000  # 1 second
    elapsed_ms = db_connection.info.get('batch_insert_time', float('inf'))
    assert elapsed_ms < max_time, f"Batch insert took {elapsed_ms}ms (limit: {max_time}ms)"
