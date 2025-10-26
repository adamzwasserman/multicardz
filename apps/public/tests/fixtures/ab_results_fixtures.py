"""
Fixtures for A/B test results calculation tests.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta, UTC
from sqlalchemy import text


@pytest.fixture
def ab_test_with_data(db_session):
    """Create an A/B test with sample data for results calculation."""
    # Create landing pages first
    page_a_id = uuid4()
    page_b_id = uuid4()

    db_session.execute(
        text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
            VALUES
                (:id_a, 'variant-a', 'REPLACEMENT', 'Variant A', 'Headline A', true, now(), now()),
                (:id_b, 'variant-b', 'REPLACEMENT', 'Variant B', 'Headline B', true, now(), now())
        """),
        {'id_a': page_a_id, 'id_b': page_b_id}
    )

    # Create A/B test
    test_id = uuid4()
    db_session.execute(
        text("""
            INSERT INTO a_b_tests (id, name, description, is_active, traffic_split, start_date, created, modified)
            VALUES (:id, 'Test Conversion', 'Testing conversion rates', true, '{"A": 50, "B": 50}'::jsonb, now(), now(), now())
        """),
        {'id': test_id}
    )

    # Create variants
    variant_a_id = uuid4()
    variant_b_id = uuid4()

    db_session.execute(
        text("""
            INSERT INTO a_b_test_variants (id, a_b_test_id, variant_name, landing_page_id, weight, created)
            VALUES
                (:id_a, :test_id, 'A', :page_a, 50, now()),
                (:id_b, :test_id, 'B', :page_b, 50, now())
        """),
        {
            'id_a': variant_a_id,
            'id_b': variant_b_id,
            'test_id': test_id,
            'page_a': page_a_id,
            'page_b': page_b_id
        }
    )

    db_session.commit()

    return {
        'test_id': test_id,
        'variant_a_id': variant_a_id,
        'variant_b_id': variant_b_id,
        'page_a_id': page_a_id,
        'page_b_id': page_b_id
    }


@pytest.fixture
def cleanup_ab_test_data(db_session):
    """Clean up A/B test data after each test."""
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


def create_session_with_conversion(
    db_session,
    variant_id,
    page_id,
    has_conversion=False,
    conversion_time_minutes=5
):
    """Helper to create a session with optional conversion."""
    session_id = uuid4()

    # Create session
    db_session.execute(
        text("""
            INSERT INTO analytics_sessions
            (session_id, a_b_variant_id, landing_page_id, first_seen, last_seen)
            VALUES (:sid, :vid, :pid, now(), now())
        """),
        {'sid': session_id, 'vid': variant_id, 'pid': page_id}
    )

    # Create funnel entry for view
    db_session.execute(
        text("""
            INSERT INTO conversion_funnel
            (session_id, landing_page_id, funnel_stage, created)
            VALUES (:sid, :pid, 'view', now())
        """),
        {'sid': session_id, 'pid': page_id}
    )

    if has_conversion:
        # Create conversion event (upgrade stage)
        conversion_time = datetime.now(UTC) + timedelta(minutes=conversion_time_minutes)
        db_session.execute(
            text("""
                INSERT INTO conversion_funnel
                (session_id, landing_page_id, funnel_stage, created)
                VALUES (:sid, :pid, 'upgrade', :created)
            """),
            {'sid': session_id, 'pid': page_id, 'created': conversion_time}
        )

    db_session.commit()
    return session_id
