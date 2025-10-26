"""
Fixtures for performance testing and index validation.
"""
import pytest
import time
import uuid
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List
from sqlalchemy import text


@pytest.fixture
def query_timer():
    """
    Utility fixture to measure query execution time.

    Returns function that executes query and returns (result, duration_ms).
    """
    def time_query(db: Any, query: str, params: Dict = None) -> tuple:
        start = time.perf_counter()
        result = db.execute(text(query), params or {})
        end = time.perf_counter()
        duration_ms = (end - start) * 1000
        return result, duration_ms

    return time_query


@pytest.fixture
def explain_analyzer():
    """
    Utility to analyze query execution plans.

    Returns function that checks if query uses index scan.
    """
    def analyze_plan(db: Any, query: str, params: Dict = None) -> Dict[str, Any]:
        explain_query = f"EXPLAIN (FORMAT JSON) {query}"
        result = db.execute(text(explain_query), params or {})
        plan = result.fetchone()[0]

        # Extract plan details
        plan_text = str(plan)
        uses_index = 'Index Scan' in plan_text
        uses_seq_scan = 'Seq Scan' in plan_text

        return {
            'uses_index': uses_index,
            'uses_seq_scan': uses_seq_scan,
            'plan': plan
        }

    return analyze_plan


@pytest.fixture
def bulk_analytics_sessions(db_connection):
    """
    Generate bulk analytics sessions for performance testing.

    Args:
        count: Number of sessions to create (default 10000)
        with_fingerprints_pct: Percentage with browser fingerprints (default 50)
    """
    def create_sessions(count: int = 10000, with_fingerprints_pct: int = 50) -> List[uuid.UUID]:
        # Create a test landing page first
        landing_page_id = uuid.uuid4()
        db_connection.execute(text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
            VALUES (:id, :slug, 'replacement', 'Test Page', 'Test Headline', true, now(), now())
        """), {
            'id': landing_page_id,
            'slug': f'test-performance-page-{uuid.uuid4().hex[:8]}'
        })

        session_ids = []
        batch_size = 1000

        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            values = []

            for j in range(batch_count):
                session_id = uuid.uuid4()
                session_ids.append(session_id)

                # Determine if this session should have a fingerprint
                has_fingerprint = (i + j) < (count * with_fingerprints_pct // 100)
                fingerprint = f'fp_{uuid.uuid4().hex}' if has_fingerprint else None

                first_seen = datetime.now(UTC) - timedelta(days=(i + j) % 30)

                values.append(f"""(
                    '{session_id}',
                    '{landing_page_id}',
                    'test-performance-page',
                    NULL,
                    'https://google.com',
                    'google.com',
                    'google',
                    'organic',
                    NULL,
                    NULL,
                    NULL,
                    'Mozilla/5.0',
                    '192.168.1.{(i + j) % 255}',
                    {'NULL' if not fingerprint else f"'{fingerprint}'"},
                    '{first_seen.isoformat()}',
                    '{first_seen.isoformat()}',
                    NULL
                )""")

            # Bulk insert batch
            query = f"""
                INSERT INTO analytics_sessions
                (session_id, landing_page_id, landing_page_slug, a_b_variant_id,
                 referrer_url, referrer_domain, utm_source, utm_medium, utm_campaign,
                 utm_term, utm_content, user_agent, ip_address, browser_fingerprint,
                 first_seen, last_seen, user_id)
                VALUES {','.join(values)}
            """
            db_connection.execute(text(query))
            db_connection.commit()

        return session_ids

    return create_sessions


@pytest.fixture
def bulk_funnel_records(db_connection):
    """
    Generate bulk conversion funnel records for performance testing.
    """
    def create_funnel_records(count: int = 50000) -> List[uuid.UUID]:
        # First, create enough sessions
        session_ids = []
        for _ in range(count // 4):  # Each session will have ~4 funnel stages
            session_id = uuid.uuid4()
            session_ids.append(session_id)

        # Create landing page
        landing_page_id = uuid.uuid4()
        db_connection.execute(text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, is_active, created, modified)
            VALUES (:id, :slug, 'replacement', 'Funnel Test Page', 'Test', true, now(), now())
        """), {
            'id': landing_page_id,
            'slug': f'funnel-test-{uuid.uuid4().hex[:8]}'
        })

        # Create sessions
        for session_id in session_ids:
            db_connection.execute(text("""
                INSERT INTO analytics_sessions
                (session_id, landing_page_id, landing_page_slug, referrer_url, referrer_domain,
                 user_agent, ip_address, first_seen, last_seen)
                VALUES (:sid, :lpid, :slug, 'https://google.com', 'google.com',
                        'Mozilla/5.0', '192.168.1.1', now(), now())
            """), {
                'sid': session_id,
                'lpid': landing_page_id,
                'slug': 'funnel-test'
            })

        db_connection.commit()

        # Create funnel records (4 stages per session on average)
        funnel_ids = []
        stages = ['landing', 'signup', 'first_card', 'upgrade']

        for i, session_id in enumerate(session_ids):
            # Each session progresses through 1-4 stages
            num_stages = min(4, ((i % 4) + 1))

            for stage_idx in range(num_stages):
                funnel_id = uuid.uuid4()
                funnel_ids.append(funnel_id)

                user_id = f'auth0|user{i}' if stage_idx >= 1 else None
                created = datetime.now(UTC) - timedelta(days=30 - (i % 30), minutes=stage_idx * 10)

                # Simple individual inserts
                db_connection.execute(text("""
                    INSERT INTO conversion_funnel
                    (id, session_id, user_id, funnel_stage, landing_page_id, created)
                    VALUES (:id, :session_id, :user_id, :funnel_stage, :landing_page_id, :created)
                """), {
                    'id': funnel_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'funnel_stage': stages[stage_idx],
                    'landing_page_id': landing_page_id,
                    'created': created
                })

            # Commit every 100 sessions
            if i % 100 == 0:
                db_connection.commit()

        db_connection.commit()
        return funnel_ids

    return create_funnel_records


@pytest.fixture
def index_checker():
    """
    Utility to check if specific indexes exist.
    """
    def check_index(db: Any, table_name: str, index_name: str) -> bool:
        result = db.execute(text("""
            SELECT 1 FROM pg_indexes
            WHERE tablename = :table_name
            AND indexname = :index_name
        """), {
            'table_name': table_name,
            'index_name': index_name
        })
        return result.fetchone() is not None

    return check_index


@pytest.fixture
def index_stats():
    """
    Get index statistics including size and usage.
    """
    def get_stats(db: Any, table_name: str = None) -> List[Dict[str, Any]]:
        query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
        """

        if table_name:
            query += " WHERE tablename = :table_name"

        query += " ORDER BY pg_relation_size(indexrelid) DESC"

        result = db.execute(text(query), {'table_name': table_name} if table_name else {})

        return [
            {
                'schema': row[0],
                'table': row[1],
                'index': row[2],
                'size': row[3],
                'scans': row[4],
                'tuples_read': row[5],
                'tuples_fetched': row[6]
            }
            for row in result
        ]

    return get_stats


@pytest.fixture
def cleanup_performance_data(db_connection):
    """
    Cleanup performance test data after tests complete.
    """
    yield

    # Clean up test data - rollback any failed transaction first
    try:
        db_connection.rollback()
    except Exception:
        pass

    try:
        db_connection.execute(text("""
            DELETE FROM conversion_funnel WHERE landing_page_id IN (
                SELECT id FROM landing_pages WHERE slug LIKE 'test-performance-%' OR slug LIKE 'funnel-test-%'
            )
        """))
        db_connection.execute(text("""
            DELETE FROM analytics_sessions WHERE landing_page_slug LIKE 'test-performance-%' OR landing_page_slug LIKE 'funnel-test-%'
        """))
        db_connection.execute(text("""
            DELETE FROM landing_pages WHERE slug LIKE 'test-performance-%' OR slug LIKE 'funnel-test-%'
        """))
        db_connection.commit()
    except Exception:
        db_connection.rollback()
