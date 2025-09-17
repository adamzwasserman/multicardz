"""
Workspace model for MultiCardz™.
Pure data model with no business logic.
"""

import uuid

from pydantic import BaseModel, Field


class Workspace(BaseModel):
    """
    Workspace containing cards and metadata.

    Pure data model for workspace organization.
    All workspace operations are implemented as pure functions.
    """

    id: str = Field(
        default_factory=lambda: f"ws-{str(uuid.uuid4())[:8].upper()}",
        description="Unique workspace identifier",
    )
    name: str = Field(
        min_length=1, max_length=100, description="Workspace display name"
    )
    description: str = Field(
        default="", max_length=500, description="Workspace description"
    )
    card_ids: frozenset[str] = Field(
        default_factory=frozenset, description="Set of card IDs in this workspace"
    )
    owner_id: str = Field(description="ID of workspace owner")

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
