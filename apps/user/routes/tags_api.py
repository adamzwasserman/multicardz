"""Tag creation and management API routes."""

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tags", tags=["tags"])


class CreateTagRequest(BaseModel):
    """Request model for tag creation."""

    name: str
    user_id: str = "default-user"  # TODO: Get from auth
    workspace_id: str = "default-workspace"  # TODO: Get from session
    tag_type: int | None = None
    color_hex: str | None = None


class CreateTagResponse(BaseModel):
    """Response model for tag creation."""

    success: bool
    tag_id: str
    message: str | None = None


@router.post("/create", response_model=CreateTagResponse)
async def create_tag(request: CreateTagRequest) -> CreateTagResponse:
    """
    Create a new tag and persist it to the database.

    Args:
        request: Tag creation request containing name, user_id, workspace_id

    Returns:
        CreateTagResponse with success status and tag_id (UUID)
    """
    tag_name = request.name
    user_id = request.user_id
    workspace_id = request.workspace_id

    logger.info(f"Creating tag: {tag_name} for user {user_id} in workspace {workspace_id}")

    try:
        db_path = Path("/var/data/tutorial_customer.db")

        from apps.shared.config.database import DATABASE_PATH
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Check if tag already exists for this user/workspace
            cursor.execute(
                "SELECT tag_id FROM tags WHERE tag = ? AND user_id = ? AND workspace_id = ? AND deleted IS NULL",
                (tag_name, user_id, workspace_id),
            )
            existing = cursor.fetchone()

            if existing:
                return CreateTagResponse(
                    success=False,
                    tag_id=existing[0],
                    message=f"Tag '{tag_name}' already exists",
                )

            # Generate UUID for new tag
            tag_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            # Insert new tag with all required fields
            cursor.execute(
                """
                INSERT INTO tags (
                    user_id, workspace_id, created, modified, deleted,
                    tag_id, tag_bitmap, tag, card_count, tag_type, color_hex
                ) VALUES (?, ?, ?, ?, NULL, ?, 0, ?, 0, ?, ?)
                """,
                (
                    user_id,
                    workspace_id,
                    now,
                    now,
                    tag_id,
                    tag_name,
                    request.tag_type,
                    request.color_hex,
                ),
            )
            conn.commit()

            logger.info(f"Tag created successfully: {tag_name} (ID: {tag_id})")

            return CreateTagResponse(
                success=True, tag_id=tag_id, message="Tag created successfully"
            )

    except Exception as e:
        logger.error(f"Failed to create tag: {e}")
        return CreateTagResponse(
            success=False, tag_id="", message=f"Failed to create tag: {str(e)}"
        )


@router.post("/delete")
async def delete_tag(request: Request):
    """Delete a tag (soft delete by setting deleted timestamp)."""
    import sqlite3
    from datetime import datetime

    data = await request.json()
    tag_id = data.get("tag_id")

    try:
        db_path = Path("/var/data/tutorial_customer.db")

        from apps.shared.config.database import DATABASE_PATH
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Soft delete - set deleted timestamp
            cursor.execute(
                "UPDATE tags SET deleted = ? WHERE tag_id = ?",
                (datetime.utcnow().isoformat(), tag_id)
            )
            conn.commit()

            logger.info(f"Tag deleted: {tag_id}")
            return {"success": True, "message": "Tag deleted"}

    except Exception as e:
        logger.error(f"Failed to delete tag: {e}")
        return {"success": False, "message": str(e)}
