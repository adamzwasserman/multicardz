# Authentication Architecture and Plan

---
**IMPLEMENTATION STATUS**: PHASED IMPLEMENTATION
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Deferred to auth phase. Current: hardcoded "default-user"/"default-workspace"
---

## Executive Summary

This document consolidates all authentication and authorization architecture for MultiCardz from four source documents into a single authoritative reference. It defines both the current development state (hardcoded user IDs) and the planned production architecture (Auth0 OAuth2 + Stripe integration + UUID zero-trust data isolation).

**Current Phase (Development - Alpha)**:
- Hardcoded user IDs: `"default-user"` / `"default-workspace"`
- No authentication system implemented
- Single-user mode acceptable for alpha testing
- Focus on core feature development without auth complexity

**Planned Architecture (Post-MVP, Pre-Beta)**:
- Auth0 OAuth2 authorization code flow with PKCE
- Secure cookie-based session management with server-side token storage
- Stripe Checkout for subscription management
- UUID-based zero-trust data isolation via `data_filter` middleware
- Anonymous-to-paid user conversion tracking

**This Document Supersedes**:
1. `016-2025-09-28-multicardz-Zero-Trust-UUID-Architecture-v1.md`
2. `multicardz_auth_architecture.md`
3. `STRIPE_AUTH0_SECURITY_DOCUMENTATION.md`
4. `auth-subscription-user-management-requirements.md`

---

## Section 1: Current Phase (Development)

### 1.1 Hardcoded User IDs for Development

**Purpose**: Enable rapid feature development without authentication complexity during alpha phase.

**Implementation**:
```python
# Current hardcoded identifiers in use
DEFAULT_USER_ID = "default-user"
DEFAULT_WORKSPACE_ID = "default-workspace"
```

**Where Used**:
- All card creation/reading operations
- Tag management operations
- Workspace isolation (placeholder)
- Database queries (no filtering currently needed)

### 1.2 Why This Approach is Acceptable for Alpha

**Justification**:
- **Single-user focus**: Alpha testing with controlled user base
- **Feature priority**: Core functionality (drag-drop, tags, groups) takes precedence
- **Migration path exists**: Clear upgrade plan to production auth (see Section 4)
- **Security adequate**: Alpha deployment is access-controlled
- **Development velocity**: Team can iterate on UX without auth friction

**Limitations Acknowledged**:
- Cannot support multiple users concurrently
- No subscription billing possible
- No true data isolation
- Not suitable for public release

### 1.3 Development/Test Mode (Future)

When authentication is implemented, a development bypass mode will be available:

**Environment Variables**:
```bash
DEV_MODE_KEY=secret-dev-key-12345  # Activates dev mode
DEV_USER_ID=test-user-uuid         # Test user for data isolation
```

**Safety Measures**:
- Only works with non-production database URLs
- Logs "DEVELOPMENT MODE ACTIVE" on every HTTP request
- Includes `X-Dev-Mode: true` header in all responses
- Still enforces UUID-based data filtering (using test user_id)
- System refuses to start if production database detected

---

## Section 2: Planned Architecture (Auth0/UUID)

### 2.1 Authentication System (Auth0 OAuth2)

#### 2.1.1 Core Authentication Flow

**Technology Stack**:
- **Auth0**: OAuth2 authorization code flow with PKCE
- **Session Management**: HTTP-only secure cookies
- **Token Storage**: Server-side thread-safe token store

**OAuth2 Flow**:
```
1. User → Auth0 Login (email/password, Google, Apple, Microsoft)
2. Auth0 → Authorization code returned
3. Application → Exchange code for tokens (ID, access, refresh)
4. Application → Extract user claims from ID token
5. Application → Create/update user in database
6. Application → Create session JWT (user_id only)
7. Application → Set secure HTTP-only cookie
8. Browser → Cookie automatically included in all requests
```

**Session Token (Client-Side Cookie)**:
```python
# Minimal session token (client-side)
payload = {
    "sub": user_id,                # Auth0 User ID
    "exp": int(time.time()) + 14400,  # 4 hour expiration
    "iat": int(time.time())           # Issue time
}
session_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

# Cookie configuration
response.set_cookie(
    key="session_token",
    value=session_token,
    httponly=True,   # Prevent JavaScript access (XSS protection)
    secure=True,     # HTTPS only
    samesite="lax",  # CSRF protection
    max_age=14400,   # 4 hours
    path="/"         # Available site-wide
)
```

**Auth0 Tokens (Server-Side Storage)**:
```python
# Server-side token store
class TokenStore:
    def __init__(self):
        self._store: Dict[str, Tuple[str, int]] = {}  # uid -> (access_token, expiry)
        self._lock = threading.Lock()

    def store_token(self, uid: str, access_token: str, refresh_token: str, expiry: int):
        with self._lock:
            self._store[uid] = (access_token, refresh_token, expiry)

    def get_token(self, uid: str) -> Optional[str]:
        with self._lock:
            if uid in self._store:
                token, refresh, expiry = self._store[uid]
                if time.time() < expiry:
                    return token
                # Auto-refresh if expired
                return self._refresh_token(uid, refresh)
            return None
```

#### 2.1.2 Authentication Middleware

**Request Processing Flow**:
```
Request → Extract Cookie → Validate Session Token → Get user_id →
Fetch Auth0 Token from Store → Validate/Refresh → Check Subscription →
Set Request Context → Proceed to Route Handler
```

**Middleware Implementation Pattern**:
```python
class Auth0Middleware:
    async def __call__(self, request: Request, call_next):
        # Extract session token from cookie
        session_token = request.cookies.get("session_token")

        if not session_token and not self._is_public_path(request.url.path):
            return JSONResponse(
                status_code=401,
                content={"redirect_url": "/static/login.html"}
            )

        # Validate session token and extract user_id
        try:
            user_id = self._verify_session_token(session_token)
        except Exception:
            return JSONResponse(status_code=401, content={"error": "Invalid session"})

        # Get Auth0 access token from server-side store
        auth0_token = auth0_token_store.get_token(user_id)
        if not auth0_token:
            return JSONResponse(status_code=401, content={"error": "Session expired"})

        # Set user context for data filtering
        request.state.user_id = user_id
        current_user_id.set(user_id)  # ContextVar for data_filter middleware

        # Continue to next middleware/handler
        response = await call_next(request)
        return response
```

### 2.2 Zero-Trust UUID Architecture

#### 2.2.1 UUID Assignment and Structure

**User Identifier Schema**:
```python
# Three identifier types per user
class User:
    multicardz_id: str  # Internal UUID (primary key, data isolation)
    auth0_id: str       # Auth0 "sub" claim (authentication)
    stripe_id: str      # Stripe customer ID (billing)
```

**UUID Generation**:
```python
import uuid

def create_user(auth0_id: str) -> User:
    user = User(
        multicardz_id=str(uuid.uuid4()),  # e.g., "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        auth0_id=auth0_id,                 # e.g., "auth0|64a1b2c3d4e5f6789012345"
        stripe_id=None                     # Added later when user subscribes
    )
    return user
```

#### 2.2.2 Data Isolation via `data_filter` Middleware

**Core Principle**: Every database query automatically filtered by `user_id` using SQLAlchemy event listeners.

**Implementation**:
```python
from sqlalchemy import event
from sqlalchemy.orm import Query

@event.listens_for(Query, "before_compile", retval=True)
def filter_query_by_user(query):
    # Skip if already filtered
    if getattr(query, '_has_user_filter', False):
        return query

    # Check if query involves filtered models
    for entity in query.column_descriptions:
        entity_type = entity.get('entity') or entity.get('type')
        if entity_type in [Cards, Tags, Workspaces]:
            # Get current user_id from context
            user_id = current_user_id.get()

            if user_id:
                # Inject WHERE user_id = ? clause
                query = query.filter(entity_type.user_id == user_id)
                query._has_user_filter = True
            else:
                # SECURITY: No user_id → block all results
                query = query.filter(entity_type.user_id == "IMPOSSIBLE_MATCH")
                query._has_user_filter = True
                security_logger.warning("SECURITY ALERT: No user ID for query")

    return query
```

**User ID Lookup Strategy** (Priority Order):
1. Thread-local cache (performance optimization)
2. ContextVar set by middleware (primary source)
3. Request object in call stack (fallback)
4. Security block if none found

**Benefits**:
- Developers cannot forget to add filtering (automatic)
- Consistent enforcement across all queries
- Defense in depth (even SQL injection can't bypass user_id filter)
- Performance: O(log n) indexed lookups

#### 2.2.3 Multi-Tenancy and Workspace Isolation

**Workspace-Level Filtering**:
```python
# For resources shared across workspace members
@event.listens_for(Query, "before_compile", retval=True)
def filter_query_by_workspace(query):
    for entity in query.column_descriptions:
        entity_type = entity.get('entity') or entity.get('type')
        if entity_type == SharedCards:
            workspace_id = current_workspace_id.get()
            query = query.filter(entity_type.workspace_id == workspace_id)
    return query
```

**Access Control**:
- User must have explicit workspace membership
- Workspace invitations managed via junction table
- Combined filtering: `WHERE workspace_id IN (user's workspaces)`

### 2.3 Subscription Management (Stripe Integration)

#### 2.3.1 Subscription Tiers

**Tier Structure**:
```python
class SubscriptionTier(Enum):
    FREE = "free"
    PROFESSIONAL = "professional"
    TEAM = "team"
    ENTERPRISE = "enterprise"

TIER_LIMITS = {
    "free": {"cards": 100, "workspaces": 1, "collaborators": 0},
    "professional": {"cards": 10000, "workspaces": 5, "collaborators": 5},
    "team": {"cards": 100000, "workspaces": 20, "collaborators": 50},
    "enterprise": {"cards": -1, "workspaces": -1, "collaborators": -1}  # Unlimited
}
```

#### 2.3.2 Stripe Checkout Integration

**Checkout Session Creation**:
```python
def create_checkout_session(user_id: str, price_id: str):
    user = db.query(User).filter(User.multicardz_id == user_id).first()

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url=f"{BASE_URL}/subscription/success",
        cancel_url=f"{BASE_URL}/subscription/cancel",
        client_reference_id=user.multicardz_id,
        customer_email=user.email,
        metadata={
            'multicardz_id': user.multicardz_id,
            'auth0_id': user.auth0_id
        }
    )

    return session.url
```

**Webhook Processing**:
```python
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    # Handle checkout completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        multicardz_id = session['metadata']['multicardz_id']

        # Update user with Stripe customer ID
        user = db.query(User).filter(User.multicardz_id == multicardz_id).first()
        user.stripe_id = session['customer']
        user.subscription_status = 'active'
        user.subscription_tier = 'professional'  # Or based on price_id
        db.commit()

    return {"status": "success"}
```

#### 2.3.3 Subscription Validation Middleware

**Middleware Pattern**:
```python
class SubscriptionMiddleware:
    async def __call__(self, request: Request, call_next):
        # Skip public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        user_id = request.state.user_id

        # Check subscription status
        user = db.query(User).filter(User.multicardz_id == user_id).first()

        if user.subscription_tier == 'free':
            # Allow access to free features only
            request.state.subscription_tier = 'free'
        elif user.stripe_id:
            # Verify with Stripe
            try:
                subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
                if subscription.status not in ['active', 'trialing']:
                    return JSONResponse(
                        status_code=402,
                        content={"error": "Subscription inactive", "redirect_url": "/subscribe"}
                    )
                request.state.subscription_tier = user.subscription_tier
            except Exception:
                # Stripe API failure → graceful degradation
                request.state.subscription_tier = user.subscription_tier

        return await call_next(request)
```

### 2.4 Dual Registration Architecture

#### 2.4.1 Auth-First Flow (Free Users)

**Flow**:
```
1. User → Click "Sign Up Free"
2. Redirect to Auth0 Universal Login
3. User authenticates (email/password or social)
4. Auth0 → Return ID token with claims
5. App → Create user in database:
   - Generate multicardz_id (UUID)
   - Store auth0_id from ID token
   - Set subscription_tier = "free"
   - stripe_id = NULL
6. App → Create session token, set cookie
7. User → Redirect to application dashboard
```

**Implementation**:
```python
@app.get("/auth/callback")
async def auth0_callback(code: str, state: str):
    # Exchange authorization code for tokens
    tokens = await exchange_code_for_tokens(code)

    # Extract user info from ID token
    user_info = jwt.decode(tokens['id_token'], verify=False)
    auth0_id = user_info['sub']

    # Check if user exists
    user = db.query(User).filter(User.auth0_id == auth0_id).first()

    if not user:
        # Create new free user
        user = User(
            multicardz_id=str(uuid.uuid4()),
            auth0_id=auth0_id,
            email=user_info['email'],
            subscription_tier='free',
            stripe_id=None
        )
        db.add(user)
        db.commit()

    # Store Auth0 tokens server-side
    auth0_token_store.store_token(
        user.multicardz_id,
        tokens['access_token'],
        tokens['refresh_token'],
        tokens['expires_in']
    )

    # Create session token
    session_token = create_session_token(user.multicardz_id)

    # Set cookie and redirect
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=14400
    )

    return response
```

#### 2.4.2 Pay-First Flow (Paid Users)

**Flow**:
```
1. User → Select paid subscription plan
2. App → Create Stripe checkout session
3. Redirect to Stripe Checkout
4. User → Complete payment
5. Stripe → Send webhook: checkout.session.completed
6. App → Create user in database:
   - Generate multicardz_id (UUID)
   - Store stripe_id from webhook
   - Set subscription_tier from price_id
   - auth0_id = NULL (not yet created)
7. App → Redirect user to Auth0 signup
8. User → Create Auth0 credentials
9. Auth0 → Return to callback
10. App → Add auth0_id to existing user record
11. App → Create session token, set cookie
12. User → Redirect to dashboard with premium access
```

**Webhook Handler**:
```python
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    event = validate_stripe_webhook(await request.body(), request.headers)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Create user from payment
        user = User(
            multicardz_id=str(uuid.uuid4()),
            stripe_id=session['customer'],
            email=session['customer_email'],
            subscription_tier='professional',  # Based on price_id
            subscription_status='active',
            auth0_id=None  # Will be added after Auth0 signup
        )
        db.add(user)
        db.commit()

        # Store multicardz_id in session for Auth0 redirect
        # (implementation detail: temporary token or state parameter)

    return {"status": "success"}
```

#### 2.4.3 Upgrade Flow (Free to Paid)

**Flow**:
```
1. User (authenticated, free tier) → Click "Upgrade"
2. App → Fetch user record (has multicardz_id + auth0_id)
3. App → Create Stripe checkout with multicardz_id in metadata
4. Redirect to Stripe Checkout
5. User → Complete payment
6. Stripe → Webhook: checkout.session.completed (includes multicardz_id)
7. App → Find existing user by multicardz_id
8. App → UPDATE user: add stripe_id, change tier to "professional"
9. Stripe → Redirect user back to app
10. User → Next API request
11. Middleware → Validate subscription with Stripe
12. App → Grant access to premium features (no re-auth needed)
```

**Critical Implementation**:
```python
# Step 3: Create checkout with metadata
session = stripe.checkout.Session.create(
    client_reference_id=user.multicardz_id,
    metadata={'multicardz_id': user.multicardz_id},  # CRITICAL: Linking key
    # ... other params
)

# Step 7-8: Webhook handler
if event['type'] == 'checkout.session.completed':
    multicardz_id = session['metadata']['multicardz_id']

    # Find EXISTING user (do not create new)
    user = db.query(User).filter(User.multicardz_id == multicardz_id).first()

    if not user:
        logger.error(f"User not found for multicardz_id: {multicardz_id}")
        return {"error": "User not found"}

    # UPDATE existing record (atomic transaction)
    user.stripe_id = session['customer']
    user.stripe_subscription_id = session['subscription']
    user.subscription_tier = 'professional'
    user.subscription_status = 'active'
    db.commit()
```

**Why This Design**:
- No re-authentication required (session remains valid)
- User data preserved (cards, tags, workspaces intact)
- Immediate feature access (next request picks up new tier)
- Idempotent (webhook can replay safely)

### 2.5 Anonymous-to-Paid Conversion Tracking

**Use Case**: Track users who browse anonymously, then sign up/pay.

**Implementation**:
```python
# Browser fingerprinting or anonymous session ID
@app.get("/")
async def landing_page(request: Request):
    anonymous_id = request.cookies.get("anonymous_id")
    if not anonymous_id:
        anonymous_id = str(uuid.uuid4())
        response.set_cookie("anonymous_id", anonymous_id, max_age=30*24*60*60)  # 30 days

    # Track anonymous session
    analytics.track_anonymous_visitor(anonymous_id)

# Link anonymous ID to user on signup
@app.get("/auth/callback")
async def auth0_callback(code: str):
    anonymous_id = request.cookies.get("anonymous_id")

    # Create user
    user = User(...)

    if anonymous_id:
        # Link conversion
        db.execute(
            "INSERT INTO conversions (anonymous_id, user_id, converted_at) VALUES (?, ?, NOW())",
            [anonymous_id, user.multicardz_id]
        )

    # ... rest of callback logic
```

**Analytics Benefits**:
- Attribute conversions to marketing campaigns
- Measure anonymous browsing → signup rate
- Track time-to-conversion
- A/B test landing pages and signup flows

---

## Section 3: Migration Strategy

### 3.1 When to Implement (Phased Rollout)

**Phase 0: Current (Alpha)**
- Hardcoded user IDs
- Single-user mode
- Focus: Core features

**Phase 1: MVP → Beta (Auth Implementation)**
- Trigger: Beta launch preparation
- Timeline: 2-4 weeks before public beta
- Implement:
  - Auth0 OAuth2 integration
  - Cookie-based session management
  - Server-side token storage
  - Basic user profiles

**Phase 2: Beta → Production (Zero-Trust Implementation)**
- Trigger: Beta users encountering multi-user scenarios
- Timeline: Within 4 weeks of beta launch
- Implement:
  - UUID assignment for all users
  - `data_filter` middleware for automatic query filtering
  - Workspace isolation
  - Data migration from hardcoded IDs to UUIDs

**Phase 3: Subscription Billing (Stripe Implementation)**
- Trigger: Monetization readiness
- Timeline: 2-3 months post-beta launch
- Implement:
  - Stripe Checkout integration
  - Subscription validation middleware
  - Dual registration flows (auth-first, pay-first, upgrade)
  - Payment webhook processing

### 3.2 Data Migration from Hardcoded to UUID

**Migration Script**:
```python
def migrate_to_uuid():
    # 1. Add UUID columns to existing tables
    db.execute("ALTER TABLE users ADD COLUMN multicardz_id UUID")
    db.execute("ALTER TABLE cards ADD COLUMN user_id_uuid UUID")
    db.execute("ALTER TABLE workspaces ADD COLUMN workspace_id_uuid UUID")

    # 2. Generate UUIDs for existing records
    db.execute("""
        UPDATE users
        SET multicardz_id = gen_random_uuid()
        WHERE user_id = 'default-user'
    """)

    # 3. Migrate foreign keys
    db.execute("""
        UPDATE cards
        SET user_id_uuid = (SELECT multicardz_id FROM users WHERE user_id = 'default-user')
        WHERE user_id = 'default-user'
    """)

    # 4. Rename columns (after verification)
    db.execute("ALTER TABLE cards DROP COLUMN user_id")
    db.execute("ALTER TABLE cards RENAME COLUMN user_id_uuid TO user_id")

    # 5. Add indexes for performance
    db.execute("CREATE INDEX idx_cards_user_id ON cards(user_id)")
    db.execute("CREATE INDEX idx_workspaces_workspace_id ON workspaces(workspace_id)")
```

**Migration Validation**:
```python
def validate_migration():
    # Check no NULL UUIDs
    assert db.execute("SELECT COUNT(*) FROM users WHERE multicardz_id IS NULL").scalar() == 0

    # Check all foreign keys updated
    assert db.execute("SELECT COUNT(*) FROM cards WHERE user_id NOT IN (SELECT multicardz_id FROM users)").scalar() == 0

    # Check data integrity
    original_card_count = db.execute("SELECT COUNT(*) FROM cards").scalar()
    migrated_card_count = db.execute("SELECT COUNT(*) FROM cards WHERE user_id IS NOT NULL").scalar()
    assert original_card_count == migrated_card_count
```

### 3.3 User Onboarding Flow

**First-Time User Experience**:
```
1. User → Arrive at multicardz.com
2. Landing Page → "Sign Up Free" or "View Plans"
3A. Free Path:
   - Redirect to Auth0
   - Create account (30 seconds)
   - Land in application with sample data/tutorial
3B. Paid Path:
   - Show pricing table
   - Select plan → Stripe Checkout
   - Complete payment (2 minutes)
   - Redirect to Auth0 for credentials
   - Land in application with premium features unlocked
```

**Onboarding Checklist**:
```python
class OnboardingProgress:
    created_first_card: bool = False
    added_first_tag: bool = False
    created_first_group: bool = False
    invited_team_member: bool = False  # Pro+ only
    completed_tutorial: bool = False

# Track completion for gamification/analytics
def check_onboarding_complete(user_id: str) -> bool:
    progress = get_onboarding_progress(user_id)
    return all([
        progress.created_first_card,
        progress.added_first_tag,
        progress.created_first_group,
        progress.completed_tutorial
    ])
```

---

## Section 4: Implementation Timeline

### 4.1 Phase Breakdown

**Phase 1: Auth0 Integration (2-3 weeks)**
- Week 1:
  - [ ] Set up Auth0 tenant
  - [ ] Configure OAuth2 application
  - [ ] Implement authorization code flow with PKCE
  - [ ] Create callback endpoint
- Week 2:
  - [ ] Implement session token generation
  - [ ] Set up HTTP-only cookie management
  - [ ] Build server-side token store
  - [ ] Add token refresh logic
- Week 3:
  - [ ] Create authentication middleware
  - [ ] Add public path configuration
  - [ ] Implement logout endpoint
  - [ ] Testing and bug fixes

**Phase 2: UUID Zero-Trust Architecture (2-3 weeks)**
- Week 1:
  - [ ] Add UUID columns to database schema
  - [ ] Implement UUID generation on user creation
  - [ ] Create migration script for existing data
- Week 2:
  - [ ] Implement `data_filter` middleware
  - [ ] Add SQLAlchemy event listeners for query filtering
  - [ ] Create user ID lookup functions (context, cache, stack)
- Week 3:
  - [ ] Add workspace isolation logic
  - [ ] Implement security logging
  - [ ] Testing: Verify no cross-user data leaks
  - [ ] Performance testing: O(log n) query performance

**Phase 3: Stripe Integration (3-4 weeks)**
- Week 1:
  - [ ] Set up Stripe account
  - [ ] Configure subscription products and prices
  - [ ] Implement checkout session creation
  - [ ] Add Stripe webhook endpoint
- Week 2:
  - [ ] Implement webhook signature verification
  - [ ] Add webhook event handlers (checkout.session.completed, subscription.updated, subscription.deleted)
  - [ ] Create subscription validation middleware
- Week 3:
  - [ ] Implement dual registration flows (auth-first, pay-first)
  - [ ] Add upgrade flow (free to paid)
  - [ ] Build subscription management UI
- Week 4:
  - [ ] Anonymous-to-paid conversion tracking
  - [ ] Testing: End-to-end payment flows
  - [ ] Integration testing with Stripe test mode
  - [ ] Documentation and runbooks

### 4.2 Dependencies

**Technical Dependencies**:
- Auth0 account and tenant configuration
- Stripe account and webhook endpoint setup
- Database schema updates (UUID columns, indexes)
- Environment variable configuration
- SSL certificate for secure cookies (production)

**Team Dependencies**:
- Backend team: Authentication middleware, database migration
- Frontend team: Login/signup UI, subscription UI
- DevOps team: Auth0/Stripe configuration, environment secrets
- QA team: End-to-end testing, security testing

### 4.3 Success Criteria

**Phase 1 Complete When**:
- [ ] Users can sign up via Auth0 (email/password, Google, Apple)
- [ ] Users can log in and maintain sessions
- [ ] Session tokens automatically refresh
- [ ] Users can log out successfully
- [ ] Authentication middleware blocks unauthenticated requests
- [ ] Zero security vulnerabilities in penetration testing

**Phase 2 Complete When**:
- [ ] All database queries automatically filtered by user_id
- [ ] Users cannot access other users' data (tested with multiple accounts)
- [ ] Workspace isolation functional
- [ ] Query performance meets O(log n) targets
- [ ] Security logging captures all data access attempts
- [ ] No cross-user data leaks in stress testing

**Phase 3 Complete When**:
- [ ] Users can subscribe via Stripe Checkout
- [ ] Webhooks correctly update subscription status
- [ ] Free users can upgrade to paid plans seamlessly
- [ ] Subscription validation blocks inactive subscribers
- [ ] Payment receipts sent via email
- [ ] 99.9% webhook processing success rate
- [ ] Zero payment fraud incidents

---

## Section 5: Security Considerations

### 5.1 Authentication Security

**Token Security**:
- Session tokens: HTTP-only cookies (XSS protection)
- Auth0 tokens: Server-side storage only (never exposed to JavaScript)
- Token expiration: 4 hours (configurable)
- Automatic token refresh: Before expiration
- Secure flag: Cookies only sent over HTTPS

**OAuth2 Security**:
- PKCE (Proof Key for Code Exchange): Prevents authorization code interception
- State parameter: CSRF protection
- Nonce: Replay attack prevention

**Session Management**:
- Thread-safe token store: Concurrent access protection
- Automatic cleanup: Expired tokens removed every hour
- Logout: Tokens immediately invalidated server-side

### 5.2 Data Isolation Security

**Zero-Trust Principles**:
- Never trust user input for user_id (always use authenticated session)
- Every query filtered by authenticated user's UUID
- Middleware enforcement (developers cannot forget)
- Defense in depth: Multiple layers verify ownership

**Fallback Safety**:
- If user_id not found in context → Block all results
- Log security alerts for investigation
- Audit trail of all data access attempts

**SQL Injection Prevention**:
- Parameterized queries via SQLAlchemy ORM
- Input sanitization
- Query filtering happens at ORM level (after parameterization)

### 5.3 Payment Security

**PCI-DSS Compliance**:
- Credit card data never touches our servers (Stripe handles it)
- Webhook signature verification prevents spoofing
- TLS 1.3 for all payment endpoints
- Audit logs retained for 7 years (compliance requirement)

**Webhook Security**:
- Signature verification using HMAC-SHA256
- Timestamp validation (prevent replay attacks)
- Idempotency: Safe to replay webhooks
- Transaction boundaries: Atomic database updates

---

## Section 6: Performance Considerations

### 6.1 Response Time Targets

**Authentication**:
- Token validation: < 100ms (95th percentile)
- Session creation: < 300ms
- Token refresh: < 500ms
- Overall auth flow: < 500ms

**Database Queries**:
- UUID-based lookups: O(log n) via B-tree indexes
- Query filtering overhead: < 10ms
- Session token cleanup: Background task (zero impact on requests)

**Scalability**:
- Horizontal scaling: Stateless application servers
- Token store: In-memory with optional Redis backend
- Database read replicas: Query distribution
- Connection pooling: Reduced connection overhead

### 6.2 Caching Strategy

**Subscription Status Caching**:
- Cache subscription status after Stripe verification
- TTL: 5 minutes (balance freshness vs API calls)
- Webhook updates invalidate cache immediately
- Cache miss triggers Stripe API call

**Token Store Optimization**:
- In-memory dictionary for O(1) token retrieval
- Thread-safe with read-write locks
- LRU eviction if memory threshold exceeded
- Periodic database persistence (crash recovery)

---

## Section 7: Monitoring and Observability

### 7.1 Security Logging

**Events Logged**:
- Authentication: Login, logout, token refresh, failures
- Authorization: Access denied, invalid tokens
- Data access: Every database query (debug mode)
- Subscription: Payment events, tier changes, cancellations

**Log Format**:
```python
{
    "timestamp": "2025-11-06T14:27:18Z",
    "event_type": "authentication.login",
    "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "auth0_id": "auth0|64a1b2c3d4e5f6789012345",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "outcome": "success"
}
```

**Log Retention**:
- Security logs: 90 days minimum
- Payment logs: 7 years (compliance)
- Audit logs: 1 year
- Debug logs: 30 days

### 7.2 Metrics and Alerts

**Key Metrics**:
- Authentication success rate: Target 99.9%
- Token refresh failures: Alert if > 1%
- Cross-user data access attempts: Alert on any occurrence
- Payment webhook processing success: Target 99.9%
- Query performance: Alert if 95th percentile > 500ms

**Alerting Thresholds**:
- Critical: Security breach, payment fraud, data leak
- High: Authentication failures spike, webhook processing failures
- Medium: Slow query performance, token refresh issues
- Low: Session cleanup delays, cache miss rate increase

---

## Section 8: References

**Source Documents** (Superseded by this document):
1. `/docs/architecture/016-2025-09-28-multicardz-Zero-Trust-UUID-Architecture-v1.md`
2. `/docs/architecture/multicardz_auth_architecture.md`
3. `/docs/architecture/STRIPE_AUTH0_SECURITY_DOCUMENTATION.md`
4. `/docs/requirements/auth-subscription-user-management-requirements.md`

**External References**:
- Auth0 Documentation: https://auth0.com/docs
- Stripe API Reference: https://stripe.com/docs/api
- OAuth 2.0 Specification: https://oauth.net/2/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

**Related Documents**:
- `/docs/architecture/038-2025-11-06-genX-Integration-Architecture-v1.md` (JavaScript framework)
- `/docs/biz/cardz-complete-patent.md` (Core product patents)

---

**Last Updated**: 2025-11-06
**Next Review**: Before beta launch (Phase 1 implementation)
**Owner**: Technical Architecture Team
