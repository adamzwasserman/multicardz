"""
Funnel stage tracking and analytics service.

Provides comprehensive funnel analytics to track user progression through
conversion stages: landing → signup → first_card → upgrade.

Pure function-based service (0 classes, 6 functions):
- get_overall_funnel_metrics() - Stage counts, conversion rates, duration stats
- get_user_funnel_progression() - Individual user journey through funnel
- get_funnel_dropoff_analysis() - Drop-off percentages between stages
- get_average_stage_durations() - Average time between funnel stages
- get_funnel_cohort_analysis() - Cohort analysis by signup date
- get_funnel_by_landing_page() - Funnel performance by landing page
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_overall_funnel_metrics(db: Session) -> Dict[str, Any]:
    """
    Get overall funnel metrics across all stages.

    Returns aggregated counts, conversion rates, and duration statistics
    for the entire conversion funnel.

    Args:
        db: Database session

    Returns:
        dict with 'stages', 'conversion_rates', 'average_durations'
    """
    # Get stage counts
    result = db.execute(text("""
        SELECT
            funnel_stage,
            COUNT(DISTINCT COALESCE(user_id, session_id::text, id::text)) as count
        FROM conversion_funnel
        GROUP BY funnel_stage
        ORDER BY
            CASE funnel_stage
                WHEN 'landing' THEN 1
                WHEN 'signup' THEN 2
                WHEN 'first_card' THEN 3
                WHEN 'upgrade' THEN 4
                ELSE 5
            END
    """)).fetchall()

    stages = {row[0]: row[1] for row in result}

    # Calculate conversion rates
    conversion_rates = {}
    if stages.get('landing', 0) > 0:
        conversion_rates['landing_to_signup'] = (
            (stages.get('signup', 0) / stages['landing']) * 100
        )
    if stages.get('signup', 0) > 0:
        conversion_rates['signup_to_first_card'] = (
            (stages.get('first_card', 0) / stages['signup']) * 100
        )
    if stages.get('first_card', 0) > 0:
        conversion_rates['first_card_to_upgrade'] = (
            (stages.get('upgrade', 0) / stages['first_card']) * 100
        )

    # Get average durations between stages
    duration_result = db.execute(text("""
        WITH user_stages AS (
            SELECT
                COALESCE(user_id, session_id::text) as user_key,
                funnel_stage,
                MIN(created) as stage_time
            FROM conversion_funnel
            GROUP BY COALESCE(user_id, session_id::text), funnel_stage
        ),
        stage_pairs AS (
            SELECT
                l.user_key,
                l.stage_time as landing_time,
                s.stage_time as signup_time,
                f.stage_time as first_card_time,
                u.stage_time as upgrade_time
            FROM user_stages l
            LEFT JOIN user_stages s ON l.user_key = s.user_key AND s.funnel_stage = 'signup'
            LEFT JOIN user_stages f ON l.user_key = f.user_key AND f.funnel_stage = 'first_card'
            LEFT JOIN user_stages u ON l.user_key = u.user_key AND u.funnel_stage = 'upgrade'
            WHERE l.funnel_stage = 'landing'
        )
        SELECT
            AVG(EXTRACT(EPOCH FROM (signup_time - landing_time))) as avg_landing_to_signup,
            AVG(EXTRACT(EPOCH FROM (first_card_time - signup_time))) as avg_signup_to_first_card,
            AVG(EXTRACT(EPOCH FROM (upgrade_time - first_card_time))) as avg_first_card_to_upgrade
        FROM stage_pairs
        WHERE signup_time IS NOT NULL
    """)).fetchone()

    average_durations = {}
    if duration_result and duration_result[0]:
        average_durations['landing_to_signup_seconds'] = float(duration_result[0] or 0)
        average_durations['signup_to_first_card_seconds'] = float(duration_result[1] or 0)
        average_durations['first_card_to_upgrade_seconds'] = float(duration_result[2] or 0)

    return {
        'stages': stages,
        'conversion_rates': conversion_rates,
        'average_durations': average_durations
    }


def get_user_funnel_progression(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get funnel progression for a specific user.

    Shows all stages the user has completed with timestamps and
    time between each stage.

    Args:
        db: Database session
        user_id: User ID to analyze

    Returns:
        dict with 'user_id', 'stages', 'stage_durations'
    """
    # Get all stages for user
    result = db.execute(text("""
        SELECT
            funnel_stage as stage,
            created as timestamp,
            data
        FROM conversion_funnel
        WHERE user_id = :user_id
        ORDER BY created ASC
    """), {'user_id': user_id}).fetchall()

    stages = []
    for row in result:
        stages.append({
            'stage': row[0],
            'timestamp': row[1].isoformat() if row[1] else None,
            'created': row[1].isoformat() if row[1] else None
        })

    # Calculate time between stages
    stage_durations = {}
    if len(stages) >= 2:
        for i in range(len(stages) - 1):
            current_stage = stages[i]['stage']
            next_stage = stages[i + 1]['stage']
            current_time = datetime.fromisoformat(stages[i]['timestamp'])
            next_time = datetime.fromisoformat(stages[i + 1]['timestamp'])
            duration_seconds = (next_time - current_time).total_seconds()
            stage_durations[f"{current_stage}_to_{next_stage}"] = duration_seconds

    return {
        'user_id': user_id,
        'stages': stages,
        'stage_durations': stage_durations,
        'time_between_stages': stage_durations  # Alias for compatibility
    }


def get_funnel_dropoff_analysis(db: Session) -> Dict[str, Any]:
    """
    Analyze drop-off rates between funnel stages.

    Calculates the percentage of users who drop off at each stage
    transition.

    Args:
        db: Database session

    Returns:
        dict with drop-off rates for each stage transition
    """
    # Get counts for each stage
    result = db.execute(text("""
        SELECT
            funnel_stage,
            COUNT(DISTINCT COALESCE(user_id, session_id::text, id::text)) as count
        FROM conversion_funnel
        GROUP BY funnel_stage
    """)).fetchall()

    stage_counts = {row[0]: row[1] for row in result}

    # Calculate drop-off rates
    dropoff_analysis = {}

    # Landing to Signup
    landing_count = stage_counts.get('landing', 0)
    signup_count = stage_counts.get('signup', 0)
    if landing_count > 0:
        dropoff_rate = ((landing_count - signup_count) / landing_count) * 100
        dropoff_analysis['landing_to_signup'] = {
            'entered': landing_count,
            'progressed': signup_count,
            'dropped_off': landing_count - signup_count,
            'dropoff_rate': dropoff_rate
        }

    # Signup to First Card
    first_card_count = stage_counts.get('first_card', 0)
    if signup_count > 0:
        dropoff_rate = ((signup_count - first_card_count) / signup_count) * 100
        dropoff_analysis['signup_to_first_card'] = {
            'entered': signup_count,
            'progressed': first_card_count,
            'dropped_off': signup_count - first_card_count,
            'dropoff_rate': dropoff_rate
        }

    # First Card to Upgrade
    upgrade_count = stage_counts.get('upgrade', 0)
    if first_card_count > 0:
        dropoff_rate = ((first_card_count - upgrade_count) / first_card_count) * 100
        dropoff_analysis['first_card_to_upgrade'] = {
            'entered': first_card_count,
            'progressed': upgrade_count,
            'dropped_off': first_card_count - upgrade_count,
            'dropoff_rate': dropoff_rate
        }

    return dropoff_analysis


def get_average_stage_durations(db: Session) -> Dict[str, Any]:
    """
    Calculate average time users spend between funnel stages.

    Args:
        db: Database session

    Returns:
        dict with average seconds for each stage transition
    """
    result = db.execute(text("""
        WITH user_stages AS (
            SELECT
                COALESCE(user_id, session_id::text) as user_key,
                funnel_stage,
                MIN(created) as stage_time
            FROM conversion_funnel
            GROUP BY COALESCE(user_id, session_id::text), funnel_stage
        ),
        durations AS (
            SELECT
                EXTRACT(EPOCH FROM (s.stage_time - l.stage_time)) as landing_to_signup,
                EXTRACT(EPOCH FROM (f.stage_time - s.stage_time)) as signup_to_first_card,
                EXTRACT(EPOCH FROM (u.stage_time - f.stage_time)) as first_card_to_upgrade
            FROM user_stages l
            LEFT JOIN user_stages s ON l.user_key = s.user_key AND s.funnel_stage = 'signup'
            LEFT JOIN user_stages f ON l.user_key = f.user_key AND f.funnel_stage = 'first_card'
            LEFT JOIN user_stages u ON l.user_key = u.user_key AND u.funnel_stage = 'upgrade'
            WHERE l.funnel_stage = 'landing'
        )
        SELECT
            AVG(landing_to_signup) FILTER (WHERE landing_to_signup IS NOT NULL) as avg_landing_to_signup,
            AVG(signup_to_first_card) FILTER (WHERE signup_to_first_card IS NOT NULL) as avg_signup_to_first_card,
            AVG(first_card_to_upgrade) FILTER (WHERE first_card_to_upgrade IS NOT NULL) as avg_first_card_to_upgrade
        FROM durations
    """)).fetchone()

    durations = {}
    if result:
        durations['landing_to_signup'] = {
            'avg_seconds': float(result[0]) if result[0] else 0
        }
        durations['signup_to_first_card'] = {
            'avg_seconds': float(result[1]) if result[1] else 0
        }
        durations['first_card_to_upgrade'] = {
            'avg_seconds': float(result[2]) if result[2] else 0
        }

    return durations


def get_funnel_cohort_analysis(db: Session, cohort_date: str) -> Dict[str, Any]:
    """
    Analyze funnel performance for a specific cohort by signup date.

    Args:
        db: Database session
        cohort_date: Date string (YYYY-MM-DD) for cohort analysis

    Returns:
        dict with cohort conversion metrics
    """
    result = db.execute(text("""
        WITH cohort_users AS (
            SELECT DISTINCT
                COALESCE(user_id, session_id::text) as user_key
            FROM conversion_funnel
            WHERE funnel_stage = 'landing'
              AND DATE(created) = :cohort_date
        ),
        cohort_stages AS (
            SELECT
                cu.user_key,
                cf.funnel_stage
            FROM cohort_users cu
            LEFT JOIN conversion_funnel cf
                ON COALESCE(cf.user_id, cf.session_id::text) = cu.user_key
        )
        SELECT
            COUNT(DISTINCT user_key) as total_users,
            COUNT(DISTINCT CASE WHEN funnel_stage = 'signup' THEN user_key END) as signups,
            COUNT(DISTINCT CASE WHEN funnel_stage = 'first_card' THEN user_key END) as first_cards,
            COUNT(DISTINCT CASE WHEN funnel_stage = 'upgrade' THEN user_key END) as upgrades
        FROM cohort_stages
    """), {'cohort_date': cohort_date}).fetchone()

    if not result or result[0] == 0:
        return {
            'cohort_date': cohort_date,
            'total_users': 0,
            'signup_conversion_rate': 0,
            'first_card_conversion_rate': 0,
            'upgrade_conversion_rate': 0
        }

    total_users = result[0]
    signups = result[1] or 0
    first_cards = result[2] or 0
    upgrades = result[3] or 0

    return {
        'cohort_date': cohort_date,
        'total_users': total_users,
        'signups': signups,
        'first_cards': first_cards,
        'upgrades': upgrades,
        'signup_conversion_rate': (signups / total_users * 100) if total_users > 0 else 0,
        'first_card_conversion_rate': (first_cards / total_users * 100) if total_users > 0 else 0,
        'upgrade_conversion_rate': (upgrades / total_users * 100) if total_users > 0 else 0
    }


def get_funnel_by_landing_page(db: Session) -> List[Dict[str, Any]]:
    """
    Analyze funnel performance by landing page.

    Returns conversion rates for each landing page, sorted by
    conversion rate (best performing first).

    Args:
        db: Database session

    Returns:
        list of dicts with landing page performance metrics
    """
    result = db.execute(text("""
        WITH page_funnel AS (
            SELECT
                lp.id as landing_page_id,
                lp.slug as page_slug,
                lp.name as page_name,
                COALESCE(cf.user_id, cf.session_id::text) as user_key,
                cf.funnel_stage
            FROM landing_pages lp
            LEFT JOIN conversion_funnel cf ON lp.id = cf.landing_page_id
            WHERE lp.is_active = true
        )
        SELECT
            landing_page_id,
            page_slug,
            page_name,
            COUNT(DISTINCT CASE WHEN funnel_stage = 'landing' THEN user_key END) as landings,
            COUNT(DISTINCT CASE WHEN funnel_stage = 'signup' THEN user_key END) as signups,
            CASE
                WHEN COUNT(DISTINCT CASE WHEN funnel_stage = 'landing' THEN user_key END) > 0
                THEN (COUNT(DISTINCT CASE WHEN funnel_stage = 'signup' THEN user_key END)::float /
                      COUNT(DISTINCT CASE WHEN funnel_stage = 'landing' THEN user_key END) * 100)
                ELSE 0
            END as conversion_rate
        FROM page_funnel
        GROUP BY landing_page_id, page_slug, page_name
        HAVING COUNT(DISTINCT CASE WHEN funnel_stage = 'landing' THEN user_key END) > 0
        ORDER BY conversion_rate DESC
    """)).fetchall()

    pages = []
    for row in result:
        pages.append({
            'landing_page_id': str(row[0]),
            'page_slug': row[1],
            'page_name': row[2],
            'landings': row[3],
            'signups': row[4],
            'conversion_rate': float(row[5])
        })

    return pages
