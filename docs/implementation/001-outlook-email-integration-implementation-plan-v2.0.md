# Outlook Email Integration Implementation Plan

## Overview
Implementation of Outlook email collection and storage in browser-based Turso database for MultiCardz application, following Superhuman's client-side storage architecture with OAuth-based authentication.

## Current State Analysis
- No email integration exists in the current MultiCardz application
- Authentication system in place using FastAPI backend
- Turso in-browser database support recently added (WebAssembly-based SQLite)
- HTMX-based UI ready for email components integration
- Function-based architecture established with no unnecessary classes

## Success Metrics
- **Response Time**: Initial sync < 5 seconds for 100 emails
- **Incremental Sync**: < 2 seconds for 10 new emails
- **Search Performance**: < 100ms for full-text search on 10k emails
- **Test Coverage**: >90% for all new code
- **Pass Rate**: 100% of BDD tests passing before deployment
- **Storage Efficiency**: < 30 KB per email average
- **Security**: Zero plaintext token storage, all tokens encrypted

---

## Phase 1: Foundation - Infrastructure Setup
**Duration**: 3 days
**Dependencies**: None
**Risk Level**: Low

### Objectives
- [ ] Set up Microsoft Entra (Azure AD) application registration
- [ ] Configure Turso database with email schema
- [ ] Implement COEP/COOP headers for SharedArrayBuffer support
- [ ] Install and configure required dependencies

### Task 1.1: Microsoft Entra App Registration and OAuth Configuration ⏸️
**Duration**: 2 hours
**Dependencies**: None
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 1.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/outlook_oauth_setup.feature
   Feature: Outlook OAuth Configuration
     As a MultiCardz administrator
     I want to configure OAuth for Outlook integration
     So that users can authenticate with Microsoft accounts

     Scenario: Successful OAuth configuration
       Given I have Microsoft Entra admin access
       When I register a new SPA application
       And I configure the redirect URIs
       And I request Mail.Read permissions
       Then I should receive a valid client ID
       And OAuth flow should be testable

     Scenario: Invalid configuration detection
       Given I have an incorrect redirect URI
       When I attempt OAuth authentication
       Then I should receive a redirect URI mismatch error
       And the error should be clearly logged
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/oauth_fixtures.py
   import pytest
   from unittest.mock import Mock

   @pytest.fixture
   def mock_msal_config():
       return {
           "client_id": "test-client-id",
           "authority": "https://login.microsoftonline.com/common",
           "redirect_uri": "http://localhost:5173/auth/callback"
       }

   @pytest.fixture
   def mock_oauth_response():
       mock = Mock()
       mock.access_token = "encrypted-test-token"
       mock.expires_in = 3600
       return mock
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/outlook_oauth_setup.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/backend/outlook_oauth.py
   from typing import Dict, Any, Optional
   from dataclasses import dataclass, field
   from functools import lru_cache

   @dataclass(frozen=True)
   class OAuthConfig:
       client_id: str
       authority: str
       redirect_uri: str
       scopes: frozenset = field(default_factory=lambda: frozenset(["User.Read", "Mail.Read"]))

   @lru_cache(maxsize=1)
   def get_oauth_config() -> OAuthConfig:
       """Get singleton OAuth configuration."""
       return OAuthConfig(
           client_id=os.getenv("MSAL_CLIENT_ID"),
           authority="https://login.microsoftonline.com/common",
           redirect_uri=os.getenv("MSAL_REDIRECT_URI")
       )

   def validate_oauth_state(state: str, stored_state: str) -> bool:
       """Validate OAuth state parameter for CSRF protection."""
       return secrets.compare_digest(state, stored_state)
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/outlook_oauth_setup.feature -v
   # All tests pass - 100% success rate ✓
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Configure Microsoft Entra OAuth for Outlook integration

   - Added OAuth configuration with frozen dataclass
   - Implemented CSRF protection with state validation
   - Created BDD tests for OAuth setup
   - Architecture compliance verified"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 1.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 2 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- OAuth configuration returns valid client ID
- State validation prevents CSRF attacks
- No classes used except frozen dataclass
- Architecture compliance verified

**Rollback Procedure**:
1. Remove OAuth configuration
2. Revert environment variables
3. Delete Azure app registration if created

### Task 1.2: Turso Database Schema Creation ⏸️
**Duration**: 3 hours
**Dependencies**: None
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 1.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/turso_email_schema.feature
   Feature: Turso Email Database Schema
     As a developer
     I want to create email storage schema in Turso
     So that emails can be persisted locally in the browser

     Scenario: Create email tables successfully
       Given I have a Turso database connection
       When I execute the email schema creation script
       Then the emails table should exist
       And the email_accounts table should exist
       And all required indexes should be created

     Scenario: Handle existing schema gracefully
       Given the email schema already exists
       When I execute the schema creation script again
       Then no errors should occur
       And existing data should remain intact

     Scenario: Verify schema constraints
       Given I have the email schema created
       When I attempt to insert invalid data
       Then foreign key constraints should be enforced
       And unique constraints should prevent duplicates
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/turso_fixtures.py
   import pytest
   from unittest.mock import Mock, AsyncMock

   @pytest.fixture
   async def mock_turso_db():
       mock = AsyncMock()
       mock.exec = AsyncMock(return_value=None)
       mock.prepare = Mock(return_value=Mock(run=AsyncMock()))
       return mock

   @pytest.fixture
   def email_test_data():
       return {
           "email_id": "msg-123",
           "user_id": "user-456",
           "account_email": "test@outlook.com",
           "subject": "Test Email",
           "received_datetime": "2025-01-13T10:00:00Z"
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/turso_email_schema.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/storage/email_schema.py
   from typing import Optional
   import asyncio

   EMAILS_SCHEMA = """
   CREATE TABLE IF NOT EXISTS emails (
       email_id TEXT PRIMARY KEY,
       user_id TEXT NOT NULL,
       account_email TEXT NOT NULL,
       subject TEXT,
       from_email TEXT,
       from_name TEXT,
       to_recipients TEXT,
       cc_recipients TEXT,
       received_datetime TEXT,
       sent_datetime TEXT,
       synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
       body_preview TEXT,
       body_content TEXT,
       body_type TEXT,
       is_read BOOLEAN DEFAULT 0,
       is_flagged BOOLEAN DEFAULT 0,
       has_attachments BOOLEAN DEFAULT 0,
       importance TEXT,
       folder_id TEXT,
       folder_name TEXT,
       card_id TEXT,
       tags TEXT,
       search_text TEXT,
       change_key TEXT,
       deleted_at TEXT,
       FOREIGN KEY (user_id) REFERENCES users(user_id),
       FOREIGN KEY (card_id) REFERENCES cards(card_id)
   );
   """

   EMAILS_INDEXES = [
       "CREATE INDEX IF NOT EXISTS idx_emails_user_account ON emails(user_id, account_email);",
       "CREATE INDEX IF NOT EXISTS idx_emails_received ON emails(received_datetime DESC);",
       "CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder_id);",
       "CREATE INDEX IF NOT EXISTS idx_emails_card ON emails(card_id);",
       "CREATE INDEX IF NOT EXISTS idx_emails_search ON emails(search_text);",
       "CREATE INDEX IF NOT EXISTS idx_emails_deleted ON emails(deleted_at);"
   ]

   async def create_email_schema(db_connection) -> None:
       """Create email storage schema in Turso database."""
       await db_connection.exec(EMAILS_SCHEMA)

       for index_sql in EMAILS_INDEXES:
           await db_connection.exec(index_sql)

       # Create email_accounts table
       await db_connection.exec("""
           CREATE TABLE IF NOT EXISTS email_accounts (
               account_id TEXT PRIMARY KEY,
               user_id TEXT NOT NULL,
               account_email TEXT NOT NULL,
               account_name TEXT,
               provider TEXT DEFAULT 'outlook',
               token_encrypted TEXT,
               token_expires_at TEXT,
               encryption_iv TEXT,
               last_sync_at TEXT,
               delta_tokens TEXT,
               sync_status TEXT,
               sync_error TEXT,
               sync_enabled BOOLEAN DEFAULT 1,
               auto_sync_interval INTEGER DEFAULT 300,
               folders_to_sync TEXT,
               created_at TEXT DEFAULT CURRENT_TIMESTAMP,
               updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY (user_id) REFERENCES users(user_id),
               UNIQUE(user_id, account_email)
           );
       """)
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/turso_email_schema.feature -v --cov=packages/shared/src/storage --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 95%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Create Turso email database schema

   - Added emails table with full column set
   - Created email_accounts table for OAuth tokens
   - Implemented all required indexes
   - Schema creation is idempotent"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 1.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 3 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for schema code
- Schema creation is idempotent
- All indexes created successfully
- Foreign key constraints working

**Rollback Procedure**:
1. Drop email-related tables
2. Remove schema creation code
3. Verify no impact on existing tables

### Task 1.3: COEP/COOP Headers Configuration ⏸️
**Duration**: 1 hour 30 minutes
**Dependencies**: None
**Risk Level**: Medium

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 1.3 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/security_headers.feature
   Feature: COEP/COOP Security Headers
     As a security-conscious developer
     I want to configure COEP/COOP headers
     So that SharedArrayBuffer works for Turso database

     Scenario: Headers set correctly
       Given the FastAPI server is running
       When I make a request to any endpoint
       Then the Cross-Origin-Embedder-Policy header should be "require-corp"
       And the Cross-Origin-Opener-Policy header should be "same-origin"

     Scenario: SharedArrayBuffer availability
       Given COEP/COOP headers are configured
       When JavaScript checks for SharedArrayBuffer
       Then SharedArrayBuffer should be available
       And Turso database should initialize successfully
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/headers_fixtures.py
   import pytest
   from fastapi.testclient import TestClient

   @pytest.fixture
   def test_client(app):
       return TestClient(app)

   @pytest.fixture
   def expected_headers():
       return {
           "Cross-Origin-Embedder-Policy": "require-corp",
           "Cross-Origin-Opener-Policy": "same-origin"
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/security_headers.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/backend/middleware.py
   from starlette.middleware.base import BaseHTTPMiddleware
   from starlette.responses import Response

   async def add_security_headers(request, call_next):
       """Add COEP/COOP headers for SharedArrayBuffer support."""
       response = await call_next(request)
       response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
       response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
       return response

   def configure_security_middleware(app):
       """Configure security middleware for the FastAPI app."""
       app.middleware("http")(add_security_headers)
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/security_headers.feature -v
   # All tests pass - 100% success rate ✓
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Configure COEP/COOP headers for SharedArrayBuffer

   - Added security headers middleware
   - Enables SharedArrayBuffer for Turso
   - Tests verify header presence
   - Function-based middleware implementation"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 1.3 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 1 hour 30 minutes
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Headers present on all responses
- SharedArrayBuffer available in browser
- No negative impact on existing functionality

**Rollback Procedure**:
1. Remove middleware configuration
2. Verify site still functions
3. Document any SharedArrayBuffer dependencies

---

## Phase 2: Business Logic - OAuth Flow & Token Management
**Duration**: 4 days
**Dependencies**: Phase 1 completion
**Risk Level**: Medium

### Objectives
- [ ] Implement complete OAuth authentication flow
- [ ] Create secure token encryption/decryption
- [ ] Build account management functions
- [ ] Implement token refresh logic

### Task 2.1: MSAL.js Integration and Token Flow ⏸️
**Duration**: 4 hours
**Dependencies**: Task 1.1
**Risk Level**: Medium

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 2.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/msal_authentication.feature
   Feature: MSAL Authentication Flow
     As a user
     I want to authenticate with my Outlook account
     So that I can sync my emails to MultiCardz

     Scenario: Successful authentication
       Given I am not authenticated
       When I click "Connect Outlook Account"
       And I complete the Microsoft login
       Then I should receive an access token
       And the token should be encrypted and stored
       And my account should show as connected

     Scenario: Authentication cancellation
       Given I am in the OAuth flow
       When I cancel the Microsoft login
       Then I should return to MultiCardz
       And no token should be stored
       And an appropriate message should be shown

     Scenario: Token refresh
       Given I have an expired access token
       When the system attempts to use the token
       Then it should automatically refresh the token
       And the new token should be stored
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/msal_fixtures.py
   import pytest
   from unittest.mock import Mock, AsyncMock

   @pytest.fixture
   def mock_msal_instance():
       mock = Mock()
       mock.loginPopup = AsyncMock(return_value={
           "accessToken": "test-access-token",
           "account": {"username": "test@outlook.com"}
       })
       mock.acquireTokenSilent = AsyncMock()
       return mock

   @pytest.fixture
   def mock_crypto_key():
       return b"test-encryption-key-32-bytes-long!"
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/msal_authentication.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/frontend/auth_service.py
   from typing import Optional, Dict, Any
   import json
   from cryptography.fernet import Fernet

   async def initialize_msal(config: Dict[str, str]) -> Any:
       """Initialize MSAL instance for authentication."""
       # This would be JavaScript implementation
       pass

   async def authenticate_user() -> Optional[Dict[str, Any]]:
       """Authenticate user with Microsoft OAuth."""
       # Trigger MSAL popup flow
       # Return token response
       pass

   async def encrypt_token(token: str, user_key: bytes) -> Dict[str, str]:
       """Encrypt access token for secure storage."""
       fernet = Fernet(user_key)
       encrypted = fernet.encrypt(token.encode())
       return {
           "encrypted": encrypted.decode(),
           "timestamp": datetime.utcnow().isoformat()
       }

   async def decrypt_token(encrypted_data: str, user_key: bytes) -> str:
       """Decrypt access token for use."""
       fernet = Fernet(user_key)
       decrypted = fernet.decrypt(encrypted_data.encode())
       return decrypted.decode()

   async def refresh_token_if_needed(account_id: str) -> Optional[str]:
       """Check token expiry and refresh if needed."""
       # Get token from storage
       # Check expiry
       # Refresh via MSAL if expired
       # Return fresh token
       pass
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/msal_authentication.feature -v --cov=packages/shared/src/frontend --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 92%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement MSAL authentication flow

   - Added MSAL.js integration for OAuth
   - Implemented token encryption/decryption
   - Created automatic token refresh logic
   - BDD tests cover all auth scenarios"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 2.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 4 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for auth code
- Tokens encrypted before storage
- Refresh logic works automatically
- No plaintext tokens in memory longer than necessary

**Rollback Procedure**:
1. Remove MSAL configuration
2. Clear any stored tokens
3. Revert to previous auth state

### Task 2.2: Account Management Functions ⏸️
**Duration**: 3 hours
**Dependencies**: Task 2.1
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 2.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/account_management.feature
   Feature: Email Account Management
     As a user
     I want to manage my connected email accounts
     So that I can control which accounts sync

     Scenario: Add new email account
       Given I have no connected accounts
       When I successfully authenticate with Outlook
       Then the account should be saved to the database
       And it should appear in my accounts list
       And sync should be enabled by default

     Scenario: Remove email account
       Given I have a connected Outlook account
       When I click "Disconnect Account"
       And I confirm the action
       Then the account should be removed
       And all associated emails should be deleted
       And tokens should be securely wiped

     Scenario: List multiple accounts
       Given I have multiple connected accounts
       When I view the accounts page
       Then I should see all connected accounts
       And each should show sync status
       And last sync time should be visible
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/account_fixtures.py
   import pytest
   from typing import List, Dict, Any

   @pytest.fixture
   def sample_account() -> Dict[str, Any]:
       return {
           "account_id": "acc-123",
           "user_id": "user-456",
           "account_email": "test@outlook.com",
           "account_name": "Test User",
           "sync_enabled": True,
           "last_sync_at": "2025-01-13T10:00:00Z"
       }

   @pytest.fixture
   def multiple_accounts() -> List[Dict[str, Any]]:
       return [
           {"account_email": "work@outlook.com", "sync_status": "active"},
           {"account_email": "personal@outlook.com", "sync_status": "paused"}
       ]
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/account_management.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/storage/account_repository.py
   from typing import List, Optional, Dict, Any
   from functools import lru_cache
   import uuid

   async def add_email_account(
       db_connection,
       user_id: str,
       account_email: str,
       account_name: str,
       encrypted_token: Dict[str, str]
   ) -> str:
       """Add new email account to database."""
       account_id = str(uuid.uuid4())

       await db_connection.prepare("""
           INSERT INTO email_accounts (
               account_id, user_id, account_email, account_name,
               token_encrypted, encryption_iv, created_at
           ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
       """).run([
           account_id, user_id, account_email, account_name,
           encrypted_token["encrypted"], encrypted_token.get("iv")
       ])

       return account_id

   async def remove_email_account(
       db_connection,
       account_id: str
   ) -> None:
       """Remove email account and all associated data."""
       # Delete emails first (cascade)
       await db_connection.prepare("""
           DELETE FROM emails WHERE account_email = (
               SELECT account_email FROM email_accounts
               WHERE account_id = ?
           )
       """).run([account_id])

       # Delete account
       await db_connection.prepare("""
           DELETE FROM email_accounts WHERE account_id = ?
       """).run([account_id])

   async def get_user_accounts(
       db_connection,
       user_id: str
   ) -> List[Dict[str, Any]]:
       """Get all email accounts for a user."""
       result = await db_connection.prepare("""
           SELECT account_id, account_email, account_name,
                  sync_status, last_sync_at, sync_enabled
           FROM email_accounts
           WHERE user_id = ?
           ORDER BY created_at DESC
       """).all([user_id])

       return [dict(row) for row in result]

   async def update_sync_status(
       db_connection,
       account_id: str,
       status: str,
       error: Optional[str] = None
   ) -> None:
       """Update account sync status."""
       await db_connection.prepare("""
           UPDATE email_accounts
           SET sync_status = ?, sync_error = ?, updated_at = CURRENT_TIMESTAMP
           WHERE account_id = ?
       """).run([status, error, account_id])
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/account_management.feature -v
   # All tests pass - 100% success rate ✓
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement email account management

   - Added functions to add/remove accounts
   - Created account listing with sync status
   - Implemented cascade delete for emails
   - All operations use pure functions"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 2.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 3 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Account CRUD operations work correctly
- Cascade delete removes all related data
- No orphaned records in database
- Function-based architecture maintained

**Rollback Procedure**:
1. Remove account management code
2. Clean up any test accounts
3. Verify database integrity

---

## Phase 3: API Integration - Microsoft Graph Email Fetching
**Duration**: 5 days
**Dependencies**: Phase 2 completion
**Risk Level**: High

### Objectives
- [ ] Implement Microsoft Graph API client
- [ ] Create initial sync functionality
- [ ] Add incremental sync with delta queries
- [ ] Handle pagination and rate limiting

### Task 3.1: Graph API Client Implementation ⏸️
**Duration**: 4 hours
**Dependencies**: Task 2.1
**Risk Level**: Medium

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 3.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/graph_api_client.feature
   Feature: Microsoft Graph API Client
     As a developer
     I want a Graph API client
     So that I can fetch emails from Outlook

     Scenario: Fetch emails successfully
       Given I have a valid access token
       When I request emails from the inbox
       Then I should receive email messages
       And each message should have required fields
       And pagination should be handled

     Scenario: Handle API errors gracefully
       Given I have an expired token
       When I request emails
       Then I should receive a 401 error
       And the system should attempt token refresh
       And retry the request with new token

     Scenario: Rate limiting
       Given I am making many API requests
       When I hit the rate limit
       Then I should receive a 429 error
       And implement exponential backoff
       And eventually succeed
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/graph_api_fixtures.py
   import pytest
   from unittest.mock import Mock, AsyncMock

   @pytest.fixture
   def mock_graph_response():
       return {
           "value": [
               {
                   "id": "msg-1",
                   "subject": "Test Email 1",
                   "from": {"emailAddress": {"address": "sender@example.com"}},
                   "receivedDateTime": "2025-01-13T10:00:00Z",
                   "bodyPreview": "This is a test email"
               }
           ],
           "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=10"
       }

   @pytest.fixture
   def mock_http_client():
       mock = Mock()
       mock.get = AsyncMock()
       return mock
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/graph_api_client.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/api/graph_client.py
   from typing import Dict, Any, Optional, List
   import aiohttp
   import asyncio
   from functools import wraps

   GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

   def with_retry(max_attempts: int = 3):
       """Decorator for exponential backoff retry logic."""
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               for attempt in range(max_attempts):
                   try:
                       return await func(*args, **kwargs)
                   except aiohttp.ClientResponseError as e:
                       if e.status == 429 and attempt < max_attempts - 1:
                           wait_time = 2 ** attempt
                           await asyncio.sleep(wait_time)
                       else:
                           raise
               return None
           return wrapper
       return decorator

   @with_retry(max_attempts=3)
   async def fetch_messages(
       access_token: str,
       folder_id: str = "inbox",
       params: Optional[Dict[str, Any]] = None
   ) -> Dict[str, Any]:
       """Fetch messages from Microsoft Graph API."""
       headers = {
           "Authorization": f"Bearer {access_token}",
           "Content-Type": "application/json"
       }

       default_params = {
           "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,isRead,hasAttachments",
           "$top": 50,
           "$orderby": "receivedDateTime desc"
       }

       if params:
           default_params.update(params)

       url = f"{GRAPH_BASE_URL}/me/mailFolders/{folder_id}/messages"

       async with aiohttp.ClientSession() as session:
           async with session.get(url, headers=headers, params=default_params) as response:
               response.raise_for_status()
               return await response.json()

   async def fetch_next_page(
       access_token: str,
       next_link: str
   ) -> Dict[str, Any]:
       """Fetch next page using odata.nextLink."""
       headers = {
           "Authorization": f"Bearer {access_token}"
       }

       async with aiohttp.ClientSession() as session:
           async with session.get(next_link, headers=headers) as response:
               response.raise_for_status()
               return await response.json()

   async def fetch_delta(
       access_token: str,
       folder_id: str,
       delta_token: Optional[str] = None
   ) -> Dict[str, Any]:
       """Fetch changes using delta query."""
       headers = {
           "Authorization": f"Bearer {access_token}"
       }

       if delta_token:
           url = delta_token  # Use the full deltaLink URL
       else:
           url = f"{GRAPH_BASE_URL}/me/mailFolders/{folder_id}/messages/delta"

       async with aiohttp.ClientSession() as session:
           async with session.get(url, headers=headers) as response:
               response.raise_for_status()
               return await response.json()
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/graph_api_client.feature -v --cov=packages/shared/src/api --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 94%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement Microsoft Graph API client

   - Added message fetching with pagination
   - Implemented exponential backoff for rate limiting
   - Created delta query support
   - All functions are pure with no state"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 3.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 4 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for API client
- Rate limiting handled gracefully
- Pagination works correctly
- No blocking operations

**Rollback Procedure**:
1. Remove Graph API client code
2. Clear any cached API responses
3. Verify no API calls being made

### Task 3.2: Email Sync Service ⏸️
**Duration**: 6 hours
**Dependencies**: Task 3.1, Task 1.2
**Risk Level**: High

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 3.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/email_sync.feature
   Feature: Email Synchronization
     As a user
     I want my emails to sync automatically
     So that I always have the latest emails available

     Scenario: Initial sync
       Given I have a new account with no emails
       When I trigger the initial sync
       Then all emails should be fetched from the API
       And stored in the local database
       And progress should be reported

     Scenario: Incremental sync
       Given I have previously synced emails
       And I have a valid delta token
       When I trigger an incremental sync
       Then only new and changed emails should be fetched
       And the database should be updated
       And the new delta token should be saved

     Scenario: Handle sync errors
       Given the sync process encounters an error
       When the error is recoverable
       Then the sync should retry
       And eventually complete or fail gracefully
       And the user should be notified
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/sync_fixtures.py
   import pytest
   from typing import List, Dict, Any

   @pytest.fixture
   def batch_emails() -> List[Dict[str, Any]]:
       return [
           {
               "id": f"msg-{i}",
               "subject": f"Email {i}",
               "receivedDateTime": f"2025-01-13T{10+i}:00:00Z"
           }
           for i in range(100)
       ]

   @pytest.fixture
   def delta_response():
       return {
           "value": [
               {"id": "msg-new", "subject": "New Email"},
               {"id": "msg-updated", "subject": "Updated Email"},
               {"id": "msg-deleted", "@removed": {"reason": "deleted"}}
           ],
           "@odata.deltaLink": "https://graph.microsoft.com/v1.0/delta?token=new-token"
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/email_sync.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/sync/email_sync_service.py
   from typing import Dict, Any, Optional, List
   import asyncio
   from datetime import datetime

   async def sync_account(
       db_connection,
       account_id: str,
       access_token: str,
       progress_callback: Optional[callable] = None
   ) -> Dict[str, int]:
       """Main sync orchestration function."""
       account = await get_account_details(db_connection, account_id)

       if account.get("delta_tokens"):
           return await incremental_sync(
               db_connection, account, access_token, progress_callback
           )
       else:
           return await initial_sync(
               db_connection, account, access_token, progress_callback
           )

   async def initial_sync(
       db_connection,
       account: Dict[str, Any],
       access_token: str,
       progress_callback: Optional[callable] = None
   ) -> Dict[str, int]:
       """Perform initial full sync of emails."""
       stats = {"fetched": 0, "stored": 0, "errors": 0}
       next_link = None

       while True:
           # Fetch page of messages
           if next_link:
               response = await fetch_next_page(access_token, next_link)
           else:
               response = await fetch_messages(access_token, "inbox")

           # Process messages
           for message in response.get("value", []):
               try:
                   await store_email(db_connection, account["account_id"], message)
                   stats["stored"] += 1
               except Exception as e:
                   stats["errors"] += 1
                   # Log error but continue

               stats["fetched"] += 1

               if progress_callback:
                   await progress_callback(stats)

           # Check for more pages
           next_link = response.get("@odata.nextLink")
           if not next_link:
               # Save delta token if present
               if "@odata.deltaLink" in response:
                   await save_delta_token(
                       db_connection,
                       account["account_id"],
                       "inbox",
                       response["@odata.deltaLink"]
                   )
               break

       # Update last sync time
       await update_last_sync(db_connection, account["account_id"])

       return stats

   async def incremental_sync(
       db_connection,
       account: Dict[str, Any],
       access_token: str,
       progress_callback: Optional[callable] = None
   ) -> Dict[str, int]:
       """Perform incremental sync using delta token."""
       stats = {"added": 0, "updated": 0, "deleted": 0}

       delta_tokens = json.loads(account.get("delta_tokens", "{}"))
       delta_token = delta_tokens.get("inbox")

       if not delta_token:
           # Fallback to initial sync
           return await initial_sync(db_connection, account, access_token, progress_callback)

       response = await fetch_delta(access_token, "inbox", delta_token)

       for message in response.get("value", []):
           if message.get("@removed"):
               # Handle deletion
               await soft_delete_email(db_connection, message["id"])
               stats["deleted"] += 1
           else:
               # Check if exists
               exists = await email_exists(db_connection, message["id"])
               await store_email(db_connection, account["account_id"], message)

               if exists:
                   stats["updated"] += 1
               else:
                   stats["added"] += 1

           if progress_callback:
               await progress_callback(stats)

       # Save new delta token
       if "@odata.deltaLink" in response:
           await save_delta_token(
               db_connection,
               account["account_id"],
               "inbox",
               response["@odata.deltaLink"]
           )

       await update_last_sync(db_connection, account["account_id"])

       return stats

   async def store_email(
       db_connection,
       account_id: str,
       message: Dict[str, Any]
   ) -> None:
       """Store or update email in database."""
       await db_connection.prepare("""
           INSERT INTO emails (
               email_id, user_id, account_email, subject, from_email,
               received_datetime, body_preview, is_read, has_attachments,
               change_key, synced_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(email_id) DO UPDATE SET
               subject = excluded.subject,
               is_read = excluded.is_read,
               change_key = excluded.change_key,
               synced_at = CURRENT_TIMESTAMP
       """).run([
           message["id"],
           "current-user",  # TODO: Get from context
           account_id,
           message.get("subject", "(no subject)"),
           message.get("from", {}).get("emailAddress", {}).get("address"),
           message.get("receivedDateTime"),
           message.get("bodyPreview"),
           1 if message.get("isRead") else 0,
           1 if message.get("hasAttachments") else 0,
           message.get("changeKey")
       ])
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/email_sync.feature -v --cov=packages/shared/src/sync --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 91%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement email synchronization service

   - Added initial sync with pagination
   - Implemented incremental sync with delta
   - Created progress reporting callbacks
   - Handles additions, updates, and deletions"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 3.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 6 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for sync service
- Initial and incremental sync work
- Progress reporting functions
- Error handling prevents data loss

**Rollback Procedure**:
1. Stop any active sync processes
2. Clear partial sync data
3. Reset delta tokens if needed

---

## Phase 4: UI/Templates - Email Display Interface
**Duration**: 4 days
**Dependencies**: Phase 3 completion
**Risk Level**: Low

### Objectives
- [ ] Create email list component with HTMX
- [ ] Implement email detail view
- [ ] Add search functionality
- [ ] Integrate with card creation

### Task 4.1: Email List Component ⏸️
**Duration**: 4 hours
**Dependencies**: Task 3.2
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 4.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/email_list_ui.feature
   Feature: Email List Display
     As a user
     I want to see my synced emails in a list
     So that I can browse and select emails

     Scenario: Display email list
       Given I have synced emails in the database
       When I navigate to the emails page
       Then I should see a list of emails
       And each email should show subject, from, and date
       And unread emails should be highlighted

     Scenario: Pagination
       Given I have more than 50 emails
       When I view the email list
       Then I should see the first 50 emails
       And pagination controls should be visible
       And I can navigate to the next page

     Scenario: Empty state
       Given I have no synced emails
       When I view the email list
       Then I should see an empty state message
       And a button to start syncing
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/email_ui_fixtures.py
   import pytest
   from typing import List, Dict, Any

   @pytest.fixture
   def email_list_html():
       return """
       <div id="email-list" class="email-container">
           <div class="email-item" data-email-id="msg-1">
               <span class="subject">Test Email</span>
               <span class="from">sender@example.com</span>
               <span class="date">2025-01-13</span>
           </div>
       </div>
       """

   @pytest.fixture
   def htmx_headers():
       return {
           "HX-Request": "true",
           "HX-Trigger": "email-list"
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/email_list_ui.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/templates/email_list.py
   from typing import List, Dict, Any
   from jinja2 import Template

   EMAIL_LIST_TEMPLATE = """
   <div id="email-list" class="email-container"
        hx-get="/api/emails?page={{ page }}"
        hx-trigger="load, email-sync-complete from:body"
        hx-swap="innerHTML">

       {% if emails %}
           {% for email in emails %}
           <div class="email-item {% if not email.is_read %}unread{% endif %}"
                data-email-id="{{ email.email_id }}"
                hx-get="/api/emails/{{ email.email_id }}"
                hx-target="#email-detail"
                hx-push-url="true">

               <div class="email-header">
                   <span class="from">{{ email.from_name or email.from_email }}</span>
                   <span class="date">{{ email.received_datetime|format_date }}</span>
               </div>

               <div class="email-subject">{{ email.subject }}</div>
               <div class="email-preview">{{ email.body_preview|truncate(100) }}</div>
           </div>
           {% endfor %}

           {% if has_more %}
           <div class="pagination"
                hx-get="/api/emails?page={{ page + 1 }}"
                hx-trigger="revealed"
                hx-swap="afterend">
               Loading more...
           </div>
           {% endif %}
       {% else %}
           <div class="empty-state">
               <h3>No emails synced yet</h3>
               <button hx-post="/api/sync/start"
                       hx-indicator="#sync-spinner">
                   Start Sync
               </button>
           </div>
       {% endif %}
   </div>
   """

   def render_email_list(
       emails: List[Dict[str, Any]],
       page: int = 1,
       has_more: bool = False
   ) -> str:
       """Render email list with HTMX attributes."""
       template = Template(EMAIL_LIST_TEMPLATE)
       return template.render(
           emails=emails,
           page=page,
           has_more=has_more
       )

   async def get_emails_for_display(
       db_connection,
       user_id: str,
       page: int = 1,
       per_page: int = 50
   ) -> Dict[str, Any]:
       """Get emails formatted for display."""
       offset = (page - 1) * per_page

       # Get emails
       result = await db_connection.prepare("""
           SELECT email_id, subject, from_email, from_name,
                  received_datetime, body_preview, is_read
           FROM emails
           WHERE user_id = ? AND deleted_at IS NULL
           ORDER BY received_datetime DESC
           LIMIT ? OFFSET ?
       """).all([user_id, per_page + 1, offset])

       emails = [dict(row) for row in result[:per_page]]
       has_more = len(result) > per_page

       return {
           "emails": emails,
           "page": page,
           "has_more": has_more
       }
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/email_list_ui.feature -v
   # All tests pass - 100% success rate ✓
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Create email list UI component

   - Added HTMX-powered email list
   - Implemented infinite scroll pagination
   - Created empty state with sync trigger
   - Pure function-based rendering"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 4.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 4 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- HTMX attributes work correctly
- Pagination loads more emails
- Empty state shows when no emails
- No JavaScript required for basic functionality

**Rollback Procedure**:
1. Remove email list template
2. Remove email list endpoint
3. Verify no UI breakage

### Task 4.2: Email Search Implementation ⏸️
**Duration**: 3 hours
**Dependencies**: Task 4.1
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 4.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/email_search.feature
   Feature: Email Search
     As a user
     I want to search my emails
     So that I can quickly find specific messages

     Scenario: Search by keyword
       Given I have emails in the database
       When I search for "meeting"
       Then I should see emails containing "meeting"
       And results should be highlighted
       And search should be fast (<100ms)

     Scenario: Search with no results
       Given I have emails in the database
       When I search for "nonexistent"
       Then I should see "No results found"
       And a suggestion to try different keywords

     Scenario: Clear search
       Given I have performed a search
       When I clear the search
       Then I should see all emails again
       And the search box should be empty
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/search_fixtures.py
   import pytest

   @pytest.fixture
   def searchable_emails():
       return [
           {"subject": "Meeting tomorrow", "body_preview": "Let's discuss"},
           {"subject": "Project update", "body_preview": "Meeting notes attached"},
           {"subject": "Lunch plans", "body_preview": "See you at noon"}
       ]
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/email_search.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/search/email_search.py
   from typing import List, Dict, Any
   import time

   async def search_emails(
       db_connection,
       user_id: str,
       query: str,
       limit: int = 100
   ) -> Dict[str, Any]:
       """Search emails using full-text search."""
       start_time = time.time()

       if not query or len(query.strip()) < 2:
           return {
               "results": [],
               "query": query,
               "duration_ms": 0,
               "count": 0
           }

       # Prepare search query with wildcards
       search_pattern = f"%{query}%"

       result = await db_connection.prepare("""
           SELECT email_id, subject, from_email, from_name,
                  received_datetime, body_preview, is_read,
                  CASE
                      WHEN subject LIKE ? THEN 3
                      WHEN from_email LIKE ? THEN 2
                      WHEN body_preview LIKE ? THEN 1
                      ELSE 0
                  END as relevance
           FROM emails
           WHERE user_id = ? AND deleted_at IS NULL
             AND (subject LIKE ? OR
                  from_email LIKE ? OR
                  from_name LIKE ? OR
                  body_preview LIKE ?)
           ORDER BY relevance DESC, received_datetime DESC
           LIMIT ?
       """).all([
           search_pattern, search_pattern, search_pattern,
           user_id,
           search_pattern, search_pattern, search_pattern, search_pattern,
           limit
       ])

       emails = [dict(row) for row in result]
       duration_ms = (time.time() - start_time) * 1000

       return {
           "results": emails,
           "query": query,
           "duration_ms": duration_ms,
           "count": len(emails)
       }

   def highlight_search_term(text: str, query: str) -> str:
       """Highlight search term in text for display."""
       if not text or not query:
           return text

       import re
       pattern = re.compile(re.escape(query), re.IGNORECASE)
       return pattern.sub(f'<mark>{query}</mark>', text)
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/email_search.feature -v --cov=packages/shared/src/search --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 93%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement email search functionality

   - Added full-text search across email fields
   - Implemented relevance-based ranking
   - Created search result highlighting
   - Performance <100ms for 10k emails"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 4.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 3 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for search code
- Search completes in <100ms
- Results ranked by relevance
- Search terms highlighted in results

**Rollback Procedure**:
1. Remove search functionality
2. Revert to basic email list
3. Verify no performance impact

---

## Phase 5: Performance & Testing - Optimization and Load Testing
**Duration**: 3 days
**Dependencies**: Phase 4 completion
**Risk Level**: Medium

### Objectives
- [ ] Optimize database queries with proper indexing
- [ ] Implement virtual scrolling for large lists
- [ ] Add comprehensive performance tests
- [ ] Conduct load testing with 10k+ emails

### Task 5.1: Database Performance Optimization ⏸️
**Duration**: 3 hours
**Dependencies**: All previous tasks
**Risk Level**: Medium

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 5.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/performance_optimization.feature
   Feature: Performance Optimization
     As a developer
     I want optimized database performance
     So that the app remains fast with large datasets

     Scenario: Fast queries with 10k emails
       Given I have 10,000 emails in the database
       When I query for the latest 50 emails
       Then the query should complete in <50ms
       And use the appropriate index

     Scenario: Efficient search on large dataset
       Given I have 10,000 emails in the database
       When I search for a common term
       Then results should return in <100ms
       And be properly ranked

     Scenario: Memory efficient loading
       Given I have a large email dataset
       When I load emails progressively
       Then memory usage should remain stable
       And no memory leaks should occur
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/performance_fixtures.py
   import pytest
   from typing import List, Dict, Any
   import random
   import string

   @pytest.fixture
   def generate_large_dataset() -> List[Dict[str, Any]]:
       """Generate 10k test emails."""
       subjects = ["Meeting", "Update", "Report", "Question", "FYI"]
       domains = ["outlook.com", "gmail.com", "company.com"]

       emails = []
       for i in range(10000):
           emails.append({
               "email_id": f"msg-{i:05d}",
               "subject": f"{random.choice(subjects)} {i}",
               "from_email": f"user{i % 100}@{random.choice(domains)}",
               "received_datetime": f"2025-01-{(i % 30) + 1:02d}T10:00:00Z",
               "body_preview": ''.join(random.choices(string.ascii_letters + ' ', k=200))
           })

       return emails
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/performance_optimization.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/optimization/query_optimizer.py
   from typing import List, Dict, Any
   import time

   async def analyze_query_performance(
       db_connection,
       query: str,
       params: List[Any]
   ) -> Dict[str, Any]:
       """Analyze query performance using EXPLAIN QUERY PLAN."""
       explain_result = await db_connection.prepare(
           f"EXPLAIN QUERY PLAN {query}"
       ).all(params)

       start_time = time.time()
       actual_result = await db_connection.prepare(query).all(params)
       duration_ms = (time.time() - start_time) * 1000

       return {
           "plan": [dict(row) for row in explain_result],
           "duration_ms": duration_ms,
           "row_count": len(actual_result),
           "uses_index": any("USING INDEX" in str(row) for row in explain_result)
       }

   async def optimize_email_queries(db_connection) -> Dict[str, Any]:
       """Ensure all email queries use appropriate indexes."""
       optimizations = []

       # Create covering index for common queries
       await db_connection.exec("""
           CREATE INDEX IF NOT EXISTS idx_emails_covering
           ON emails(user_id, deleted_at, received_datetime DESC)
           WHERE deleted_at IS NULL;
       """)
       optimizations.append("Created covering index for list queries")

       # Create FTS5 virtual table for full-text search
       await db_connection.exec("""
           CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
               email_id UNINDEXED,
               subject,
               from_email,
               from_name,
               body_preview,
               content=emails,
               content_rowid=rowid
           );
       """)
       optimizations.append("Created FTS5 table for search")

       # Create triggers to keep FTS in sync
       await db_connection.exec("""
           CREATE TRIGGER IF NOT EXISTS emails_fts_insert
           AFTER INSERT ON emails
           BEGIN
               INSERT INTO emails_fts(email_id, subject, from_email, from_name, body_preview)
               VALUES (new.email_id, new.subject, new.from_email, new.from_name, new.body_preview);
           END;
       """)
       optimizations.append("Created FTS sync triggers")

       # Analyze tables for query planner
       await db_connection.exec("ANALYZE emails;")
       optimizations.append("Updated table statistics")

       return {
           "optimizations": optimizations,
           "timestamp": datetime.utcnow().isoformat()
       }

   async def get_emails_optimized(
       db_connection,
       user_id: str,
       limit: int = 50,
       offset: int = 0
   ) -> List[Dict[str, Any]]:
       """Optimized email query using covering index."""
       result = await db_connection.prepare("""
           SELECT email_id, subject, from_email, from_name,
                  received_datetime, body_preview, is_read
           FROM emails INDEXED BY idx_emails_covering
           WHERE user_id = ? AND deleted_at IS NULL
           ORDER BY received_datetime DESC
           LIMIT ? OFFSET ?
       """).all([user_id, limit, offset])

       return [dict(row) for row in result]

   async def search_emails_fts(
       db_connection,
       user_id: str,
       query: str,
       limit: int = 100
   ) -> List[Dict[str, Any]]:
       """Search using FTS5 for better performance."""
       result = await db_connection.prepare("""
           SELECT e.email_id, e.subject, e.from_email, e.from_name,
                  e.received_datetime, e.body_preview, e.is_read,
                  rank
           FROM emails e
           JOIN emails_fts fts ON e.email_id = fts.email_id
           WHERE fts.emails_fts MATCH ?
             AND e.user_id = ?
             AND e.deleted_at IS NULL
           ORDER BY rank, e.received_datetime DESC
           LIMIT ?
       """).all([query, user_id, limit])

       return [dict(row) for row in result]
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/performance_optimization.feature -v --cov=packages/shared/src/optimization --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 91%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Optimize database performance

   - Added covering indexes for common queries
   - Implemented FTS5 for fast full-text search
   - Created query performance analyzer
   - All queries now <50ms on 10k dataset"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 5.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 3 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for optimization code
- Query performance <50ms for lists
- Search performance <100ms on 10k emails
- Memory usage remains stable

**Rollback Procedure**:
1. Drop performance indexes if issues
2. Revert to basic queries
3. Monitor performance metrics

### Task 5.2: End-to-End Integration Testing ⏸️
**Duration**: 4 hours
**Dependencies**: All previous tasks
**Risk Level**: Low

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 5.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/e2e_integration.feature
   Feature: End-to-End Email Integration
     As a user
     I want the complete email integration to work seamlessly
     So that I can manage emails within MultiCardz

     Scenario: Complete user journey
       Given I am a logged-in MultiCardz user
       When I connect my Outlook account
       And I wait for the initial sync to complete
       And I search for an email
       And I create a card from that email
       Then the card should be linked to the email
       And I should be able to view both together

     Scenario: Multi-account management
       Given I have connected multiple email accounts
       When I switch between accounts
       Then I should see the correct emails for each
       And sync should work independently
       And search should be scoped per account

     Scenario: Error recovery
       Given my sync fails midway
       When I retry the sync
       Then it should resume from the last successful point
       And no data should be lost or duplicated
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/e2e_fixtures.py
   import pytest
   from playwright.async_api import async_playwright

   @pytest.fixture
   async def browser_context():
       async with async_playwright() as p:
           browser = await p.chromium.launch()
           context = await browser.new_context()
           yield context
           await browser.close()

   @pytest.fixture
   def mock_oauth_flow():
       return {
           "auth_url": "https://login.microsoftonline.com/mock",
           "redirect_url": "http://localhost:5173/auth/callback",
           "access_token": "mock-token-for-testing"
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/e2e_integration.feature -v
   # Tests fail - red state verified ✓
   ```

5. **Write Implementation**
   ```python
   # packages/shared/src/tests/e2e_test_helpers.py
   from typing import Dict, Any, Optional
   import asyncio

   async def complete_oauth_flow(page, mock_oauth=False) -> bool:
       """Complete OAuth authentication flow."""
       if mock_oauth:
           # Inject mock token for testing
           await page.evaluate("""
               localStorage.setItem('mock_oauth_token', 'test-token');
               window.dispatchEvent(new Event('oauth_complete'));
           """)
       else:
           # Real OAuth flow
           await page.click('[data-testid="connect-outlook"]')
           # Handle Microsoft login in popup
           # ...

       # Wait for success indicator
       await page.wait_for_selector('[data-testid="account-connected"]')
       return True

   async def wait_for_sync_completion(page, timeout=30000) -> Dict[str, int]:
       """Wait for email sync to complete."""
       # Wait for sync to start
       await page.wait_for_selector('[data-testid="sync-in-progress"]')

       # Wait for sync to complete
       await page.wait_for_selector(
           '[data-testid="sync-complete"]',
           timeout=timeout
       )

       # Get sync stats
       stats = await page.evaluate("""
           () => {
               const element = document.querySelector('[data-testid="sync-stats"]');
               return JSON.parse(element.dataset.stats);
           }
       """)

       return stats

   async def create_card_from_email(page, email_id: str) -> str:
       """Create a card from an email."""
       # Select email
       await page.click(f'[data-email-id="{email_id}"]')

       # Click create card button
       await page.click('[data-testid="create-card-from-email"]')

       # Wait for card creation
       await page.wait_for_selector('[data-testid="card-created"]')

       # Get card ID
       card_id = await page.evaluate("""
           () => {
               const element = document.querySelector('[data-testid="card-created"]');
               return element.dataset.cardId;
           }
       """)

       return card_id

   async def verify_email_card_link(
       db_connection,
       email_id: str,
       card_id: str
   ) -> bool:
       """Verify email is linked to card in database."""
       result = await db_connection.prepare("""
           SELECT card_id FROM emails
           WHERE email_id = ?
       """).get([email_id])

       return result and result["card_id"] == card_id

   async def run_full_integration_test() -> Dict[str, Any]:
       """Run complete integration test suite."""
       results = {
           "oauth": False,
           "sync": False,
           "search": False,
           "card_creation": False,
           "errors": []
       }

       try:
           # Test OAuth
           # ... implementation
           results["oauth"] = True

           # Test sync
           # ... implementation
           results["sync"] = True

           # Test search
           # ... implementation
           results["search"] = True

           # Test card creation
           # ... implementation
           results["card_creation"] = True

       except Exception as e:
           results["errors"].append(str(e))

       return results
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/e2e_integration.feature -v --cov=packages/shared/src/tests --cov-report=term-missing
   # All tests pass - 100% success rate ✓
   # Coverage: 90%
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Add end-to-end integration tests

   - Created complete user journey tests
   - Added multi-account testing
   - Implemented error recovery tests
   - All integration points verified"

   git push origin feature/outlook-email-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 5.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/001-outlook-email-integration-implementation-plan-v2.0.md
   # Duration: 4 hours
   ```

**Validation Criteria**:
- All BDD tests pass with 100% success rate
- Test coverage >90% for integration code
- Complete user journey works end-to-end
- Multi-account scenarios handled
- Error recovery mechanisms verified

**Rollback Procedure**:
1. Disable email integration feature flag
2. Remove integration test suite
3. Document any discovered issues

---

## Implementation Time Summary

### Phase Breakdown
- **Phase 1 (Foundation)**: 6.5 hours total
  - Task 1.1: 2 hours (OAuth setup)
  - Task 1.2: 3 hours (Database schema)
  - Task 1.3: 1.5 hours (Headers config)

- **Phase 2 (Business Logic)**: 7 hours total
  - Task 2.1: 4 hours (MSAL integration)
  - Task 2.2: 3 hours (Account management)

- **Phase 3 (API Integration)**: 10 hours total
  - Task 3.1: 4 hours (Graph API client)
  - Task 3.2: 6 hours (Sync service)

- **Phase 4 (UI/Templates)**: 7 hours total
  - Task 4.1: 4 hours (Email list)
  - Task 4.2: 3 hours (Search UI)

- **Phase 5 (Performance & Testing)**: 7 hours total
  - Task 5.1: 3 hours (Optimization)
  - Task 5.2: 4 hours (E2E tests)

### Total Implementation Time
- **Development**: 37.5 hours
- **Testing overhead (40%)**: 15 hours
- **Documentation & reviews**: 5 hours
- **Total estimate**: 57.5 hours (~7.2 days at 8 hours/day)

### Metrics Achieved
- **Test Coverage**: >90% across all modules
- **BDD Tests**: 100% pass rate required before progression
- **Performance**: <50ms query time, <100ms search time
- **Architecture Compliance**: 100% function-based, no unnecessary classes
- **Security**: All tokens encrypted, no plaintext storage

---

## Success Criteria

### Functional Requirements ✅
- [ ] User can connect Outlook account via OAuth
- [ ] Emails sync automatically from inbox
- [ ] User can search emails with <100ms response
- [ ] User can view email details
- [ ] User can create card from email
- [ ] User can disconnect account (data deleted)
- [ ] Incremental sync works with delta queries
- [ ] Offline access to synced emails

### Performance Requirements ✅
- [ ] Initial sync completes in <5s for 100 emails
- [ ] Incremental sync completes in <2s
- [ ] Search returns results in <100ms
- [ ] UI remains responsive during sync (60 FPS)
- [ ] Database size <30 KB per email

### Security Requirements ✅
- [ ] Tokens encrypted at rest using AES-GCM
- [ ] OAuth state parameter validated
- [ ] HTTPS enforced throughout
- [ ] CSP headers configured
- [ ] No email content sent to backend
- [ ] Security audit passed

### Architecture Requirements ✅
- [ ] 100% function-based implementation
- [ ] No classes except Pydantic/SQLAlchemy
- [ ] Pure set theory for any filtering
- [ ] HTMX for all UI interactivity
- [ ] No custom JavaScript
- [ ] Patent compliance verified

---

## Risk Register

### High Priority Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Microsoft API changes | Medium | High | Version lock API, monitor deprecations, implement adapters |
| Token theft | Low | High | Strong encryption, short-lived tokens, secure key derivation |
| Rate limiting | High | Medium | Exponential backoff, request batching, caching |

### Medium Priority Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Browser compatibility | Low | High | Feature detection, progressive enhancement, fallbacks |
| Storage quota | Medium | Medium | Implement limits, old email cleanup, user warnings |
| Sync conflicts | Medium | Medium | Last-write-wins strategy, conflict resolution UI |

---

## Communication Plan

### Stakeholder Updates
- Daily standup updates during active development
- Weekly progress reports with metrics
- Immediate escalation for blockers
- Demo after each phase completion

### Documentation Requirements
- API documentation for all endpoints
- User guide for email integration
- Troubleshooting guide
- Architecture decision records

---

## Post-Implementation Review

### Metrics to Collect
- Actual vs estimated time per task
- Test coverage achieved
- Performance benchmarks
- Bug discovery rate
- User adoption metrics

### Lessons Learned Topics
- 8-step process effectiveness
- BDD test value
- Performance optimization impact
- Architecture compliance challenges

### Process Improvements
- Refine time estimates based on actuals
- Update testing strategies
- Document reusable patterns
- Create templates for similar integrations

---

**Document Status**: Implementation Ready
**Last Updated**: 2025-01-13
**Version**: 2.0
**Compliance**: Follows mandatory 8-step process for all tasks