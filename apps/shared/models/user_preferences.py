"""
User Preferences model for MultiCardz™.
Handles all user UI/UX customization settings.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ViewSettings(BaseModel):
    """User view and layout preferences."""

    cards_start_visible: bool = Field(
        default=True,
        description="Whether cards start visible or collapsed on workspace load",
    )
    cards_start_expanded: bool = Field(
        default=False, description="Whether cards start expanded showing full content"
    )
    tag_layout: str = Field(
        default="horizontal",
        pattern="^(horizontal|vertical)$",
        description="Tag layout orientation",
    )
    show_tag_colors: bool = Field(
        default=True, description="Whether to show colors on tags and cards"
    )
    card_density: str = Field(
        default="comfortable",
        pattern="^(compact|comfortable|spacious)$",
        description="Card spacing density",
    )
    cards_per_page: int = Field(
        default=50, ge=10, le=500, description="Number of cards to show per page"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class ThemeSettings(BaseModel):
    """User theme and visual preferences."""

    theme: str = Field(
        default="system",
        pattern="^(light|dark|system)$",
        description="Color theme preference",
    )
    font_family: str = Field(
        default="Inter",
        pattern="^(Inter|Roboto|Arial|Georgia|Courier)$",
        description="Font family for interface",
    )
    font_size: str = Field(
        default="medium",
        pattern="^(small|medium|large|extra-large)$",
        description="Base font size",
    )
    high_contrast: bool = Field(
        default=False, description="Enable high contrast mode for accessibility"
    )
    reduce_motion: bool = Field(
        default=False, description="Reduce animations and transitions"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class TagSettings(BaseModel):
    """User tag organization preferences."""

    separate_user_ai_tags: bool = Field(
        default=True,
        description="Visually separate user-created from AI-suggested tags",
    )
    show_tag_counts: bool = Field(
        default=True, description="Show number of cards for each tag"
    )
    auto_complete_tags: bool = Field(
        default=True, description="Enable tag auto-completion during typing"
    )
    tag_sort_order: str = Field(
        default="alphabetical",
        pattern="^(alphabetical|frequency|recent)$",
        description="Default tag sorting method",
    )
    max_visible_tags: int = Field(
        default=20, ge=5, le=100, description="Maximum tags to show before collapsing"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class WorkspaceSettings(BaseModel):
    """User workspace behavior preferences."""

    default_workspace: str = Field(
        default="main",
        min_length=1,
        max_length=50,
        description="Default workspace to load on startup",
    )
    auto_save_frequency: int = Field(
        default=30, ge=5, le=300, description="Auto-save interval in seconds"
    )
    confirm_destructive_actions: bool = Field(
        default=True, description="Show confirmation dialogs for delete operations"
    )
    default_card_view: str = Field(
        default="summary",
        pattern="^(summary|detail|grid)$",
        description="Default view mode for new workspaces",
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class UserPreferences(BaseModel):
    """
    Complete user preferences model.

    Stores all user customization settings as immutable preferences.
    Applied server-side during HTML generation for stateless operation.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8].upper(),
        description="Unique preferences identifier",
    )
    user_id: str = Field(description="Associated user identifier")
    view_settings: ViewSettings = Field(
        default_factory=ViewSettings, description="View and layout preferences"
    )
    theme_settings: ThemeSettings = Field(
        default_factory=ThemeSettings, description="Theme and visual preferences"
    )
    tag_settings: TagSettings = Field(
        default_factory=TagSettings, description="Tag organization preferences"
    )
    workspace_settings: WorkspaceSettings = Field(
        default_factory=WorkspaceSettings, description="Workspace behavior preferences"
    )
    custom_settings: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom settings for extensibility"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Preferences creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last preferences update timestamp"
    )
    version: int = Field(
        default=1, description="Preferences schema version for migrations"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    def to_template_context(self) -> dict[str, Any]:
        """Convert preferences to template rendering context."""
        return {
            "cards_visible": self.view_settings.cards_start_visible,
            "cards_expanded": self.view_settings.cards_start_expanded,
            "tag_layout": self.view_settings.tag_layout,
            "show_tag_colors": self.view_settings.show_tag_colors,
            "card_density": self.view_settings.card_density,
            "theme_class": f"theme-{self.theme_settings.theme}",
            "font_class": f"font-{self.theme_settings.font_family.lower()}",
            "font_size_class": f"text-{self.theme_settings.font_size}",
            "high_contrast": self.theme_settings.high_contrast,
            "reduce_motion": self.theme_settings.reduce_motion,
            "separate_user_ai_tags": self.tag_settings.separate_user_ai_tags,
            "show_tag_counts": self.tag_settings.show_tag_counts,
            "auto_complete_tags": self.tag_settings.auto_complete_tags,
            "tag_sort_order": self.tag_settings.tag_sort_order,
            "default_workspace": self.workspace_settings.default_workspace,
            "auto_save_frequency": self.workspace_settings.auto_save_frequency,
            "confirm_destructive": self.workspace_settings.confirm_destructive_actions,
        }
