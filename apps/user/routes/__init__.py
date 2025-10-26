"""
multicardz User Application Routes
"""

from .cards_api import router as cards_router
from .group_tags_api import router as group_tags_router
from .tags_api import router as tags_router

__all__ = ("cards_router", "group_tags_router", "tags_router")
