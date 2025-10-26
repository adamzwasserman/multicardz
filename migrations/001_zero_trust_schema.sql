-- ============================================================================
-- Zero-Trust Database Schema Migration
-- Version: 1.0
-- Purpose: Drop old schema and create correct zero-trust schema
-- ============================================================================

-- Drop all existing tables
DROP TABLE IF EXISTS card_tags;
DROP TABLE IF EXISTS card_summaries;
DROP TABLE IF EXISTS cards;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS lesson_state;

-- ============================================================================
-- CARDS TABLE
-- ============================================================================

CREATE TABLE cards (
    -- Minimum required fields (all tables)
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    deleted TEXT,

    -- Card-specific fields
    card_id TEXT PRIMARY KEY,
    card_bitmap INTEGER NOT NULL DEFAULT 0,
    name TEXT NOT NULL,
    description TEXT,
    tags TEXT,  -- Inverted index: comma-separated tag_ids

    -- Constraints
    CHECK (length(card_id) > 0),
    CHECK (length(name) > 0)
);

-- Cards indexes
CREATE INDEX idx_cards_user_workspace ON cards(user_id, workspace_id);
CREATE INDEX idx_cards_workspace ON cards(workspace_id);
CREATE INDEX idx_cards_deleted ON cards(deleted) WHERE deleted IS NULL;
CREATE INDEX idx_cards_modified ON cards(modified DESC);
CREATE INDEX idx_cards_bitmap ON cards(card_bitmap);

-- ============================================================================
-- CARD_CONTENTS TABLE (polymorphic content storage)
-- ============================================================================

CREATE TABLE card_contents (
    -- Minimum required fields (all tables)
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    deleted TEXT,

    -- Content-specific fields (polymorphic)
    card_id TEXT NOT NULL,
    content_id TEXT PRIMARY KEY,
    type INTEGER NOT NULL,
    label TEXT,
    value_text TEXT,
    value_number REAL,
    value_boolean INTEGER,
    value_json TEXT,

    -- REQUIRED FOREIGN KEY
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE,

    -- Constraints
    CHECK (length(card_id) > 0),
    CHECK (length(content_id) > 0)
);

-- Card contents indexes
CREATE INDEX idx_card_contents_card ON card_contents(card_id);
CREATE INDEX idx_card_contents_type ON card_contents(type);
CREATE INDEX idx_card_contents_user_workspace ON card_contents(user_id, workspace_id);
CREATE INDEX idx_card_contents_deleted ON card_contents(deleted) WHERE deleted IS NULL;

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

CREATE TABLE tags (
    -- Minimum required fields (all tables)
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    deleted TEXT,

    -- Tag-specific fields
    tag_id TEXT PRIMARY KEY,
    tag_bitmap INTEGER NOT NULL DEFAULT 0,
    tag TEXT NOT NULL,
    card_count INTEGER NOT NULL DEFAULT 0,
    tag_type INTEGER,
    color_hex TEXT,

    -- Constraints
    CHECK (length(tag_id) > 0),
    CHECK (length(tag) > 0),
    CHECK (card_count >= 0)
);

-- Tags indexes
CREATE INDEX idx_tags_user_workspace ON tags(user_id, workspace_id);
CREATE INDEX idx_tags_workspace ON tags(workspace_id);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_tags_deleted ON tags(deleted) WHERE deleted IS NULL;
CREATE INDEX idx_tags_bitmap ON tags(tag_bitmap);
CREATE INDEX idx_tags_card_count ON tags(card_count DESC);

-- ============================================================================
-- TRIGGERS FOR AUTO-MAINTAINING tags.card_count
-- ============================================================================

-- Update card_count when a card is inserted with tags
CREATE TRIGGER update_tag_card_count_on_card_insert
AFTER INSERT ON cards
WHEN NEW.tags IS NOT NULL AND NEW.tags != ''
BEGIN
    UPDATE tags
    SET card_count = card_count + 1,
        modified = datetime('now')
    WHERE tag_id IN (SELECT value FROM json_each('["' || replace(NEW.tags, ',', '","') || '"]'));
END;

-- Update card_count when a card's tags are modified
CREATE TRIGGER update_tag_card_count_on_card_update
AFTER UPDATE OF tags ON cards
BEGIN
    -- Decrement card_count for old tags
    UPDATE tags
    SET card_count = card_count - 1,
        modified = datetime('now')
    WHERE OLD.tags IS NOT NULL
      AND OLD.tags != ''
      AND tag_id IN (SELECT value FROM json_each('["' || replace(OLD.tags, ',', '","') || '"]'));

    -- Increment card_count for new tags
    UPDATE tags
    SET card_count = card_count + 1,
        modified = datetime('now')
    WHERE NEW.tags IS NOT NULL
      AND NEW.tags != ''
      AND tag_id IN (SELECT value FROM json_each('["' || replace(NEW.tags, ',', '","') || '"]'));
END;

-- Update card_count when a card is deleted
CREATE TRIGGER update_tag_card_count_on_card_delete
AFTER DELETE ON cards
WHEN OLD.tags IS NOT NULL AND OLD.tags != ''
BEGIN
    UPDATE tags
    SET card_count = card_count - 1,
        modified = datetime('now')
    WHERE tag_id IN (SELECT value FROM json_each('["' || replace(OLD.tags, ',', '","') || '"]'));
END;

-- ============================================================================
-- BITMAP SEQUENCE TRACKING
-- ============================================================================

-- Bitmap sequence tracking table for auto-generating sequential integer bitmaps
CREATE TABLE bitmap_sequences (
    sequence_name TEXT PRIMARY KEY,
    current_value INTEGER NOT NULL DEFAULT 0,
    CHECK (current_value >= 0)
);

-- Initialize sequences for cards and tags
INSERT INTO bitmap_sequences (sequence_name, current_value) VALUES ('card_bitmap_seq', 0);
INSERT INTO bitmap_sequences (sequence_name, current_value) VALUES ('tag_bitmap_seq', 0);

-- ============================================================================
-- TRIGGERS FOR AUTO-CALCULATING BITMAPS
-- ============================================================================

-- Auto-calculate card_bitmap using sequential integers
-- Note: SQLite triggers cannot use SELECT INTO, so we use a two-step process
CREATE TRIGGER auto_calculate_card_bitmap
AFTER INSERT ON cards
WHEN NEW.card_bitmap = 0
BEGIN
    UPDATE bitmap_sequences
    SET current_value = current_value + 1
    WHERE sequence_name = 'card_bitmap_seq';

    UPDATE cards
    SET card_bitmap = (SELECT current_value FROM bitmap_sequences WHERE sequence_name = 'card_bitmap_seq')
    WHERE card_id = NEW.card_id;
END;

-- Auto-calculate tag_bitmap using sequential integers
CREATE TRIGGER auto_calculate_tag_bitmap
AFTER INSERT ON tags
WHEN NEW.tag_bitmap = 0
BEGIN
    UPDATE bitmap_sequences
    SET current_value = current_value + 1
    WHERE sequence_name = 'tag_bitmap_seq';

    UPDATE tags
    SET tag_bitmap = (SELECT current_value FROM bitmap_sequences WHERE sequence_name = 'tag_bitmap_seq')
    WHERE tag_id = NEW.tag_id;
END;
