"""
Card models for multicardz™.
Two-tier architecture for optimal performance.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CardSummary(BaseModel):
    """
    Minimal card data for fast list rendering (~50 bytes).

    Used for card lists and search results where only basic info is needed.
    This is a pure data model with no business logic.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8].upper(),
        description="Unique 8-character identifier",
    )
    title: str = Field(min_length=1, max_length=255, description="Card title")
    tags: frozenset[str] = Field(
        default_factory=frozenset, description="Immutable set of tags"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    modified_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last modification timestamp"
    )
    has_attachments: bool = Field(
        default=False, description="Whether card has attachments"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class CardDetail(BaseModel):
    """
    Complete card data loaded on-demand.

    Contains all card content including attachments and metadata.
    Only loaded when user opens a card for editing or viewing.
    """

    id: str = Field(description="Unique 8-character identifier matching CardSummary")
    content: str = Field(default="", description="Full card content/description")
    metadata: dict = Field(
        default_factory=dict, description="Extended metadata (custom fields, etc.)"
    )
    attachment_count: int = Field(default=0, description="Number of attachments")
    total_attachment_size: int = Field(
        default=0, description="Total size of all attachments in bytes"
    )
    version: int = Field(default=1, description="Version number for optimistic locking")

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class Attachment(BaseModel):
    """
    File attachment stored as BLOB in SQLite.

    Supports per-user storage quotas for pricing tiers.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8].upper(),
        description="Unique attachment identifier",
    )
    card_id: str = Field(description="Parent card identifier")
    filename: str = Field(min_length=1, max_length=255, description="Original filename")
    content_type: str = Field(description="MIME type of the file")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    data: bytes = Field(description="File content as binary data")
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )

    model_config = {"frozen": True, "validate_assignment": True}


class UserTier(BaseModel):
    """
    User subscription tier for storage quotas and feature access.

    Enables pricing based on storage and attachment limits.
    """

    user_id: str = Field(description="User identifier")
    tier: str = Field(
        pattern="^(free|pro|enterprise|elite)$", description="Subscription tier"
    )
    max_attachment_size_mb: int = Field(
        description="Maximum single attachment size in MB"
    )
    total_storage_quota_gb: int = Field(description="Total storage quota in GB")
    current_storage_bytes: int = Field(
        default=0, ge=0, description="Current storage usage in bytes"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Tier assignment timestamp"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    @property
    def storage_quota_bytes(self) -> int:
        """Convert GB quota to bytes."""
        return self.total_storage_quota_gb * 1024 * 1024 * 1024

    @property
    def attachment_size_limit_bytes(self) -> int:
        """Convert MB limit to bytes."""
        return self.max_attachment_size_mb * 1024 * 1024

    @property
    def storage_usage_percentage(self) -> float:
        """Calculate storage usage as percentage."""
        if self.storage_quota_bytes == 0:
            return 0.0
        return (self.current_storage_bytes / self.storage_quota_bytes) * 100
