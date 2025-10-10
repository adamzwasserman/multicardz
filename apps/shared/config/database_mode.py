"""Database mode selection and management for MultiCardz.

This module implements the three operational modes:
- DEV: Local development with local Turso instance
- NORMAL: Standard cloud-based Turso deployment
- PRIVACY: Browser-based WASM database with bitmap-only server sync

Architecture Compliance:
- Pure functions only (no classes except Enum)
- Zero-trust UUID architecture compatible
- <700 lines per file
- Event-sourcing pattern ready
"""
from enum import Enum
from typing import Literal, NamedTuple
import os


class DatabaseMode(str, Enum):
    """Database operational modes for MultiCardz.

    Attributes:
        DEV: Local development mode with local Turso instance
        NORMAL: Standard cloud-based mode with full server storage
        PRIVACY: Privacy mode with browser WASM DB and bitmap-only sync
    """
    DEV = "dev"
    NORMAL = "normal"
    PRIVACY = "privacy"


class ModeConfig(NamedTuple):
    """Configuration for a database mode.

    Attributes:
        mode: The database mode
        enabled: Whether this mode is available
        requires_subscription: Subscription tier required (None for free modes)
        url: Database connection URL (None for browser-only modes)
    """
    mode: DatabaseMode
    enabled: bool
    requires_subscription: str | None
    url: str | None


def get_database_mode() -> DatabaseMode:
    """Get current database mode from environment configuration.

    Returns:
        DatabaseMode: The current operational mode

    Environment Variables:
        DB_MODE: Mode selection (dev|normal|privacy), defaults to 'normal'
    """
    mode_str = os.getenv('DB_MODE', 'normal').lower()
    try:
        return DatabaseMode(mode_str)
    except ValueError:
        # Default to normal mode if invalid mode specified
        return DatabaseMode.NORMAL


def get_mode_config(mode: DatabaseMode) -> ModeConfig:
    """Get configuration for a specific database mode.

    Args:
        mode: The database mode to get configuration for

    Returns:
        ModeConfig: Configuration details for the mode
    """
    configs = {
        DatabaseMode.DEV: ModeConfig(
            mode=DatabaseMode.DEV,
            enabled=True,
            requires_subscription=None,
            url=os.getenv('TURSO_DEV_URL', 'http://127.0.0.1:8080')
        ),
        DatabaseMode.NORMAL: ModeConfig(
            mode=DatabaseMode.NORMAL,
            enabled=True,
            requires_subscription=None,
            url=os.getenv('TURSO_DATABASE_URL')
        ),
        DatabaseMode.PRIVACY: ModeConfig(
            mode=DatabaseMode.PRIVACY,
            enabled=True,
            requires_subscription='premium',
            url=None  # Browser-only, no server URL needed
        )
    }
    return configs[mode]


def is_privacy_mode_enabled(user_id: str, workspace_id: str) -> bool:
    """Check if user has access to privacy mode.

    Args:
        user_id: User UUID
        workspace_id: Workspace UUID

    Returns:
        bool: True if user has premium subscription and privacy mode access

    Note:
        This is a placeholder. In production, this would check actual
        subscription status via subscription service.
    """
    # TODO: Implement actual subscription check
    # For now, return False (standard mode only)
    return False


def validate_mode_access(mode: DatabaseMode, user_id: str, workspace_id: str) -> tuple[bool, str | None]:
    """Validate if user can access the requested database mode.

    Args:
        mode: Requested database mode
        user_id: User UUID
        workspace_id: Workspace UUID

    Returns:
        tuple[bool, str | None]: (access_granted, error_message)
            - (True, None) if access granted
            - (False, error_message) if access denied
    """
    config = get_mode_config(mode)

    if not config.enabled:
        return False, f"Mode '{mode.value}' is not currently available"

    if config.requires_subscription:
        if not is_privacy_mode_enabled(user_id, workspace_id):
            return False, f"Mode '{mode.value}' requires {config.requires_subscription} subscription"

    return True, None


def set_database_mode(mode: DatabaseMode, user_id: str, workspace_id: str) -> tuple[bool, str | None]:
    """Set the database mode for the current session.

    Args:
        mode: Desired database mode
        user_id: User UUID
        workspace_id: Workspace UUID

    Returns:
        tuple[bool, str | None]: (success, error_message)
            - (True, None) if mode set successfully
            - (False, error_message) if mode change failed
    """
    # Validate access
    has_access, error = validate_mode_access(mode, user_id, workspace_id)
    if not has_access:
        return False, error

    # In production, this would update user preferences
    # For now, we just validate that the mode can be set
    os.environ['DB_MODE'] = mode.value

    return True, None
