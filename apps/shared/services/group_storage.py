"""
Group tag storage service implementing pure functional operations.

This module provides storage and retrieval for group tags with immutable
frozenset operations following the patent specifications for semantic tag sets.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from apps.shared.models.database_models import (
    GroupTag,
    GroupTagCreate,
    GroupMembership,
    GroupMembershipCreate,
)
from apps.shared.services.database_connection import get_workspace_connection


# ============ Database Connection ============

import sqlite3

# Global connection cache for the default database
_default_connection = None

# This function can be monkey-patched during testing
def get_connection():
    """
    Get database connection.

    Returns a connection to the default database path.
    For testing, this function is monkey-patched with a test database.
    """
    global _default_connection

    if _default_connection is None:
        from apps.shared.config.database import DATABASE_PATH
        _default_connection = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
        _default_connection.execute("PRAGMA foreign_keys = ON")

        # Initialize schema if needed
        _initialize_schema(_default_connection)

    return _default_connection


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """Initialize group tags schema if tables don't exist."""
    conn.executescript("""
        -- Group tags table
        CREATE TABLE IF NOT EXISTS group_tags (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visual_style TEXT DEFAULT '{}',
            max_nesting_depth INTEGER DEFAULT 10,
            UNIQUE(workspace_id, name)
        );

        -- Group memberships
        CREATE TABLE IF NOT EXISTS group_memberships (
            group_id TEXT NOT NULL,
            member_tag_id TEXT NOT NULL,
            member_type TEXT NOT NULL CHECK (member_type IN ('tag', 'group')),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by TEXT NOT NULL,
            PRIMARY KEY (group_id, member_tag_id),
            FOREIGN KEY (group_id) REFERENCES group_tags(id) ON DELETE CASCADE,
            CHECK (group_id != member_tag_id)
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_group_tags_workspace ON group_tags(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_group_memberships_group ON group_memberships(group_id);
        CREATE INDEX IF NOT EXISTS idx_group_memberships_member ON group_memberships(member_tag_id);
    """)
    conn.commit()


# ============ Pure Validation Functions ============


def validate_group_name(name: str, workspace_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate group name format and uniqueness.

    Returns (is_valid, error_message)
    """
    if not name or len(name) > 100:
        return False, "Group name must be 1-100 characters"

    if not name.replace('-', '').replace('_', '').replace(' ', '').isalnum():
        return False, "Group name must be alphanumeric with dashes, underscores, or spaces"

    # Check uniqueness in workspace
    if group_exists_by_name(name, workspace_id):
        return False, f"Group '{name}' already exists in workspace"

    return True, None


def validate_no_self_reference(group_id: str, member_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate that group doesn't reference itself.

    Returns (is_valid, error_message)
    """
    if group_id == member_id:
        return False, "Cannot add group to itself"

    return True, None


# ============ Database Query Functions ============


def group_exists_by_name(name: str, workspace_id: str) -> bool:
    """Check if a group with the given name exists in workspace."""
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT 1 FROM group_tags
        WHERE workspace_id = ? AND name = ?
        LIMIT 1
        """,
        (workspace_id, name)
    )
    return cursor.fetchone() is not None


def get_group_by_id(group_id: str) -> Optional[GroupTag]:
    """
    Retrieve group by ID with all member relationships.

    Pure function - returns immutable GroupTag or None.
    """
    conn = get_connection()

    # Get group data
    cursor = conn.execute(
        """
        SELECT id, workspace_id, name, created_by, created_at,
               visual_style, max_nesting_depth
        FROM group_tags
        WHERE id = ?
        """,
        (group_id,)
    )
    row = cursor.fetchone()

    if not row:
        return None

    # Get member IDs
    member_cursor = conn.execute(
        """
        SELECT member_tag_id, member_type
        FROM group_memberships
        WHERE group_id = ?
        """,
        (group_id,)
    )
    member_rows = member_cursor.fetchall()
    member_tag_ids = frozenset(row[0] for row in member_rows)

    # Get parent group IDs
    parent_cursor = conn.execute(
        """
        SELECT group_id
        FROM group_memberships
        WHERE member_tag_id = ? AND member_type = 'group'
        """,
        (group_id,)
    )
    parent_rows = parent_cursor.fetchall()
    parent_group_ids = frozenset(row[0] for row in parent_rows)

    # Parse visual_style JSON
    import json
    visual_style = json.loads(row[5]) if row[5] else {}

    return GroupTag(
        id=row[0],
        workspace_id=row[1],
        name=row[2],
        created_by=row[3],
        created_at=datetime.fromisoformat(row[4]),
        visual_style=visual_style,
        max_nesting_depth=row[6],
        member_tag_ids=member_tag_ids,
        parent_group_ids=parent_group_ids
    )


def get_groups_by_workspace(workspace_id: str) -> tuple[GroupTag, ...]:
    """
    Get all groups in a workspace.

    Returns immutable tuple of GroupTag objects.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT id FROM group_tags
        WHERE workspace_id = ?
        ORDER BY created_at DESC
        """,
        (workspace_id,)
    )

    group_ids = [row[0] for row in cursor.fetchall()]
    groups = [get_group_by_id(gid) for gid in group_ids]
    return tuple(g for g in groups if g is not None)


def is_group_tag(tag_id: str) -> bool:
    """Check if a tag ID references a group tag."""
    return tag_id.startswith('group_')


def tag_exists(tag_id: str, workspace_id: str) -> bool:
    """Check if a regular tag exists in workspace."""
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT 1 FROM tags
        WHERE id = ?
        LIMIT 1
        """,
        (tag_id,)
    )
    return cursor.fetchone() is not None


# ============ Group Creation Functions ============


def create_group(
    name: str,
    workspace_id: str,
    created_by: str,
    initial_member_ids: frozenset[str] = frozenset(),
    visual_style: Optional[dict] = None
) -> str:
    """
    Create a new group tag.

    Pure functional implementation with validation.
    Returns group_id on success, raises ValueError on failure.
    """
    # Validate inputs
    is_valid, error = validate_group_name(name, workspace_id)
    if not is_valid:
        raise ValueError(error)

    # Generate ID
    group_id = f"group_{uuid4().hex[:12]}"

    # Default visual style
    if visual_style is None:
        visual_style = {
            'border_style': 'dashed',
            'opacity': 0.95,
            'icon': 'folder-minimal',
            'border_color': 'rgba(0, 0, 0, 0.2)',
            'background_pattern': 'subtle-dots'
        }

    # Insert group record
    import json
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO group_tags (id, workspace_id, name, created_by, visual_style, max_nesting_depth)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (group_id, workspace_id, name, created_by, json.dumps(visual_style), 10)
    )

    # Add initial members
    for member_id in initial_member_ids:
        member_type = 'group' if is_group_tag(member_id) else 'tag'
        conn.execute(
            """
            INSERT INTO group_memberships (group_id, member_tag_id, member_type, added_by)
            VALUES (?, ?, ?, ?)
            """,
            (group_id, member_id, member_type, created_by)
        )

    conn.commit()
    return group_id


# ============ Membership Operations ============


def add_member_to_group(
    group_id: str,
    member_id: str,
    added_by: str
) -> bool:
    """
    Add a member to an existing group.

    Pure functional operation with validation.
    Returns True on success, raises ValueError on invalid operation.
    """
    # Validate no self-reference
    is_valid, error = validate_no_self_reference(group_id, member_id)
    if not is_valid:
        raise ValueError(error)

    # Get existing group
    group = get_group_by_id(group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")

    # Check if already a member (idempotent operation)
    if member_id in group.member_tag_ids:
        return True

    # Determine member type
    member_type = 'group' if is_group_tag(member_id) else 'tag'

    # Insert membership record
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO group_memberships (group_id, member_tag_id, member_type, added_by)
        VALUES (?, ?, ?, ?)
        """,
        (group_id, member_id, member_type, added_by)
    )
    conn.commit()

    return True


def remove_member_from_group(
    group_id: str,
    member_id: str
) -> bool:
    """
    Remove a member from a group.

    Returns True if removed, False if member wasn't in group.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        DELETE FROM group_memberships
        WHERE group_id = ? AND member_tag_id = ?
        """,
        (group_id, member_id)
    )
    conn.commit()

    return cursor.rowcount > 0


def add_multiple_members_to_group(
    group_id: str,
    member_ids: frozenset[str],
    added_by: str
) -> tuple[bool, frozenset[str], Optional[str]]:
    """
    Add multiple members to a group in a single transaction.

    Returns (success, added_member_ids, error_message)
    """
    # Validate group exists
    group = get_group_by_id(group_id)
    if not group:
        return False, frozenset(), f"Group {group_id} not found"

    # Filter out existing members and invalid additions
    new_members = member_ids - group.member_tag_ids

    # Remove self-reference if present
    new_members = new_members - {group_id}

    if not new_members:
        return True, frozenset(), None  # All already members

    # Add all new members in transaction
    conn = get_connection()
    try:
        for member_id in new_members:
            member_type = 'group' if is_group_tag(member_id) else 'tag'
            conn.execute(
                """
                INSERT INTO group_memberships (group_id, member_tag_id, member_type, added_by)
                VALUES (?, ?, ?, ?)
                """,
                (group_id, member_id, member_type, added_by)
            )
        conn.commit()
        return True, new_members, None

    except Exception as e:
        conn.rollback()
        return False, frozenset(), str(e)


# ============ Group Deletion ============


def delete_group(group_id: str) -> bool:
    """
    Delete a group and all its memberships.

    Cascading delete is handled by database constraints.
    Member tags are NOT deleted.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        DELETE FROM group_tags
        WHERE id = ?
        """,
        (group_id,)
    )
    conn.commit()

    return cursor.rowcount > 0


# ============ Statistics Functions ============


def get_group_statistics(group_id: str) -> dict:
    """
    Get statistics for a group.

    Returns dict with member counts and nesting info.
    """
    group = get_group_by_id(group_id)
    if not group:
        return {}

    regular_tags = frozenset(m for m in group.member_tag_ids if not is_group_tag(m))
    nested_groups = frozenset(m for m in group.member_tag_ids if is_group_tag(m))

    return {
        'total_members': len(group.member_tag_ids),
        'regular_tags': len(regular_tags),
        'nested_groups': len(nested_groups),
        'parent_groups': len(group.parent_group_ids),
        'created_at': group.created_at.isoformat(),
        'created_by': group.created_by
    }
