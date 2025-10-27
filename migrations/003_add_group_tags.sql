-- ============================================================================
-- Group Tags Migration
-- Version: 3.0
-- Purpose: Add group tag functionality with nested groups and polymorphic dispatch
-- ============================================================================

-- Create group tags table
CREATE TABLE IF NOT EXISTS group_tags (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visual_style TEXT DEFAULT '{}',  -- JSON stored as TEXT in SQLite
    expansion_behavior TEXT DEFAULT 'recursive',
    max_nesting_depth INTEGER DEFAULT 10,

    UNIQUE(workspace_id, name),
    CHECK (max_nesting_depth > 0 AND max_nesting_depth <= 20)
);

-- Create group membership table (many-to-many)
CREATE TABLE IF NOT EXISTS group_memberships (
    group_id TEXT NOT NULL,
    member_tag_id TEXT NOT NULL,
    member_type TEXT NOT NULL CHECK (member_type IN ('tag', 'group')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by TEXT NOT NULL,

    PRIMARY KEY (group_id, member_tag_id),
    FOREIGN KEY (group_id) REFERENCES group_tags(id) ON DELETE CASCADE,

    -- Prevent self-reference
    CHECK (group_id != member_tag_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_group_tags_workspace ON group_tags(workspace_id);
CREATE INDEX IF NOT EXISTS idx_group_tags_name ON group_tags(workspace_id, name);
CREATE INDEX IF NOT EXISTS idx_group_memberships_group ON group_memberships(group_id);
CREATE INDEX IF NOT EXISTS idx_group_memberships_member ON group_memberships(member_tag_id);
CREATE INDEX IF NOT EXISTS idx_group_memberships_type ON group_memberships(member_type);
