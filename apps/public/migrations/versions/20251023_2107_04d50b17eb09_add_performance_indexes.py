"""add_performance_indexes

Revision ID: 04d50b17eb09
Revises: 753380067677
Create Date: 2025-10-23 21:07:45.283888+00:00

Add critical performance indexes for frequently queried columns:
- browser_fingerprint lookups (session reconnection)
- a_b_variant_id filtering (A/B test analytics)
- funnel created timestamps (time-based queries)
- user/session funnel progression (composite indexes)
- last_seen ordering (recent session queries)

These indexes optimize the most common query patterns in the analytics
and conversion tracking services.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04d50b17eb09'
down_revision = '753380067677'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance optimization indexes."""

    # Use raw SQL with IF NOT EXISTS for idempotency
    conn = op.get_bind()

    # Index 1: browser_fingerprint for session lookup and reconnection
    # Used by: webhook_service.py - find_session_by_fingerprint()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_fingerprint
        ON analytics_sessions (browser_fingerprint)
        WHERE browser_fingerprint IS NOT NULL
    """))

    # Index 2: a_b_variant_id for A/B test filtering
    # Used by: ab_test_service.py - get_variant_performance()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_variant_id
        ON analytics_sessions (a_b_variant_id)
        WHERE a_b_variant_id IS NOT NULL
    """))

    # Index 3: conversion_funnel created DESC for time-based queries
    # Used by: funnel_service.py - get_funnel_cohort_analysis()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_funnel_created_desc
        ON conversion_funnel (created DESC)
    """))

    # Index 4: composite index for user funnel progression
    # Used by: funnel_service.py - get_user_funnel_progression()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_funnel_user_stage_created
        ON conversion_funnel (user_id, funnel_stage, created DESC)
        WHERE user_id IS NOT NULL
    """))

    # Index 5: composite index for session funnel progression
    # Used by: funnel_service.py - get_overall_funnel_metrics()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_funnel_session_stage_created
        ON conversion_funnel (session_id, funnel_stage, created DESC)
    """))

    # Index 6: last_seen DESC for recent session queries
    # Used by: webhook_service.py - find_most_recent_session_for_user()
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_last_seen_desc
        ON analytics_sessions (last_seen DESC)
    """))


def downgrade():
    """Remove performance optimization indexes."""
    op.drop_index('idx_sessions_last_seen_desc', table_name='analytics_sessions')
    op.drop_index('idx_funnel_session_stage_created', table_name='conversion_funnel')
    op.drop_index('idx_funnel_user_stage_created', table_name='conversion_funnel')
    op.drop_index('idx_funnel_created_desc', table_name='conversion_funnel')
    op.drop_index('idx_sessions_variant_id', table_name='analytics_sessions')
    op.drop_index('idx_sessions_fingerprint', table_name='analytics_sessions')
