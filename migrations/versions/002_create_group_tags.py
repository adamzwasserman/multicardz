"""Create group tags tables

Revision ID: 002
Revises: 001
Create Date: 2025-10-26 15:42:30.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: str | None = '001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create group tags and membership tables."""

    # Group tags table
    op.create_table('group_tags',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('workspace_id', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('visual_style', sa.Text(), nullable=True, default='{}'),  # JSON stored as text
        sa.Column('max_nesting_depth', sa.Integer(), nullable=True, default=10),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for group_tags
    op.create_index('idx_group_tags_workspace', 'group_tags', ['workspace_id'])
    op.create_index('idx_group_tags_name_workspace', 'group_tags', ['workspace_id', 'name'], unique=True)
    op.create_index('idx_group_tags_created_by', 'group_tags', ['created_by'])

    # Group memberships table (many-to-many)
    op.create_table('group_memberships',
        sa.Column('group_id', sa.Text(), nullable=False),
        sa.Column('member_tag_id', sa.Text(), nullable=False),
        sa.Column('member_type', sa.Text(), nullable=False),
        sa.Column('added_at', sa.Text(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('added_by', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['group_tags.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('group_id', 'member_tag_id'),
        sa.CheckConstraint("member_type IN ('tag', 'group')", name='ck_group_memberships_type'),
        sa.CheckConstraint("group_id != member_tag_id", name='ck_group_memberships_no_self_reference')
    )

    # Create indexes for group_memberships
    op.create_index('idx_group_memberships_group', 'group_memberships', ['group_id'])
    op.create_index('idx_group_memberships_member', 'group_memberships', ['member_tag_id'])
    op.create_index('idx_group_memberships_type', 'group_memberships', ['member_type'])


def downgrade() -> None:
    """Drop group tags tables."""
    op.drop_table('group_memberships')
    op.drop_table('group_tags')
