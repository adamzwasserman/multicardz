"""Tag creation and management API routes."""

import logging
import sqlite3
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/tags", tags=["tags"])


class CreateTagRequest(BaseModel):
    """Request model for tag creation."""

    name: str
    type: str = "user"


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
        request: Tag creation request containing name and type

    Returns:
        CreateTagResponse with success status and tag_id
    """
    tag_name = request.name
    tag_type = request.type

    logger.info(f"Creating tag: {tag_name} (type: {tag_type})")

    try:
        # Get database path
        db_path = Path("/var/data/tutorial_customer.db")

        # Insert tag into database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if tag already exists
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            existing = cursor.fetchone()

            if existing:
                return CreateTagResponse(
                    success=False,
                    tag_id=str(existing[0]),
                    message=f"Tag '{tag_name}' already exists",
                )

            # Insert new tag
            cursor.execute(
                "INSERT INTO tags (name) VALUES (?)",
                (tag_name,),
            )
            conn.commit()

            tag_id = str(cursor.lastrowid)

            logger.info(f"Tag created successfully: {tag_name} (ID: {tag_id})")

            return CreateTagResponse(
                success=True, tag_id=tag_id, message="Tag created successfully"
            )

    except Exception as e:
        logger.error(f"Failed to create tag: {e}")
        return CreateTagResponse(
            success=False, tag_id="", message=f"Failed to create tag: {str(e)}"
        )
