"""Zero-trust Pydantic models with workspace isolation.

These models enforce immutability (frozen=True) and workspace isolation
as per the zero-trust architecture principles.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base tag model with workspace isolation."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., description="User UUID for isolation")
    workspace_id: str = Field(..., description="Workspace UUID for isolation")
    tag_bitmap: int = Field(..., ge=0, description="Integer bitmap for RoaringBitmap")


class Tag(TagBase):
    """Tag with auto-maintained card count."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    tag_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    card_count: int = Field(default=0, ge=0, description="Auto-maintained")
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: datetime | None = None


class CardBase(BaseModel):
    """Base card model with isolation."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    user_id: str = Field(..., description="User UUID for isolation")
    workspace_id: str = Field(..., description="Workspace UUID for isolation")


class Card(CardBase):
    """Card with inverted index for tags."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    card_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tag_ids: list[str] = Field(default_factory=list)
    tag_bitmaps: list[int] = Field(default_factory=list)
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: datetime | None = None
