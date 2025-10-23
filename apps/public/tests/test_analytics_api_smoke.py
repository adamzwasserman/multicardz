"""Smoke tests for analytics API endpoints."""
import pytest
from uuid import uuid4


def test_session_endpoint_exists(test_client):
    """Verify session endpoint exists and responds."""
    response = test_client.post('/api/analytics/session', json={
        'session_id': str(uuid4()),
        'user_agent': 'TestAgent'
    })
    assert response.status_code in [201, 422, 500]  # Endpoint exists


def test_page_view_endpoint_exists(test_client):
    """Verify page view endpoint exists and responds."""
    response = test_client.post('/api/analytics/page-view', json={
        'session_id': str(uuid4()),
        'url': 'https://test.com'
    })
    assert response.status_code in [201, 422, 500]  # Endpoint exists


def test_events_batch_endpoint_exists(test_client):
    """Verify events batch endpoint exists and responds."""
    response = test_client.post('/api/analytics/events/batch', json={
        'session_id': str(uuid4()),
        'page_view_id': str(uuid4()),
        'events': []
    })
    assert response.status_code in [201, 422, 500]  # Endpoint exists


def test_mouse_tracking_endpoint_exists(test_client):
    """Verify mouse tracking endpoint exists and responds."""
    response = test_client.post('/api/analytics/mouse-tracking', json={
        'session_id': str(uuid4()),
        'page_view_id': str(uuid4()),
        'coordinates': []
    })
    assert response.status_code in [201, 422, 500]  # Endpoint exists


def test_full_analytics_flow(test_client):
    """Test complete analytics flow across all endpoints."""
    # 1. Create session
    session_id = str(uuid4())
    session_response = test_client.post('/api/analytics/session', json={
        'session_id': session_id,
        'referrer_url': 'https://google.com',
        'user_agent': 'TestAgent/1.0'
    })
    assert session_response.status_code == 201
    
    # 2. Log page view
    page_view_response = test_client.post('/api/analytics/page-view', json={
        'session_id': session_id,
        'url': 'https://multicardz.com/test',
        'duration_ms': 5000,
        'scroll_depth_percent': 50
    })
    assert page_view_response.status_code == 201
    page_view_id = page_view_response.json()['page_view_id']
    
    # 3. Submit events
    events_response = test_client.post('/api/analytics/events/batch', json={
        'session_id': session_id,
        'page_view_id': page_view_id,
        'events': [
            {
                'event_type': 'click',
                'element_selector': '.cta-button',
                'timestamp_ms': 1000
            }
        ]
    })
    assert events_response.status_code == 201
    assert events_response.json()['events_created'] == 1
    
    # 4. Submit mouse tracking
    mouse_response = test_client.post('/api/analytics/mouse-tracking', json={
        'session_id': session_id,
        'page_view_id': page_view_id,
        'coordinates': [
            {'x': 100, 'y': 200, 'timestamp_ms': 500, 'event_type': 'move'},
            {'x': 150, 'y': 250, 'timestamp_ms': 600, 'event_type': 'move'}
        ]
    })
    assert mouse_response.status_code == 201
    assert mouse_response.json()['points_created'] == 2
