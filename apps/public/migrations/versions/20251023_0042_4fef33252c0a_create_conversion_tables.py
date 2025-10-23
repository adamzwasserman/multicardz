"""create_conversion_tables

Revision ID: 4fef33252c0a
Revises: 8dc6d9c14aea
Create Date: 2025-10-23 00:42:43.959653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '4fef33252c0a'
down_revision: Union[str, None] = '8dc6d9c14aea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create conversion funnel and A/B testing tables.

    Tables created:
    - conversion_funnel: Track user progression through conversion stages
    - a_b_tests: A/B test configuration
    - a_b_test_variants: Variant definitions with traffic_percentage
    - analytics_heatmap_data: Pre-aggregated click data in 10px buckets
    """

    # Create conversion_funnel table
    op.create_table(
        'conversion_funnel',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('analytics_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('funnel_stage', sa.Text(), nullable=False),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id'), nullable=True),
        sa.Column('data', JSONB(), nullable=True),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Indexes for conversion_funnel
    op.create_index('idx_funnel_session', 'conversion_funnel', ['session_id'])
    op.create_index(
        'idx_funnel_user',
        'conversion_funnel',
        ['user_id'],
        postgresql_where=sa.text('user_id IS NOT NULL')
    )
    op.create_index(
        'idx_funnel_stage',
        'conversion_funnel',
        ['funnel_stage', sa.text('created DESC')],
        postgresql_using='btree'
    )
    op.create_index('idx_funnel_page', 'conversion_funnel', ['landing_page_id'])

    # Create a_b_tests table
    op.create_table(
        'a_b_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('traffic_split', JSONB(), nullable=False),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('modified', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Indexes for a_b_tests
    op.create_index(
        'idx_ab_tests_active',
        'a_b_tests',
        ['is_active'],
        postgresql_where=sa.text('is_active = true')
    )

    # Create a_b_test_variants table
    op.create_table(
        'a_b_test_variants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('a_b_test_id', UUID(as_uuid=True), sa.ForeignKey('a_b_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variant_name', sa.Text(), nullable=False),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id'), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=False, default=50),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Unique constraint for a_b_test_variants
    op.create_unique_constraint(
        'uq_ab_test_variant',
        'a_b_test_variants',
        ['a_b_test_id', 'variant_name']
    )

    # Indexes for a_b_test_variants
    op.create_index('idx_variants_test', 'a_b_test_variants', ['a_b_test_id'])

    # Add foreign key from analytics_sessions to a_b_test_variants (now that table exists)
    op.create_foreign_key(
        'fk_sessions_variant',
        'analytics_sessions',
        'a_b_test_variants',
        ['a_b_variant_id'],
        ['id']
    )

    # Create analytics_heatmap_data table
    op.create_table(
        'analytics_heatmap_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('viewport_bucket', sa.Text(), nullable=False),
        sa.Column('x_bucket', sa.Integer(), nullable=False),
        sa.Column('y_bucket', sa.Integer(), nullable=False),
        sa.Column('click_count', sa.Integer(), default=0, nullable=False),
        sa.Column('hover_duration_ms', sa.BigInteger(), default=0, nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Unique constraint for heatmap buckets
    op.create_unique_constraint(
        'uq_heatmap_bucket',
        'analytics_heatmap_data',
        ['landing_page_id', 'viewport_bucket', 'x_bucket', 'y_bucket']
    )

    # Indexes for analytics_heatmap_data
    op.create_index(
        'idx_heatmap_page',
        'analytics_heatmap_data',
        ['landing_page_id', 'viewport_bucket']
    )


def downgrade() -> None:
    """Drop conversion and A/B testing tables."""
    # Drop foreign key first
    op.drop_constraint('fk_sessions_variant', 'analytics_sessions', type_='foreignkey')

    # Drop tables in reverse order
    op.drop_table('analytics_heatmap_data')
    op.drop_table('a_b_test_variants')
    op.drop_table('a_b_tests')
    op.drop_table('conversion_funnel')
