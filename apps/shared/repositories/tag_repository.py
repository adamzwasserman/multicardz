"""
Tag repository with declarative methods for tag operations.
"""
from typing import Optional
from pathlib import Path

from .base_repository import BaseRepository


class TagRepository(BaseRepository):
    """Repository for tag operations."""

    def get_by_id(self, tag_id: str, workspace_id: str) -> Optional[dict]:
        """
        Get tag by ID with workspace isolation.

        Args:
            tag_id: Tag UUID
            workspace_id: Workspace UUID

        Returns:
            Tag dict with keys: tag_id, name, workspace_id, card_count, created, modified, deleted
        """
        query = """
            SELECT tag_id, name, workspace_id, card_count, created, modified, deleted
            FROM tags
            WHERE tag_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        row = self.execute_query_one(query, (tag_id, workspace_id))
        return dict(row) if row else None

    def get_by_name(self, name: str, workspace_id: str) -> Optional[dict]:
        """
        Get tag by name with workspace isolation.

        Args:
            name: Tag name
            workspace_id: Workspace UUID

        Returns:
            Tag dict or None
        """
        query = """
            SELECT tag_id, name, workspace_id, card_count, created, modified, deleted
            FROM tags
            WHERE name = ? AND workspace_id = ? AND deleted IS NULL
        """
        row = self.execute_query_one(query, (name, workspace_id))
        return dict(row) if row else None

    def list_by_workspace(self, workspace_id: str, limit: int = 1000) -> list[dict]:
        """
        List all non-deleted tags in workspace.

        Args:
            workspace_id: Workspace UUID
            limit: Maximum number of tags to return

        Returns:
            List of tag dicts
        """
        query = """
            SELECT tag_id, name, workspace_id, card_count, created, modified, deleted
            FROM tags
            WHERE workspace_id = ? AND deleted IS NULL
            ORDER BY name ASC
            LIMIT ?
        """
        rows = self.execute_query(query, (workspace_id, limit))
        return [dict(row) for row in rows]

    def get_counts(self, workspace_id: str) -> dict[str, int]:
        """
        Get card_count for all non-deleted tags in workspace.

        Args:
            workspace_id: Workspace UUID

        Returns:
            Dict mapping tag_id to card_count
        """
        query = """
            SELECT tag_id, card_count
            FROM tags
            WHERE workspace_id = ? AND deleted IS NULL
        """
        rows = self.execute_query(query, (workspace_id,))
        return {row["tag_id"]: row["card_count"] for row in rows}

    def create(self, tag_id: str, name: str, workspace_id: str) -> dict:
        """
        Create new tag. Triggers auto-fill created and modified.

        Args:
            tag_id: Tag UUID
            name: Tag name
            workspace_id: Workspace UUID

        Returns:
            Created tag dict
        """
        command = """
            INSERT INTO tags (tag_id, name, workspace_id, card_count, user_id, created, modified)
            VALUES (?, ?, ?, 0, 'default-user', datetime('now'), datetime('now'))
        """
        self.execute_command(command, (tag_id, name, workspace_id))

        return self.get_by_id(tag_id, workspace_id)

    def soft_delete(self, tag_id: str, workspace_id: str) -> bool:
        """
        Soft delete tag (sets deleted timestamp). Trigger auto-updates modified.

        Args:
            tag_id: Tag UUID
            workspace_id: Workspace UUID

        Returns:
            True if deleted, False if not found
        """
        command = """
            UPDATE tags
            SET deleted = datetime('now')
            WHERE tag_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (tag_id, workspace_id))
        return rowcount > 0

    def get_card_count(self, tag_id: str, workspace_id: str) -> int:
        """
        Get card count for a tag.

        Args:
            tag_id: Tag UUID
            workspace_id: Workspace UUID

        Returns:
            Card count (0 if tag not found)
        """
        tag = self.get_by_id(tag_id, workspace_id)
        return tag["card_count"] if tag else 0
