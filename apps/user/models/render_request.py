"""
Pydantic models for MultiCardz™ card rendering requests.
Provides validation and type safety for the dynamic drag-drop system.
"""


from pydantic import BaseModel, Field, validator


class ZoneMetadata(BaseModel):
    """Metadata for a drop zone."""
    label: str = ""
    accepts: list[str] = Field(default_factory=lambda: ["tags"])
    position: str = "static"
    maxTags: int | None = None
    behavior: str = "standard"
    temporalRange: str | None = None

    @validator('accepts', each_item=True)
    def validate_accepts(cls, accept_type):
        valid_types = {'tags', 'group-tags', 'ai-tags', 'system-tags'}
        if accept_type not in valid_types:
            raise ValueError(f"Invalid accept type: {accept_type}")
        return accept_type

    @validator('behavior')
    def validate_behavior(cls, behavior):
        valid_behaviors = {
            'standard', 'union', 'intersection', 'difference', 'exclude',
            'boost', 'temporal', 'dimensional'
        }
        if behavior not in valid_behaviors:
            raise ValueError(f"Invalid behavior: {behavior}")
        return behavior

    @validator('maxTags')
    def validate_max_tags(cls, max_tags):
        if max_tags is not None and max_tags < 1:
            raise ValueError("maxTags must be positive")
        return max_tags


class ZoneData(BaseModel):
    """Data for a single zone including tags and metadata."""
    tags: list[str] = Field(default_factory=list)
    metadata: ZoneMetadata = Field(default_factory=ZoneMetadata)

    @validator('tags', each_item=True)
    def validate_tag(cls, tag):
        if not isinstance(tag, str):
            raise ValueError("Tag must be string")
        if len(tag) > 100:
            raise ValueError("Tag too long")
        if len(tag.strip()) == 0:
            raise ValueError("Tag cannot be empty")
        return tag.strip()

    @validator('tags')
    def validate_tag_list(cls, tags):
        if len(tags) > 50:  # Reasonable limit per zone
            raise ValueError("Too many tags in zone")
        return tags


class RenderControls(BaseModel):
    """UI controls that affect rendering."""
    startWithAllCards: bool = False
    startWithCardsExpanded: bool = True
    showColors: bool = True

    # Add other controls as they're discovered dynamically
    class Config:
        extra = "allow"  # Allow additional fields from dynamic discovery

    @validator('*', pre=True)
    def validate_control_values(cls, value):
        # Convert string booleans if needed
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        return value


class TagsInPlay(BaseModel):
    """Complete state from the UI."""
    zones: dict[str, ZoneData] = Field(default_factory=dict)
    controls: RenderControls = Field(default_factory=RenderControls)

    @validator('zones')
    def validate_zones(cls, zones):
        if len(zones) > 50:  # Reasonable limit
            raise ValueError("Too many zones")

        # Validate zone names
        for zone_name in zones.keys():
            if not isinstance(zone_name, str) or len(zone_name) > 50:
                raise ValueError(f"Invalid zone name: {zone_name}")

        return zones

    @validator('zones')
    def validate_total_tags(cls, zones):
        """Ensure total tags across all zones is reasonable."""
        total_tags = sum(len(zone_data.tags) for zone_data in zones.values())
        if total_tags > 500:
            raise ValueError("Too many total tags across all zones")
        return zones


class RenderRequest(BaseModel):
    """Request body for card rendering."""
    tagsInPlay: TagsInPlay

    class Config:
        # Allow for future extensibility
        extra = "ignore"

    @validator('tagsInPlay')
    def validate_tags_in_play(cls, tags_in_play):
        if not isinstance(tags_in_play, TagsInPlay):
            raise ValueError("Invalid tagsInPlay structure")
        return tags_in_play


# Response models for consistency

class CardData(BaseModel):
    """Basic card data for rendering."""
    id: str
    title: str
    tags: list[str]
    content: str | None = None
    metadata: dict = Field(default_factory=dict)


class RenderResponse(BaseModel):
    """Response from card rendering."""
    html: str
    card_count: int
    zones_processed: int
    processing_time_ms: float
    cache_hit: bool = False

    class Config:
        extra = "allow"  # Allow for future response fields
