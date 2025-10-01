"""Initial MultiCardz database schema

Revision ID: 001
Revises:
Create Date: 2025-09-22 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    # Users table
    op.create_table('users',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=True, default=''),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.Text(), nullable=True),
        sa.Column('default_workspace_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # User sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_expires', 'user_sessions', ['expires_at'])

    # User roles table
    op.create_table('user_roles',
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('granted_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('granted_by', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role'),
        sa.CheckConstraint("role IN ('user', 'admin', 'superuser')", name='ck_user_roles_role')
    )
    op.create_index('idx_user_roles_user', 'user_roles', ['user_id'])

    # Card summaries table
    op.create_table('card_summaries',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('tags_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.Column('modified_at', sa.Text(), nullable=False),
        sa.Column('has_attachments', sa.Boolean(), nullable=True, default=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_card_summaries_tags', 'card_summaries', ['tags_json'])
    op.create_index('idx_card_summaries_modified', 'card_summaries', ['modified_at'])

    # Tags table (normalized)
    op.create_table('tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tags_name', 'tags', ['name'], unique=True)

    # Card-tag relationships
    op.create_table('card_tags',
        sa.Column('card_id', sa.Text(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['card_summaries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id']),
        sa.PrimaryKeyConstraint('card_id', 'tag_id')
    )
    op.create_index('idx_card_tags_card', 'card_tags', ['card_id'])
    op.create_index('idx_card_tags_tag', 'card_tags', ['tag_id'])

    # Card details table
    op.create_table('card_details',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True, default=''),
        sa.Column('metadata_json', sa.Text(), nullable=True, default='{}'),
        sa.Column('attachment_count', sa.Integer(), nullable=True, default=0),
        sa.Column('total_attachment_size', sa.Integer(), nullable=True, default=0),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.ForeignKeyConstraint(['id'], ['card_summaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # User workspaces junction table
    op.create_table('user_workspaces',
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('workspace_id', sa.Text(), nullable=False),
        sa.Column('card_id', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('added_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['card_id'], ['card_summaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'workspace_id', 'card_id')
    )
    op.create_index('idx_user_workspaces_user', 'user_workspaces', ['user_id'])
    op.create_index('idx_user_workspaces_workspace', 'user_workspaces', ['workspace_id'])

    # User preferences table
    op.create_table('user_preferences',
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('preferences_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Attachments table
    op.create_table('attachments',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('card_id', sa.Text(), nullable=False),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Text(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('uploaded_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['card_id'], ['card_summaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_attachments_card_id', 'attachments', ['card_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('attachments')
    op.drop_table('user_preferences')
    op.drop_table('user_workspaces')
    op.drop_table('card_details')
    op.drop_table('card_tags')
    op.drop_table('tags')
    op.drop_table('card_summaries')
    op.drop_table('user_roles')
    op.drop_table('user_sessions')
    op.drop_table('users')