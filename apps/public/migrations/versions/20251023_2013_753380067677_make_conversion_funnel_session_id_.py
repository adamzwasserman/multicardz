"""make_conversion_funnel_session_id_nullable

Revision ID: 753380067677
Revises: 3de712318974
Create Date: 2025-10-23 20:13:25.162896+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '753380067677'
down_revision = '3de712318974'
branch_labels = None
depends_on = None


def upgrade():
    """
    Make session_id nullable in conversion_funnel table.

    This allows tracking conversions even when there's no matching analytics session
    (e.g., user signs up from a different device/browser than where they first landed).
    """
    op.alter_column(
        'conversion_funnel',
        'session_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True
    )


def downgrade():
    """Revert session_id back to NOT NULL."""
    op.alter_column(
        'conversion_funnel',
        'session_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False
    )
