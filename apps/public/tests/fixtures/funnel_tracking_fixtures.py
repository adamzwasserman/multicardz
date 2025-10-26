"""
Fixtures for funnel tracking BDD tests.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import text


@pytest.fixture
def context():
    """Test context dictionary for storing data between steps."""
    return {}


@pytest.fixture
def test_landing_page(db_session):
    """Create a test landing page."""
    page_id = uuid4()
    db_session.execute(text("""
        INSERT INTO landing_pages (id, slug, category, name, headline, subheadline, is_active)
        VALUES (:id, :slug, :category, :name, :headline, :subheadline, :is_active)
    """), {
        'id': page_id,
        'slug': 'test-page',
        'category': 'REPLACEMENT',
        'name': 'Test Page',
        'headline': 'Test Headline',
        'subheadline': 'Test Subheadline',
        'is_active': True
    })
    db_session.commit()
    return page_id


@pytest.fixture
def analytics_sessions_with_funnel(db_session, test_landing_page):
    """Create analytics sessions with various funnel stages."""
    sessions = []
    now = datetime.now(timezone.utc)

    # Create 10 sessions with different funnel progressions
    for i in range(10):
        session_id = uuid4()
        user_id = f"auth0|user{i}" if i < 5 else None

        # Create session
        db_session.execute(text("""
            INSERT INTO analytics_sessions
            (session_id, browser_fingerprint, user_id, first_seen, last_seen)
            VALUES (:session_id, :fingerprint, :user_id, :first_seen, :last_seen)
        """), {
            'session_id': session_id,
            'fingerprint': f"fingerprint_{i}",
            'user_id': user_id,
            'first_seen': now - timedelta(hours=i),
            'last_seen': now - timedelta(hours=i)
        })

        # Everyone hits landing page
        db_session.execute(text("""
            INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, landing_page_id, created)
            VALUES (:id, :session_id, :user_id, 'landing', :page_id, :created)
        """), {
            'id': uuid4(),
            'session_id': session_id,
            'user_id': user_id,
            'page_id': test_landing_page,
            'created': now - timedelta(hours=i)
        })

        # 70% sign up
        if i < 7:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'signup', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(minutes=5)
            })

        # 50% create first card (of those who signed up)
        if i < 4:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'first_card', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(minutes=30)
            })

        # 25% upgrade (of those who created first card)
        if i < 2:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'upgrade', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(hours=2)
            })

        sessions.append({
            'session_id': session_id,
            'user_id': user_id,
            'fingerprint': f"fingerprint_{i}"
        })

    db_session.commit()
    return sessions


@pytest.fixture
def user_with_complete_funnel(db_session, test_landing_page):
    """Create a user who completed all funnel stages."""
    session_id = uuid4()
    user_id = "auth0|user123"
    now = datetime.now(timezone.utc)

    # Create session
    db_session.execute(text("""
        INSERT INTO analytics_sessions
        (session_id, browser_fingerprint, user_id, first_seen, last_seen)
        VALUES (:session_id, :fingerprint, :user_id, :first_seen, :last_seen)
    """), {
        'session_id': session_id,
        'fingerprint': "fingerprint_complete",
        'user_id': user_id,
        'first_seen': now - timedelta(hours=48),
        'last_seen': now
    })

    # Add all funnel stages with known timestamps
    stages = [
        ('landing', now - timedelta(hours=48)),
        ('signup', now - timedelta(hours=47, minutes=50)),  # 10 min after landing
        ('first_card', now - timedelta(hours=46)),  # 2 hours after signup
        ('upgrade', now - timedelta(hours=24))  # 24 hours after first card
    ]

    for stage, created_at in stages:
        db_session.execute(text("""
            INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, landing_page_id, created)
            VALUES (:id, :session_id, :user_id, :stage, :page_id, :created)
        """), {
            'id': uuid4(),
            'session_id': session_id,
            'user_id': user_id,
            'stage': stage,
            'page_id': test_landing_page if stage == 'landing' else None,
            'created': created_at
        })

    db_session.commit()
    return {
        'session_id': session_id,
        'user_id': user_id,
        'stages': stages
    }


@pytest.fixture
def funnel_sessions_by_count(db_session, test_landing_page):
    """Create exact number of sessions at each funnel stage for drop-off analysis."""
    now = datetime.now(timezone.utc)
    sessions_created = {'landing': 0, 'signup': 0, 'first_card': 0, 'upgrade': 0}

    # Create 100 landing sessions
    for i in range(100):
        session_id = uuid4()
        user_id = f"auth0|dropoff_{i}" if i < 60 else None

        db_session.execute(text("""
            INSERT INTO analytics_sessions
            (session_id, browser_fingerprint, user_id, first_seen, last_seen)
            VALUES (:session_id, :fingerprint, :user_id, :first_seen, :last_seen)
        """), {
            'session_id': session_id,
            'fingerprint': f"fingerprint_dropoff_{i}",
            'user_id': user_id,
            'first_seen': now - timedelta(hours=i),
            'last_seen': now - timedelta(hours=i)
        })

        # Landing stage - all 100
        db_session.execute(text("""
            INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, landing_page_id, created)
            VALUES (:id, :session_id, :user_id, 'landing', :page_id, :created)
        """), {
            'id': uuid4(),
            'session_id': session_id,
            'user_id': user_id,
            'page_id': test_landing_page,
            'created': now - timedelta(hours=i)
        })
        sessions_created['landing'] += 1

        # Signup - 60 sessions
        if i < 60:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'signup', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(minutes=10)
            })
            sessions_created['signup'] += 1

        # First card - 40 sessions
        if i < 40:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'first_card', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(hours=1)
            })
            sessions_created['first_card'] += 1

        # Upgrade - 20 sessions
        if i < 20:
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                VALUES (:id, :session_id, :user_id, 'upgrade', :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'created': now - timedelta(hours=i) + timedelta(hours=24)
            })
            sessions_created['upgrade'] += 1

    db_session.commit()
    return sessions_created


@pytest.fixture
def funnel_cohort_data(db_session, test_landing_page):
    """Create funnel data for cohort analysis by date."""
    base_date = datetime(2025, 10, 20, 0, 0, 0, tzinfo=timezone.utc)

    # Create cohorts for 30 days
    for day_offset in range(30):
        cohort_date = base_date + timedelta(days=day_offset)

        # Create 10 sessions per day
        for i in range(10):
            session_id = uuid4()
            user_id = f"auth0|cohort_{day_offset}_{i}"

            db_session.execute(text("""
                INSERT INTO analytics_sessions
                (session_id, browser_fingerprint, user_id, first_seen, last_seen)
                VALUES (:session_id, :fingerprint, :user_id, :first_seen, :last_seen)
            """), {
                'session_id': session_id,
                'fingerprint': f"fp_cohort_{day_offset}_{i}",
                'user_id': user_id,
                'first_seen': cohort_date + timedelta(hours=i),
                'last_seen': cohort_date + timedelta(hours=i)
            })

            # Landing - all 10
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, landing_page_id, created)
                VALUES (:id, :session_id, :user_id, 'landing', :page_id, :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'page_id': test_landing_page,
                'created': cohort_date + timedelta(hours=i)
            })

            # Signup - 7 out of 10
            if i < 7:
                db_session.execute(text("""
                    INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                    VALUES (:id, :session_id, :user_id, 'signup', :created)
                """), {
                    'id': uuid4(),
                    'session_id': session_id,
                    'user_id': user_id,
                    'created': cohort_date + timedelta(hours=i, minutes=15)
                })

            # First card - 5 out of 10
            if i < 5:
                db_session.execute(text("""
                    INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                    VALUES (:id, :session_id, :user_id, 'first_card', :created)
                """), {
                    'id': uuid4(),
                    'session_id': session_id,
                    'user_id': user_id,
                    'created': cohort_date + timedelta(hours=i+2)
                })

            # Upgrade - 3 out of 10
            if i < 3:
                db_session.execute(text("""
                    INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                    VALUES (:id, :session_id, :user_id, 'upgrade', :created)
                """), {
                    'id': uuid4(),
                    'session_id': session_id,
                    'user_id': user_id,
                    'created': cohort_date + timedelta(days=1)
                })

    db_session.commit()
    return {'start_date': base_date, 'days': 30}


@pytest.fixture
def multiple_landing_pages_funnel(db_session):
    """Create multiple landing pages with different conversion rates."""
    pages = []
    now = datetime.now(timezone.utc)

    page_configs = [
        {'slug': 'high-converting', 'name': 'High Converting Page', 'conversion_rate': 0.8},
        {'slug': 'medium-converting', 'name': 'Medium Converting Page', 'conversion_rate': 0.5},
        {'slug': 'low-converting', 'name': 'Low Converting Page', 'conversion_rate': 0.2}
    ]

    for config in page_configs:
        page_id = uuid4()
        db_session.execute(text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, subheadline, is_active)
            VALUES (:id, :slug, 'REPLACEMENT', :name, 'Headline', 'Subheadline', true)
        """), {
            'id': page_id,
            'slug': config['slug'],
            'name': config['name']
        })

        # Create 50 sessions per page
        for i in range(50):
            session_id = uuid4()
            user_id = f"auth0|{config['slug']}_{i}"

            db_session.execute(text("""
                INSERT INTO analytics_sessions
                (session_id, browser_fingerprint, user_id, first_seen, last_seen)
                VALUES (:session_id, :fingerprint, :user_id, :first_seen, :last_seen)
            """), {
                'session_id': session_id,
                'fingerprint': f"fp_{config['slug']}_{i}",
                'user_id': user_id,
                'first_seen': now - timedelta(hours=i),
                'last_seen': now - timedelta(hours=i)
            })

            # Landing - all 50
            db_session.execute(text("""
                INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, landing_page_id, created)
                VALUES (:id, :session_id, :user_id, 'landing', :page_id, :created)
            """), {
                'id': uuid4(),
                'session_id': session_id,
                'user_id': user_id,
                'page_id': page_id,
                'created': now - timedelta(hours=i)
            })

            # Signup - based on conversion rate
            if i < int(50 * config['conversion_rate']):
                db_session.execute(text("""
                    INSERT INTO conversion_funnel (id, session_id, user_id, funnel_stage, created)
                    VALUES (:id, :session_id, :user_id, 'signup', :created)
                """), {
                    'id': uuid4(),
                    'session_id': session_id,
                    'user_id': user_id,
                    'created': now - timedelta(hours=i) + timedelta(minutes=10)
                })

        pages.append({
            'id': page_id,
            'slug': config['slug'],
            'name': config['name'],
            'expected_conversion_rate': config['conversion_rate']
        })

    db_session.commit()
    return pages
