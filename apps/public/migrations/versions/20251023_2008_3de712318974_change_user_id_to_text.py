"""change_user_id_to_text

Revision ID: 3de712318974
Revises: 4fef33252c0a
Create Date: 2025-10-23 20:08:46.008867+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '3de712318974'
down_revision = '4fef33252c0a'
branch_labels = None
depends_on = None


def upgrade():
    """
    Change user_id from UUID to Text to support Auth0 user IDs.

    Auth0 user IDs are strings like "auth0|user123", not UUIDs.
    """
    # Change user_id in analytics_sessions from UUID to Text
    op.alter_column(
        'analytics_sessions',
        'user_id',
        type_=sa.Text(),
        existing_type=UUID(as_uuid=True),
        nullable=True
    )

    # Change user_id in conversion_funnel from UUID to Text
    op.alter_column(
        'conversion_funnel',
        'user_id',
        type_=sa.Text(),
        existing_type=UUID(as_uuid=True),
        nullable=True
    )


def downgrade():
    """Revert user_id back to UUID type."""
    # Revert conversion_funnel user_id to UUID
    op.alter_column(
        'conversion_funnel',
        'user_id',
        type_=UUID(as_uuid=True),
        existing_type=sa.Text(),
        nullable=True
    )

    # Revert analytics_sessions user_id to UUID
    op.alter_column(
        'analytics_sessions',
        'user_id',
        type_=UUID(as_uuid=True),
        existing_type=sa.Text(),
        nullable=True
    )
