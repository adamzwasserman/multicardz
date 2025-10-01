# 022 MultiCardz Multi-Tier Database Architecture v1

## Executive Summary

MultiCardz requires a sophisticated multi-tier database architecture that separates authentication/billing concerns from high-performance project data while maintaining sub-millisecond set theory operations and patent compliance. This architecture implements a three-tier system: Central PostgreSQL for authentication/billing, individual Turso instances for project data, and master customer instances for cross-project user preferences.

**Key Architectural Decisions:**
- **Central Tier**: PostgreSQL cloud instance for authentication, billing, and subscription management
- **Project Tier**: Individual Turso (SQLite) instances per workspace providing optimal isolation and performance
- **Master Customer Tier**: Primary Turso instance per customer for cross-project preferences and UI state
- **Set Theory Operations**: Pure mathematical operations using RoaringBitmap inverted indexes for O(1) performance
- **Authentication Integration**: OAuth2 with Auth0 using state parameter for workspace context switching

**Expected Outcomes:**
- Sub-millisecond tag filtering operations on 1M+ cards per project
- Complete data isolation between customers and subscription tiers
- Seamless workspace switching with OAuth state parameter management
- Horizontal scaling through customer-specific Turso instance distribution
- 99.99% uptime through distributed architecture with no single points of failure

## System Context

### Current State Architecture

The existing MultiCardz system uses a single SQLite database with an advanced two-tier storage pattern:
- **CardSummary** objects for fast list operations (~50 bytes per card)
- **CardDetail** objects for on-demand content loading
- **Normalized tag schema** with card-tag relationship tables
- **User preferences** stored in JSON format
- **Performance optimization** through tag count tuples for selectivity ordering

### Integration Points and Dependencies

**External Systems:**
- **Auth0**: OAuth2 provider for authentication with workspace context
- **Turso**: Distributed SQLite-compatible database service
- **PostgreSQL Cloud**: Central authentication and billing database
- **Payment Processors**: Stripe integration for subscription billing
- **Monitoring**: Database performance and health monitoring

**Internal Dependencies:**
- **Set Operations Library**: Pure functional operations on frozensets
- **Card Multiplicity System**: Semantic card instance proliferation
- **Spatial Tag Manipulation**: Patent-compliant tag zone operations
- **HTMX Frontend**: HTML-based UI with minimal JavaScript

### Data Flow Patterns

**Authentication Flow:**
```
User Request → Auth0 OAuth2 → Central PostgreSQL → Session Validation → Project Turso Access
```

**Tag Operation Flow:**
```
Spatial Drag → JavaScript Event → Backend Set Operations → RoaringBitmap Query → HTML Response
```

**Cross-Project Operations:**
```
User Action → Master Customer Instance → Project Data Sync → UI State Update
```

### Security Boundaries

**Tier Isolation:**
- Central PostgreSQL: Authentication, billing, session management
- Customer Turso Instances: Complete project data isolation
- Network-level security between tiers with encrypted connections
- Zero trust architecture with per-request authentication validation

## Technical Design

### Component Architecture

#### 3.1 Central PostgreSQL Tier

**Responsibilities:**
- User authentication and authorization
- Subscription management and billing
- OAuth2 session tracking with workspace context
- Customer-to-Turso instance mapping
- Cross-customer analytics (anonymized)

**Interface:**
```python
from typing import Protocol

class CentralAuthService(Protocol):
    async def authenticate_user(
        self,
        oauth_token: str,
        workspace_context: str
    ) -> AuthenticationResult: ...

    async def validate_subscription(
        self,
        user_id: str,
        workspace_id: str
    ) -> SubscriptionStatus: ...

    async def get_turso_connection_info(
        self,
        user_id: str,
        workspace_id: str
    ) -> TursoConnectionInfo: ...
```

**Communication Patterns:**
- Synchronous HTTPS API calls for authentication
- Connection pooling for high-throughput operations
- Read replicas for subscription validation
- Write operations limited to session management and billing events

#### 3.2 Project Turso Tier

**Responsibilities:**
- High-performance card storage with CardSummary/CardDetail separation
- RoaringBitmap inverted indexes for tag operations
- Normalized tag schema for scalability
- Project-specific user preferences and UI state
- Card multiplicity support for semantic instance proliferation

**Interface:**
```python
class ProjectDataService(Protocol):
    async def filter_cards_intersection_first(
        self,
        all_cards: frozenset[Card],
        filter_tags: frozenset[str],
        union_tags: frozenset[str],
        *,
        workspace_id: str,
        user_id: str
    ) -> frozenset[Card]: ...

    async def create_tag_count_tuples(
        self,
        workspace_id: str
    ) -> list[tuple[str, int]]: ...
```

**Communication Patterns:**
- Direct SQLite connections for maximum performance
- Asynchronous operations for bulk data loading
- Connection per workspace for isolation
- Streaming operations for large datasets

#### 3.3 Master Customer Tier

**Responsibilities:**
- Cross-project user preferences synchronization
- UI state persistence (zone visibility, themes, layouts)
- Workspace access history and favorites
- Customer-level analytics and usage tracking

**Interface:**
```python
class MasterCustomerService(Protocol):
    async def sync_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferences
    ) -> SyncResult: ...

    async def get_workspace_list(
        self,
        user_id: str
    ) -> list[WorkspaceInfo]: ...
```

### Data Architecture

#### 3.4 Central PostgreSQL Schema

```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    auth0_user_id TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- OAuth2 Sessions with Workspace Context
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    auth0_session_id TEXT NOT NULL,
    workspace_context TEXT, -- OAuth state parameter
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address INET,
    user_agent TEXT
);

-- Subscription Management
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'basic', 'premium', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    stripe_subscription_id TEXT UNIQUE,
    max_workspaces INTEGER NOT NULL DEFAULT 1,
    max_cards_per_workspace INTEGER NOT NULL DEFAULT 100
);

-- Customer Turso Instance Mapping
CREATE TABLE customer_turso_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id TEXT NOT NULL,
    turso_database_url TEXT NOT NULL,
    turso_auth_token TEXT NOT NULL,
    is_master_instance BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    tier_level TEXT NOT NULL CHECK (tier_level IN ('shared', 'dedicated', 'enterprise')),
    UNIQUE(user_id, workspace_id)
);

-- Billing and Usage Tracking
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id TEXT,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_users_auth0_id ON users(auth0_user_id);
CREATE INDEX idx_sessions_user_workspace ON user_sessions(user_id, workspace_context);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_turso_instances_user_workspace ON customer_turso_instances(user_id, workspace_id);
CREATE INDEX idx_usage_events_user_time ON usage_events(user_id, created_at);
```

#### 3.5 Project Turso Schema (Per Workspace)

```sql
-- Card Summaries: Optimized for List Operations (~50 bytes per card)
CREATE TABLE card_summaries (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    has_attachments BOOLEAN DEFAULT FALSE,
    user_id TEXT NOT NULL -- Workspace isolation
);

-- Normalized Tags for RoaringBitmap Optimization
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Card-Tag Relations: Core of Set Operations
CREATE TABLE card_tags (
    card_id TEXT NOT NULL REFERENCES card_summaries(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (card_id, tag_id)
);

-- RoaringBitmap Inverted Indexes (BLOB storage for compressed bitmaps)
CREATE TABLE tag_inverted_index (
    tag_id INTEGER PRIMARY KEY REFERENCES tags(id),
    card_bitmap BLOB NOT NULL, -- RoaringBitmap serialized
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Card Details: On-Demand Loading
CREATE TABLE card_details (
    id TEXT PRIMARY KEY REFERENCES card_summaries(id) ON DELETE CASCADE,
    content TEXT DEFAULT '',
    metadata_json TEXT DEFAULT '{}',
    attachment_count INTEGER DEFAULT 0,
    total_attachment_size INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1
);

-- User Preferences (Project-Specific)
CREATE TABLE user_preferences (
    user_id TEXT NOT NULL,
    zone_visibility_state TEXT DEFAULT '{}', -- JSON: {zone_id: boolean}
    ui_theme TEXT DEFAULT 'light',
    card_view_mode TEXT DEFAULT 'grid',
    sort_preferences TEXT DEFAULT '{}', -- JSON: sorting configurations
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
);

-- System Tags and Operations History
CREATE TABLE system_tag_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    operation_type TEXT NOT NULL, -- 'COUNT', 'SUM', 'MIGRATE_SPRINT', etc.
    target_tags TEXT NOT NULL, -- JSON array of tags
    affected_cards_count INTEGER,
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms REAL
);

-- Performance Indexes
CREATE INDEX idx_card_summaries_user ON card_summaries(user_id);
CREATE INDEX idx_card_summaries_modified ON card_summaries(modified_at DESC);
CREATE INDEX idx_card_tags_card ON card_tags(card_id);
CREATE INDEX idx_card_tags_tag ON card_tags(tag_id);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_usage_count ON tags(usage_count DESC);
CREATE INDEX idx_system_operations_user_time ON system_tag_operations(user_id, executed_at);
```

#### 3.6 Master Customer Schema

```sql
-- Cross-Project User Preferences
CREATE TABLE global_user_preferences (
    user_id TEXT PRIMARY KEY,
    default_theme TEXT DEFAULT 'light',
    notification_settings TEXT DEFAULT '{}', -- JSON
    keyboard_shortcuts TEXT DEFAULT '{}', -- JSON
    accessibility_settings TEXT DEFAULT '{}', -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Workspace Access History
CREATE TABLE workspace_access_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    workspace_name TEXT,
    last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    is_favorite BOOLEAN DEFAULT FALSE
);

-- Cross-Project Search History
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    search_query TEXT NOT NULL,
    workspace_id TEXT,
    result_count INTEGER,
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Customer Analytics (Privacy-Preserving)
CREATE TABLE usage_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    workspace_id TEXT,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_workspace_history_user ON workspace_access_history(user_id);
CREATE INDEX idx_workspace_history_accessed ON workspace_access_history(last_accessed DESC);
CREATE INDEX idx_search_history_user_time ON search_history(user_id, executed_at DESC);
CREATE INDEX idx_analytics_user_metric ON usage_analytics(user_id, metric_name);
```

### Polymorphic Architecture Mandates

#### 3.7 Database Connection Management

All database operations MUST use polymorphic interfaces to enable seamless switching between tiers:

```python
from typing import Protocol, TypeVar, Generic
from abc import abstractmethod

T = TypeVar('T')

class DatabaseConnectionProvider(Protocol[T]):
    @abstractmethod
    async def get_connection(self, context: ConnectionContext) -> T: ...

    @abstractmethod
    async def release_connection(self, connection: T) -> None: ...

class DataRepository(Protocol[T]):
    @abstractmethod
    async def save(self, entity: T, connection_context: ConnectionContext) -> str: ...

    @abstractmethod
    async def load(self, entity_id: str, connection_context: ConnectionContext) -> T: ...

# Factory Pattern Implementation
def create_database_provider(tier: str) -> DatabaseConnectionProvider:
    """Factory for tier-specific database providers."""
    if tier == "central":
        return PostgreSQLConnectionProvider()
    elif tier == "project":
        return TursoConnectionProvider()
    elif tier == "master_customer":
        return MasterTursoConnectionProvider()
    else:
        raise ValueError(f"Unknown database tier: {tier}")
```

#### 3.8 Set Operations Enhancement for Multi-Tier

```python
from typing import FrozenSet, Callable
import roaringbitmap

def filter_cards_with_roaring_bitmap(
    all_cards: FrozenSet[Card],
    filter_tags: FrozenSet[str],
    union_tags: FrozenSet[str],
    *,
    bitmap_provider: Callable[[str], roaringbitmap.RoaringBitmap],
    workspace_id: str,
    user_id: str
) -> FrozenSet[Card]:
    """
    Enhanced set operations using RoaringBitmap for universe-scale performance.

    Mathematical specification:
    Phase 1: U' = {c ∈ U : ∀t ∈ I, t ∈ c.tags}  (intersection using bitmap AND)
    Phase 2: R = {c ∈ U' : ∃t ∈ O, t ∈ c.tags}   (union using bitmap OR)

    Complexity: O(|I| + |O|) bitmap operations, O(|R|) card materialization
    Memory: O(|universe|/8) for bitmaps + O(|R|) for results
    """
    if not filter_tags and not union_tags:
        return all_cards

    # Phase 1: Intersection filtering using bitmap AND operations
    if filter_tags:
        intersection_bitmap = roaringbitmap.RoaringBitmap([])
        intersection_bitmap.update(range(len(all_cards)))  # Start with universe

        for tag in filter_tags:
            tag_bitmap = bitmap_provider(tag)
            intersection_bitmap &= tag_bitmap
    else:
        intersection_bitmap = roaringbitmap.RoaringBitmap(range(len(all_cards)))

    # Phase 2: Union selection using bitmap OR operations
    if union_tags:
        union_bitmap = roaringbitmap.RoaringBitmap([])
        for tag in union_tags:
            tag_bitmap = bitmap_provider(tag)
            union_bitmap |= tag_bitmap

        final_bitmap = intersection_bitmap & union_bitmap
    else:
        final_bitmap = intersection_bitmap

    # Materialize cards from bitmap indexes
    card_list = list(all_cards)
    result_cards = frozenset(card_list[i] for i in final_bitmap)

    return result_cards
```

### Card Multiplicity Architecture

#### 3.9 Multi-Tier Card Instance Management

Cards in the multi-tier architecture maintain their multiplicity properties while enabling cross-project operations:

```python
def transform_operational_event_multi_tier(
    event: OperationalEvent,
    tier_context: TierContext,
    semantic_extractor: SemanticExtractor
) -> Card:
    """
    Transform operational data into semantic Cards across tiers.

    Tier Context determines storage location:
    - Central Tier: User action events, billing events
    - Project Tier: Card content and tag operations
    - Master Customer Tier: Cross-project preference events
    """
    semantic_content = semantic_extractor.extract_meaning(event)
    selection_tags = semantic_extractor.extract_attributes(event)
    detailed_content = semantic_extractor.extract_details(event)

    # Add tier-specific tags for routing
    tier_tags = {f"#tier-{tier_context.tier_name}", f"#workspace-{tier_context.workspace_id}"}
    enhanced_tags = selection_tags | tier_tags

    return Card(
        content=semantic_content,
        tags=enhanced_tags,
        details=detailed_content,
        tier_context=tier_context
    )
```

### System Tags Implementation Requirements

#### 3.10 Multi-Tier System Tag Operations

System tags operate across tiers with proper isolation and security:

```python
class MultiTierSystemTagFunction(Protocol):
    @abstractmethod
    async def apply(
        self,
        matrix: dict[str, dict[str, frozenset[Card]]],
        target_tags: frozenset[str],
        tier_context: TierContext,
        mutation_context: Optional[MutationContext] = None
    ) -> dict[str, dict[str, frozenset[Card]]]:
        """Apply system tag operation across appropriate tiers."""
        ...

# Example: COUNT operation across project tier only
async def count_system_tag_apply(
    matrix: dict[str, dict[str, frozenset[Card]]],
    target_tags: frozenset[str],
    tier_context: TierContext,
    mutation_context: Optional[MutationContext] = None
) -> dict[str, dict[str, frozenset[Card]]]:
    """Generate COUNT cards within project tier isolation."""
    if tier_context.tier_name != "project":
        raise ValueError("COUNT operations only allowed in project tier")

    # Perform counting within workspace isolation
    for row_key, columns in matrix.items():
        for col_key, cards in columns.items():
            if target_tags.intersection({tag for card in cards for tag in card.tags}):
                count_card = Card(
                    content=f"Count: {len(cards)} cards",
                    tags={f"#count", f"#workspace-{tier_context.workspace_id}"},
                    details={"count": len(cards), "tags": list(target_tags)}
                )
                # Add count card to appropriate cell
                matrix[row_key][col_key] = cards | {count_card}

    return matrix
```

### Poka-yoke Safety Mechanisms

#### 3.11 Multi-Tier Mutation Safety

Safety mechanisms operate with tier-awareness:

```python
class MultiTierMutationPreview:
    cards_affected: frozenset[Card]
    tier_changes: dict[str, TagDiff]  # tier_name → changes
    workspace_scope: str
    mutation_count_by_tier: dict[str, int]

    async def commit(
        self,
        confirm_zone: ConfirmZone,
        audit: AuditContext,
        auth_service: CentralAuthService
    ) -> MutationResult:
        """Execute mutations with cross-tier validation."""
        # Validate permissions across all affected tiers
        for tier_name in self.tier_changes.keys():
            if not await auth_service.validate_tier_access(
                audit.user_id, self.workspace_scope, tier_name
            ):
                raise PermissionDeniedError(f"Access denied for tier {tier_name}")

        # Execute mutations in dependency order
        results = {}
        for tier_name in ["central", "project", "master_customer"]:
            if tier_name in self.tier_changes:
                tier_result = await self._apply_tier_mutations(
                    tier_name, self.tier_changes[tier_name], audit
                )
                results[tier_name] = tier_result

        return MutationResult(tier_results=results)
```

## Architectural Principles Compliance

### Set Theory Operations

All filtering operations use pure mathematical set theory enhanced with RoaringBitmap optimization:

**Mathematical Notation:**
- `U` = Universe of all cards in workspace
- `I` = Intersection tags (filter_tags)
- `O` = Union tags (union_tags)
- `B(t)` = RoaringBitmap for tag t
- `R` = Result set

**Enhanced Operations:**
```
Phase 1 (Intersection): U' = {c ∈ U : ∀t ∈ I, c ∈ B(t)}
Phase 2 (Union): R = {c ∈ U' : ∃t ∈ O, c ∈ B(t)}
```

**RoaringBitmap Implementation:**
- O(1) bitmap lookup for tag membership
- O(|I|) intersection operations using bitmap AND
- O(|O|) union operations using bitmap OR
- O(|R|) final card materialization

### Function-Based Architecture

**Database Layer:** All database operations implemented as pure functions with explicit tier context:

```python
async def save_card_multi_tier(
    card: Card,
    tier_context: TierContext,
    connection_provider: DatabaseConnectionProvider
) -> str:
    """Save card to appropriate tier with full type safety."""
    connection = await connection_provider.get_connection(tier_context)
    try:
        if tier_context.tier_name == "project":
            return await save_card_to_project_tier(card, connection)
        elif tier_context.tier_name == "master_customer":
            return await save_card_to_master_tier(card, connection)
        else:
            raise ValueError(f"Invalid tier for card storage: {tier_context.tier_name}")
    finally:
        await connection_provider.release_connection(connection)
```

**Authentication Integration:** OAuth2 flow implemented as pure functions:

```python
async def authenticate_with_workspace_context(
    oauth_code: str,
    workspace_state: str,
    auth_provider: OAuth2Provider,
    central_db: DatabaseConnectionProvider
) -> AuthenticationResult:
    """Pure function for OAuth2 authentication with workspace context."""
    # Validate OAuth2 code with Auth0
    tokens = await auth_provider.exchange_code_for_tokens(oauth_code)

    # Extract user info and workspace from state parameter
    user_info = await auth_provider.get_user_info(tokens.access_token)
    workspace_id = extract_workspace_from_state(workspace_state)

    # Validate subscription and get Turso connection info
    connection = await central_db.get_connection(ConnectionContext(tier="central"))
    try:
        subscription = await validate_user_subscription(user_info.user_id, connection)
        turso_info = await get_turso_connection_info(
            user_info.user_id, workspace_id, connection
        )

        return AuthenticationResult(
            user=user_info,
            workspace_id=workspace_id,
            subscription=subscription,
            turso_connection=turso_info,
            session_token=tokens.session_token
        )
    finally:
        await central_db.release_connection(connection)
```

### JavaScript Restrictions

Minimal JavaScript required only for:
- **Spatial drag-drop operations** (patent-compliant zone manipulation)
- **OAuth2 redirect handling** (workspace state parameter management)
- **Real-time connection status** (Turso instance health monitoring)

All other interactivity handled by HTMX with HTML responses from appropriate tiers.

## Performance Considerations

### Polymorphic Performance Requirements

**Database Tier Selection:** O(1) lookup through factory pattern using connection context:

```python
CONNECTION_FACTORIES = {
    "central": PostgreSQLConnectionFactory(),
    "project": TursoConnectionFactory(),
    "master_customer": MasterTursoConnectionFactory()
}

def get_connection_factory(tier_name: str) -> DatabaseConnectionFactory:
    """O(1) factory lookup with no polymorphic overhead."""
    return CONNECTION_FACTORIES[tier_name]
```

**RoaringBitmap Operations:**
- Bitmap creation: O(n) where n = number of cards
- Intersection (AND): O(min(|B1|, |B2|))
- Union (OR): O(|B1| + |B2|)
- Card materialization: O(|result_set|)

**Target Performance Metrics:**
- Tag filtering (1000 cards): <0.5ms
- Tag filtering (100K cards): <5ms
- Tag filtering (1M cards): <50ms
- Cross-tier authentication: <100ms
- Workspace switching: <200ms

### Scalability Analysis

**Horizontal Scaling Capability:**

1. **Central PostgreSQL Tier:**
   - Read replicas for subscription validation
   - Connection pooling for high concurrency
   - Partitioning by user_id for large datasets

2. **Project Turso Tier:**
   - Unlimited horizontal scaling through customer-specific instances
   - Geographic distribution based on customer location
   - Independent scaling per workspace

3. **Master Customer Tier:**
   - One instance per customer enables perfect isolation
   - Sharding by customer_id for enterprise deployment
   - Cross-region replication for global customers

### Caching Strategies

**Singleton Pattern for Global Structures:**

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def get_connection_pool_singleton(tier_name: str) -> ConnectionPool:
    """Singleton connection pool per tier type."""
    return create_connection_pool(tier_name)

@lru_cache(maxsize=1000)
def get_roaring_bitmap_cached(tag_name: str, workspace_id: str) -> roaringbitmap.RoaringBitmap:
    """LRU cache for frequently accessed tag bitmaps."""
    return load_roaring_bitmap_from_database(tag_name, workspace_id)
```

**Caching Hierarchy:**
- L1: In-memory RoaringBitmap cache (tag → bitmap)
- L2: Connection pool cache (tier → pool)
- L3: Subscription validation cache (user_id → subscription)
- L4: Turso connection info cache (workspace_id → connection_info)

## Security Architecture

### Authentication and Authorization Patterns

**OAuth2 with Workspace Context:**

1. **Initial Authentication:** User authenticates via Auth0 with workspace hint in state parameter
2. **Session Management:** Central PostgreSQL stores session with workspace context
3. **Tier Access Validation:** Each tier validates permissions through central service
4. **Token Refresh:** Automatic token refresh with workspace context preservation

```python
async def validate_tier_access(
    session_token: str,
    tier_name: str,
    workspace_id: str,
    central_auth: CentralAuthService
) -> bool:
    """Validate user access to specific tier and workspace."""
    session = await central_auth.validate_session(session_token)
    if not session:
        return False

    subscription = await central_auth.get_user_subscription(session.user_id)
    workspace_access = await central_auth.check_workspace_access(
        session.user_id, workspace_id
    )

    return (
        session.is_valid and
        subscription.allows_tier(tier_name) and
        workspace_access.has_permission("read")
    )
```

### Data Isolation Mechanisms

**Subscription-Based Isolation:**

1. **Free Tier:** Shared Turso instances with strict workspace separation
2. **Basic Tier:** Dedicated Turso instances with multiple workspaces
3. **Premium Tier:** Dedicated Turso instances per workspace
4. **Enterprise Tier:** Dedicated infrastructure with custom isolation

**Network Security:**
- TLS 1.3 encryption for all inter-tier communication
- VPN tunnels for enterprise customer instances
- Certificate pinning for Turso connections
- WAF protection for central PostgreSQL tier

### Secret Management Approach

**Hierarchical Secret Management:**

```python
from typing import Protocol

class SecretProvider(Protocol):
    async def get_secret(self, key: str, context: SecurityContext) -> str: ...

class TierSecretManager:
    def __init__(self, providers: dict[str, SecretProvider]):
        self.providers = providers

    async def get_database_credentials(
        self,
        tier_name: str,
        workspace_id: str
    ) -> DatabaseCredentials:
        """Get tier-specific database credentials with workspace context."""
        provider = self.providers[tier_name]

        if tier_name == "central":
            return await provider.get_secret("postgresql_central")
        elif tier_name == "project":
            turso_token = await provider.get_secret(f"turso_project_{workspace_id}")
            return TursoCredentials(workspace_id=workspace_id, token=turso_token)
        elif tier_name == "master_customer":
            customer_id = extract_customer_from_workspace(workspace_id)
            turso_token = await provider.get_secret(f"turso_master_{customer_id}")
            return TursoCredentials(customer_id=customer_id, token=turso_token)
```

### Audit Logging Requirements

**Comprehensive Audit Trail:**

```python
@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    user_id: str
    workspace_id: str
    tier_name: str
    operation: str
    affected_entities: list[str]
    timestamp: datetime
    ip_address: str
    success: bool
    error_message: Optional[str] = None

async def log_audit_event(
    event: AuditEvent,
    central_logger: AuditLogger
) -> None:
    """Log security event to central audit system."""
    await central_logger.write_event(event)

    # Critical events also logged to SIEM
    if event.operation in CRITICAL_OPERATIONS:
        await central_logger.forward_to_siem(event)
```

## Error Handling

### Error Classification and Handling Strategies

**Tier-Specific Error Hierarchy:**

```python
class MultiTierError(Exception):
    """Base exception for multi-tier operations."""
    def __init__(self, message: str, tier_name: str, workspace_id: str):
        super().__init__(message)
        self.tier_name = tier_name
        self.workspace_id = workspace_id

class CentralTierError(MultiTierError):
    """Errors from central PostgreSQL tier."""
    pass

class ProjectTierError(MultiTierError):
    """Errors from project Turso tier."""
    pass

class MasterCustomerTierError(MultiTierError):
    """Errors from master customer tier."""
    pass

class CrossTierConsistencyError(MultiTierError):
    """Errors in cross-tier data consistency."""
    pass
```

**Graceful Degradation Patterns:**

```python
async def get_cards_with_fallback(
    workspace_id: str,
    user_id: str,
    tier_services: dict[str, DatabaseService]
) -> frozenset[Card]:
    """Get cards with graceful degradation across tiers."""
    try:
        # Primary: Try project tier (fastest)
        return await tier_services["project"].get_cards(workspace_id, user_id)
    except ProjectTierError as e:
        logger.warning(f"Project tier unavailable: {e}")

        try:
            # Fallback: Try master customer tier (slower but available)
            return await tier_services["master_customer"].get_cached_cards(user_id)
        except MasterCustomerTierError as e:
            logger.error(f"Master customer tier unavailable: {e}")

            # Last resort: Return empty set with error context
            return frozenset()
```

### Rollback Procedures

**Multi-Tier Rollback Strategy:**

```python
async def rollback_multi_tier_transaction(
    transaction_id: str,
    affected_tiers: list[str],
    rollback_context: RollbackContext
) -> RollbackResult:
    """Rollback transaction across multiple tiers."""
    rollback_results = {}

    # Rollback in reverse dependency order
    for tier_name in reversed(affected_tiers):
        try:
            tier_service = get_tier_service(tier_name)
            result = await tier_service.rollback_transaction(
                transaction_id, rollback_context
            )
            rollback_results[tier_name] = result
        except Exception as e:
            logger.error(f"Rollback failed for tier {tier_name}: {e}")
            rollback_results[tier_name] = RollbackResult(
                success=False, error=str(e)
            )

    return RollbackResult(tier_results=rollback_results)
```

### Recovery Mechanisms

**Automated Recovery Procedures:**

1. **Connection Recovery:** Automatic reconnection to failed Turso instances
2. **Data Synchronization:** Cross-tier consistency checking and repair
3. **Backup Restoration:** Point-in-time recovery for corrupted instances
4. **Instance Migration:** Transparent migration to healthy instances

### User Experience During Failures

**Progressive Enhancement Strategy:**

1. **Full Functionality:** All tiers operational
2. **Read-Only Mode:** Central tier available, project tiers degraded
3. **Cached Mode:** Local storage fallback with eventual consistency
4. **Offline Mode:** Complete offline operation with sync on reconnection

## Testing Strategy

### Unit Test Requirements

**100% Coverage Target with Tier-Specific Testing:**

```python
# tests/test_multi_tier_operations.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_tier_services():
    return {
        "central": Mock(spec=CentralAuthService),
        "project": Mock(spec=ProjectDataService),
        "master_customer": Mock(spec=MasterCustomerService)
    }

@pytest.mark.asyncio
async def test_cross_tier_authentication(mock_tier_services):
    """Test authentication flow across all tiers."""
    # Setup mocks
    mock_tier_services["central"].authenticate_user = AsyncMock(
        return_value=AuthenticationResult(user_id="test", workspace_id="ws1")
    )

    # Test authentication
    result = await authenticate_with_workspace_context(
        oauth_code="test_code",
        workspace_state="ws1",
        auth_provider=mock_tier_services["central"],
        central_db=mock_tier_services["central"]
    )

    assert result.user_id == "test"
    assert result.workspace_id == "ws1"
```

### Integration Test Patterns

**Cross-Tier Integration Testing:**

```python
@pytest.mark.integration
async def test_end_to_end_card_operations():
    """Test complete card operations across all tiers."""
    # Setup test environment with real database connections
    central_db = await create_test_postgresql_connection()
    project_db = await create_test_turso_connection("test_workspace")
    master_db = await create_test_turso_connection("test_customer")

    try:
        # Test user authentication
        auth_result = await authenticate_user(central_db)

        # Test card creation in project tier
        card = await create_card(project_db, auth_result.user_id)

        # Test preference sync to master tier
        await sync_preferences(master_db, auth_result.user_id)

        # Verify cross-tier consistency
        assert await verify_cross_tier_consistency(
            central_db, project_db, master_db, auth_result.user_id
        )
    finally:
        await cleanup_test_databases(central_db, project_db, master_db)
```

### Performance Test Criteria

**Multi-Tier Performance Benchmarks:**

```python
@pytest.mark.performance
async def test_roaring_bitmap_performance():
    """Verify RoaringBitmap operations meet performance targets."""
    # Setup 1M card test dataset
    cards = generate_test_cards(1_000_000)
    bitmap_provider = create_test_bitmap_provider(cards)

    # Test intersection performance
    start_time = time.perf_counter()
    result = await filter_cards_with_roaring_bitmap(
        all_cards=frozenset(cards),
        filter_tags=frozenset(["#urgent", "#bug"]),
        union_tags=frozenset(["#frontend", "#backend"]),
        bitmap_provider=bitmap_provider,
        workspace_id="test_ws",
        user_id="test_user"
    )
    end_time = time.perf_counter()

    operation_time_ms = (end_time - start_time) * 1000
    assert operation_time_ms < 50  # Target: <50ms for 1M cards
    assert len(result) > 0  # Verify results returned
```

### Migration Test Procedures

**Database Migration Validation:**

```python
@pytest.mark.migration
async def test_sqlite_to_multi_tier_migration():
    """Test migration from single SQLite to multi-tier architecture."""
    # Setup legacy SQLite database
    legacy_db = await create_legacy_sqlite_database()
    await populate_legacy_test_data(legacy_db)

    # Perform migration
    migration_result = await migrate_to_multi_tier(
        source_db=legacy_db,
        target_config=MultiTierConfig(
            central_url="postgresql://test",
            project_url="turso://test_project",
            master_url="turso://test_master"
        )
    )

    # Verify migration success
    assert migration_result.success
    assert migration_result.cards_migrated > 0
    assert migration_result.users_migrated > 0
    assert migration_result.preferences_migrated > 0

    # Verify data integrity
    await verify_migrated_data_integrity(migration_result)
```

## Deployment Architecture

### Environment Configurations

**Multi-Tier Environment Setup:**

```yaml
# docker-compose.multi-tier.yml
version: '3.8'
services:
  central-postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: multicardz_central
      POSTGRES_USER: multicardz
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - central_data:/var/lib/postgresql/data
      - ./sql/central_schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
    ports:
      - "5432:5432"
    networks:
      - multicardz_central

  turso-proxy:
    image: multicardz/turso-proxy:latest
    environment:
      TURSO_API_TOKEN: ${TURSO_API_TOKEN}
      TURSO_ORG: ${TURSO_ORG}
    ports:
      - "8080:8080"
    networks:
      - multicardz_project
      - multicardz_master

  multicardz-api:
    image: multicardz/api:latest
    environment:
      CENTRAL_DB_URL: postgresql://multicardz:${POSTGRES_PASSWORD}@central-postgres:5432/multicardz_central
      TURSO_PROXY_URL: http://turso-proxy:8080
      AUTH0_DOMAIN: ${AUTH0_DOMAIN}
      AUTH0_CLIENT_ID: ${AUTH0_CLIENT_ID}
      AUTH0_CLIENT_SECRET: ${AUTH0_CLIENT_SECRET}
    depends_on:
      - central-postgres
      - turso-proxy
    ports:
      - "8000:8000"
    networks:
      - multicardz_central
      - multicardz_project
      - multicardz_master

networks:
  multicardz_central:
    driver: bridge
  multicardz_project:
    driver: bridge
  multicardz_master:
    driver: bridge

volumes:
  central_data:
```

### Rollout Strategy

**Phased Deployment Approach:**

1. **Phase 1:** Deploy central PostgreSQL tier with authentication
2. **Phase 2:** Migrate existing users to central authentication
3. **Phase 3:** Deploy project Turso instances for new workspaces
4. **Phase 4:** Migrate existing workspaces to project tier
5. **Phase 5:** Deploy master customer tier for preferences
6. **Phase 6:** Enable cross-tier operations and full functionality

### Rollback Procedures

**Deployment Rollback Plan:**

```bash
#!/bin/bash
# rollback-multi-tier.sh

set -e

BACKUP_DIR="/var/backups/multicardz"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting multi-tier rollback at $TIMESTAMP"

# 1. Stop new deployments
kubectl scale deployment multicardz-api --replicas=0

# 2. Backup current state
pg_dump multicardz_central > "$BACKUP_DIR/central_pre_rollback_$TIMESTAMP.sql"

# 3. Restore previous central database
psql multicardz_central < "$BACKUP_DIR/central_last_known_good.sql"

# 4. Restore Turso instances
for workspace_id in $(cat "$BACKUP_DIR/active_workspaces.txt"); do
    turso db restore "multicardz_${workspace_id}" \
        --backup-file "$BACKUP_DIR/turso_${workspace_id}_last_known_good.db"
done

# 5. Restart with previous version
kubectl set image deployment/multicardz-api \
    multicardz-api=multicardz/api:$PREVIOUS_VERSION

kubectl scale deployment multicardz-api --replicas=3

echo "Rollback completed successfully"
```

### Monitoring and Alerting

**Multi-Tier Monitoring Strategy:**

```python
from typing import Dict, List
import asyncio
import logging

class MultiTierMonitor:
    def __init__(self, tier_services: Dict[str, DatabaseService]):
        self.tier_services = tier_services
        self.logger = logging.getLogger(__name__)

    async def health_check_all_tiers(self) -> Dict[str, bool]:
        """Check health of all database tiers."""
        health_status = {}

        for tier_name, service in self.tier_services.items():
            try:
                await service.ping()
                health_status[tier_name] = True
                self.logger.info(f"Tier {tier_name}: HEALTHY")
            except Exception as e:
                health_status[tier_name] = False
                self.logger.error(f"Tier {tier_name}: UNHEALTHY - {e}")

        return health_status

    async def monitor_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Monitor performance metrics across all tiers."""
        metrics = {}

        for tier_name, service in self.tier_services.items():
            try:
                tier_metrics = await service.get_performance_metrics()
                metrics[tier_name] = {
                    "avg_response_time_ms": tier_metrics.avg_response_time,
                    "active_connections": tier_metrics.connection_count,
                    "memory_usage_mb": tier_metrics.memory_usage,
                    "disk_usage_percentage": tier_metrics.disk_usage
                }
            except Exception as e:
                self.logger.error(f"Failed to get metrics for {tier_name}: {e}")
                metrics[tier_name] = {"error": str(e)}

        return metrics

# Alerting Configuration
ALERT_THRESHOLDS = {
    "response_time_ms": 1000,  # Alert if >1 second
    "connection_count": 100,   # Alert if >100 connections
    "memory_usage_mb": 1024,   # Alert if >1GB memory
    "disk_usage_percentage": 80  # Alert if >80% disk usage
}

async def check_and_alert(monitor: MultiTierMonitor, alerting_service: AlertingService):
    """Check metrics and send alerts if thresholds exceeded."""
    metrics = await monitor.monitor_performance_metrics()

    for tier_name, tier_metrics in metrics.items():
        for metric_name, value in tier_metrics.items():
            if metric_name in ALERT_THRESHOLDS:
                threshold = ALERT_THRESHOLDS[metric_name]
                if value > threshold:
                    alert = Alert(
                        severity="WARNING",
                        message=f"Tier {tier_name} {metric_name} exceeded threshold: {value} > {threshold}",
                        tier=tier_name,
                        metric=metric_name,
                        value=value
                    )
                    await alerting_service.send_alert(alert)
```

## Risk Assessment

### Technical Risks and Mitigations

**High-Priority Technical Risks:**

1. **Cross-Tier Data Consistency**
   - **Risk:** Data inconsistency between tiers during high-concurrency operations
   - **Probability:** Medium
   - **Impact:** High
   - **Mitigation:** Implement eventual consistency with conflict resolution
   - **Monitoring:** Automated consistency checks every 5 minutes

2. **Turso Instance Limit Scaling**
   - **Risk:** Hitting Turso organizational limits with thousands of customer instances
   - **Probability:** High
   - **Impact:** High
   - **Mitigation:** Implement tiered instance allocation and shared instances for lower tiers
   - **Monitoring:** Track instance count and implement automated tier adjustments

3. **RoaringBitmap Memory Usage**
   - **Risk:** Memory exhaustion with universe-scale datasets (10M+ cards)
   - **Probability:** Medium
   - **Impact:** Medium
   - **Mitigation:** Implement streaming bitmap operations and LRU cache eviction
   - **Monitoring:** Memory usage alerts and automatic cache cleanup

### Operational Risks

**Database Operations Risks:**

1. **Central PostgreSQL Single Point of Failure**
   - **Risk:** Authentication and billing unavailable during PostgreSQL outage
   - **Mitigation:** High-availability PostgreSQL with read replicas and automatic failover
   - **Recovery Time Objective:** 30 seconds
   - **Recovery Point Objective:** 0 data loss

2. **Turso API Rate Limiting**
   - **Risk:** Customer instance provisioning blocked during traffic spikes
   - **Mitigation:** Pre-provision instances and implement request queuing
   - **Monitoring:** API rate limit usage tracking

### Security Risks

**Multi-Tier Security Considerations:**

1. **Cross-Tier Authentication Token Management**
   - **Risk:** Token compromise allowing unauthorized cross-tier access
   - **Mitigation:** Short-lived tokens, per-tier token validation, automatic rotation
   - **Detection:** Anomaly detection for unusual cross-tier access patterns

2. **Turso Instance Access Control**
   - **Risk:** Customer data leakage through misconfigured instance permissions
   - **Mitigation:** Automated access control validation, instance isolation testing
   - **Audit:** Daily access control compliance checks

### Business Continuity Plans

**Disaster Recovery Strategy:**

```python
@dataclass
class DisasterRecoveryPlan:
    recovery_time_objective: timedelta  # Maximum downtime
    recovery_point_objective: timedelta  # Maximum data loss
    backup_strategy: BackupStrategy
    failover_procedures: List[FailoverStep]
    testing_schedule: TestingSchedule

# Multi-Tier Disaster Recovery
MULTI_TIER_DR_PLAN = DisasterRecoveryPlan(
    recovery_time_objective=timedelta(minutes=15),
    recovery_point_objective=timedelta(minutes=5),
    backup_strategy=BackupStrategy(
        central_tier=BackupConfig(
            frequency=timedelta(minutes=5),
            retention=timedelta(days=30),
            method="continuous_replication"
        ),
        project_tier=BackupConfig(
            frequency=timedelta(hours=1),
            retention=timedelta(days=7),
            method="turso_branching"
        ),
        master_customer_tier=BackupConfig(
            frequency=timedelta(hours=6),
            retention=timedelta(days=14),
            method="turso_backup"
        )
    ),
    failover_procedures=[
        FailoverStep("Detect failure through health checks", duration=timedelta(seconds=30)),
        FailoverStep("Activate standby PostgreSQL instance", duration=timedelta(minutes=2)),
        FailoverStep("Update DNS to point to standby", duration=timedelta(minutes=3)),
        FailoverStep("Verify all tier connectivity", duration=timedelta(minutes=5)),
        FailoverStep("Resume normal operations", duration=timedelta(minutes=5))
    ],
    testing_schedule=TestingSchedule(
        full_dr_test=timedelta(weeks=4),
        partial_failover_test=timedelta(weeks=1),
        backup_restore_test=timedelta(days=1)
    )
)
```

## Decision Log

### Key Decisions with Rationale

**Decision 1: PostgreSQL for Central Tier**
- **Rationale:** ACID compliance required for billing operations, proven scalability for authentication
- **Alternatives Considered:** SQLite (insufficient for multi-user), MongoDB (no ACID for billing)
- **Trade-offs Accepted:** Additional operational complexity vs. data consistency guarantees

**Decision 2: Turso for Project and Master Customer Tiers**
- **Rationale:** SQLite compatibility preserves existing optimizations, geographic distribution capabilities
- **Alternatives Considered:** PostgreSQL (too heavy for project data), Redis (no SQL capabilities)
- **Trade-offs Accepted:** Vendor lock-in vs. optimal performance and scaling characteristics

**Decision 3: RoaringBitmap for Tag Operations**
- **Rationale:** O(1) set operations on compressed bitmaps, proven performance at universe scale
- **Alternatives Considered:** Hash-based sets (memory intensive), B-tree indexes (slower for set ops)
- **Trade-offs Accepted:** Additional complexity vs. performance requirements for 1M+ cards

**Decision 4: OAuth2 with Workspace State Parameter**
- **Rationale:** Industry standard, Auth0 compatibility, workspace context preservation
- **Alternatives Considered:** Custom JWT (maintenance overhead), Session-based (not stateless)
- **Trade-offs Accepted:** Auth0 dependency vs. development velocity and security

### Future Considerations

**Evolutionary Architecture Decisions:**

1. **Event Sourcing for Audit Trail**
   - **Consideration:** Implement event sourcing across all tiers for complete audit capabilities
   - **Timeline:** 6-12 months after initial deployment
   - **Dependencies:** Proven stability of current architecture

2. **CQRS for Read/Write Separation**
   - **Consideration:** Separate read and write models for better performance optimization
   - **Timeline:** 12-18 months for high-scale customers
   - **Dependencies:** Clear performance bottlenecks identified

3. **GraphQL API Layer**
   - **Consideration:** Unified API across all tiers with fine-grained permissions
   - **Timeline:** 18-24 months for API ecosystem development
   - **Dependencies:** Client-side requirements for flexible queries

## Appendices

### Glossary of Terms

**Multi-Tier Architecture:** Database architecture separating concerns across multiple database instances with different optimization characteristics

**RoaringBitmap:** Compressed bitmap data structure optimized for set operations on sparse datasets

**Card Multiplicity:** Patent-compliant approach allowing semantic content instances to proliferate across spatial zones

**Turso:** Distributed SQLite-compatible database service providing global edge deployment

**OAuth2 State Parameter:** Mechanism for preserving application context (workspace) across authentication redirects

**Set Theory Operations:** Mathematical operations (intersection, union, difference) applied to card collections

**Polymorphic Rendering:** Architecture pattern enabling multiple output formats through common interfaces

### Reference Documentation Links

**Database Technologies:**
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Turso Documentation](https://docs.turso.tech/)
- [SQLite Documentation](https://sqlite.org/docs.html)
- [RoaringBitmap Implementation](https://github.com/RoaringBitmap/roaring)

**Authentication Standards:**
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Auth0 Documentation](https://auth0.com/docs)
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

**Performance Optimization:**
- [Database Performance Tuning](https://use-the-index-luke.com/)
- [SQLite Performance Tuning](https://sqlite.org/optoverview.html)
- [Set Theory in Computer Science](https://en.wikipedia.org/wiki/Set_theory)

### Detailed Calculations

**RoaringBitmap Memory Usage Calculation:**

For a workspace with 1,000,000 cards and 10,000 unique tags:
- **Uncompressed bitmap size:** 1,000,000 bits × 10,000 tags = 1.25 GB
- **RoaringBitmap compressed size:** ~10-50% of uncompressed = 125-625 MB
- **Memory overhead per tag:** 12.5-62.5 KB average
- **Cache size for 1000 most frequent tags:** 12.5-62.5 MB

**Cross-Tier Authentication Latency:**

Assuming network latencies:
- Client → Auth0: 50ms
- Auth0 → Central PostgreSQL: 30ms
- Central PostgreSQL → Turso: 20ms
- **Total authentication time:** 100ms target, 150ms maximum

**Performance Scaling Projections:**

| Cards | Tags | Memory (MB) | Query Time (ms) | Storage (GB) |
|-------|------|-------------|-----------------|--------------|
| 100K  | 1K   | 1.25-6.25   | 0.5-2          | 0.1         |
| 1M    | 10K  | 12.5-62.5   | 5-20           | 1           |
| 10M   | 100K | 125-625     | 50-200         | 10          |

### Supporting Research

**Set Theory Performance Research:**
- Academic studies on bitmap indexing performance
- Industry benchmarks for tag-based filtering systems
- Comparative analysis of set operation algorithms

**Multi-Tier Database Patterns:**
- Microservices database decomposition strategies
- CQRS and event sourcing implementation patterns
- Cross-service transaction management approaches

**Authentication Architecture:**
- OAuth2 implementation best practices
- Multi-tenant authentication patterns
- Workspace context preservation techniques