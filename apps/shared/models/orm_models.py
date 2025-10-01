"""
SQLAlchemy ORM models for multicardz database.
These models define the database schema and relationships.
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


# ============ Project Database Tables ============

class Cards(Base):
    """Cards table - core entity of the project database."""
    __tablename__ = "cards"

    card_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created = Column(DateTime, nullable=False, default=func.now())
    modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted = Column(DateTime, nullable=True)
    tag_ids = Column(JSON, nullable=False, default=list)  # JSON array of tag UUIDs
    tag_bitmaps = Column(JSON, default=list)  # JSON array of tag integer bitmaps

    # Relationships
    contents = relationship("CardContents", back_populates="card", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_cards_user_workspace', 'user_id', 'workspace_id'),
        Index('idx_cards_workspace_created', 'workspace_id', 'created'),
    )


class Tags(Base):
    """Tags table - unitary and immutable tags."""
    __tablename__ = "tags"

    tag_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    tag_bitmap = Column(Integer, nullable=False)  # Integer bitmap for RoaringBitmap
    created = Column(DateTime, nullable=False, default=func.now())
    modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted = Column(DateTime, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_tags_user_workspace', 'user_id', 'workspace_id'),
        Index('idx_tags_workspace_name', 'workspace_id', 'name'),
        Index('idx_tags_bitmap', 'tag_bitmap'),
    )


class CardContents(Base):
    """Card contents table - polymorphic content storage."""
    __tablename__ = "card_contents"

    id = Column(String, primary_key=True, default=generate_uuid)
    card_id = Column(String, ForeignKey('cards.card_id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(Integer, nullable=False)  # 1=text, 2=number, 3=boolean, 4=json, 5=combined
    label = Column(String(255))
    value_text = Column(Text)
    value_number = Column(Float)
    value_boolean = Column(Boolean)
    value_json = Column(JSON)  # JSON type for PostgreSQL, TEXT for SQLite
    created = Column(DateTime, nullable=False, default=func.now())
    modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    card = relationship("Cards", back_populates="contents")


# ============ User Preferences Database Tables ============

class UserPreferences(Base):
    """User preferences table - stores UI/UX settings."""
    __tablename__ = "user_preferences"

    user_id = Column(String, primary_key=True)
    # Global settings
    start_cards_visible = Column(Boolean, default=True)
    start_cards_expanded = Column(Boolean, default=False)
    show_tag_colors = Column(Boolean, default=True)
    # UI settings
    theme = Column(String(20), default='system')
    font_family = Column(String(50), default='Inter')
    separate_user_ai_tags = Column(Boolean, default=True)
    stack_tags_vertically = Column(Boolean, default=False)
    # Timestamps
    created = Column(DateTime, nullable=False, default=func.now())
    modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    saved_views = relationship("SavedViews", back_populates="user", cascade="all, delete-orphan")


class SavedViews(Base):
    """Saved views table - stores user's saved tag combinations."""
    __tablename__ = "saved_views"

    view_id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('user_preferences.user_id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(String, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    tags_in_play = Column(JSON, nullable=False, default=list)  # JSON array of tag combinations
    created = Column(DateTime, nullable=False, default=func.now())
    modified = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserPreferences", back_populates="saved_views")

    # Indexes
    __table_args__ = (
        Index('idx_saved_views_user_workspace', 'user_id', 'workspace_id'),
    )


# ============ PostgreSQL Obfuscated Tables (Privacy Mode) ============

def create_obfuscated_cards_table(user_id: str, workspace_id: str):
    """
    Factory function to create user/workspace-specific cards table for Privacy Mode.
    These tables exist only on the PostgreSQL server for RoaringBitmap operations.
    """
    class ObfuscatedCards(Base):
        __tablename__ = f"cards_{user_id}_{workspace_id}"
        __table_args__ = {'extend_existing': True}

        user_id = Column(String, nullable=False)
        workspace_id = Column(String, nullable=False)
        card_id = Column(String, primary_key=True)
        card_integer_bitmap = Column(Integer, nullable=False, index=True)
        inverted_index_tag_bitmaps = Column(JSON, nullable=False)  # Array of tag bitmaps

    return ObfuscatedCards


def create_obfuscated_tags_table(user_id: str, workspace_id: str):
    """
    Factory function to create user/workspace-specific tags table for Privacy Mode.
    These tables exist only on the PostgreSQL server for RoaringBitmap operations.
    """
    class ObfuscatedTags(Base):
        __tablename__ = f"tags_{user_id}_{workspace_id}"
        __table_args__ = {'extend_existing': True}

        user_id = Column(String, nullable=False)
        workspace_id = Column(String, nullable=False)
        tag_id = Column(String, primary_key=True)
        tag_integer_bitmap = Column(Integer, nullable=False, index=True)

    return ObfuscatedTags