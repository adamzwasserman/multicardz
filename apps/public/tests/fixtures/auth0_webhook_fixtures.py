"""
Fixtures for Auth0 webhook integration tests.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
import hashlib
import hmac
import os


@pytest.fixture
def auth0_webhook_secret(monkeypatch):
    """Set and return a test webhook secret for HMAC verification."""
    secret = "test_webhook_secret_key_12345"
    monkeypatch.setenv('AUTH0_WEBHOOK_SECRET', secret)
    return secret


@pytest.fixture
def valid_auth0_token(auth0_webhook_secret):
    """Generate a valid HMAC token for webhook authentication."""
    import json
    payload = {
        'user_id': 'auth0|secure',
        'browser_fingerprint': 'fp_secure',
        'email': 'user@example.com',
        'created_at': '2025-10-23T15:30:00Z'
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    signature = hmac.new(
        auth0_webhook_secret.encode(),
        payload_json,
        hashlib.sha256
    ).hexdigest()
    return signature


@pytest.fixture
def invalid_auth0_token(monkeypatch):
    """Return an invalid HMAC token and set webhook secret."""
    secret = "test_webhook_secret_key_12345"
    monkeypatch.setenv('AUTH0_WEBHOOK_SECRET', secret)
    return "invalid_token_signature"


@pytest.fixture
def analytics_session_with_fingerprint(db_connection):
    """Create an analytics session with a specific fingerprint."""
    created_sessions = []

    def _create_session(fingerprint: str, user_id: str = None, landing_page_id: str = None):
        # Check if session with this fingerprint already exists
        existing = db_connection.execute(text("""
            SELECT session_id, landing_page_id, user_id
            FROM analytics_sessions
            WHERE browser_fingerprint = :fingerprint
        """), {'fingerprint': fingerprint}).fetchone()

        if existing:
            return {
                'session_id': str(existing[0]),
                'fingerprint': fingerprint,
                'user_id': existing[2],
                'landing_page_id': str(existing[1])
            }

        session_id = uuid4()

        # Create landing page if needed
        if landing_page_id is None:
            landing_page_id = uuid4()
            # Check if landing page with this slug exists
            slug = f'test-page-{fingerprint}'
            existing_page = db_connection.execute(text("""
                SELECT id FROM landing_pages WHERE slug = :slug
            """), {'slug': slug}).fetchone()

            if not existing_page:
                db_connection.execute(text("""
                    INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
                    VALUES (:id, :slug, 'replacement', 'Test Page', 'Test Headline', true, :now, :now)
                """), {
                    'id': landing_page_id,
                    'slug': slug,
                    'now': datetime.now(timezone.utc)
                })
            else:
                landing_page_id = existing_page[0]

        # Create session (or update if user_id specified)
        if user_id:
            # Update existing session with user_id
            db_connection.execute(text("""
                INSERT INTO analytics_sessions (
                    session_id, landing_page_id, browser_fingerprint, user_id,
                    first_seen, last_seen
                )
                VALUES (:session_id, :landing_page_id, :fingerprint, :user_id, :now, :now)
                ON CONFLICT (session_id) DO UPDATE
                SET user_id = :user_id, last_seen = :now
            """), {
                'session_id': session_id,
                'landing_page_id': landing_page_id,
                'fingerprint': fingerprint,
                'user_id': user_id,
                'now': datetime.now(timezone.utc)
            })
        else:
            db_connection.execute(text("""
                INSERT INTO analytics_sessions (
                    session_id, landing_page_id, browser_fingerprint, user_id,
                    first_seen, last_seen
                )
                VALUES (:session_id, :landing_page_id, :fingerprint, :user_id, :now, :now)
            """), {
                'session_id': session_id,
                'landing_page_id': landing_page_id,
                'fingerprint': fingerprint,
                'user_id': user_id,
                'now': datetime.now(timezone.utc)
            })
        db_connection.commit()

        created_sessions.append(str(session_id))

        return {
            'session_id': str(session_id),
            'fingerprint': fingerprint,
            'user_id': user_id,
            'landing_page_id': str(landing_page_id)
        }

    return _create_session


@pytest.fixture
def cleanup_auth0_test_data(db_connection):
    """Clean up test data after Auth0 webhook tests."""
    yield

    # Clean up in reverse dependency order
    db_connection.execute(text("DELETE FROM conversion_funnel WHERE funnel_stage = 'signup'"))
    db_connection.execute(text("DELETE FROM analytics_sessions WHERE browser_fingerprint LIKE 'fp%'"))
    db_connection.execute(text("DELETE FROM landing_pages WHERE slug LIKE 'test-page-%'"))
    db_connection.commit()


@pytest.fixture
def batch_analytics_sessions(db_connection, analytics_session_with_fingerprint):
    """Create multiple analytics sessions for batch testing."""
    def _create_batch(count: int):
        sessions = []
        for i in range(count):
            fingerprint = f"fp_batch_{i}"
            session = analytics_session_with_fingerprint(fingerprint)
            sessions.append(session)
        return sessions

    return _create_batch


@pytest.fixture
def count_funnel_records(db_connection):
    """Count conversion funnel records with specific criteria."""
    def _count(stage: str = None, user_id: str = None, session_id: str = None):
        query = "SELECT COUNT(*) FROM conversion_funnel WHERE 1=1"
        params = {}

        if stage:
            query += " AND funnel_stage = :stage"
            params['stage'] = stage

        if user_id:
            query += " AND user_id = :user_id"
            params['user_id'] = user_id

        if session_id:
            query += " AND session_id = :session_id"
            params['session_id'] = session_id

        result = db_connection.execute(text(query), params).fetchone()
        return result[0] if result else 0

    return _count


@pytest.fixture
def get_session_user_id(db_connection):
    """Get the user_id for a session with given fingerprint."""
    def _get(fingerprint: str):
        result = db_connection.execute(text("""
            SELECT user_id FROM analytics_sessions
            WHERE browser_fingerprint = :fingerprint
        """), {'fingerprint': fingerprint}).fetchone()

        return result[0] if result and result[0] else None

    return _get


@pytest.fixture
def get_funnel_record(db_connection):
    """Get funnel record details."""
    def _get(user_id: str = None, session_id: str = None, stage: str = 'signup'):
        query = "SELECT * FROM conversion_funnel WHERE funnel_stage = :stage"
        params = {'stage': stage}

        if user_id:
            query += " AND user_id = :user_id"
            params['user_id'] = user_id

        if session_id:
            query += " AND session_id = :session_id"
            params['session_id'] = session_id

        result = db_connection.execute(text(query), params).fetchone()

        if result:
            return {
                'id': result[0],
                'session_id': result[1],
                'user_id': result[2],
                'funnel_stage': result[3],
                'landing_page_id': result[4],
                'data': result[5],
                'created': result[6]
            }
        return None

    return _get
