"""
Pydantic models for multicardz database entities.
These models define the data validation and serialization layer.
"""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

# ============ Card Models ============

class CardBase(BaseModel):
    """Base card model with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    user_id: str
    workspace_id: str
    tag_ids: list[str] = Field(default_factory=list, description="List of tag UUIDs")
    tag_bitmaps: list[int] = Field(default_factory=list, description="List of tag integer bitmaps")

class CardCreate(CardBase):
    """Model for creating a new card."""
    pass

class CardUpdate(BaseModel):
    """Model for updating a card."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tag_ids: list[str] | None = None
    tag_bitmaps: list[int] | None = None

class Card(CardBase):
    """Complete card model with all fields."""
    card_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============ Tag Models ============

class TagBase(BaseModel):
    """Base tag model with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    tag_bitmap: int = Field(..., description="Integer bitmap for RoaringBitmap operations")
    user_id: str
    workspace_id: str

class TagCreate(TagBase):
    """Model for creating a new tag."""
    pass

class TagUpdate(BaseModel):
    """Model for updating a tag (only name can change)."""
    name: str | None = Field(None, min_length=1, max_length=100)

class Tag(TagBase):
    """Complete tag model with all fields."""
    tag_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ============ CardContent Models ============

class CardContentBase(BaseModel):
    """Base card content model."""
    card_id: str
    type: int = Field(..., ge=1, le=5, description="1=text, 2=number, 3=boolean, 4=json, 5=combined")
    label: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_boolean: bool | None = None
    value_json: str | None = None  # JSON stored as string

class CardContentCreate(CardContentBase):
    """Model for creating card content."""
    pass

class CardContentUpdate(BaseModel):
    """Model for updating card content."""
    type: int | None = Field(None, ge=1, le=5)
    label: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_boolean: bool | None = None
    value_json: str | None = None

class CardContent(CardContentBase):
    """Complete card content model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# ============ User Preferences Models ============

class UserPreferencesBase(BaseModel):
    """Base user preferences model."""
    user_id: str
    # Global settings
    start_cards_visible: bool = True
    start_cards_expanded: bool = False
    show_tag_colors: bool = True
    # UI settings
    theme: str = Field(default="system", pattern="^(system|light|dark|earth)$")
    font_family: str = Field(default="Inter", pattern="^(Inter|Roboto|Arial|Georgia|Courier)$")
    separate_user_ai_tags: bool = True
    stack_tags_vertically: bool = False

class UserPreferencesCreate(UserPreferencesBase):
    """Model for creating user preferences."""
    pass

class UserPreferencesUpdate(BaseModel):
    """Model for updating user preferences."""
    start_cards_visible: bool | None = None
    start_cards_expanded: bool | None = None
    show_tag_colors: bool | None = None
    theme: str | None = Field(None, pattern="^(system|light|dark|earth)$")
    font_family: str | None = Field(None, pattern="^(Inter|Roboto|Arial|Georgia|Courier)$")
    separate_user_ai_tags: bool | None = None
    stack_tags_vertically: bool | None = None

class UserPreferences(UserPreferencesBase):
    """Complete user preferences model."""
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# ============ Saved View Models ============

class SavedViewBase(BaseModel):
    """Base saved view model."""
    user_id: str
    workspace_id: str
    name: str = Field(..., min_length=1, max_length=100)
    tags_in_play: list[str] = Field(default_factory=list, description="JSON array of tag combinations")

class SavedViewCreate(SavedViewBase):
    """Model for creating a saved view."""
    pass

class SavedViewUpdate(BaseModel):
    """Model for updating a saved view."""
    name: str | None = Field(None, min_length=1, max_length=100)
    tags_in_play: list[str] | None = None

class SavedView(SavedViewBase):
    """Complete saved view model."""
    view_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# ============ Group Tag Models ============

class GroupTagBase(BaseModel):
    """Base group tag model with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    workspace_id: str
    created_by: str
    visual_style: dict = Field(
        default_factory=lambda: {
            'border_style': 'dashed',
            'opacity': 0.95,
            'icon': 'folder-minimal',
            'border_color': 'rgba(0, 0, 0, 0.2)',
            'background_pattern': 'subtle-dots'
        },
        description="Visual styling configuration following Muji principles"
    )
    max_nesting_depth: int = Field(default=10, ge=1, le=20)

class GroupTagCreate(GroupTagBase):
    """Model for creating a new group tag."""
    initial_member_ids: frozenset[str] = Field(
        default_factory=frozenset,
        description="Initial member tag IDs to add to group"
    )

class GroupTagUpdate(BaseModel):
    """Model for updating a group tag."""
    name: str | None = Field(None, min_length=1, max_length=100)
    visual_style: dict | None = None
    max_nesting_depth: int | None = Field(None, ge=1, le=20)

class GroupTag(GroupTagBase):
    """Complete group tag model with all fields."""
    id: str = Field(default_factory=lambda: f"group_{uuid4().hex[:12]}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    member_tag_ids: frozenset[str] = Field(
        default_factory=frozenset,
        description="Set of member tag/group IDs"
    )
    parent_group_ids: frozenset[str] = Field(
        default_factory=frozenset,
        description="Groups that contain this group"
    )

    model_config = ConfigDict(from_attributes=True)


# ============ Group Membership Models ============

class GroupMembershipBase(BaseModel):
    """Base group membership model."""
    group_id: str
    member_tag_id: str
    member_type: str = Field(..., pattern="^(tag|group)$")
    added_by: str

class GroupMembershipCreate(GroupMembershipBase):
    """Model for creating a group membership."""
    pass

class GroupMembership(GroupMembershipBase):
    """Complete group membership model."""
    added_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
