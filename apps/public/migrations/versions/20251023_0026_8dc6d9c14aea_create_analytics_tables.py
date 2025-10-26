"""create_analytics_tables

Revision ID: 8dc6d9c14aea
Revises: 25a8d12d52be
Create Date: 2025-10-23 00:26:57.494150+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB


# revision identifiers, used by Alembic.
revision = '8dc6d9c14aea'
down_revision = '25a8d12d52be'
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics tables for session tracking and event logging."""

    # Create analytics_sessions table
    op.create_table(
        'analytics_sessions',
        sa.Column('session_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id')),
        sa.Column('landing_page_slug', sa.Text()),
        sa.Column('a_b_variant_id', UUID(as_uuid=True)),  # FK added in Task 1.3
        sa.Column('referrer_url', sa.Text()),
        sa.Column('referrer_domain', sa.Text()),
        sa.Column('utm_source', sa.Text()),
        sa.Column('utm_medium', sa.Text()),
        sa.Column('utm_campaign', sa.Text()),
        sa.Column('utm_term', sa.Text()),
        sa.Column('utm_content', sa.Text()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('ip_address', INET()),
        sa.Column('browser_fingerprint', sa.Text()),
        sa.Column('first_seen', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_seen', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('user_id', UUID(as_uuid=True))  # Linked after account creation
    )

    # Indexes for analytics_sessions
    op.create_index('idx_sessions_landing_page', 'analytics_sessions', ['landing_page_id'])
    op.create_index('idx_sessions_created', 'analytics_sessions', [sa.text('first_seen DESC')])
    op.create_index('idx_sessions_user', 'analytics_sessions', ['user_id'], postgresql_where=sa.text('user_id IS NOT NULL'))
    op.create_index('idx_sessions_referrer', 'analytics_sessions', ['referrer_domain'])
    op.create_index('idx_sessions_utm', 'analytics_sessions', ['utm_source', 'utm_medium', 'utm_campaign'])

    # Create analytics_page_views table
    op.create_table(
        'analytics_page_views',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('analytics_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id')),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('referrer', sa.Text()),
        sa.Column('duration_ms', sa.BigInteger()),
        sa.Column('scroll_depth_percent', sa.Integer()),
        sa.Column('viewport_width', sa.Integer()),
        sa.Column('viewport_height', sa.Integer()),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Add check constraint for scroll_depth_percent
    op.create_check_constraint(
        'ck_scroll_depth_percent',
        'analytics_page_views',
        'scroll_depth_percent BETWEEN 0 AND 100'
    )

    # Indexes for analytics_page_views
    op.create_index('idx_page_views_session', 'analytics_page_views', ['session_id'])
    op.create_index('idx_page_views_page', 'analytics_page_views', ['landing_page_id'])
    op.create_index('idx_page_views_created', 'analytics_page_views', [sa.text('created DESC')])

    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('analytics_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_view_id', UUID(as_uuid=True), sa.ForeignKey('analytics_page_views.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('element_selector', sa.Text()),
        sa.Column('element_text', sa.Text()),
        sa.Column('element_position_x', sa.Integer()),
        sa.Column('element_position_y', sa.Integer()),
        sa.Column('timestamp_ms', sa.BigInteger(), nullable=False),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Indexes for analytics_events
    op.create_index('idx_events_session', 'analytics_events', ['session_id'])
    op.create_index('idx_events_page_view', 'analytics_events', ['page_view_id'])
    op.create_index('idx_events_type', 'analytics_events', ['event_type'])
    op.create_index('idx_events_created', 'analytics_events', [sa.text('created DESC')])

    # Create analytics_mouse_tracking table
    op.create_table(
        'analytics_mouse_tracking',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('analytics_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_view_id', UUID(as_uuid=True), sa.ForeignKey('analytics_page_views.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp_ms', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('x', sa.Integer()),
        sa.Column('y', sa.Integer()),
        sa.Column('scroll_x', sa.Integer()),
        sa.Column('scroll_y', sa.Integer()),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Indexes for analytics_mouse_tracking
    op.create_index('idx_mouse_session', 'analytics_mouse_tracking', ['session_id'])
    op.create_index('idx_mouse_page_view', 'analytics_mouse_tracking', ['page_view_id', 'timestamp_ms'])
    op.create_index('idx_mouse_created', 'analytics_mouse_tracking', [sa.text('created DESC')])


def downgrade():
    """Drop analytics tables."""
    op.drop_table('analytics_mouse_tracking')
    op.drop_table('analytics_events')
    op.drop_table('analytics_page_views')
    op.drop_table('analytics_sessions')
