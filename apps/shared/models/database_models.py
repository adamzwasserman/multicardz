"""
Pydantic models for multicardz database entities.
These models define the data validation and serialization layer.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


# ============ Card Models ============

class CardBase(BaseModel):
    """Base card model with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    user_id: str
    workspace_id: str
    tag_ids: List[str] = Field(default_factory=list, description="List of tag UUIDs")
    tag_bitmaps: List[int] = Field(default_factory=list, description="List of tag integer bitmaps")

class CardCreate(CardBase):
    """Model for creating a new card."""
    pass

class CardUpdate(BaseModel):
    """Model for updating a card."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tag_ids: Optional[List[str]] = None
    tag_bitmaps: Optional[List[int]] = None

class Card(CardBase):
    """Complete card model with all fields."""
    card_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: Optional[datetime] = None

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
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class Tag(TagBase):
    """Complete tag model with all fields."""
    tag_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
    deleted: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============ CardContent Models ============

class CardContentBase(BaseModel):
    """Base card content model."""
    card_id: str
    type: int = Field(..., ge=1, le=5, description="1=text, 2=number, 3=boolean, 4=json, 5=combined")
    label: Optional[str] = None
    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    value_json: Optional[str] = None  # JSON stored as string

class CardContentCreate(CardContentBase):
    """Model for creating card content."""
    pass

class CardContentUpdate(BaseModel):
    """Model for updating card content."""
    type: Optional[int] = Field(None, ge=1, le=5)
    label: Optional[str] = None
    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    value_json: Optional[str] = None

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
    start_cards_visible: Optional[bool] = None
    start_cards_expanded: Optional[bool] = None
    show_tag_colors: Optional[bool] = None
    theme: Optional[str] = Field(None, pattern="^(system|light|dark|earth)$")
    font_family: Optional[str] = Field(None, pattern="^(Inter|Roboto|Arial|Georgia|Courier)$")
    separate_user_ai_tags: Optional[bool] = None
    stack_tags_vertically: Optional[bool] = None

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
    tags_in_play: List[str] = Field(default_factory=list, description="JSON array of tag combinations")

class SavedViewCreate(SavedViewBase):
    """Model for creating a saved view."""
    pass

class SavedViewUpdate(BaseModel):
    """Model for updating a saved view."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    tags_in_play: Optional[List[str]] = None

class SavedView(SavedViewBase):
    """Complete saved view model."""
    view_id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)