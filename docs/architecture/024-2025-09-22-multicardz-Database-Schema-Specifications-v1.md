# 024 multicardz Database Schema Specifications v1

## Executive Summary

This document provides comprehensive database schema specifications for multicardz's three-tier architecture: Central PostgreSQL tier for authentication/billing, Project Turso instances for high-performance card operations, and Master Customer instances for cross-project preferences. Each schema is optimized for its specific role while maintaining mathematical correctness for set theory operations and patent compliance.

**Key Schema Design Principles:**
- **Separation of Concerns**: Each tier handles distinct data domains without overlap
- **Set Theory Optimization**: RoaringBitmap inverted indexes for O(1) tag operations
- **Card Multiplicity Support**: Semantic instance proliferation without normalization constraints
- **Horizontal Scaling**: Schema designs enable unlimited customer-specific scaling
- **Performance-First**: All tables indexed for sub-millisecond query performance

**Expected Outcomes:**
- Central authentication handling 10,000+ concurrent users
- Project tier supporting 1M+ cards per workspace with <50ms queries
- Master customer tier synchronizing preferences across unlimited workspaces
- Complete data isolation between customers and subscription tiers

## Central PostgreSQL Tier Schema

### Overview and Purpose

The Central PostgreSQL tier serves as the authoritative source for authentication, authorization, billing, and customer-to-Turso instance mapping. This tier prioritizes ACID compliance for financial operations and provides the foundation for OAuth2 workspace context management.

**Core Responsibilities:**
- User authentication and OAuth2 session management
- Subscription billing and tier enforcement
- Customer-to-Turso instance routing
- Cross-customer analytics (anonymized)
- Audit logging for security events

### Schema Definition

```sql
-- ============================================================================
-- CENTRAL POSTGRESQL TIER SCHEMA
-- Version: 1.0
-- Purpose: Authentication, billing, and customer instance management
-- Performance Target: <100ms for all authentication operations
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- AUTHENTICATION AND USER MANAGEMENT
-- ============================================================================

-- Users: Core authentication entities
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    auth0_user_id TEXT UNIQUE NOT NULL,
    full_name TEXT DEFAULT '',
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    login_count INTEGER DEFAULT 0,

    -- Audit fields
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT auth0_id_format CHECK (auth0_user_id ~ '^[a-zA-Z0-9|_-]+$')
);

-- User profiles: Extended user information
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company_name TEXT,
    job_title TEXT,
    phone_number TEXT,
    timezone TEXT DEFAULT 'UTC',
    language_preference TEXT DEFAULT 'en',
    marketing_consent BOOLEAN DEFAULT FALSE,
    beta_program_participant BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INTEGER DEFAULT 1,

    -- Profile metadata
    profile_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- OAuth2 sessions with workspace context preservation
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    auth0_session_id TEXT NOT NULL,
    workspace_context TEXT, -- OAuth state parameter for workspace routing

    -- Session lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- Security metadata
    ip_address INET,
    user_agent TEXT,
    device_fingerprint TEXT,
    login_method TEXT DEFAULT 'oauth2',

    -- Security flags
    is_suspicious BOOLEAN DEFAULT FALSE,
    requires_mfa BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT valid_expiration CHECK (expires_at > created_at),
    CONSTRAINT workspace_context_format CHECK (
        workspace_context IS NULL OR
        workspace_context ~ '^workspace=[a-zA-Z0-9_-]+(&[a-zA-Z0-9_]+=.*)*$'
    )
);

-- Session events: Detailed session activity tracking
CREATE TABLE session_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,

    -- Event classification
    CONSTRAINT valid_event_type CHECK (
        event_type IN ('login', 'logout', 'token_refresh', 'workspace_switch', 'suspicious_activity')
    )
);

-- ============================================================================
-- SUBSCRIPTION AND BILLING MANAGEMENT
-- ============================================================================

-- Subscription plans: Available tiers and pricing
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_name TEXT UNIQUE NOT NULL,
    plan_tier TEXT NOT NULL CHECK (plan_tier IN ('free', 'basic', 'premium', 'enterprise')),
    monthly_price_cents INTEGER NOT NULL DEFAULT 0,
    annual_price_cents INTEGER NOT NULL DEFAULT 0,

    -- Limits and features
    max_workspaces INTEGER NOT NULL DEFAULT 1,
    max_cards_per_workspace INTEGER NOT NULL DEFAULT 100,
    max_storage_gb INTEGER NOT NULL DEFAULT 1,
    max_team_members INTEGER NOT NULL DEFAULT 1,

    -- Feature flags
    features JSONB DEFAULT '{}',

    -- Plan lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT positive_pricing CHECK (monthly_price_cents >= 0 AND annual_price_cents >= 0),
    CONSTRAINT reasonable_limits CHECK (
        max_workspaces > 0 AND
        max_cards_per_workspace > 0 AND
        max_storage_gb > 0 AND
        max_team_members > 0
    )
);

-- User subscriptions: Active subscription management
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),

    -- Subscription status
    status TEXT NOT NULL CHECK (status IN ('active', 'trialing', 'past_due', 'canceled', 'unpaid')),

    -- Billing cycle
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    trial_end TIMESTAMPTZ,
    canceled_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    -- Payment integration
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,

    -- Usage tracking
    current_workspaces INTEGER DEFAULT 0,
    current_cards INTEGER DEFAULT 0,
    current_storage_bytes BIGINT DEFAULT 0,

    -- Subscription lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_period CHECK (current_period_end > current_period_start),
    CONSTRAINT valid_trial CHECK (trial_end IS NULL OR trial_end > created_at),
    CONSTRAINT positive_usage CHECK (
        current_workspaces >= 0 AND
        current_cards >= 0 AND
        current_storage_bytes >= 0
    )
);

-- Billing events: Payment and subscription change history
CREATE TABLE billing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',

    -- Financial data
    amount_cents INTEGER,
    currency TEXT DEFAULT 'USD',

    -- Event metadata
    stripe_event_id TEXT UNIQUE,
    processed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Event classification
    CONSTRAINT valid_billing_event CHECK (
        event_type IN (
            'subscription_created', 'subscription_updated', 'subscription_deleted',
            'invoice_created', 'invoice_paid', 'invoice_payment_failed',
            'plan_changed', 'trial_started', 'trial_ended'
        )
    )
);

-- ============================================================================
-- TURSO INSTANCE MANAGEMENT
-- ============================================================================

-- Customer Turso instances: Mapping users to their database instances
CREATE TABLE customer_turso_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL,

    -- Turso connection details
    turso_database_name TEXT NOT NULL,
    turso_database_url TEXT NOT NULL,
    turso_auth_token_hash TEXT NOT NULL, -- Hashed token for security
    turso_region TEXT DEFAULT 'default',

    -- Instance classification
    instance_type TEXT NOT NULL CHECK (instance_type IN ('project', 'master_customer')),
    tier_level TEXT NOT NULL CHECK (tier_level IN ('shared', 'dedicated', 'enterprise')),
    is_primary BOOLEAN DEFAULT FALSE,

    -- Instance lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    provisioning_status TEXT DEFAULT 'pending' CHECK (
        provisioning_status IN ('pending', 'provisioning', 'active', 'error', 'decommissioned')
    ),

    -- Usage tracking
    storage_used_bytes BIGINT DEFAULT 0,
    query_count_today INTEGER DEFAULT 0,
    last_backup_at TIMESTAMPTZ,

    -- Unique constraints
    UNIQUE(user_id, workspace_id, instance_type),

    -- Business logic constraints
    CONSTRAINT valid_workspace_id CHECK (workspace_id ~ '^[a-zA-Z0-9_-]+$'),
    CONSTRAINT turso_name_format CHECK (turso_database_name ~ '^[a-zA-Z0-9_-]+$')
);

-- Turso instance events: Provisioning and lifecycle events
CREATE TABLE turso_instance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instance_id UUID NOT NULL REFERENCES customer_turso_instances(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',

    -- Event timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    duration_ms INTEGER,

    -- Event status
    success BOOLEAN,
    error_message TEXT,

    -- Event classification
    CONSTRAINT valid_instance_event CHECK (
        event_type IN (
            'provision_requested', 'provision_started', 'provision_completed',
            'backup_started', 'backup_completed', 'migration_started', 'migration_completed',
            'decommission_requested', 'decommission_completed', 'health_check_failed'
        )
    )
);

-- ============================================================================
-- ORGANIZATION AND TEAM MANAGEMENT
-- ============================================================================

-- Organizations: Multi-tenant organization support
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,

    -- Organization metadata
    description TEXT,
    website_url TEXT,
    logo_url TEXT,

    -- Billing
    billing_email TEXT,
    tax_id TEXT,

    -- Organization settings
    settings JSONB DEFAULT '{}',

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT slug_format CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT org_name_length CHECK (length(name) >= 2 AND length(name) <= 100)
);

-- Organization members: User-organization relationships
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role and permissions
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}',

    -- Membership lifecycle
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    joined_at TIMESTAMPTZ,
    invited_by UUID REFERENCES users(id),

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended')),

    -- Unique membership
    UNIQUE(organization_id, user_id)
);

-- ============================================================================
-- AUDIT AND COMPLIANCE
-- ============================================================================

-- Audit log: Comprehensive activity tracking
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Actor information
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    organization_id UUID REFERENCES organizations(id),

    -- Action details
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,

    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,

    -- Change tracking
    old_values JSONB,
    new_values JSONB,

    -- Event metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Data retention
    retention_days INTEGER DEFAULT 2555, -- 7 years for compliance

    -- Performance index hint
    CONSTRAINT audit_action_format CHECK (action ~ '^[a-z_]+$')
);

-- GDPR compliance: Data processing records
CREATE TABLE data_processing_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Processing details
    processing_purpose TEXT NOT NULL,
    legal_basis TEXT NOT NULL,
    data_categories JSONB NOT NULL,

    -- Consent management
    consent_given BOOLEAN DEFAULT FALSE,
    consent_withdrawn BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMPTZ,

    -- Retention
    retention_period_days INTEGER NOT NULL,
    delete_after TIMESTAMPTZ,

    -- Record lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Compliance constraints
    CONSTRAINT valid_legal_basis CHECK (
        legal_basis IN ('consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests')
    )
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- ============================================================================

-- User authentication indexes
CREATE INDEX idx_users_auth0_id ON users(auth0_user_id) WHERE is_active = true;
CREATE INDEX idx_users_email ON users(email) WHERE is_active = true;
CREATE INDEX idx_users_last_login ON users(last_login DESC);

-- Session management indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id) WHERE is_active = true;
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at) WHERE is_active = true;
CREATE INDEX idx_sessions_workspace_context ON user_sessions(workspace_context) WHERE workspace_context IS NOT NULL;
CREATE INDEX idx_sessions_auth0_session ON user_sessions(auth0_session_id);

-- Subscription and billing indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status) WHERE status = 'active';
CREATE INDEX idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
CREATE INDEX idx_billing_events_subscription ON billing_events(subscription_id);
CREATE INDEX idx_billing_events_processed ON billing_events(processed_at DESC);

-- Turso instance management indexes
CREATE INDEX idx_turso_instances_user_workspace ON customer_turso_instances(user_id, workspace_id);
CREATE INDEX idx_turso_instances_type ON customer_turso_instances(instance_type, tier_level);
CREATE INDEX idx_turso_instances_active ON customer_turso_instances(is_active, provisioning_status);
CREATE INDEX idx_turso_instances_last_accessed ON customer_turso_instances(last_accessed DESC);

-- Organization indexes
CREATE INDEX idx_org_members_org_id ON organization_members(organization_id) WHERE status = 'active';
CREATE INDEX idx_org_members_user_id ON organization_members(user_id) WHERE status = 'active';

-- Audit and compliance indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action, created_at DESC);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_retention ON audit_log(created_at) WHERE retention_days IS NOT NULL;

-- ============================================================================
-- DATA RETENTION AND CLEANUP
-- ============================================================================

-- Automated cleanup function for expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW() - INTERVAL '1 day'
    AND is_active = false;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    INSERT INTO audit_log (action, resource_type, new_values)
    VALUES ('cleanup_expired_sessions', 'user_sessions',
            jsonb_build_object('deleted_count', deleted_count));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Automated cleanup function for old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

### Central Tier Relationship Mappings

**Primary Relationships:**
```
users (1) → (∞) user_sessions
users (1) → (1) user_profiles
users (1) → (∞) subscriptions
users (1) → (∞) customer_turso_instances
users (∞) → (∞) organizations (via organization_members)

subscriptions (∞) → (1) subscription_plans
subscriptions (1) → (∞) billing_events

customer_turso_instances (1) → (∞) turso_instance_events
```

**Business Rules:**
- One active subscription per user (enforced at application level)
- One master customer instance per user
- Multiple project instances per user (limited by subscription)
- Organization membership requires active user account
- Audit logs retain for 7 years for compliance

## Project Turso Tier Schema

### Overview and Purpose

The Project Turso tier contains workspace-specific data optimized for high-performance tag operations and card manipulation. Each workspace gets its own Turso instance, providing complete data isolation and unlimited horizontal scaling.

**Core Responsibilities:**
- High-performance card storage with CardSummary/CardDetail separation
- RoaringBitmap inverted indexes for O(1) tag operations
- Normalized tag schema for million-card scalability
- System tag operation history and audit trail
- Workspace-specific user preferences and UI state

### Schema Definition

```sql
-- ============================================================================
-- PROJECT TURSO TIER SCHEMA (Per Workspace Instance)
-- Version: 1.0
-- Purpose: High-performance card operations and tag manipulation
-- Performance Target: <50ms for 1M+ card operations
-- ============================================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Performance optimizations for Turso/SQLite
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456; -- 256MB memory mapping

-- ============================================================================
-- CARD STORAGE SYSTEM
-- ============================================================================

-- Card summaries: Optimized for list operations (~50 bytes per card)
CREATE TABLE card_summaries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL, -- ISO format for SQLite compatibility
    modified_at TEXT NOT NULL, -- ISO format for SQLite compatibility
    has_attachments BOOLEAN DEFAULT FALSE,

    -- Workspace isolation
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL, -- Creator/owner

    -- Content preview for fast rendering
    preview_text TEXT DEFAULT '',
    word_count INTEGER DEFAULT 0,

    -- Card state
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TEXT,

    -- Performance hints
    tag_count INTEGER DEFAULT 0,
    last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- Constraints
    CHECK (length(id) > 0),
    CHECK (length(title) > 0),
    CHECK (word_count >= 0),
    CHECK (tag_count >= 0),
    CHECK (access_count >= 0)
);

-- Card details: On-demand loading for full content
CREATE TABLE card_details (
    id TEXT PRIMARY KEY REFERENCES card_summaries(id) ON DELETE CASCADE,
    content TEXT DEFAULT '',
    content_type TEXT DEFAULT 'markdown',

    -- Rich metadata
    metadata_json TEXT DEFAULT '{}',

    -- Attachment management
    attachment_count INTEGER DEFAULT 0,
    total_attachment_size INTEGER DEFAULT 0,

    -- Version control
    version INTEGER DEFAULT 1,
    content_hash TEXT, -- For change detection

    -- Full-text search support
    search_vector TEXT DEFAULT '', -- Preprocessed search content

    -- Constraints
    CHECK (attachment_count >= 0),
    CHECK (total_attachment_size >= 0),
    CHECK (version >= 1)
);

-- ============================================================================
-- NORMALIZED TAG SYSTEM FOR SCALE
-- ============================================================================

-- Tags: Normalized tag storage for million-card scalability
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,

    -- Usage analytics
    usage_count INTEGER DEFAULT 0,
    first_used TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Tag metadata
    tag_type TEXT DEFAULT 'user', -- 'user', 'system', 'auto'
    color_hex TEXT,
    description TEXT,

    -- Hierarchy support
    parent_tag_id INTEGER REFERENCES tags(id),
    tag_level INTEGER DEFAULT 0,

    -- Tag lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    -- Constraints
    CHECK (length(name) > 0),
    CHECK (usage_count >= 0),
    CHECK (tag_level >= 0),
    CHECK (tag_type IN ('user', 'system', 'auto')),
    CHECK (color_hex IS NULL OR color_hex GLOB '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]')
);

-- Card-tag relationships: Core of set operations
CREATE TABLE card_tags (
    card_id TEXT NOT NULL REFERENCES card_summaries(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id),

    -- Relationship metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,

    -- Tag application context
    confidence REAL DEFAULT 1.0, -- For auto-tagged content
    source TEXT DEFAULT 'user', -- 'user', 'system', 'ai', 'import'

    -- Primary key
    PRIMARY KEY (card_id, tag_id),

    -- Constraints
    CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CHECK (source IN ('user', 'system', 'ai', 'import'))
);

-- ============================================================================
-- ROARINGBITMAP INVERTED INDEXES
-- ============================================================================

-- Tag inverted indexes: RoaringBitmap storage for O(1) set operations
CREATE TABLE tag_inverted_index (
    tag_id INTEGER PRIMARY KEY REFERENCES tags(id) ON DELETE CASCADE,

    -- Compressed bitmap data
    card_bitmap BLOB NOT NULL, -- RoaringBitmap serialized binary
    bitmap_version INTEGER DEFAULT 1,

    -- Index statistics
    card_count INTEGER NOT NULL DEFAULT 0,
    compression_ratio REAL, -- Original size / compressed size

    -- Index lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    last_rebuild TEXT,

    -- Index health
    is_valid BOOLEAN DEFAULT TRUE,
    needs_rebuild BOOLEAN DEFAULT FALSE,

    -- Constraints
    CHECK (card_count >= 0),
    CHECK (bitmap_version >= 1),
    CHECK (compression_ratio IS NULL OR compression_ratio > 0)
);

-- Bitmap index metadata: Statistics and performance tracking
CREATE TABLE bitmap_index_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id INTEGER NOT NULL REFERENCES tags(id),

    -- Performance metrics
    operation_type TEXT NOT NULL, -- 'rebuild', 'update', 'query'
    duration_ms INTEGER NOT NULL,
    cards_processed INTEGER NOT NULL,

    -- Memory usage
    memory_used_bytes INTEGER,
    compression_achieved REAL,

    -- Operation context
    triggered_by TEXT NOT NULL, -- 'schedule', 'manual', 'auto'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (operation_type IN ('rebuild', 'update', 'query')),
    CHECK (duration_ms >= 0),
    CHECK (cards_processed >= 0),
    CHECK (triggered_by IN ('schedule', 'manual', 'auto'))
);

-- ============================================================================
-- SYSTEM TAG OPERATIONS
-- ============================================================================

-- System tag functions: Definitions for COUNT, SUM, MIGRATE_SPRINT, etc.
CREATE TABLE system_tag_functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT UNIQUE NOT NULL,
    function_type TEXT NOT NULL, -- 'operator', 'modifier', 'mutation'

    -- Function definition
    description TEXT NOT NULL,
    parameters_schema TEXT, -- JSON schema for function parameters
    output_schema TEXT, -- JSON schema for function output

    -- Implementation details
    implementation_version TEXT DEFAULT '1.0',
    python_function_name TEXT, -- Maps to Python function

    -- Function lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (function_type IN ('operator', 'modifier', 'mutation')),
    CHECK (length(function_name) > 0),
    CHECK (length(description) > 0)
);

-- System tag operations: History of applied system tag functions
CREATE TABLE system_tag_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    function_name TEXT NOT NULL REFERENCES system_tag_functions(function_name),

    -- Operation context
    operation_type TEXT NOT NULL, -- Same as function_type for quick filtering
    target_tags TEXT NOT NULL, -- JSON array of targeted tags
    operation_parameters TEXT DEFAULT '{}', -- JSON parameters

    -- Execution details
    affected_cards_count INTEGER NOT NULL DEFAULT 0,
    execution_time_ms REAL NOT NULL,
    memory_used_bytes INTEGER,

    -- Operation results
    operation_status TEXT DEFAULT 'completed', -- 'pending', 'running', 'completed', 'failed'
    output_data TEXT DEFAULT '{}', -- JSON operation output
    error_message TEXT,

    -- Audit trail
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    workspace_id TEXT NOT NULL,

    -- Undo support
    undo_operation_id INTEGER REFERENCES system_tag_operations(id),
    can_undo BOOLEAN DEFAULT FALSE,
    undo_data TEXT, -- JSON data for undo operation

    -- Constraints
    CHECK (operation_type IN ('operator', 'modifier', 'mutation')),
    CHECK (affected_cards_count >= 0),
    CHECK (execution_time_ms >= 0),
    CHECK (operation_status IN ('pending', 'running', 'completed', 'failed'))
);

-- ============================================================================
-- USER PREFERENCES AND UI STATE
-- ============================================================================

-- User preferences: Workspace-specific user settings
CREATE TABLE user_preferences (
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,

    -- Zone visibility state (spatial interface)
    zone_visibility_state TEXT DEFAULT '{}', -- JSON: {zone_id: boolean}
    zone_layout_config TEXT DEFAULT '{}', -- JSON: zone positions and sizes

    -- UI preferences
    ui_theme TEXT DEFAULT 'light',
    card_view_mode TEXT DEFAULT 'grid', -- 'grid', 'list', 'kanban'
    cards_per_page INTEGER DEFAULT 50,

    -- Sorting and filtering defaults
    default_sort_field TEXT DEFAULT 'modified_at',
    default_sort_direction TEXT DEFAULT 'desc',
    default_filters TEXT DEFAULT '{}', -- JSON filter state

    -- Keyboard shortcuts
    keyboard_shortcuts TEXT DEFAULT '{}', -- JSON: {action: key_combination}

    -- Feature flags
    feature_flags TEXT DEFAULT '{}', -- JSON: {feature: enabled}
    beta_features_enabled BOOLEAN DEFAULT FALSE,

    -- Accessibility settings
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    large_font_size BOOLEAN DEFAULT FALSE,
    reduce_animations BOOLEAN DEFAULT FALSE,

    -- Preferences lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Primary key
    PRIMARY KEY (user_id, workspace_id),

    -- Constraints
    CHECK (ui_theme IN ('light', 'dark', 'auto')),
    CHECK (card_view_mode IN ('grid', 'list', 'kanban')),
    CHECK (cards_per_page > 0 AND cards_per_page <= 200),
    CHECK (default_sort_direction IN ('asc', 'desc'))
);

-- User activity: Track user interactions for analytics
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,

    -- Activity details
    activity_type TEXT NOT NULL,
    activity_data TEXT DEFAULT '{}', -- JSON activity context

    -- Target entities
    card_id TEXT,
    tag_id INTEGER,

    -- Activity metadata
    session_id TEXT,
    ip_address TEXT,
    user_agent TEXT,

    -- Timing
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER, -- For activities with duration

    -- Activity classification
    CHECK (activity_type IN (
        'card_created', 'card_updated', 'card_deleted', 'card_viewed',
        'tag_applied', 'tag_removed', 'tag_created',
        'filter_applied', 'search_performed', 'export_requested',
        'system_tag_executed', 'workspace_accessed'
    ))
);

-- ============================================================================
-- COLLABORATION AND SHARING
-- ============================================================================

-- Workspace collaborators: User access control within workspace
CREATE TABLE workspace_collaborators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    -- Access control
    role TEXT NOT NULL, -- 'owner', 'editor', 'viewer'
    permissions TEXT DEFAULT '{}', -- JSON: granular permissions

    -- Collaboration state
    invitation_status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'declined'
    invited_by TEXT NOT NULL,
    invited_at TEXT DEFAULT CURRENT_TIMESTAMP,
    joined_at TEXT,

    -- Access restrictions
    can_create_cards BOOLEAN DEFAULT TRUE,
    can_edit_cards BOOLEAN DEFAULT TRUE,
    can_delete_cards BOOLEAN DEFAULT FALSE,
    can_manage_tags BOOLEAN DEFAULT FALSE,
    can_invite_others BOOLEAN DEFAULT FALSE,

    -- Unique collaboration
    UNIQUE(workspace_id, user_id),

    -- Constraints
    CHECK (role IN ('owner', 'editor', 'viewer')),
    CHECK (invitation_status IN ('pending', 'accepted', 'declined'))
);

-- Card comments: Collaboration through card-level comments
CREATE TABLE card_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES card_summaries(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,

    -- Comment content
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'markdown',

    -- Comment threading
    parent_comment_id INTEGER REFERENCES card_comments(id),
    thread_level INTEGER DEFAULT 0,

    -- Comment lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TEXT,

    -- Mention support
    mentions TEXT DEFAULT '[]', -- JSON array of mentioned user_ids

    -- Constraints
    CHECK (length(content) > 0),
    CHECK (thread_level >= 0),
    CHECK (content_type IN ('markdown', 'plain_text'))
);

-- ============================================================================
-- ATTACHMENTS AND MEDIA
-- ============================================================================

-- Attachments: BLOB storage for workspace-specific files
CREATE TABLE attachments (
    id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES card_summaries(id) ON DELETE CASCADE,

    -- File metadata
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,

    -- File storage
    data BLOB NOT NULL,
    thumbnail_data BLOB, -- Small preview for images

    -- File processing
    file_hash TEXT NOT NULL, -- SHA-256 for deduplication
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',

    -- Upload metadata
    uploaded_by TEXT NOT NULL,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,

    -- Access control
    is_public BOOLEAN DEFAULT FALSE,
    access_key TEXT, -- For secure public access

    -- Constraints
    CHECK (size_bytes > 0),
    CHECK (length(filename) > 0),
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- ============================================================================
-- WORKSPACE METADATA
-- ============================================================================

-- Workspace settings: Configuration for the workspace instance
CREATE TABLE workspace_settings (
    workspace_id TEXT PRIMARY KEY,
    workspace_name TEXT NOT NULL,

    -- Workspace metadata
    description TEXT DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Workspace configuration
    is_public BOOLEAN DEFAULT FALSE,
    default_card_template TEXT DEFAULT '',
    auto_tag_rules TEXT DEFAULT '[]', -- JSON array of auto-tagging rules

    -- Workspace limits (enforced by subscription)
    max_cards INTEGER DEFAULT 1000,
    max_storage_bytes INTEGER DEFAULT 1073741824, -- 1GB default
    max_collaborators INTEGER DEFAULT 5,

    -- Feature configuration
    features_enabled TEXT DEFAULT '{}', -- JSON feature flags
    integrations_config TEXT DEFAULT '{}', -- JSON integration settings

    -- Workspace lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    archived_at TEXT,

    -- Constraints
    CHECK (length(workspace_name) > 0),
    CHECK (max_cards > 0),
    CHECK (max_storage_bytes > 0),
    CHECK (max_collaborators > 0)
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- ============================================================================

-- Card summary indexes for fast list operations
CREATE INDEX idx_card_summaries_workspace ON card_summaries(workspace_id, is_deleted, modified_at DESC);
CREATE INDEX idx_card_summaries_user ON card_summaries(user_id, is_deleted);
CREATE INDEX idx_card_summaries_title ON card_summaries(title) WHERE is_deleted = FALSE;
CREATE INDEX idx_card_summaries_has_attachments ON card_summaries(has_attachments) WHERE has_attachments = TRUE;
CREATE INDEX idx_card_summaries_archived ON card_summaries(is_archived, archived_at);

-- Tag system indexes for O(1) lookups
CREATE INDEX idx_tags_name ON tags(name) WHERE is_active = TRUE;
CREATE INDEX idx_tags_usage_count ON tags(usage_count DESC) WHERE is_active = TRUE;
CREATE INDEX idx_tags_type ON tags(tag_type, is_active);
CREATE INDEX idx_tags_parent ON tags(parent_tag_id) WHERE parent_tag_id IS NOT NULL;

-- Card-tag relationship indexes for set operations
CREATE INDEX idx_card_tags_card ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag ON card_tags(tag_id);
CREATE INDEX idx_card_tags_source ON card_tags(source, created_at);
CREATE INDEX idx_card_tags_confidence ON card_tags(confidence DESC) WHERE source = 'ai';

-- RoaringBitmap index optimization
CREATE INDEX idx_bitmap_index_tag ON tag_inverted_index(tag_id, is_valid);
CREATE INDEX idx_bitmap_index_updated ON tag_inverted_index(last_updated DESC) WHERE needs_rebuild = TRUE;
CREATE INDEX idx_bitmap_stats_tag ON bitmap_index_stats(tag_id, created_at DESC);

-- System tag operation indexes
CREATE INDEX idx_system_operations_user ON system_tag_operations(user_id, executed_at DESC);
CREATE INDEX idx_system_operations_function ON system_tag_operations(function_name, operation_status);
CREATE INDEX idx_system_operations_workspace ON system_tag_operations(workspace_id, executed_at DESC);
CREATE INDEX idx_system_operations_undo ON system_tag_operations(can_undo, executed_at DESC) WHERE can_undo = TRUE;

-- User preference and activity indexes
CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_user_activity_user_workspace ON user_activity(user_id, workspace_id, created_at DESC);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type, created_at DESC);

-- Collaboration indexes
CREATE INDEX idx_workspace_collaborators_workspace ON workspace_collaborators(workspace_id, invitation_status);
CREATE INDEX idx_workspace_collaborators_user ON workspace_collaborators(user_id, invitation_status);
CREATE INDEX idx_card_comments_card ON card_comments(card_id, is_deleted, created_at DESC);
CREATE INDEX idx_card_comments_user ON card_comments(user_id, created_at DESC);

-- Attachment indexes
CREATE INDEX idx_attachments_card ON attachments(card_id);
CREATE INDEX idx_attachments_hash ON attachments(file_hash);
CREATE INDEX idx_attachments_uploaded ON attachments(uploaded_by, uploaded_at DESC);
CREATE INDEX idx_attachments_public ON attachments(is_public, access_key) WHERE is_public = TRUE;

-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY AND AUTOMATION
-- ============================================================================

-- Update tag usage count when card-tag relationships change
CREATE TRIGGER update_tag_usage_count_insert
AFTER INSERT ON card_tags
BEGIN
    UPDATE tags
    SET usage_count = usage_count + 1,
        last_used = CURRENT_TIMESTAMP
    WHERE id = NEW.tag_id;

    -- Update card tag count
    UPDATE card_summaries
    SET tag_count = (
        SELECT COUNT(*) FROM card_tags WHERE card_id = NEW.card_id
    )
    WHERE id = NEW.card_id;
END;

CREATE TRIGGER update_tag_usage_count_delete
AFTER DELETE ON card_tags
BEGIN
    UPDATE tags
    SET usage_count = usage_count - 1
    WHERE id = OLD.tag_id;

    -- Update card tag count
    UPDATE card_summaries
    SET tag_count = (
        SELECT COUNT(*) FROM card_tags WHERE card_id = OLD.card_id
    )
    WHERE id = OLD.card_id;
END;

-- Update card summary when details change
CREATE TRIGGER update_card_summary_on_detail_change
AFTER UPDATE ON card_details
BEGIN
    UPDATE card_summaries
    SET modified_at = CURRENT_TIMESTAMP,
        word_count = (
            CASE
                WHEN NEW.content_type = 'markdown' THEN
                    LENGTH(NEW.content) - LENGTH(REPLACE(NEW.content, ' ', '')) + 1
                ELSE
                    LENGTH(NEW.content) - LENGTH(REPLACE(NEW.content, ' ', '')) + 1
            END
        )
    WHERE id = NEW.id;
END;

-- Mark bitmap indexes for rebuild when card-tag relationships change
CREATE TRIGGER mark_bitmap_for_rebuild_on_tag_change
AFTER INSERT ON card_tags
BEGIN
    UPDATE tag_inverted_index
    SET needs_rebuild = TRUE,
        is_valid = FALSE
    WHERE tag_id = NEW.tag_id;
END;

-- Update attachment count on card summaries
CREATE TRIGGER update_attachment_count_insert
AFTER INSERT ON attachments
BEGIN
    UPDATE card_summaries
    SET has_attachments = TRUE
    WHERE id = NEW.card_id;

    UPDATE card_details
    SET attachment_count = attachment_count + 1,
        total_attachment_size = total_attachment_size + NEW.size_bytes
    WHERE id = NEW.card_id;
END;

CREATE TRIGGER update_attachment_count_delete
AFTER DELETE ON attachments
BEGIN
    UPDATE card_details
    SET attachment_count = attachment_count - 1,
        total_attachment_size = total_attachment_size - OLD.size_bytes
    WHERE id = OLD.card_id;

    -- Update has_attachments flag
    UPDATE card_summaries
    SET has_attachments = (
        SELECT COUNT(*) > 0 FROM attachments WHERE card_id = OLD.card_id
    )
    WHERE id = OLD.card_id;
END;
```

### Project Tier Performance Optimizations

**RoaringBitmap Integration Points:**
```python
# Example bitmap operations for tag filtering
def create_roaring_bitmap_from_cards(card_ids: list[str]) -> roaringbitmap.RoaringBitmap:
    """Create RoaringBitmap from card ID list."""
    # Convert card IDs to integers for bitmap storage
    card_indices = [hash(card_id) % (2**32) for card_id in card_ids]
    return roaringbitmap.RoaringBitmap(card_indices)

def update_tag_bitmap_index(tag_id: int, card_ids: list[str], connection):
    """Update RoaringBitmap index for tag."""
    bitmap = create_roaring_bitmap_from_cards(card_ids)
    serialized_bitmap = bitmap.serialize()

    connection.execute(
        "UPDATE tag_inverted_index SET card_bitmap = ?, last_updated = ?, needs_rebuild = FALSE WHERE tag_id = ?",
        (serialized_bitmap, datetime.utcnow().isoformat(), tag_id)
    )
```

## Master Customer Tier Schema

### Overview and Purpose

The Master Customer tier maintains cross-project user data, global preferences, and customer-level analytics. Each customer gets one master instance that synchronizes data across all their project workspaces.

**Core Responsibilities:**
- Cross-project user preferences synchronization
- Global UI state persistence (themes, layouts, shortcuts)
- Workspace access history and favorites management
- Customer-level usage analytics and insights
- Cross-workspace search history and patterns

### Schema Definition

```sql
-- ============================================================================
-- MASTER CUSTOMER TIER SCHEMA (Per Customer Instance)
-- Version: 1.0
-- Purpose: Cross-project preferences and customer-level data
-- Performance Target: <200ms for preference synchronization
-- ============================================================================

-- Enable foreign key constraints and optimizations
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;

-- ============================================================================
-- GLOBAL USER PREFERENCES
-- ============================================================================

-- Global user preferences: Settings that apply across all workspaces
CREATE TABLE global_user_preferences (
    user_id TEXT PRIMARY KEY,

    -- UI/UX preferences
    default_theme TEXT DEFAULT 'light',
    animation_speed TEXT DEFAULT 'normal', -- 'slow', 'normal', 'fast'
    compact_mode BOOLEAN DEFAULT FALSE,

    -- Notification preferences
    notification_settings TEXT DEFAULT '{}', -- JSON notification config
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    digest_frequency TEXT DEFAULT 'weekly', -- 'never', 'daily', 'weekly', 'monthly'

    -- Keyboard shortcuts (global)
    keyboard_shortcuts TEXT DEFAULT '{}', -- JSON: {action: key_combination}
    custom_shortcuts TEXT DEFAULT '{}', -- JSON: user-defined shortcuts

    -- Accessibility settings
    accessibility_settings TEXT DEFAULT '{}', -- JSON accessibility config
    high_contrast_mode BOOLEAN DEFAULT FALSE,
    large_font_size BOOLEAN DEFAULT FALSE,
    reduce_animations BOOLEAN DEFAULT FALSE,
    screen_reader_mode BOOLEAN DEFAULT FALSE,

    -- Language and localization
    language_preference TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    date_format TEXT DEFAULT 'YYYY-MM-DD',
    time_format TEXT DEFAULT '24h', -- '12h', '24h'

    -- Privacy preferences
    analytics_consent BOOLEAN DEFAULT TRUE,
    data_sharing_consent BOOLEAN DEFAULT FALSE,
    marketing_consent BOOLEAN DEFAULT FALSE,

    -- Preferences lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (default_theme IN ('light', 'dark', 'auto')),
    CHECK (animation_speed IN ('slow', 'normal', 'fast')),
    CHECK (digest_frequency IN ('never', 'daily', 'weekly', 'monthly')),
    CHECK (time_format IN ('12h', '24h'))
);

-- Preference sync log: Track cross-workspace preference synchronization
CREATE TABLE preference_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES global_user_preferences(user_id),

    -- Sync details
    sync_type TEXT NOT NULL, -- 'push', 'pull', 'conflict_resolution'
    workspace_id TEXT NOT NULL,

    -- Sync data
    preference_key TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Sync metadata
    sync_source TEXT NOT NULL, -- 'user_action', 'scheduled', 'manual'
    sync_direction TEXT NOT NULL, -- 'workspace_to_master', 'master_to_workspace'

    -- Sync result
    sync_status TEXT DEFAULT 'completed', -- 'pending', 'completed', 'failed', 'conflict'
    error_message TEXT,

    -- Timing
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,

    -- Constraints
    CHECK (sync_type IN ('push', 'pull', 'conflict_resolution')),
    CHECK (sync_source IN ('user_action', 'scheduled', 'manual')),
    CHECK (sync_direction IN ('workspace_to_master', 'master_to_workspace')),
    CHECK (sync_status IN ('pending', 'completed', 'failed', 'conflict'))
);

-- ============================================================================
-- WORKSPACE MANAGEMENT
-- ============================================================================

-- Workspace access history: Track user access patterns across workspaces
CREATE TABLE workspace_access_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,

    -- Workspace metadata
    workspace_name TEXT NOT NULL,
    workspace_description TEXT DEFAULT '',

    -- Access tracking
    first_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
    last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    total_time_spent_minutes INTEGER DEFAULT 0,

    -- User relationship to workspace
    user_role TEXT DEFAULT 'member', -- 'owner', 'admin', 'member', 'viewer'
    is_favorite BOOLEAN DEFAULT FALSE,
    favorite_since TEXT,

    -- Workspace status
    is_active BOOLEAN DEFAULT TRUE,
    archived_at TEXT,
    access_revoked_at TEXT,

    -- Access patterns
    preferred_view_mode TEXT DEFAULT 'grid',
    most_used_features TEXT DEFAULT '[]', -- JSON array of feature names

    -- Unique workspace per user
    UNIQUE(user_id, workspace_id),

    -- Constraints
    CHECK (access_count > 0),
    CHECK (total_time_spent_minutes >= 0),
    CHECK (user_role IN ('owner', 'admin', 'member', 'viewer')),
    CHECK (preferred_view_mode IN ('grid', 'list', 'kanban'))
);

-- Workspace favorites: Quick access to frequently used workspaces
CREATE TABLE workspace_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,

    -- Favorite metadata
    custom_name TEXT, -- User-defined name override
    custom_description TEXT,
    custom_color TEXT, -- Hex color for visual organization

    -- Organization
    favorite_order INTEGER DEFAULT 0,
    folder_name TEXT, -- Group favorites into folders

    -- Favorite lifecycle
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 0,

    -- Unique favorite per workspace per user
    UNIQUE(user_id, workspace_id),

    -- Constraints
    CHECK (favorite_order >= 0),
    CHECK (use_count >= 0)
);

-- ============================================================================
-- CROSS-WORKSPACE SEARCH AND DISCOVERY
-- ============================================================================

-- Search history: Track search queries across all workspaces
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Search details
    search_query TEXT NOT NULL,
    search_type TEXT DEFAULT 'cards', -- 'cards', 'tags', 'users', 'all'

    -- Search context
    workspace_id TEXT, -- NULL for global searches
    search_filters TEXT DEFAULT '{}', -- JSON search filters applied

    -- Search results
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_card_id TEXT, -- Most relevant result

    -- Search performance
    execution_time_ms INTEGER,
    search_source TEXT DEFAULT 'user', -- 'user', 'autocomplete', 'suggestion'

    -- Search metadata
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,

    -- Constraints
    CHECK (search_type IN ('cards', 'tags', 'users', 'all')),
    CHECK (result_count >= 0),
    CHECK (execution_time_ms >= 0),
    CHECK (search_source IN ('user', 'autocomplete', 'suggestion'))
);

-- Popular search terms: Aggregated search analytics
CREATE TABLE popular_search_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Search term analysis
    search_term TEXT NOT NULL,
    search_count INTEGER DEFAULT 1,

    -- Term metadata
    first_searched TEXT DEFAULT CURRENT_TIMESTAMP,
    last_searched TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Success metrics
    avg_result_count REAL DEFAULT 0,
    avg_click_through_rate REAL DEFAULT 0,

    -- Term context
    most_common_workspace TEXT,
    common_filters TEXT DEFAULT '{}', -- JSON common filter patterns

    -- Unique term per user
    UNIQUE(user_id, search_term),

    -- Constraints
    CHECK (search_count > 0),
    CHECK (avg_result_count >= 0),
    CHECK (avg_click_through_rate >= 0 AND avg_click_through_rate <= 1)
);

-- ============================================================================
-- CUSTOMER ANALYTICS AND INSIGHTS
-- ============================================================================

-- Usage analytics: Privacy-preserving customer insights
CREATE TABLE usage_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Metric identification
    metric_name TEXT NOT NULL,
    metric_category TEXT NOT NULL, -- 'performance', 'feature_usage', 'content', 'collaboration'

    -- Metric data
    metric_value REAL NOT NULL,
    metric_unit TEXT DEFAULT 'count', -- 'count', 'seconds', 'bytes', 'percentage'

    -- Context
    workspace_id TEXT, -- NULL for global metrics
    feature_name TEXT,

    -- Aggregation period
    period_type TEXT DEFAULT 'daily', -- 'hourly', 'daily', 'weekly', 'monthly'
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,

    -- Metric lifecycle
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Privacy compliance
    is_anonymized BOOLEAN DEFAULT FALSE,
    retention_days INTEGER DEFAULT 90,

    -- Constraints
    CHECK (metric_category IN ('performance', 'feature_usage', 'content', 'collaboration')),
    CHECK (metric_unit IN ('count', 'seconds', 'bytes', 'percentage', 'ratio')),
    CHECK (period_type IN ('hourly', 'daily', 'weekly', 'monthly')),
    CHECK (retention_days > 0)
);

-- Feature adoption tracking: Monitor feature usage patterns
CREATE TABLE feature_adoption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Feature identification
    feature_name TEXT NOT NULL,
    feature_version TEXT DEFAULT '1.0',
    feature_category TEXT NOT NULL,

    -- Adoption metrics
    first_used TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 1,
    total_usage_time_seconds INTEGER DEFAULT 0,

    -- Usage patterns
    usage_frequency TEXT DEFAULT 'unknown', -- 'daily', 'weekly', 'monthly', 'rarely', 'unknown'
    proficiency_level TEXT DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced', 'expert'

    -- Feature context
    most_used_in_workspace TEXT,
    common_use_cases TEXT DEFAULT '[]', -- JSON array of use case descriptions

    -- User feedback
    satisfaction_rating INTEGER, -- 1-5 scale
    feedback_provided TEXT,

    -- Unique feature per user
    UNIQUE(user_id, feature_name),

    -- Constraints
    CHECK (usage_count > 0),
    CHECK (total_usage_time_seconds >= 0),
    CHECK (usage_frequency IN ('daily', 'weekly', 'monthly', 'rarely', 'unknown')),
    CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    CHECK (satisfaction_rating IS NULL OR (satisfaction_rating >= 1 AND satisfaction_rating <= 5))
);

-- ============================================================================
-- COLLABORATION INSIGHTS
-- ============================================================================

-- Cross-workspace collaboration: Track collaboration patterns
CREATE TABLE cross_workspace_collaboration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Collaboration partner
    collaborator_user_id TEXT NOT NULL,

    -- Collaboration context
    shared_workspaces TEXT NOT NULL, -- JSON array of workspace IDs
    collaboration_type TEXT NOT NULL, -- 'regular', 'occasional', 'project_based'

    -- Collaboration metrics
    first_collaboration TEXT DEFAULT CURRENT_TIMESTAMP,
    last_collaboration TEXT DEFAULT CURRENT_TIMESTAMP,
    collaboration_count INTEGER DEFAULT 1,

    -- Collaboration patterns
    common_activities TEXT DEFAULT '[]', -- JSON array of activity types
    most_active_workspace TEXT,

    -- Relationship status
    is_active BOOLEAN DEFAULT TRUE,
    blocked_at TEXT,

    -- Unique collaboration pair
    UNIQUE(user_id, collaborator_user_id),

    -- Constraints
    CHECK (collaboration_type IN ('regular', 'occasional', 'project_based')),
    CHECK (collaboration_count > 0)
);

-- Sharing patterns: Track how users share content
CREATE TABLE sharing_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Sharing details
    content_type TEXT NOT NULL, -- 'card', 'workspace', 'tag_collection'
    sharing_method TEXT NOT NULL, -- 'link', 'email', 'export', 'embed'

    -- Sharing frequency
    share_count INTEGER DEFAULT 1,
    first_shared TEXT DEFAULT CURRENT_TIMESTAMP,
    last_shared TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Sharing preferences
    default_permissions TEXT DEFAULT 'view', -- 'view', 'comment', 'edit'
    privacy_preference TEXT DEFAULT 'private', -- 'private', 'team', 'public'

    -- Sharing success
    avg_engagement_rate REAL DEFAULT 0, -- 0-1 scale

    -- Unique sharing pattern per user per type
    UNIQUE(user_id, content_type, sharing_method),

    -- Constraints
    CHECK (content_type IN ('card', 'workspace', 'tag_collection')),
    CHECK (sharing_method IN ('link', 'email', 'export', 'embed')),
    CHECK (share_count > 0),
    CHECK (default_permissions IN ('view', 'comment', 'edit')),
    CHECK (privacy_preference IN ('private', 'team', 'public')),
    CHECK (avg_engagement_rate >= 0 AND avg_engagement_rate <= 1)
);

-- ============================================================================
-- SYSTEM INTEGRATIONS AND EXPORTS
-- ============================================================================

-- Integration connections: External service connections
CREATE TABLE integration_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Integration details
    service_name TEXT NOT NULL, -- 'google_drive', 'dropbox', 'slack', 'notion', etc.
    service_type TEXT NOT NULL, -- 'storage', 'communication', 'productivity', 'analytics'

    -- Connection metadata
    connection_name TEXT NOT NULL, -- User-friendly name
    connection_config TEXT DEFAULT '{}', -- JSON configuration

    -- Authentication
    auth_type TEXT NOT NULL, -- 'oauth2', 'api_key', 'webhook'
    auth_data_hash TEXT NOT NULL, -- Hashed authentication data

    -- Connection status
    is_active BOOLEAN DEFAULT TRUE,
    last_successful_sync TEXT,
    last_sync_attempt TEXT,
    sync_error_count INTEGER DEFAULT 0,

    -- Connection lifecycle
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT, -- For token-based auth

    -- Constraints
    CHECK (service_type IN ('storage', 'communication', 'productivity', 'analytics')),
    CHECK (auth_type IN ('oauth2', 'api_key', 'webhook')),
    CHECK (sync_error_count >= 0)
);

-- Export history: Track data exports and backups
CREATE TABLE export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,

    -- Export details
    export_type TEXT NOT NULL, -- 'full_backup', 'workspace_export', 'card_export', 'preferences_export'
    export_format TEXT NOT NULL, -- 'json', 'csv', 'markdown', 'pdf'

    -- Export scope
    workspace_ids TEXT DEFAULT '[]', -- JSON array of included workspace IDs
    card_count INTEGER DEFAULT 0,

    -- Export metadata
    export_size_bytes INTEGER NOT NULL,
    compression_used BOOLEAN DEFAULT FALSE,
    encryption_used BOOLEAN DEFAULT FALSE,

    -- Export status
    export_status TEXT DEFAULT 'completed', -- 'pending', 'processing', 'completed', 'failed'
    download_url TEXT, -- Temporary download URL
    url_expires_at TEXT,

    -- Export lifecycle
    requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    downloaded_at TEXT,

    -- Cleanup
    auto_delete_at TEXT, -- Automatic cleanup date

    -- Constraints
    CHECK (export_type IN ('full_backup', 'workspace_export', 'card_export', 'preferences_export')),
    CHECK (export_format IN ('json', 'csv', 'markdown', 'pdf')),
    CHECK (export_size_bytes >= 0),
    CHECK (card_count >= 0),
    CHECK (export_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- ============================================================================

-- Global preferences indexes
CREATE INDEX idx_global_prefs_user ON global_user_preferences(user_id);
CREATE INDEX idx_preference_sync_user ON preference_sync_log(user_id, created_at DESC);
CREATE INDEX idx_preference_sync_workspace ON preference_sync_log(workspace_id, sync_status);

-- Workspace management indexes
CREATE INDEX idx_workspace_history_user ON workspace_access_history(user_id, last_accessed DESC);
CREATE INDEX idx_workspace_history_active ON workspace_access_history(is_active, access_count DESC);
CREATE INDEX idx_workspace_favorites_user ON workspace_favorites(user_id, favorite_order);

-- Search and discovery indexes
CREATE INDEX idx_search_history_user ON search_history(user_id, executed_at DESC);
CREATE INDEX idx_search_history_query ON search_history(search_query, result_count DESC);
CREATE INDEX idx_popular_search_user ON popular_search_terms(user_id, search_count DESC);

-- Analytics indexes
CREATE INDEX idx_usage_analytics_user ON usage_analytics(user_id, recorded_at DESC);
CREATE INDEX idx_usage_analytics_metric ON usage_analytics(metric_name, metric_category);
CREATE INDEX idx_feature_adoption_user ON feature_adoption(user_id, last_used DESC);
CREATE INDEX idx_feature_adoption_feature ON feature_adoption(feature_name, usage_frequency);

-- Collaboration indexes
CREATE INDEX idx_collaboration_user ON cross_workspace_collaboration(user_id, is_active);
CREATE INDEX idx_collaboration_partner ON cross_workspace_collaboration(collaborator_user_id, is_active);
CREATE INDEX idx_sharing_patterns_user ON sharing_patterns(user_id, content_type);

-- Integration and export indexes
CREATE INDEX idx_integration_user ON integration_connections(user_id, is_active);
CREATE INDEX idx_integration_service ON integration_connections(service_name, service_type);
CREATE INDEX idx_export_history_user ON export_history(user_id, requested_at DESC);
CREATE INDEX idx_export_history_status ON export_history(export_status, auto_delete_at);

-- ============================================================================
-- DATA CLEANUP AND MAINTENANCE
-- ============================================================================

-- Cleanup old search history (keep only last 1000 searches per user)
CREATE TRIGGER cleanup_old_search_history
AFTER INSERT ON search_history
BEGIN
    DELETE FROM search_history
    WHERE user_id = NEW.user_id
    AND id NOT IN (
        SELECT id FROM search_history
        WHERE user_id = NEW.user_id
        ORDER BY executed_at DESC
        LIMIT 1000
    );
END;

-- Update workspace access statistics
CREATE TRIGGER update_workspace_access_stats
AFTER INSERT ON search_history
WHEN NEW.workspace_id IS NOT NULL
BEGIN
    UPDATE workspace_access_history
    SET last_accessed = NEW.executed_at,
        access_count = access_count + 1
    WHERE user_id = NEW.user_id AND workspace_id = NEW.workspace_id;
END;

-- Update popular search terms
CREATE TRIGGER update_popular_search_terms
AFTER INSERT ON search_history
BEGIN
    INSERT INTO popular_search_terms (user_id, search_term, search_count, avg_result_count)
    VALUES (NEW.user_id, NEW.search_query, 1, NEW.result_count)
    ON CONFLICT(user_id, search_term) DO UPDATE SET
        search_count = search_count + 1,
        last_searched = NEW.executed_at,
        avg_result_count = (avg_result_count * (search_count - 1) + NEW.result_count) / search_count;
END;
```

## Cross-Tier Relationship Mappings and Constraints

### Data Consistency Rules

**Cross-Tier Reference Integrity:**
```sql
-- Central tier tracks all Turso instances
customer_turso_instances.user_id → users.id (Central)
customer_turso_instances.workspace_id → workspace_settings.workspace_id (Project)

-- Project tier references central authentication
card_summaries.user_id → users.id (Central, via application-level validation)
user_preferences.user_id → users.id (Central, via application-level validation)

-- Master customer tier aggregates project data
workspace_access_history.workspace_id → workspace_settings.workspace_id (Project)
search_history.workspace_id → workspace_settings.workspace_id (Project)
```

**Business Logic Constraints:**
1. **User Existence**: All user_id references must exist in central tier
2. **Workspace Ownership**: Users can only access workspaces they own or are invited to
3. **Subscription Limits**: Project tier operations must respect central tier subscription limits
4. **Data Retention**: All tiers respect GDPR and data retention policies

### Performance Optimization Strategy

**Query Optimization Guidelines:**
1. **Central Tier**: Optimized for high-concurrency authentication (connection pooling)
2. **Project Tier**: Optimized for tag operations and card filtering (RoaringBitmap indexes)
3. **Master Customer Tier**: Optimized for cross-workspace aggregation (time-series indexes)

**Caching Strategy:**
- L1: Application-level caching for frequently accessed data
- L2: Database-level query result caching
- L3: CDN caching for static content and preferences

**Backup and Recovery:**
- Central Tier: Continuous replication with 5-minute RPO
- Project Tier: Hourly snapshots with instant restore capability
- Master Customer Tier: Daily backups with point-in-time recovery

This comprehensive database schema specification provides the foundation for multicardz's multi-tier architecture, ensuring optimal performance, complete data isolation, and seamless cross-tier operations while maintaining patent compliance and set theory mathematical correctness.