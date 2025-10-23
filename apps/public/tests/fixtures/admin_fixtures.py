"""
Fixtures for admin dashboard tests.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta, UTC
from sqlalchemy import text


@pytest.fixture
def analytics_sample_data(db_session):
    """Create sample analytics data for dashboard testing."""
    # Create landing pages
    page_ids = [uuid4(), uuid4(), uuid4()]

    for i, page_id in enumerate(page_ids):
        db_session.execute(
            text("""
                INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
                VALUES (:id, :slug, 'REPLACEMENT', :name, :headline, true, now(), now())
            """),
            {
                'id': page_id,
                'slug': f'page-{i+1}',
                'name': f'Landing Page {i+1}',
                'headline': f'Headline {i+1}'
            }
        )

    # Create sessions with various sources
    session_ids = []
    sources = [
        {'referrer_url': None, 'referrer_domain': None},  # Direct
        {'referrer_url': 'https://google.com/search?q=multicardz', 'referrer_domain': 'google.com'},  # Organic
        {'referrer_url': 'https://facebook.com', 'referrer_domain': 'facebook.com'},  # Social
        {'referrer_url': 'https://example.com/article', 'referrer_domain': 'example.com'},  # Referral
    ]

    for i in range(20):
        session_id = uuid4()
        session_ids.append(session_id)
        source = sources[i % len(sources)]
        page_id = page_ids[i % len(page_ids)]

        db_session.execute(
            text("""
                INSERT INTO analytics_sessions
                (session_id, landing_page_id, referrer_url, referrer_domain, first_seen, last_seen)
                VALUES (:sid, :pid, :ref_url, :ref_domain, :first_seen, :last_seen)
            """),
            {
                'sid': session_id,
                'pid': page_id,
                'ref_url': source['referrer_url'],
                'ref_domain': source['referrer_domain'],
                'first_seen': datetime.now(UTC) - timedelta(hours=i),
                'last_seen': datetime.now(UTC) - timedelta(hours=i) + timedelta(minutes=5)
            }
        )

        # Add page view
        db_session.execute(
            text("""
                INSERT INTO analytics_page_views
                (session_id, landing_page_id, page_url, created)
                VALUES (:sid, :pid, :url, :created)
            """),
            {
                'sid': session_id,
                'pid': page_id,
                'url': f'/page-{(i % len(page_ids)) + 1}',
                'created': datetime.now(UTC) - timedelta(hours=i)
            }
        )

        # Add funnel entry (view)
        db_session.execute(
            text("""
                INSERT INTO conversion_funnel
                (session_id, landing_page_id, funnel_stage, created)
                VALUES (:sid, :pid, 'view', :created)
            """),
            {
                'sid': session_id,
                'pid': page_id,
                'created': datetime.now(UTC) - timedelta(hours=i)
            }
        )

        # Add conversions (30% conversion rate)
        if i % 3 == 0:
            db_session.execute(
                text("""
                    INSERT INTO conversion_funnel
                    (session_id, landing_page_id, funnel_stage, created)
                    VALUES (:sid, :pid, 'upgrade', :created)
                """),
                {
                    'sid': session_id,
                    'pid': page_id,
                    'created': datetime.now(UTC) - timedelta(hours=i) + timedelta(minutes=3)
                }
            )

    db_session.commit()

    return {
        'page_ids': page_ids,
        'session_ids': session_ids,
        'total_sessions': len(session_ids),
        'total_conversions': len([i for i in range(20) if i % 3 == 0])
    }


@pytest.fixture
def cleanup_admin_data(db_session):
    """Clean up admin dashboard test data."""
    yield
    # Clean up in reverse FK dependency order
    db_session.execute(text("DELETE FROM conversion_funnel"))
    db_session.execute(text("DELETE FROM analytics_page_views"))
    db_session.execute(text("DELETE FROM analytics_events"))
    db_session.execute(text("DELETE FROM analytics_mouse_tracking"))
    db_session.execute(text("DELETE FROM analytics_sessions"))
    db_session.execute(text("DELETE FROM a_b_test_variants"))
    db_session.execute(text("DELETE FROM a_b_tests"))
    db_session.execute(text("DELETE FROM landing_page_sections"))
    db_session.execute(text("DELETE FROM landing_pages"))
    db_session.commit()
