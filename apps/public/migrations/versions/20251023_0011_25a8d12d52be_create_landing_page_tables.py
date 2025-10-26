"""create_landing_page_tables

Revision ID: 25a8d12d52be
Revises:
Create Date: 2025-10-23 00:11:09.453984+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '25a8d12d52be'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create landing page tables."""

    # Create landing_pages table
    op.create_table(
        'landing_pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.Text(), nullable=False, unique=True),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('headline', sa.Text(), nullable=False),
        sa.Column('subheadline', sa.Text()),
        sa.Column('competitor_name', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('modified', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted', sa.TIMESTAMP(timezone=True))
    )

    # Create indexes for landing_pages
    op.create_index(
        'idx_landing_pages_slug',
        'landing_pages',
        ['slug'],
        unique=False,
        postgresql_where=sa.text('deleted IS NULL')
    )
    op.create_index(
        'idx_landing_pages_active',
        'landing_pages',
        ['is_active'],
        unique=False,
        postgresql_where=sa.text('deleted IS NULL')
    )
    op.create_index(
        'idx_landing_pages_category',
        'landing_pages',
        ['category']
    )

    # Create landing_page_sections table
    op.create_table(
        'landing_page_sections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('landing_page_id', UUID(as_uuid=True), sa.ForeignKey('landing_pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_type', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), default=0, nullable=False),
        sa.Column('data', JSONB(), nullable=False),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('modified', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()'))
    )

    # Create indexes for landing_page_sections
    op.create_index(
        'idx_sections_page',
        'landing_page_sections',
        ['landing_page_id', 'order_index']
    )
    op.create_index(
        'idx_sections_type',
        'landing_page_sections',
        ['section_type']
    )


def downgrade():
    """Drop landing page tables."""
    op.drop_table('landing_page_sections')
    op.drop_table('landing_pages')
