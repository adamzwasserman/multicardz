# multicardz Public Website & Analytics System Architecture v1

**Document Version**: 1.0
**Date**: 2025-10-22
**Author**: System Architect
**Status**: ARCHITECTURE DESIGN - READY FOR IMPLEMENTATION

---

---
**IMPLEMENTATION STATUS**: PLANNED
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Architecture documented. Implementation status not verified.
---



## 1. Executive Summary

The multicardz Public Website & Analytics System provides a comprehensive marketing and conversion tracking platform consisting of 8 targeted landing page variations, complete in-house analytics (no 3rd party dependencies), and full-funnel conversion tracking from initial page view through paid upgrade. This system replaces traditional analytics services (Hotjar, Google Analytics) with a privacy-respecting, actionable data collection system optimized for conversion optimization.

The architecture leverages a separate FastAPI application (`apps/public`) with shared PostgreSQL database access, enabling independent deployment while maintaining data continuity for conversion tracking. Key innovations include: (1) Polymorphic content storage for landing page variations, (2) Client-side analytics with batched server ingestion, (3) Session replay via lightweight mouse tracking, (4) Heatmap generation through coordinate bucketing, (5) A/B testing with deterministic variant assignment, (6) Smart routing based on referrer detection, and (7) Complete funnel tracking linking anonymous sessions to authenticated users.

The system processes 8 landing page variations targeting specific competitor refugees (Trello, Notion) and complementary use cases (Product Managers, Operations Teams, Legal/Compliance, Data Privacy, Spreadsheet Users). Each variation is dynamically served from database content, enabling rapid iteration without code deployment. Analytics capture includes page views, element-level interactions, scroll depth, mouse movement heatmaps, CTA click tracking, and complete session replay.

Expected outcomes: 90% reduction in analytics costs, 100% data ownership, granular actionable insights at element level, conversion funnel visibility with abandonment tracking, A/B test results for continuous optimization, and privacy compliance through self-hosted data storage.

---

## 2. System Context

### 2.1 Current State Architecture

multicardz currently lacks a public-facing website and conversion tracking infrastructure. The main application (`apps/user`) serves authenticated users, while `apps/shared` provides common functionality. The `apps/public` directory exists as a placeholder with minimal FastAPI scaffolding.

**Existing Infrastructure**:
- **apps/user**: Authenticated user application (app.multicardz.com)
- **apps/shared**: Common models, middleware, database access
- **apps/admin**: Internal administration tools
- **apps/public**: Placeholder for public site (empty structure)
- **PostgreSQL**: Shared database with UUID-based data isolation
- **Auth0**: Authentication provider for user accounts
- **Stripe**: Payment processing and subscription management

### 2.2 Business Requirements

The public website must support:
1. **Multiple audience segments**: 8 distinct landing page variations targeting specific use cases
2. **Complete conversion tracking**: From anonymous visitor → account creation → activation → paid upgrade
3. **In-house analytics**: No dependency on 3rd party services (Hotjar, Google Analytics)
4. **A/B testing**: Systematic variant testing to optimize conversion rates
5. **Smart routing**: Automatic landing page selection based on traffic source
6. **Actionable insights**: Element-level interaction data, not just page-level metrics
7. **Session replay**: Visual playback of user sessions for UX optimization
8. **Heatmap visualization**: Click and hover patterns across landing pages

### 2.3 Integration Dependencies

```
Public Website System Dependencies:
├── apps/shared/models (database models)
├── apps/shared/config (database connection)
├── PostgreSQL (shared database)
├── Auth0 (webhook integration for account creation)
├── Stripe (webhook integration for subscription events)
├── apps/user (conversion funnel handoff)
└── CDN (static asset delivery)
```

### 2.4 Data Flow Patterns

```
Anonymous Visitor Flow:
1. Visitor arrives → session created → landing page assigned (URL/A/B/smart routing)
2. Page view logged → analytics JS loads → tracking begins
3. Mouse movement sampled → clicks captured → scroll depth tracked
4. CTA clicked → funnel stage logged → redirect to signup
5. Account created → session linked to user_id
6. First card created → "activate" stage logged
7. Subscription purchased → "upgrade" stage logged

Data Persistence:
- Session data: analytics_sessions table (anonymous)
- Page views: analytics_page_views table (duration, scroll)
- Events: analytics_events table (clicks, interactions)
- Mouse data: analytics_mouse_tracking table (replay)
- Heatmaps: analytics_heatmap_data table (aggregated)
- Funnel: conversion_funnel table (stage progression)
```

---

## 3. Technical Design

### 3.1 Component Architecture

#### 3.1.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     multicardz Public Website                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Frontend Layer                              │  │
│  │  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │  │
│  │  │  Landing     │  Analytics   │  Session     │  Conversion │ │  │
│  │  │  Templates   │  JavaScript  │  Replay JS   │  Tracking   │ │  │
│  │  └──────────────┴──────────────┴──────────────┴─────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                         │  │
│  │  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │  │
│  │  │  Landing     │  Analytics   │  A/B Test    │  Admin      │ │  │
│  │  │  Routes      │  API Routes  │  Routes      │  Dashboard  │ │  │
│  │  └──────────────┴──────────────┴──────────────┴─────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                               │  │
│  │  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │  │
│  │  │  Content     │  Analytics   │  Session     │  Smart      │ │  │
│  │  │  Service     │  Service     │  Service     │  Routing    │ │  │
│  │  └──────────────┴──────────────┴──────────────┴─────────────┘ │  │
│  │  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │  │
│  │  │  A/B Test    │  Heatmap     │  Funnel      │  Aggregation││ │  │
│  │  │  Service     │  Service     │  Service     │  Service    │ │  │
│  │  └──────────────┴──────────────┴──────────────┴─────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Data Layer                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │                 PostgreSQL Database                        │ │  │
│  │  │  ┌────────────┬────────────┬────────────┬────────────┐   │ │  │
│  │  │  │ Landing    │ Analytics  │ Conversion │ A/B Test   │   │ │  │
│  │  │  │ Pages      │ Events     │ Funnel     │ Variants   │   │ │  │
│  │  │  └────────────┴────────────┴────────────┴────────────┘   │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Component Responsibilities

**Frontend Layer**:
- **Landing Templates**: Jinja2 templates rendering landing page variations from database content
- **Analytics JavaScript**: Client-side event capture with batched API calls
- **Session Replay JS**: Lightweight mouse tracking with coordinate sampling
- **Conversion Tracking**: CTA click detection and funnel stage progression

**FastAPI Application**:
- **Landing Routes**: Serve landing pages by slug, handle A/B test assignment, smart routing
- **Analytics API Routes**: Ingest page views, events, mouse data via POST endpoints
- **A/B Test Routes**: Variant assignment logic, traffic splitting
- **Admin Dashboard**: Analytics visualization, heatmaps, funnel reports, session replay

**Service Layer**:
- **Content Service**: Retrieve landing page content from database
- **Analytics Service**: Process and store incoming analytics events
- **Session Service**: Manage session lifecycle, cookie handling
- **Smart Routing Service**: Detect referrer and assign appropriate landing page
- **A/B Test Service**: Deterministic variant assignment with weighting
- **Heatmap Service**: Aggregate mouse coordinates into visualization buckets
- **Funnel Service**: Track conversion stages, calculate abandonment rates
- **Aggregation Service**: Background jobs for heatmaps, summaries

**Data Layer**:
- **PostgreSQL Database**: Shared with main app, isolated by tables
- **Landing Page Tables**: Content storage for variations
- **Analytics Tables**: Events, sessions, mouse data
- **Conversion Tables**: Funnel tracking, user linkage
- **A/B Test Tables**: Test configurations, variant assignments

### 3.2 Data Architecture

#### 3.2.1 Database Schema Overview

**Landing Page Content Tables**:
1. `landing_pages` - Page metadata, slugs, headlines
2. `landing_page_sections` - Polymorphic content storage (pain points, benefits, pricing)

**Analytics Tables**:
3. `analytics_sessions` - Anonymous visitor sessions with referrer tracking
4. `analytics_page_views` - Individual page loads with duration and scroll depth
5. `analytics_events` - Clicks, interactions, element-level tracking
6. `analytics_mouse_tracking` - Mouse coordinates for session replay
7. `analytics_heatmap_data` - Pre-aggregated click/hover heatmaps

**Conversion & Testing Tables**:
8. `conversion_funnel` - Funnel stage progression (view → upgrade)
9. `a_b_tests` - A/B test configurations
10. `a_b_test_variants` - Test variant definitions with landing page links

#### 3.2.2 Detailed Schema Definitions

**1. landing_pages**
```sql
CREATE TABLE landing_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,  -- 'trello-performance', 'notion-performance'
    category TEXT NOT NULL,      -- 'REPLACEMENT', 'COMPLEMENTARY'
    name TEXT NOT NULL,          -- 'Trello Performance Refugees'
    headline TEXT NOT NULL,      -- HTML allowed for <br>
    subheadline TEXT,
    competitor_name TEXT,        -- 'Trello', 'Notion', etc.
    is_active BOOLEAN DEFAULT true,
    created TIMESTAMP NOT NULL DEFAULT now(),
    modified TIMESTAMP NOT NULL DEFAULT now(),
    deleted TIMESTAMP
);

CREATE INDEX idx_landing_pages_slug ON landing_pages(slug) WHERE deleted IS NULL;
CREATE INDEX idx_landing_pages_active ON landing_pages(is_active) WHERE deleted IS NULL;
```

**2. landing_page_sections**
```sql
CREATE TABLE landing_page_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    landing_page_id UUID NOT NULL REFERENCES landing_pages(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL,  -- 'pain_point', 'benefit', 'comparison_metric',
                                  -- 'testimonial', 'pricing', 'differentiator'
    order_index INTEGER NOT NULL DEFAULT 0,
    data JSONB NOT NULL,          -- Flexible structure per section_type
    created TIMESTAMP NOT NULL DEFAULT now(),
    modified TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_sections_page ON landing_page_sections(landing_page_id, order_index);
CREATE INDEX idx_sections_type ON landing_page_sections(section_type);
```

**3. analytics_sessions**
```sql
CREATE TABLE analytics_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    landing_page_id UUID REFERENCES landing_pages(id),
    landing_page_slug TEXT,               -- For quick filtering
    a_b_variant_id UUID REFERENCES a_b_test_variants(id),
    referrer_url TEXT,
    referrer_domain TEXT,                 -- Extracted for smart routing
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_term TEXT,
    utm_content TEXT,
    user_agent TEXT,
    ip_address INET,
    browser_fingerprint TEXT,             -- For deduplication
    first_seen TIMESTAMP NOT NULL DEFAULT now(),
    last_seen TIMESTAMP NOT NULL DEFAULT now(),
    user_id UUID,                         -- Linked after account creation

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_sessions_landing_page ON analytics_sessions(landing_page_id);
CREATE INDEX idx_sessions_created ON analytics_sessions(first_seen DESC);
CREATE INDEX idx_sessions_user ON analytics_sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_sessions_referrer ON analytics_sessions(referrer_domain);
CREATE INDEX idx_sessions_utm ON analytics_sessions(utm_source, utm_medium, utm_campaign);
```

**4. analytics_page_views**
```sql
CREATE TABLE analytics_page_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES analytics_sessions(session_id) ON DELETE CASCADE,
    landing_page_id UUID REFERENCES landing_pages(id),
    url TEXT NOT NULL,
    referrer TEXT,
    duration_ms BIGINT,                   -- Time on page
    scroll_depth_percent INTEGER CHECK (scroll_depth_percent BETWEEN 0 AND 100),
    viewport_width INTEGER,
    viewport_height INTEGER,
    created TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_page_views_session ON analytics_page_views(session_id);
CREATE INDEX idx_page_views_page ON analytics_page_views(landing_page_id);
CREATE INDEX idx_page_views_created ON analytics_page_views(created DESC);
```

**5. analytics_events**
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES analytics_sessions(session_id) ON DELETE CASCADE,
    page_view_id UUID NOT NULL REFERENCES analytics_page_views(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,             -- 'click', 'cta_click', 'scroll', 'section_view'
    element_selector TEXT,                -- CSS selector
    element_text TEXT,                    -- Button text, link text
    element_position_x INTEGER,
    element_position_y INTEGER,
    timestamp_ms BIGINT NOT NULL,         -- Milliseconds since page load
    created TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_events_session ON analytics_events(session_id);
CREATE INDEX idx_events_page_view ON analytics_events(page_view_id);
CREATE INDEX idx_events_type ON analytics_events(event_type);
CREATE INDEX idx_events_created ON analytics_events(created DESC);
```

**6. analytics_mouse_tracking**
```sql
CREATE TABLE analytics_mouse_tracking (
    id BIGSERIAL PRIMARY KEY,             -- BIGSERIAL for high-volume inserts
    session_id UUID NOT NULL REFERENCES analytics_sessions(session_id) ON DELETE CASCADE,
    page_view_id UUID NOT NULL REFERENCES analytics_page_views(id) ON DELETE CASCADE,
    timestamp_ms BIGINT NOT NULL,
    event_type TEXT NOT NULL,             -- 'move', 'click', 'scroll'
    x INTEGER,
    y INTEGER,
    scroll_x INTEGER,
    scroll_y INTEGER,
    created TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_mouse_session ON analytics_mouse_tracking(session_id);
CREATE INDEX idx_mouse_page_view ON analytics_mouse_tracking(page_view_id, timestamp_ms);
-- Partition by month for performance
CREATE INDEX idx_mouse_created ON analytics_mouse_tracking(created DESC);
```

**7. analytics_heatmap_data** (pre-aggregated)
```sql
CREATE TABLE analytics_heatmap_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    landing_page_id UUID NOT NULL REFERENCES landing_pages(id) ON DELETE CASCADE,
    viewport_bucket TEXT NOT NULL,        -- 'mobile', 'tablet', 'desktop'
    x_bucket INTEGER NOT NULL,            -- Rounded to 10px buckets
    y_bucket INTEGER NOT NULL,            -- Rounded to 10px buckets
    click_count INTEGER DEFAULT 0,
    hover_duration_ms BIGINT DEFAULT 0,
    updated TIMESTAMP NOT NULL DEFAULT now(),

    UNIQUE(landing_page_id, viewport_bucket, x_bucket, y_bucket)
);

CREATE INDEX idx_heatmap_page ON analytics_heatmap_data(landing_page_id, viewport_bucket);
```

**8. conversion_funnel**
```sql
CREATE TABLE conversion_funnel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES analytics_sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    funnel_stage TEXT NOT NULL,           -- 'view', 'cta_click', 'account_create',
                                          -- 'activate', 'upgrade'
    landing_page_id UUID REFERENCES landing_pages(id),
    data JSONB,                           -- Stage-specific metadata
    created TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_funnel_session ON conversion_funnel(session_id);
CREATE INDEX idx_funnel_user ON conversion_funnel(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_funnel_stage ON conversion_funnel(funnel_stage, created DESC);
CREATE INDEX idx_funnel_page ON conversion_funnel(landing_page_id);
```

**9. a_b_tests**
```sql
CREATE TABLE a_b_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    traffic_split JSONB NOT NULL,         -- {"variant_a": 50, "variant_b": 50}
    start_date TIMESTAMP NOT NULL DEFAULT now(),
    end_date TIMESTAMP,
    created TIMESTAMP NOT NULL DEFAULT now(),
    modified TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_ab_tests_active ON a_b_tests(is_active) WHERE is_active = true;
```

**10. a_b_test_variants**
```sql
CREATE TABLE a_b_test_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    a_b_test_id UUID NOT NULL REFERENCES a_b_tests(id) ON DELETE CASCADE,
    variant_name TEXT NOT NULL,           -- 'control', 'variant_a', 'variant_b'
    landing_page_id UUID REFERENCES landing_pages(id),
    weight INTEGER NOT NULL DEFAULT 50,    -- Percentage of traffic
    created TIMESTAMP NOT NULL DEFAULT now(),

    UNIQUE(a_b_test_id, variant_name)
);

CREATE INDEX idx_variants_test ON a_b_test_variants(a_b_test_id);
```

### 3.3 Client-Side Analytics Architecture

#### 3.3.1 JavaScript Architecture

**analytics.js** (core tracking):
```javascript
// Session Management
- Generate UUID on first visit
- Store in cookie (HttpOnly via server) and localStorage
- Send session_id with every API request

// Page View Tracking
- Log viewport dimensions
- Start timer on page load
- Send duration on beforeunload
- Track scroll depth (Intersection Observer API)
- Batch: Send on unload or 30-second intervals

// Event Tracking
- Automatic click tracking on .cta-button
- Section visibility (Intersection Observer)
- Element position capture (getBoundingClientRect)
- Batch: Send every 5 seconds or 10 events

// Performance
- RequestIdleCallback for non-critical tracking
- Batched API calls (POST with arrays)
- LocalStorage queue for offline resilience
```

**mouse-tracking.js** (session replay):
```javascript
// Throttled Mouse Tracking
- Sample every 100ms (10 events/second max)
- Capture x, y relative to viewport
- Capture scroll position
- Timestamp relative to page load

// Click Tracking
- Exact click position
- Element selector (CSS)
- Element text content

// Performance Optimization
- Throttle to 100ms intervals
- Batch send every 10 seconds
- Max 1000 events per session
- Clear buffer after successful send
```

**conversion-tracking.js** (funnel):
```javascript
// Funnel Stage Detection
- CTA click → POST /api/analytics/conversion {stage: 'cta_click'}
- Account creation → Webhook from Auth0
- Activation → Polling /api/user/status until first_card_created
- Upgrade → Webhook from Stripe

// Session Linkage
- Store session_id in cookie
- Auth0 callback passes session_id → links to user_id
- All future funnel events include user_id
```

#### 3.3.2 API Integration Pattern

```javascript
// Batched Event Submission
const eventQueue = [];
const BATCH_SIZE = 10;
const BATCH_INTERVAL = 5000; // 5 seconds

function trackEvent(event) {
    eventQueue.push(event);
    if (eventQueue.length >= BATCH_SIZE) {
        sendBatch();
    }
}

async function sendBatch() {
    if (eventQueue.length === 0) return;

    const batch = eventQueue.splice(0, eventQueue.length);
    await fetch('/api/analytics/events', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: getSessionId(),
            events: batch
        })
    });
}

// Send on interval
setInterval(sendBatch, BATCH_INTERVAL);

// Send on page unload
window.addEventListener('beforeunload', sendBatch);
```

### 3.4 A/B Testing Architecture

#### 3.4.1 Variant Assignment Logic

```python
# services/a_b_test_service.py

def assign_variant(
    session_id: UUID,
    test_id: UUID,
    db: Session
) -> UUID:
    """
    Assign visitor to A/B test variant using deterministic hashing.

    Uses session_id hash to ensure consistent assignment across requests.
    Weights variants based on traffic_split configuration.
    """
    # Check existing assignment
    existing = db.query(analytics_sessions).filter(
        analytics_sessions.c.session_id == session_id
    ).first()

    if existing and existing.a_b_variant_id:
        return existing.a_b_variant_id

    # Get test configuration
    test = db.query(a_b_tests).filter(
        a_b_tests.c.id == test_id,
        a_b_tests.c.is_active == True
    ).first()

    if not test:
        return None

    # Get variants
    variants = db.query(a_b_test_variants).filter(
        a_b_test_variants.c.a_b_test_id == test_id
    ).all()

    # Deterministic assignment using hash
    session_hash = int(session_id.hex[:8], 16)
    total_weight = sum(v.weight for v in variants)
    bucket = session_hash % total_weight

    cumulative = 0
    for variant in variants:
        cumulative += variant.weight
        if bucket < cumulative:
            # Update session
            db.query(analytics_sessions).filter(
                analytics_sessions.c.session_id == session_id
            ).update({
                'a_b_variant_id': variant.id
            })
            db.commit()
            return variant.landing_page_id

    return variants[0].landing_page_id  # Fallback
```

#### 3.4.2 A/B Test Results Analysis

```python
# Admin dashboard analytics query
def get_ab_test_results(test_id: UUID, db: Session) -> dict:
    """Calculate conversion rates per variant."""

    results = db.execute("""
        WITH variant_sessions AS (
            SELECT
                v.variant_name,
                COUNT(DISTINCT s.session_id) as total_sessions
            FROM a_b_test_variants v
            LEFT JOIN analytics_sessions s ON s.a_b_variant_id = v.id
            WHERE v.a_b_test_id = :test_id
            GROUP BY v.variant_name
        ),
        variant_conversions AS (
            SELECT
                v.variant_name,
                COUNT(DISTINCT cf.user_id) as conversions
            FROM a_b_test_variants v
            LEFT JOIN analytics_sessions s ON s.a_b_variant_id = v.id
            LEFT JOIN conversion_funnel cf ON cf.session_id = s.session_id
            WHERE v.a_b_test_id = :test_id
              AND cf.funnel_stage = 'account_create'
            GROUP BY v.variant_name
        )
        SELECT
            vs.variant_name,
            vs.total_sessions,
            COALESCE(vc.conversions, 0) as conversions,
            COALESCE(vc.conversions::float / NULLIF(vs.total_sessions, 0), 0) * 100 as conversion_rate
        FROM variant_sessions vs
        LEFT JOIN variant_conversions vc ON vs.variant_name = vc.variant_name
    """, {'test_id': test_id})

    return [dict(row) for row in results]
```

### 3.5 Smart Routing Architecture

#### 3.5.1 Referrer Detection Service

```python
# services/smart_routing_service.py

def detect_landing_page(
    referrer: str | None,
    utm_params: dict,
    user_agent: str
) -> str | None:
    """
    Analyze traffic source and assign appropriate landing page.

    Priority:
    1. UTM parameters (explicit targeting)
    2. Referrer domain (inferred intent)
    3. Search query params (keyword targeting)
    4. Default (None → show generic home)
    """

    # UTM-based routing
    if utm_params.get('utm_content'):
        if 'trello' in utm_params['utm_content'].lower():
            return 'trello-performance'
        if 'notion' in utm_params['utm_content'].lower():
            return 'notion-performance'

    # Referrer-based routing
    if referrer:
        domain = extract_domain(referrer)

        # Direct competitor referrals
        if 'trello.com' in domain:
            return 'trello-performance'
        if 'notion.so' in domain or 'notion.com' in domain:
            return 'notion-performance'

        # Search engine keyword detection
        if is_search_engine(domain):
            query = extract_search_query(referrer)
            if query:
                if 'trello alternative' in query.lower():
                    return 'trello-performance'
                if 'notion alternative' in query.lower():
                    return 'notion-performance'
                if 'product manager tools' in query.lower():
                    return 'product-manager-multitool'

    # Default: show generic home or A/B test
    return None


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_search_engine(domain: str) -> bool:
    """Check if domain is a search engine."""
    search_engines = ['google.com', 'bing.com', 'duckduckgo.com',
                     'yahoo.com', 'baidu.com']
    return any(se in domain for se in search_engines)


def extract_search_query(url: str) -> str | None:
    """Extract search query from referrer URL."""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Google, Bing: q parameter
    if 'q' in params:
        return params['q'][0]

    # Yahoo: p parameter
    if 'p' in params:
        return params['p'][0]

    return None
```

### 3.6 Heatmap Generation Architecture

#### 3.6.1 Aggregation Service

```python
# services/heatmap_service.py

def aggregate_heatmap_data(
    landing_page_id: UUID,
    viewport_bucket: str,  # 'mobile', 'tablet', 'desktop'
    db: Session
) -> None:
    """
    Aggregate mouse tracking data into heatmap buckets.

    Runs hourly via background job (APScheduler).
    Groups coordinates into 10px buckets for visualization.
    """

    # Get recent mouse tracking data
    cutoff = datetime.now(UTC) - timedelta(hours=1)

    mouse_data = db.execute("""
        SELECT
            FLOOR(x / 10) * 10 as x_bucket,
            FLOOR(y / 10) * 10 as y_bucket,
            COUNT(*) as event_count,
            SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as click_count
        FROM analytics_mouse_tracking mt
        JOIN analytics_page_views pv ON mt.page_view_id = pv.id
        WHERE pv.landing_page_id = :page_id
          AND mt.created > :cutoff
          AND pv.viewport_width BETWEEN :min_width AND :max_width
        GROUP BY x_bucket, y_bucket
    """, {
        'page_id': landing_page_id,
        'cutoff': cutoff,
        'min_width': get_viewport_min(viewport_bucket),
        'max_width': get_viewport_max(viewport_bucket)
    })

    # Upsert into heatmap table
    for row in mouse_data:
        db.execute("""
            INSERT INTO analytics_heatmap_data
                (landing_page_id, viewport_bucket, x_bucket, y_bucket,
                 click_count, hover_duration_ms, updated)
            VALUES (:page_id, :viewport, :x, :y, :clicks, 0, now())
            ON CONFLICT (landing_page_id, viewport_bucket, x_bucket, y_bucket)
            DO UPDATE SET
                click_count = analytics_heatmap_data.click_count + :clicks,
                updated = now()
        """, {
            'page_id': landing_page_id,
            'viewport': viewport_bucket,
            'x': row.x_bucket,
            'y': row.y_bucket,
            'clicks': row.click_count
        })

    db.commit()


def get_viewport_min(bucket: str) -> int:
    """Get minimum viewport width for bucket."""
    if bucket == 'mobile':
        return 0
    elif bucket == 'tablet':
        return 768
    else:  # desktop
        return 1024


def get_viewport_max(bucket: str) -> int:
    """Get maximum viewport width for bucket."""
    if bucket == 'mobile':
        return 767
    elif bucket == 'tablet':
        return 1023
    else:  # desktop
        return 9999
```

### 3.7 Conversion Funnel Architecture

#### 3.7.1 Funnel Stage Tracking

```python
# services/conversion_funnel_service.py

async def track_funnel_stage(
    session_id: UUID,
    stage: str,
    landing_page_id: UUID | None = None,
    user_id: UUID | None = None,
    metadata: dict | None = None,
    db: Session = None
) -> None:
    """
    Log funnel stage progression.

    Stages:
    - view: Page loaded
    - cta_click: CTA button clicked
    - account_create: Auth0 account created
    - activate: First card created in main app
    - upgrade: Stripe subscription purchased
    """

    # Insert funnel event
    db.execute("""
        INSERT INTO conversion_funnel
            (session_id, user_id, funnel_stage, landing_page_id, data, created)
        VALUES (:session_id, :user_id, :stage, :page_id, :data, now())
    """, {
        'session_id': session_id,
        'user_id': user_id,
        'stage': stage,
        'page_id': landing_page_id,
        'data': json.dumps(metadata) if metadata else None
    })

    # If user_id provided, link session
    if user_id and stage == 'account_create':
        db.execute("""
            UPDATE analytics_sessions
            SET user_id = :user_id
            WHERE session_id = :session_id
        """, {'user_id': user_id, 'session_id': session_id})

    db.commit()


async def get_funnel_metrics(
    landing_page_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = None
) -> dict:
    """
    Calculate conversion funnel metrics.

    Returns counts and conversion rates for each stage.
    """

    query = """
        WITH funnel_counts AS (
            SELECT
                funnel_stage,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) as unique_users
            FROM conversion_funnel
            WHERE 1=1
                {page_filter}
                {date_filter}
            GROUP BY funnel_stage
        ),
        stage_order AS (
            SELECT 'view' as stage, 1 as order_num
            UNION ALL SELECT 'cta_click', 2
            UNION ALL SELECT 'account_create', 3
            UNION ALL SELECT 'activate', 4
            UNION ALL SELECT 'upgrade', 5
        )
        SELECT
            so.stage,
            COALESCE(fc.unique_sessions, 0) as count,
            COALESCE(fc.unique_users, 0) as users,
            LAG(fc.unique_sessions) OVER (ORDER BY so.order_num) as prev_count
        FROM stage_order so
        LEFT JOIN funnel_counts fc ON fc.funnel_stage = so.stage
        ORDER BY so.order_num
    """

    # Build filters
    page_filter = "AND landing_page_id = :page_id" if landing_page_id else ""
    date_filter = ""
    if start_date:
        date_filter += "AND created >= :start_date"
    if end_date:
        date_filter += "AND created <= :end_date"

    query = query.format(page_filter=page_filter, date_filter=date_filter)

    params = {}
    if landing_page_id:
        params['page_id'] = landing_page_id
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    results = db.execute(query, params).fetchall()

    # Calculate conversion rates
    funnel = []
    for row in results:
        conversion_rate = None
        if row.prev_count and row.prev_count > 0:
            conversion_rate = (row.count / row.prev_count) * 100

        funnel.append({
            'stage': row.stage,
            'count': row.count,
            'users': row.users,
            'conversion_rate': conversion_rate,
            'abandonment_rate': 100 - conversion_rate if conversion_rate else None
        })

    return {
        'stages': funnel,
        'overall_conversion': (funnel[-1]['count'] / funnel[0]['count'] * 100) if funnel[0]['count'] > 0 else 0
    }
```

#### 3.7.2 Integration with Main App

**Auth0 Callback Integration**:
```python
# apps/user/routes/auth.py

@router.get("/callback")
async def auth0_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Auth0 OAuth callback - link session to user."""

    # Exchange code for tokens (existing logic)
    user_info = await exchange_auth0_code(code)
    user_id = create_or_get_user(user_info, db)

    # Link analytics session (NEW)
    session_id = request.cookies.get('session_id')
    if session_id:
        await track_funnel_stage(
            session_id=UUID(session_id),
            stage='account_create',
            user_id=user_id,
            db=db
        )

    # Continue existing flow...
```

**First Card Creation Detection**:
```python
# apps/user/routes/cards.py

@router.post("/cards")
async def create_card(
    card: CardCreate,
    user_id: UUID = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Create card and track activation if first card."""

    # Create card (existing logic)
    new_card = card_service.create(card, user_id, db)

    # Check if first card (NEW)
    card_count = db.query(cards).filter(
        cards.c.user_id == user_id
    ).count()

    if card_count == 1:  # First card
        # Get session_id from analytics
        session = db.query(analytics_sessions).filter(
            analytics_sessions.c.user_id == user_id
        ).first()

        if session:
            await track_funnel_stage(
                session_id=session.session_id,
                stage='activate',
                user_id=user_id,
                metadata={'card_id': str(new_card.card_id)},
                db=db
            )

    return new_card
```

**Stripe Webhook Integration**:
```python
# apps/user/webhooks/stripe.py

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""

    event = await validate_stripe_webhook(request)

    if event['type'] == 'checkout.session.completed':
        customer_id = event['data']['object']['customer']

        # Get user_id from Stripe customer
        user = db.query(users).filter(
            users.c.stripe_customer_id == customer_id
        ).first()

        if user:
            # Get session_id from analytics
            session = db.query(analytics_sessions).filter(
                analytics_sessions.c.user_id == user.id
            ).first()

            if session:
                await track_funnel_stage(
                    session_id=session.session_id,
                    stage='upgrade',
                    user_id=user.id,
                    metadata={'stripe_customer_id': customer_id},
                    db=db
                )

    return {'status': 'success'}
```

---

## 4. Performance Considerations

### 4.1 Database Optimization

**Indexing Strategy**:
- All foreign keys indexed
- Created timestamps indexed (DESC for recent queries)
- Composite indexes for common query patterns
- Partial indexes for active records only

**Query Optimization**:
- Batched inserts for analytics events (COPY or multi-row INSERT)
- Pre-aggregated heatmap data (not computed on-demand)
- Materialized views for funnel metrics (refresh hourly)
- Read replicas for analytics queries (separate from transactional load)

**Data Retention**:
- Archive sessions older than 90 days
- Compress mouse tracking data older than 30 days
- Aggregate old data into summary tables
- Partition large tables by month (analytics_mouse_tracking)

### 4.2 Client-Side Performance

**JavaScript Optimization**:
- Throttled mouse tracking (100ms intervals)
- Batched API calls (reduce network overhead)
- RequestIdleCallback for non-critical tracking
- LocalStorage queue for offline resilience

**Bundle Size**:
- analytics.js: ~5KB gzipped
- mouse-tracking.js: ~3KB gzipped
- conversion-tracking.js: ~2KB gzipped
- Total: <10KB additional payload

### 4.3 API Performance

**Rate Limiting**:
- Per-session limits: 100 events/minute
- Per-IP limits: 1000 events/minute
- Throttling responses for abuse detection

**Async Processing**:
- Background workers for aggregation (Celery/APScheduler)
- Non-blocking event ingestion
- Batch processing for efficiency

---

## 5. Security & Privacy

### 5.1 Data Privacy

**Anonymous by Default**:
- Session IDs are UUIDs (not personally identifiable)
- IP addresses stored but can be anonymized
- No tracking cookies (only session identification)
- User linkage only after explicit account creation

**GDPR Compliance**:
- Right to be forgotten: Delete session data on request
- Data export: Provide all session data in JSON format
- Consent tracking: Log analytics consent per session
- Minimal data collection: Only actionable metrics

### 5.2 Security Measures

**Input Validation**:
- All analytics inputs validated with Pydantic models
- SQL injection prevention via parameterized queries
- XSS prevention in admin dashboard (escape all user input)

**Access Control**:
- Admin dashboard requires authentication
- Session data isolated by session_id
- No cross-session data access
- Rate limiting on analytics API

---

## 6. Deployment Architecture

### 6.1 Application Deployment

**Subdomain Structure**:
- **www.multicardz.com**: Public website (apps/public)
- **app.multicardz.com**: Main application (apps/user)
- **admin.multicardz.com**: Admin tools (apps/admin)

**Separate Processes**:
- Each app runs as independent FastAPI process
- Shared PostgreSQL database
- Separate uvicorn workers
- Independent scaling and deployment

### 6.2 Static Asset Delivery

**CDN Integration**:
- Serve analytics.js from CDN (CloudFront/Cloudflare)
- Cache landing page CSS
- Fast global delivery
- Automatic compression (gzip/brotli)

---

## 7. Success Metrics

### 7.1 Technical Metrics

- **Page Load Time**: <500ms for landing pages (95th percentile)
- **Analytics Latency**: <100ms API response time
- **Data Accuracy**: >99% event capture rate
- **Uptime**: 99.9% availability

### 7.2 Business Metrics

- **Conversion Rate**: View → Account (baseline)
- **Activation Rate**: Account → First Card
- **Upgrade Rate**: Free → Paid
- **Funnel Abandonment**: Drop-off at each stage
- **A/B Test Significance**: p < 0.05 for variant winners

---

## 8. Future Enhancements

### 8.1 Phase 2 Features

- Real-time dashboard updates (WebSockets)
- Funnel cohort analysis (retention curves)
- Advanced segmentation (by referrer, device, geography)
- Predictive analytics (conversion probability scoring)
- Session replay video export
- Heatmap overlay on actual landing pages

### 8.2 Phase 3 Features

- Multi-touch attribution modeling
- Campaign ROI tracking
- Integration with ad platforms (Google Ads, Facebook)
- Custom event tracking API
- Automated A/B test recommendations

---

## 9. Conclusion

The multicardz Public Website & Analytics System provides a comprehensive, privacy-respecting, cost-effective alternative to third-party analytics platforms. By building in-house, we maintain complete control over user data, gain granular actionable insights, and eliminate ongoing SaaS costs.

The architecture leverages existing multicardz infrastructure (PostgreSQL, FastAPI, function-based design) while adding specialized tables and services for public-facing functionality. The system is designed for scalability, maintainability, and extensibility.

**Key Architectural Decisions**:
1. **Shared Database**: Seamless conversion tracking from anonymous → authenticated
2. **Batched Analytics**: Performance optimization for high-volume event collection
3. **Pre-Aggregated Heatmaps**: Fast visualization without real-time computation
4. **Deterministic A/B Testing**: Consistent variant assignment across sessions
5. **Smart Routing**: Automatic landing page selection based on traffic source
6. **Full Funnel Tracking**: Complete visibility from view to upgrade

This architecture positions multicardz for rapid iteration on landing page variations, data-driven conversion optimization, and complete ownership of the customer acquisition journey.

---

**End of Architecture Document**
