-- ============================================================================
-- Bitmap Sequence Migration
-- Version: 2.0
-- Purpose: Add bitmap sequence tracking and auto-calculation triggers
-- ============================================================================

-- Create bitmap sequence tracking table
CREATE TABLE IF NOT EXISTS bitmap_sequences (
    sequence_name TEXT PRIMARY KEY,
    current_value INTEGER NOT NULL DEFAULT 0,
    CHECK (current_value >= 0)
);

-- Initialize sequences (only if they don't exist)
INSERT OR IGNORE INTO bitmap_sequences (sequence_name, current_value) VALUES ('card_bitmap_seq', 0);
INSERT OR IGNORE INTO bitmap_sequences (sequence_name, current_value) VALUES ('tag_bitmap_seq', 0);

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS auto_calculate_card_bitmap;
DROP TRIGGER IF EXISTS auto_calculate_tag_bitmap;

-- Auto-calculate card_bitmap using sequential integers
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
