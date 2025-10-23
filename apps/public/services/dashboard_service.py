"""
Admin Dashboard Service.

Provides functions for:
- Aggregating analytics metrics for dashboard overview
- Calculating top-performing landing pages
- Retrieving A/B test summaries
- Traffic source breakdown
"""

from typing import Any, Optional
from sqlalchemy import text


def get_dashboard_overview(db: Any, days: int = 30) -> dict:
    """
    Get dashboard overview metrics.

    Args:
        db: Database connection
        days: Number of days to look back (default: 30)

    Returns:
        dict with overview metrics:
        - total_sessions: Count of unique sessions
        - total_page_views: Count of page views
        - total_conversions: Count of upgrade conversions
        - overall_conversion_rate: Percentage (conversions / sessions * 100)
        - avg_session_duration_seconds: Average session length
        - top_landing_pages: List of top performers
        - active_ab_tests: List of active tests with results
        - traffic_sources: Breakdown by source type
    """
    # Get total sessions
    sessions = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
        """),
        {'days': days}
    ).fetchone()

    total_sessions = sessions[0] if sessions else 0

    # Get total page views
    page_views = db.execute(
        text("""
            SELECT COUNT(*)
            FROM analytics_page_views
            WHERE created >= now() - interval ':days days'
        """),
        {'days': days}
    ).fetchone()

    total_page_views = page_views[0] if page_views else 0

    # Get total conversions (upgrade stage)
    conversions = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM conversion_funnel
            WHERE funnel_stage = 'upgrade'
            AND created >= now() - interval ':days days'
        """),
        {'days': days}
    ).fetchone()

    total_conversions = conversions[0] if conversions else 0

    # Calculate overall conversion rate
    overall_conversion_rate = (total_conversions / total_sessions * 100) if total_sessions > 0 else 0.0

    # Calculate average session duration
    avg_duration = db.execute(
        text("""
            SELECT AVG(EXTRACT(EPOCH FROM (last_seen - first_seen)))
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
            AND last_seen > first_seen
        """),
        {'days': days}
    ).fetchone()

    avg_session_duration_seconds = float(avg_duration[0]) if avg_duration and avg_duration[0] else 0.0

    # Get top landing pages
    top_landing_pages = get_top_landing_pages(db, days, limit=10)

    # Get active A/B tests
    active_ab_tests = get_active_ab_tests_summary(db)

    # Get traffic source breakdown
    traffic_sources = get_traffic_source_breakdown(db, days)

    return {
        'total_sessions': total_sessions,
        'total_page_views': total_page_views,
        'total_conversions': total_conversions,
        'overall_conversion_rate': round(overall_conversion_rate, 2),
        'avg_session_duration_seconds': round(avg_session_duration_seconds, 2),
        'top_landing_pages': top_landing_pages,
        'active_ab_tests': active_ab_tests,
        'traffic_sources': traffic_sources,
        'lookback_days': days
    }


def get_top_landing_pages(db: Any, days: int = 30, limit: int = 10) -> list:
    """
    Get top-performing landing pages ranked by conversion rate.

    Args:
        db: Database connection
        days: Number of days to look back
        limit: Maximum number of results to return

    Returns:
        List of landing page dicts with:
        - landing_page_id: UUID
        - page_name: Landing page name
        - slug: Landing page slug
        - sessions_count: Number of sessions
        - conversions_count: Number of conversions
        - conversion_rate: Percentage
    """
    results = db.execute(
        text("""
            SELECT
                lp.id as landing_page_id,
                lp.name as page_name,
                lp.slug,
                COUNT(DISTINCT s.session_id) as sessions_count,
                COUNT(DISTINCT CASE WHEN cf.funnel_stage = 'upgrade' THEN cf.session_id END) as conversions_count,
                CASE
                    WHEN COUNT(DISTINCT s.session_id) > 0
                    THEN (COUNT(DISTINCT CASE WHEN cf.funnel_stage = 'upgrade' THEN cf.session_id END)::float / COUNT(DISTINCT s.session_id) * 100)
                    ELSE 0
                END as conversion_rate
            FROM landing_pages lp
            LEFT JOIN analytics_sessions s ON lp.id = s.landing_page_id
                AND s.first_seen >= now() - interval ':days days'
            LEFT JOIN conversion_funnel cf ON s.session_id = cf.session_id
            WHERE lp.is_active = true
            GROUP BY lp.id, lp.name, lp.slug
            HAVING COUNT(DISTINCT s.session_id) > 0
            ORDER BY conversion_rate DESC, sessions_count DESC
            LIMIT :limit
        """),
        {'days': days, 'limit': limit}
    ).fetchall()

    return [
        {
            'landing_page_id': str(row[0]),
            'page_name': row[1],
            'slug': row[2],
            'sessions_count': row[3],
            'conversions_count': row[4],
            'conversion_rate': round(float(row[5]), 2)
        }
        for row in results
    ]


def get_active_ab_tests_summary(db: Any) -> list:
    """
    Get summary of active A/B tests with results.

    Args:
        db: Database connection

    Returns:
        List of A/B test dicts with:
        - test_id: UUID
        - test_name: Test name
        - leading_variant: Variant with highest conversion rate
        - is_significant: Whether results are statistically significant
        - sessions_count: Total sessions across all variants
    """
    # Get active tests
    tests = db.execute(
        text("""
            SELECT id, name
            FROM a_b_tests
            WHERE is_active = true
            AND (end_date IS NULL OR end_date > now())
            ORDER BY start_date DESC
            LIMIT 10
        """)
    ).fetchall()

    results = []
    for test in tests:
        test_id = test[0]
        test_name = test[1]

        # Get session count for this test
        sessions = db.execute(
            text("""
                SELECT COUNT(DISTINCT s.session_id)
                FROM analytics_sessions s
                JOIN a_b_test_variants v ON s.a_b_variant_id = v.id
                WHERE v.a_b_test_id = :test_id
            """),
            {'test_id': test_id}
        ).fetchone()

        sessions_count = sessions[0] if sessions else 0

        # Calculate results (simplified - full calculation in ab_test_service)
        from services.ab_test_service import calculate_ab_test_results

        test_results = calculate_ab_test_results(test_id, db)

        results.append({
            'test_id': str(test_id),
            'test_name': test_name,
            'leading_variant': test_results.get('leading_variant'),
            'is_significant': test_results.get('statistical_significance', {}).get('is_significant', False),
            'sessions_count': sessions_count
        })

    return results


def get_traffic_source_breakdown(db: Any, days: int = 30) -> dict:
    """
    Get traffic source breakdown.

    Args:
        db: Database connection
        days: Number of days to look back

    Returns:
        dict with traffic source percentages:
        - direct: % of sessions with no referrer
        - organic_search: % from search engines
        - referral: % from other websites
        - social: % from social media
        - other: % from other sources
    """
    # Get total sessions
    total = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
        """),
        {'days': days}
    ).fetchone()

    total_sessions = total[0] if total else 0

    if total_sessions == 0:
        return {
            'direct': 0,
            'organic_search': 0,
            'referral': 0,
            'social': 0,
            'other': 0
        }

    # Get direct traffic (no referrer or self-referrer)
    direct = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
            AND (referrer_url IS NULL OR referrer_url = '' OR referrer_domain = 'multicardz.com')
        """),
        {'days': days}
    ).fetchone()

    direct_count = direct[0] if direct else 0

    # Get organic search (common search engines)
    organic = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
            AND referrer_domain IN ('google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com', 'baidu.com', 'yandex.com', 'ask.com')
        """),
        {'days': days}
    ).fetchone()

    organic_count = organic[0] if organic else 0

    # Get social traffic
    social = db.execute(
        text("""
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_sessions
            WHERE first_seen >= now() - interval ':days days'
            AND referrer_domain IN ('facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'reddit.com', 'tiktok.com')
        """),
        {'days': days}
    ).fetchone()

    social_count = social[0] if social else 0

    # Calculate referral and other
    referral_count = total_sessions - direct_count - organic_count - social_count
    referral_count = max(0, referral_count)  # Ensure non-negative

    return {
        'direct': round((direct_count / total_sessions * 100), 2),
        'organic_search': round((organic_count / total_sessions * 100), 2),
        'social': round((social_count / total_sessions * 100), 2),
        'referral': round((referral_count / total_sessions * 100), 2),
        'total_sessions': total_sessions
    }
