# multicardz Authentication, Authorization & Access Architecture


---
**IMPLEMENTATION STATUS**: SUPERSEDED
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Consolidated into doc 039-2025-11-06-Authentication-Architecture-and-Plan.md
**SUPERSEDED BY**: docs/architecture/039-2025-11-06-Authentication-Architecture-and-Plan.md
---


## Overview

multicardz uses Auth0 as its primary authentication provider with a secure cookie-based authentication system. This approach enhances security and user experience by:

1. Only storing minimal user information (User ID) in secure HTTP-only session cookies
2. Keeping Auth0 access tokens securely on the server in a thread-safe in-memory store
3. Using secure, HTTP-only cookies for all authentication (no client-side token management)
4. Supporting OAuth2 authorization code flow with PKCE
5. Integrating subscription validation middleware for premium features
6. Eliminating browser refresh authentication issues through automatic cookie transmission

## Authentication Flow

### 1. User Registration & Login (Auth0 OAuth2 Flow)

1. User visits `/login` endpoint which redirects to Auth0 authorization endpoint
2. Auth0 handles authentication via:
   - Email/password forms
   - Social providers (Google, Apple, etc.)
   - Enterprise SSO connections
3. Auth0 redirects back to `/callback` with authorization code and state parameter
4. Server exchanges authorization code for tokens using Auth0 API:
   - ID token (contains user profile information)
   - Access token (for Auth0 Management API calls)
   - Refresh token (for token renewal)
5. Server processes authentication:
   - Extracts user profile from ID token
   - Creates or updates user record in database using Auth0 ID as primary key
   - **NEW**: Parses state parameter for subscription linking (if present)
   - **NEW**: Links new users to subscription records when subscription ID found in state
   - Stores Auth0 tokens in server-side token store (`auth0_token_store`)
   - Creates session JWT containing only the user ID
   - Sets session JWT in secure HTTP-only cookie
6. Client receives secure cookie automatically
7. For subsequent requests, cookie is automatically included by browser

### 2. Subscription Integration via OAuth State Parameter

multicardz integrates subscription flow with authentication using the OAuth state parameter:

1. **After Stripe Payment**:
   - Admin app receives Stripe webhook/success callback
   - Creates subscription record in database
   - Redirects user to Auth0 with subscription ID embedded in state parameter:
     ```json
     {"subscriptionID": 12345}
     ```

2. **Auth0 Callback Processing**:
   - Main app callback receives auth code + state parameter
   - Parses state to extract subscription ID
   - Links authenticated user to subscription record
   - Redirects new subscription users to `/profile` for account setup

3. **State Parameter Format**:
   ```python
   # Admin app generates Auth0 URL with state
   state_data = {"subscriptionID": subscription_id, "returnTo": "/custom-page"}
   state_json = json.dumps(state_data)
   state_encoded = urllib.parse.quote(state_json)
   auth0_url = f"https://domain.auth0.com/authorize?...&state={state_encoded}"

   # Main app callback parses state
   state_decoded = urllib.parse.unquote(state_param)
   state_data = json.loads(state_decoded)
   subscription_id = state_data.get("subscriptionID")
   ```

This OAuth state-based approach provides secure subscription integration using industry-standard patterns.

### 2. Token Management

- **Two-token system**:
  - **Auth0 tokens**: Access/ID/refresh tokens stored server-side in `auth0_token_store`
  - **Session JWT**: Contains only the user ID, stored in secure HTTP-only cookie
- **Storage**: Session JWT stored in secure cookie with proper security flags:
  - `HttpOnly`: Prevents JavaScript access, protecting against XSS attacks
  - `Secure`: Cookie only sent over HTTPS connections
  - `SameSite=Lax`: CSRF protection while allowing normal navigation
  - `Path=/`: Available for entire application
- **Usage**: Session JWT automatically included in all HTTP requests via cookie
- **Expiration**: Session tokens expire after configurable period (default: 14400 seconds / 4 hours)
- **Cleanup**: Background thread removes expired tokens from server memory
- **Persistence**: Auth0 token store periodically saved to database via `token_snapshots` table
- **Browser Refresh Support**: Cookies automatically included in refresh requests, eliminating authentication issues

## Authorization Architecture

### 1. Request Authorization Flow

1. Browser automatically includes session cookie in all requests:
   ```http
   Cookie: session_token=<session_jwt_token>
   ```

2. The `Auth0Middleware` intercepts all requests to extract and verify the token:
   ```python
   # Extract token from secure cookie
   session_token = request.cookies.get("session_token")

   # Verify session token and retrieve user info
   user_info = await self._verify_session_token(session_token)
   ```

3. Token verification process:
   ```python
   # 1. Verify session JWT to get user ID
   user_id = verify_session_token(token)

   # 2. Get Auth0 tokens from server-side store using user ID
   auth0_tokens = auth0_token_store.get_tokens(user_id)

   # 3. Validate Auth0 access token if needed
   # 4. Set user context for request processing
   ```

4. On successful verification:
   - User information is added to request state
   - User ID is set in context variables for data filtering
   - Request proceeds to subscription validation middleware (if enabled)
   - Then proceeds to the route handler

5. On failed verification:
   - Returns JSON response with redirect information for client-side handling
   - No special browser refresh handling needed due to automatic cookie transmission

### 2. Subscription Validation Middleware

After successful authentication, requests pass through subscription validation middleware:

```python
# Enabled via environment variable and global config
ENABLE_SUBSCRIPTION_VALIDATION = True

# Middleware validates user subscription status
class SubscriptionValidationMiddleware:
    async def __call__(self, request: Request, call_next):
        user_id = get_current_user_id()

        # Check subscription status via Stripe API or local database
        subscription_status = await validate_subscription(user_id)

        if not subscription_status.is_active:
            return redirect_to_subscription_page()

        return await call_next(request)
```

### 3. Simplified Client-Side Authentication

With cookie-based authentication, client-side code is greatly simplified:

```javascript
// Handle logout responses
function handleAuthResponse(response) {
    // Handle redirect if provided
    if (response.redirect_url) {
        window.location.href = response.redirect_url;
    }

    // Handle logout (cookie cleared server-side)
    if (response.logged_out) {
        window.location.href = "/static/new_first_page.html";
    }
}

// Handle JSON responses that might contain auth info
document.body.addEventListener("htmx:afterRequest", function(event) {
    const xhr = event.detail.xhr;
    if (xhr.getResponseHeader("Content-Type")?.includes("application/json")) {
        try {
            const response = JSON.parse(xhr.responseText);
            handleAuthResponse(response);
        } catch (e) {
            console.error("Error parsing JSON response", e);
        }
    }
});

// No manual token management needed - cookies handled automatically
// No need to add headers to HTMX requests - cookies included automatically
```

### 4. Middleware Architecture

The `Auth0Middleware` provides several key functions:

1. **Path Protection**: Enforces authentication for non-public paths
2. **Token Verification**: Validates session tokens and retrieves Auth0 tokens from the token store
3. **User Context**: Sets user information in request state
4. **Database Filtering**: Sets up SQLAlchemy event listeners for automatic data filtering
5. **Response Formatting**: Returns JSON responses with redirect information
6. **Cookie Management**: Handles secure cookie extraction and validation

#### Token Store Implementation

The token store uses a thread-safe in-memory dictionary with database persistence to securely manage Auth0 tokens:

```python
class TokenStore:
    def __init__(self):
        self._store: Dict[str, Tuple[str, int]] = {}  # uid -> (auth0_token, expiry)
        self._lock = threading.Lock()
        self._cleanup_timer = None
        self._persistence_timer = None
        self._instance_id = SERVER_INSTANCE_ID

        # Start maintenance tasks
        self._schedule_cleanup()
        if ENABLE_PERSISTENCE:
            self._schedule_persistence()

    def store_token(self, uid: str, auth0_token: str, expiry: int) -> None:
        with self._lock:
            self._store[uid] = (auth0_token, expiry)
            security_logger.info(f"Token stored for user {uid}, expires at {expiry}")

    def get_token(self, uid: str) -> Optional[str]:
        with self._lock:
            if uid not in self._store:
                security_logger.info(f"No token found for user {uid}")
                return None

            token, expiry = self._store[uid]
            current_time = int(time.time())

            # Check if token is expired
            if current_time >= expiry:
                # Remove expired token
                del self._store[uid]
                security_logger.info(f"Expired token removed for user {uid}")
                return None

            return token

    def remove_token(self, uid: str) -> None:
        """Remove a token from the store (e.g., during logout)."""
        with self._lock:
            if uid in self._store:
                del self._store[uid]
                security_logger.info(f"Token manually removed for user {uid}")
```

The store includes automatic cleanup to prevent memory bloat and database persistence for token recovery between server restarts:

```python
def _cleanup_expired_tokens(self):
    """Periodically remove expired tokens to prevent memory bloat."""
    try:
        current_time = int(time.time())
        expired_count = 0

        with self._lock:
            expired_uids = []
            for uid, (_, expiry) in self._store.items():
                if current_time >= expiry:
                    expired_uids.append(uid)

            for uid in expired_uids:
                del self._store[uid]
                expired_count += 1

        security_logger.info(f"Token cleanup: removed {expired_count} expired tokens. Store size: {len(self._store)}")
    finally:
        # Always reschedule, even after errors
        self._schedule_cleanup()

def _persist_to_database(self):
    """Periodically save token store to database for persistence across restarts."""
    if not ENABLE_PERSISTENCE:
        return

    try:
        # Create a copy of the store to avoid holding the lock too long
        with self._lock:
            store_copy = self._store.copy()

        # Only persist if we have tokens
        if not store_copy:
            security_logger.info("No tokens to persist, skipping database snapshot")
            return

        # Serialize token store (excluding the expiration timestamps)
        serialized_data = {}
        current_time = int(time.time())

        for uid, (auth0_token, expiry) in store_copy.items():
            # Only persist non-expired tokens
            if current_time < expiry:
                serialized_data[uid] = auth0_token

        # Skip if no valid tokens
        if not serialized_data:
            security_logger.info("No valid tokens to persist, skipping database snapshot")
            return

        # Convert to JSON and save to database
        snapshot_json = json.dumps(serialized_data)

        # Save snapshot to token_snapshots table
        # ...

        security_logger.info(f"Token store persisted to database. Snapshot contains {len(serialized_data)} tokens.")

    finally:
        # Always reschedule, even after errors
        self._schedule_persistence()
```

## HTMX-Based Navigation with Cookie Authentication

The application uses HTMX for all navigation with cookies automatically included in every request to maintain seamless authentication across the application.

### IMPORTANT: Never Use HX-Redirect for Authentication Redirects

NEVER use the `HX-Redirect` header in authentication-related responses as it will ALWAYS break the middleware authentication flow. Instead:

1. Return a standard JSON response with a 401 status code
2. Include a `redirect_url` field in the JSON body
3. Let client-side JavaScript handle the redirect based on the response body
4. Client code should check for 401 status codes and redirect accordingly

Example middleware approach:
```python
# CORRECT APPROACH
response = JSONResponse(status_code=401,
                       content={"status": "error",
                               "message": "Authentication required",
                               "redirect_url": "/static/new_first_page.html"})
return response
```

Example client-side handler:
```javascript
document.body.addEventListener("htmx:responseError", function(event) {
    if (event.detail.xhr.status === 401) {
        try {
            const response = JSON.parse(event.detail.xhr.responseText);
            if (response.redirect_url) {
                window.location.href = response.redirect_url;
            }
        } catch (e) {
            // Default fallback
            window.location.href = "/static/new_first_page.html";
        }
    }
});
```

### 1. HTMX Navigation with Authentication

Every HTMX request automatically includes session cookies with no client-side configuration needed:

```html
<!-- Standard navigation link -->
<a href="#"
   hx-get="/card_dashboard"
   hx-target="body"
   hx-push-url="true">
   Dashboard
</a>

<!-- Navigation with additional parameters -->
<button
    class="bg-multicardz-blue text-white px-6 py-2 rounded shadow-button"
    hx-get="/card_builder?card_id={{ card.id }}"
    hx-target="body"
    hx-push-url="true">
    Next
</button>
```

Cookies are automatically included by the browser:
```http
GET /card_dashboard HTTP/1.1
Host: app.multicardz.com
Cookie: session_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 2. Form Submissions with Cookie Setting

Authentication forms set secure cookies and return JSON responses with redirect information:

```html
<form class="space-y-4"
      hx-post="/auth/signin"
      hx-target="#response-container">
    <!-- Form fields -->
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Sign In</button>
</form>
```

Server route implementation:
```python
@router.post("/callback")
async def callback(request: Request, code: str, state: str = ""):
    # Exchange Auth0 code for tokens
    tokens = await exchange_code_for_tokens(code)

    # Extract user info from ID token
    user_info = extract_user_info_from_token(tokens["id_token"])
    user_id = user_info.get("auth0_id")

    # Store Auth0 tokens in server-side store
    auth0_token_store.store_token(user_id, tokens["access_token"],
                                 tokens["refresh_token"], tokens["expires_in"])

    # Create session token with only the user ID
    session_token = create_session_token(user_id)

    # Set secure cookie and redirect
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,      # Prevent JavaScript access
        secure=True,        # HTTPS only
        samesite="lax",     # CSRF protection
        max_age=14400,      # 4 hours
        path="/"            # Available site-wide
    )
    return response
```

### 3. Simplified Client-Side Handling

Client-side JavaScript is greatly simplified with cookie authentication:

```javascript
// Function to handle authentication responses
function handleAuthResponse(response) {
    // Handle redirect if provided
    if (response.redirect_url) {
        window.location.href = response.redirect_url;
    }

    // Handle logout (cookies cleared server-side)
    if (response.logged_out) {
        window.location.href = "/static/new_first_page.html";
    }
}

// Listen for responses that might contain auth info
document.body.addEventListener("htmx:afterRequest", function(event) {
    if (event.detail.xhr.getResponseHeader("Content-Type")?.includes("application/json")) {
        try {
            const response = JSON.parse(event.detail.xhr.responseText);
            handleAuthResponse(response);
        } catch (e) {
            console.error("Error handling auth response", e);
        }
    }
});

// No token management needed - cookies handled automatically by browser
```

### 4. HTML Responses with Authentication

For HTML responses that require authentication, the middleware uses JSON with redirect information:

```python
# In the middleware
def _handle_unauthenticated(self, request: Request):
    """Handle unauthenticated requests based on content type."""
    # Determine if this is an API request or browser request
    accepts_html = "text/html" in request.headers.get("accept", "")
    is_htmx = request.headers.get("HX-Request", "") == "true"

    if accepts_html:
        if is_htmx:
            # For HTMX requests, use HTMX headers for redirection
            response = JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "Authentication required",
                    "redirect_url": self.login_redirect
                }
            )
            response.headers["HX-Redirect"] = self.login_redirect
            return response
        else:
            # Regular browser request - return JSON with redirect info
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "Authentication required",
                    "redirect_url": self.login_redirect
                }
            )
    else:
        # API request - return standard 401 response
        return JSONResponse(
            status_code=401,
            content={"status": "error", "detail": "Not authenticated"}
        )
```

## Special Considerations

### 1. Simplified Client-Side Authentication Flow

The cookie-based authentication approach eliminates most client-side complexity:

1. **No token storage needed**:
   ```javascript
   // Cookies are automatically managed by the browser
   // No localStorage or manual token management required
   ```

2. **Automatic inclusion in requests**:
   ```javascript
   // All requests automatically include cookies
   fetch('/api/data');  // Cookie automatically included

   // HTMX requests automatically include cookies - no configuration needed
   ```

3. **Handle JSON responses with redirect information**:
   ```javascript
   // Process responses for redirects and logout
   async function processResponse(response) {
       if (response.headers.get('Content-Type')?.includes('application/json')) {
           const data = await response.json();

           // Handle redirects
           if (data.redirect_url) {
               window.location.href = data.redirect_url;
           }

           // Handle logout (cookie cleared server-side)
           if (data.logged_out) {
               window.location.href = "/static/new_first_page.html";
           }

           return data;
       }
       return response;
   }
   ```

4. **Handle 401 responses for authentication failures**:
   ```javascript
   // Generic error handler for fetch requests
   function handleResponse(response) {
       if (response.status === 401) {
           // Authentication failed, redirect to login
           const data = await response.json();
           window.location.href = data.redirect_url || '/login';
           return null;
       }
       return response;
   }
   ```

### 2. User Model Structure

The user model has been migrated to use Auth0 as the primary authentication provider:

```python
class User(Base):
    __tablename__ = "users"

    # Primary key: Auth0 user ID
    id = Column(String, primary_key=True)  # e.g., "auth0|64a1b2c3d4e5f6789012345"

    # User profile data from Auth0
    email = Column(String, unique=True, nullable=False)
    auth_provider = Column(String, default="auth0")

    # Additional profile fields populated from Auth0 ID token
    name = Column(String)
    picture = Column(String)
    email_verified = Column(Boolean, default=False)

    # Automatic user creation/update from Auth0 profile
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

**Implementation Notes:**
- User ID uses Auth0 ID as primary key
- Email serves as unique identifier
- Automatic profile synchronization from Auth0 ID token claims
- Cookie-based authentication eliminates client-side token management

### 3. Public Paths

The following paths are excluded from authentication requirements:

```python
public_paths = [
    "/login",      # Auth0 login redirect
    "/callback",   # Auth0 callback endpoint
    "/terms",
    "/static/",
    "/favicon.ico"
]
```

### 4. Data Filtering

multicardz uses a multi-layered approach to automatically filter database queries based on the authenticated user:

#### 3.1 User ID Lookup Strategy

The system uses multiple methods to find the current user ID, in this priority order:

1. In-memory thread-local cache (to avoid repeated lookups)
2. ContextVar set by the middleware (primary source)
3. Request object in call stack (fallback method)

```python
# Cached lookup for better performance
def get_user_id_from_stack():
    # Check thread-local cache first
    thread_id = threading.get_ident()
    if thread_id in REQUEST_UID_CACHE and not expired:
        return REQUEST_UID_CACHE[thread_id][0]

    # Try to get from context variable (set by middleware)
    from py_core.middleware import current_user_id
    user_id = current_user_id.get()
    if user_id:
        # Cache and return
        REQUEST_UID_CACHE[thread_id] = (user_id, time.time())
        return user_id

    # Fallback: find request in call stack
    # (stack search implementation)

    # Cache result for future calls
    REQUEST_UID_CACHE[thread_id] = (user_id, time.time())
    return user_id
```

#### 3.2 SQLAlchemy Event Listeners

The system uses event listeners to automatically filter queries based on the user context:

```python
@event.listens_for(Query, "before_compile", retval=True)
def filter_query_by_user(query):
    # Skip if already filtered
    if getattr(query, '_has_user_filter', False):
        return query

    # Check if any model in query needs filtering
    need_filtering = False
    for entity in query.column_descriptions:
        entity_type = entity.get('entity', None) or entity.get('type', None)
        if entity_type in FILTERED_MODELS:
            need_filtering = True
            break

    if need_filtering:
        # Get user ID using our optimized lookup function
        user_id = get_user_id_from_stack()

        if user_id:
            # Apply filter using user ID
            query = query.filter(Cards.user_id == user_id)
            query._has_user_filter = True
        else:
            # SECURITY: If no user ID found, return empty results
            # This prevents data leakage between users
            query = query.filter(Cards.user_id == "IMPOSSIBLE_MATCH_SECURITY_BLOCK")
            query._has_user_filter = True
            security_logger.warning("SECURITY ALERT: No user ID for query - blocking results")

    return query
```

#### 3.3 Security Measures in Data Filtering

The system includes several security features:

1. **Zero-data policy**: When user ID can't be determined, queries return zero results
2. **Detailed security logging**: Failed authentication attempts are logged with context
3. **Memory management**: Cached user IDs are automatically cleaned up to prevent leaks
4. **Optimized lookup**: Thread-local caching reduces overhead and call stack searches
5. **Middleware synchronization**: Data filters work with the middleware authentication system

## Token Verification Details

The Auth0-based two-token approach provides enhanced security:

### 1. Session JWT Format

The client-side session token contains minimal information:
```python
payload = {
    "sub": user_id,                          # Auth0 User ID
    "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,  # Expiration time
    "iat": int(time.time())                   # Issue time
}
token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

### 2. Verification Process

The token verification is a multi-step process:
```python
# Step 1: Verify session JWT to get user ID
user_id = verify_session_token(token)
if not user_id:
    security_logger.warning("Authentication failed: Invalid session token")
    return None

# Step 2: Get Auth0 tokens from store using user ID
auth0_tokens = auth0_token_store.get_tokens(user_id)
if not auth0_tokens:
    security_logger.warning(f"Authentication failed: No Auth0 tokens found for user: {user_id}")
    return None

# Step 3: Validate Auth0 access token (if needed for API calls)
try:
    # Auth0 tokens are validated during the OAuth2 flow
    security_logger.info(f"Authentication successful for user: {user_id}")
    return user_info
except Exception as e:
    security_logger.warning(f"Authentication failed: Auth0 token invalid for user: {user_id}")
    # If Auth0 tokens are invalid, remove them from the store
    auth0_token_store.remove_tokens(user_id)
    return None
```

### 3. Auth0 Token Store

The Auth0 token store provides secure server-side storage and automatic cleanup:
```python
# Store tokens
auth0_token_store.store_tokens(user_id, access_token, id_token, refresh_token, expiry)

# Retrieve tokens
tokens = auth0_token_store.get_tokens(user_id)

# Remove tokens (e.g., during logout)
auth0_token_store.remove_tokens(user_id)
```

## Security Enhancements

The Auth0-based authentication system with secure cookies enhances security in several ways:

1. **OAuth2 Security Model**: Uses industry-standard OAuth2 authorization code flow with PKCE
   - Eliminates password handling on application servers
   - Auth0 manages secure credential storage and validation
   - Built-in protection against common attacks (CSRF, replay attacks)

2. **Secure Cookie Architecture**: Separates client-side session tokens from sensitive Auth0 tokens
   - Session cookies are HTTP-only, preventing JavaScript access and XSS attacks
   - Secure flag ensures cookies only transmitted over HTTPS
   - SameSite=Lax provides CSRF protection while allowing normal navigation
   - Auth0 access/ID tokens stay server-side, protected from client-side attacks
   - Refresh tokens enable secure token renewal without re-authentication

3. **Reduced Attack Surface**:
   - No client-side token storage eliminates localStorage/sessionStorage attacks
   - No direct password handling reduces credential theft risks
   - Auth0's security infrastructure handles authentication complexity
   - Regular security updates managed by Auth0
   - Browser refresh authentication works seamlessly without security compromises

4. **Dedicated Security Logging**: All authentication events are logged:
   ```python
   # Security logger that always logs regardless of debug settings
   security_logger = logging.getLogger('security')
   security_logger.setLevel(logging.INFO)
   security_logger.propagate = False
   ```

5. **Memory Management**: Prevents memory bloat through automatic cleanup:
   ```python
   # Token cleanup runs periodically and removes expired tokens
   def _cleanup_expired_tokens(self):
       current_time = int(time.time())
       with self._lock:
           expired_tokens = [user_id for user_id, (_, expiry) in self._store.items()
                           if current_time >= expiry]
           for user_id in expired_tokens:
               del self._store[user_id]
   ```

6. **Multi-Factor Authentication**: Auth0 supports MFA out of the box
   - SMS, email, and authenticator app options
   - Risk-based authentication triggers
   - Administrative control over MFA policies

## Environment Configuration

The Auth0-based authentication system is configurable through environment variables:

```python
# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")  # e.g., "your-domain.auth0.com"
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")  # For Management API access

# JWT configuration for session tokens
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Token expiration (default: 4 hours / 14400 seconds)
TOKEN_EXPIRY_SECONDS = int(os.getenv("TOKEN_EXPIRY_SECONDS", "14400"))

# Auth0 token store maintenance
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600"))
PERSISTENCE_INTERVAL_SECONDS = int(os.getenv("PERSISTENCE_INTERVAL_SECONDS", "300"))
ENABLE_PERSISTENCE = os.getenv("ENABLE_PERSISTENCE", "True").lower() in ('true', '1', 't')

# Subscription validation
ENABLE_SUBSCRIPTION_VALIDATION = os.getenv("ENABLE_SUBSCRIPTION_VALIDATION", "True").lower() in ('true', '1', 't')
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# Environment detection
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
```

## Standalone Authentication Page Architecture

### 1. Architectural Overview

As of the latest update, the application now uses a standalone static HTML page (`first_page.html`) as the landing page. This represents a significant architectural change from the previous approach:

1. **Static File vs. FastAPI Route**:
   - The landing page is now served as a static file from the `/static` directory
   - The root route (`/`) redirects to `/static/first_page.html`
   - The page operates entirely outside FastAPI's routing and middleware system

2. **Authentication Flow Changes**:
   - Authentication occurs directly between the browser and Auth0
   - After successful authentication, tokens are submitted to the server via standard form POST
   - No HTMX is used in this initial authentication flow

3. **Authentication UI**:
   - A modal signin/signup form appears either on button click or after a 30-second delay
   - Both forms (signin and signup) exist in the same page with a smooth transition between them
   - Authentication errors are handled and displayed directly in the UI

### 2. Rationale for This Approach

This architectural change was implemented for several key reasons:

1. **Middleware Isolation**:
   - By serving the landing page as a static file, it completely bypasses all FastAPI middleware
   - This eliminates middleware as a potential source of authentication problems
   - Particularly useful for isolating issues with `Auth0Middleware`

2. **Direct Auth0 Communication**:
   - The page communicates directly with Auth0 Authentication services
   - No server-side code is involved until after successful authentication
   - This simplifies debugging of Auth0 API issues

3. **Cross-Domain Testing**:
   - The static page can be accessed via different hostnames (localhost vs 127.0.0.1)
   - This helps troubleshoot hostname-specific authentication issues (particularly relevant for Apple Sign-In)

4. **Authentication Diagnostics**:
   - The page includes detailed logging of authentication steps
   - A debug panel shows token information and API responses
   - This makes it easier to pinpoint exactly where authentication fails

### 3. Technical Implementation

The implementation involves these components:

1. **FastAPI Root Route Redirect**:
   ```python
   @app.get("/")
   async def root(request: Request):
       logger.info("Loading first page")
       return RedirectResponse(url="/static/first_page.html")
   ```

2. **Static Authentication Page**:
   - A completely self-contained HTML page in the static directory
   - Includes all required CSS and JavaScript
   - Implements Auth0 initialization, authentication, and token handling
   - Submits tokens via standard form POST (not HTMX)

3. **Server-Side Token Processing**:
   - The `/signin` and `/signup` endpoints still handle token verification
   - They continue to implement the two-token system described earlier
   - No changes to the server-side token processing logic were needed

### 4. Security Considerations

This approach maintains the same security model as before, with some additional considerations:

1. **No Middleware Protection**:
   - Since the page bypasses middleware, it doesn't benefit from middleware security features
   - This is acceptable for the authentication page which is inherently public

2. **Direct API Access**:
   - The page communicates directly with Auth0 APIs
   - API key restrictions should be properly configured in Auth0 Dashboard

3. **Static File Serving**:
   - The page is served as a static file, which may have different caching behavior
   - Cache headers should be appropriately set if needed

## Implementation Recommendations

For production implementation, consider:

1. **Secret Key Management**:
   - Store JWT_SECRET_KEY in a secure secret manager
   - Implement key rotation periodically
   - Use different keys for development and production

2. **Additional Security Headers**:
   - Add Content-Security-Policy headers
   - Add X-XSS-Protection headers
   - Implement strict CORS policies

3. **Rate Limiting**:
   - Implement rate limiting for authentication endpoints
   - Add progressive delays for repeated failed login attempts

4. **Token Refresh Mechanism**:
   - Implement token refresh to extend session lifetime for active users
   - Consider refresh tokens with longer expiry for persistent sessions

5. **HTTPS Enforcement**:
   - Ensure all authentication traffic is over HTTPS
   - Use HSTS headers to prevent protocol downgrade attacks