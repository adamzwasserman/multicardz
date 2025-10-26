"""create_ab_test_tables

Revision ID: 9f7e4a3b2c1d
Revises: 04d50b17eb09
Create Date: 2025-10-24 14:20:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '9f7e4a3b2c1d'
down_revision = '04d50b17eb09'
branch_labels = None
depends_on = None


def upgrade():
    """Create A/B testing tables."""

    # Create a_b_tests table
    op.create_table(
        'a_b_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('element_selector', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('modified', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Create indexes for a_b_tests
    op.create_index('idx_ab_tests_active', 'a_b_tests', ['is_active'])
    op.create_index('idx_ab_tests_dates', 'a_b_tests', ['start_date', 'end_date'])

    # Create a_b_test_variants table
    op.create_table(
        'a_b_test_variants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('a_b_test_id', UUID(as_uuid=True), sa.ForeignKey('a_b_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('content', JSONB(), nullable=False),
        sa.Column('traffic_allocation_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('is_control', sa.Boolean(), default=False, nullable=False),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Add check constraint for traffic allocation
    op.create_check_constraint(
        'ck_traffic_allocation',
        'a_b_test_variants',
        'traffic_allocation_percent BETWEEN 0 AND 100'
    )

    # Create indexes for a_b_test_variants
    op.create_index('idx_variants_test', 'a_b_test_variants', ['a_b_test_id'])
    op.create_index('idx_variants_control', 'a_b_test_variants', ['a_b_test_id', 'is_control'])

    # Add foreign key to analytics_sessions if not already linked
    # The column already exists from earlier migration, just ensure FK
    try:
        op.create_foreign_key(
            'fk_sessions_variant',
            'analytics_sessions',
            'a_b_test_variants',
            ['a_b_variant_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # FK might already exist
        pass


def downgrade():
    """Drop A/B testing tables."""
    op.drop_table('a_b_test_variants')
    op.drop_table('a_b_tests')
