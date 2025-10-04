"""
Card repository with declarative methods for card operations.
"""
from typing import Optional
from pathlib import Path
from datetime import datetime

from .base_repository import BaseRepository


class CardRepository(BaseRepository):
    """Repository for card operations."""

    def get_by_id(self, card_id: str, workspace_id: str) -> Optional[dict]:
        """
        Get card by ID with workspace isolation.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID

        Returns:
            Card dict with keys: card_id, name, workspace_id, tags, created, modified, deleted
        """
        query = """
            SELECT card_id, name, workspace_id, tags, created, modified, deleted
            FROM cards
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        row = self.execute_query_one(query, (card_id, workspace_id))
        return dict(row) if row else None

    def list_by_workspace(self, workspace_id: str, limit: int = 1000) -> list[dict]:
        """
        List all non-deleted cards in workspace.

        Args:
            workspace_id: Workspace UUID
            limit: Maximum number of cards to return

        Returns:
            List of card dicts
        """
        query = """
            SELECT card_id, name, workspace_id, tags, created, modified, deleted
            FROM cards
            WHERE workspace_id = ? AND deleted IS NULL
            ORDER BY created DESC
            LIMIT ?
        """
        rows = self.execute_query(query, (workspace_id, limit))
        return [dict(row) for row in rows]

    def create(self, card_id: str, name: str, workspace_id: str, tag_ids: list[str]) -> dict:
        """
        Create new card with tags.

        Args:
            card_id: Card UUID
            name: Card name
            workspace_id: Workspace UUID
            tag_ids: List of tag UUIDs

        Returns:
            Created card dict
        """
        tags_csv = ",".join(tag_ids) if tag_ids else ""

        # Triggers will auto-fill created and modified
        command = """
            INSERT INTO cards (card_id, name, workspace_id, tags, user_id, card_bitmap, created, modified)
            VALUES (?, ?, ?, ?, 'default-user', 0, datetime('now'), datetime('now'))
        """
        self.execute_command(command, (card_id, name, workspace_id, tags_csv))

        return self.get_by_id(card_id, workspace_id)

    def update_title(self, card_id: str, workspace_id: str, title: str) -> bool:
        """
        Update card title. Trigger auto-updates modified timestamp.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID
            title: New title

        Returns:
            True if updated, False if not found
        """
        command = """
            UPDATE cards
            SET name = ?
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (title, card_id, workspace_id))
        return rowcount > 0

    def update_content(self, card_id: str, workspace_id: str, content: str) -> bool:
        """
        Update card description/content. Trigger auto-updates modified timestamp.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID
            content: New description/content

        Returns:
            True if updated, False if not found
        """
        command = """
            UPDATE cards
            SET description = ?
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (content, card_id, workspace_id))
        return rowcount > 0

    def add_tag(self, card_id: str, workspace_id: str, tag_id: str) -> bool:
        """
        Add tag to card (updates comma-separated tags column). Trigger auto-updates modified.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID
            tag_id: Tag UUID to add

        Returns:
            True if added, False if not found or already present
        """
        # Get current tags
        card = self.get_by_id(card_id, workspace_id)
        if not card:
            return False

        current_tags = card["tags"].split(",") if card["tags"] else []

        # Check if tag already present
        if tag_id in current_tags:
            return False

        # Add tag
        current_tags.append(tag_id)
        new_tags_csv = ",".join(current_tags)

        command = """
            UPDATE cards
            SET tags = ?
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (new_tags_csv, card_id, workspace_id))
        return rowcount > 0

    def remove_tag(self, card_id: str, workspace_id: str, tag_id: str) -> bool:
        """
        Remove tag from card (updates comma-separated tags column). Trigger auto-updates modified.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID
            tag_id: Tag UUID to remove

        Returns:
            True if removed, False if not found
        """
        # Get current tags
        card = self.get_by_id(card_id, workspace_id)
        if not card:
            return False

        current_tags = card["tags"].split(",") if card["tags"] else []

        # Check if tag present
        if tag_id not in current_tags:
            return False

        # Remove tag
        current_tags.remove(tag_id)
        new_tags_csv = ",".join(current_tags)

        command = """
            UPDATE cards
            SET tags = ?
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (new_tags_csv, card_id, workspace_id))
        return rowcount > 0

    def soft_delete(self, card_id: str, workspace_id: str) -> bool:
        """
        Soft delete card (sets deleted timestamp). Trigger auto-updates modified.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID

        Returns:
            True if deleted, False if not found
        """
        command = """
            UPDATE cards
            SET deleted = datetime('now')
            WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
        """
        rowcount = self.execute_command(command, (card_id, workspace_id))
        return rowcount > 0

    def get_tag_ids(self, card_id: str, workspace_id: str) -> list[str]:
        """
        Get list of tag IDs for a card.

        Args:
            card_id: Card UUID
            workspace_id: Workspace UUID

        Returns:
            List of tag UUIDs (empty if card not found)
        """
        card = self.get_by_id(card_id, workspace_id)
        if not card or not card["tags"]:
            return []

        return card["tags"].split(",")
