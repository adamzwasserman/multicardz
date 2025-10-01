"""
User model for MultiCardz™ authentication and authorization.
Pure data model with no business logic.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """
    User account for authentication and workspace ownership.

    Pure data model for user management.
    All user operations are implemented as pure functions.
    """

    id: str = Field(
        default_factory=lambda: f"user-{str(uuid.uuid4())[:8].upper()}",
        description="Unique user identifier",
    )
    username: str = Field(
        min_length=3, max_length=50, description="Unique username for login"
    )
    email: EmailStr = Field(description="User's email address")
    password_hash: str = Field(description="Hashed password (never store plaintext)")
    full_name: str = Field(
        default="", max_length=100, description="User's full display name"
    )
    is_active: bool = Field(default=True, description="Whether account is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation timestamp"
    )
    last_login: Optional[datetime] = Field(
        default=None, description="Last login timestamp"
    )
    default_workspace_id: Optional[str] = Field(
        default=None, description="Default workspace to load on login"
    )

    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class UserSession(BaseModel):
    """
    User session for authentication tracking.

    Simple session management for stateless operation.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier",
    )
    user_id: str = Field(description="Associated user identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Session creation timestamp"
    )
    expires_at: datetime = Field(description="Session expiration timestamp")
    ip_address: Optional[str] = Field(
        default=None, description="Client IP address for security"
    )
    user_agent: Optional[str] = Field(
        default=None, description="Client user agent for security"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at


class UserWorkspace(BaseModel):
    """
    Junction table model for user-workspace-card relationships.

    Enables workspace isolation and per-user card organization.
    """

    user_id: str = Field(description="User identifier")
    workspace_id: str = Field(description="Workspace identifier")
    card_id: str = Field(description="Card identifier")
    position: Optional[int] = Field(
        default=None, description="Card position within workspace for ordering"
    )
    added_at: datetime = Field(
        default_factory=datetime.utcnow, description="When card was added to workspace"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class UserRole(BaseModel):
    """
    User role for simple authorization.

    Basic role-based access control.
    """

    user_id: str = Field(description="User identifier")
    role: str = Field(
        pattern="^(user|admin|superuser)$",
        description="User role level"
    )
    granted_at: datetime = Field(
        default_factory=datetime.utcnow, description="When role was granted"
    )
    granted_by: Optional[str] = Field(
        default=None, description="Who granted this role"
    )

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }