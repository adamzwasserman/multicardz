# MultiCardz Outlook Email Integration Implementation Plan

## Implementation Overview

### Scope and Objectives
Implement complete Outlook email integration for MultiCardz following the architecture specification, enabling users to transform emails into semantic cards for spatial manipulation while maintaining 100% privacy through browser-only storage.

### Success Criteria
- ✅ Functional OAuth authentication with MSAL.js and PKCE
- ✅ Email synchronization from Microsoft Graph API
- ✅ Browser-based storage in Turso WASM
- ✅ Statistical tagging running client-side
- ✅ Optional LLM tagging with user consent
- ✅ Full-text search across email content
- ✅ Deep linking back to Outlook
- ✅ Performance: <100ms tag generation, <50ms search

### Timeline Estimates
**Total Estimated Effort**: 48-56 hours across 8 phases
**Recommended Duration**: 2-3 weeks with parallel work streams
**Team Size**: 1-2 developers

### Resource Requirements
- Azure AD app registration access
- Microsoft 365 developer tenant for testing
- Browser with localStorage and WASM support
- Development certificate for HTTPS localhost

## Prerequisite Analysis

### Dependencies Identification
- Existing Turso WASM browser database implementation
- Current card/tag infrastructure
- Spatial manipulation interface
- Zero-trust schema migration system

### Environment Setup Requirements
- Node.js for JavaScript bundling
- HTTPS localhost setup (required for OAuth)
- Azure portal access for app registration
- Test email accounts in Microsoft 365

### Access and Permissions Needed
- Azure AD admin consent for Mail.Read scope
- GitHub repository write access
- Development environment with modern browser

### Knowledge Prerequisites
- OAuth 2.0 and PKCE flow understanding
- Microsoft Graph API familiarity
- JavaScript async/await patterns
- SQL and FTS5 query syntax

## Phase 1: MSAL.js Client-Side Authentication

**Duration**: 6-8 hours
**Dependencies**: Azure AD app registration
**Risk Level**: Medium (OAuth complexity)

### Objectives
- [ ] Implement MSAL.js configuration and initialization
- [ ] Create login/logout flows with PKCE
- [ ] Implement token management and refresh
- [ ] Add session persistence across tabs

### Task 1.1: Create Azure AD App Registration
**Duration**: 1 hour
**Assignee**: DevOps/Developer

**Azure Portal Configuration**:
1. Navigate to Azure Active Directory → App registrations
2. Create new registration:
   - Name: "MultiCardz Email Integration"
   - Supported account types: "Multitenant and personal accounts"
   - Redirect URI: `http://localhost:3000/auth/callback` (SPA type)
3. Configure authentication:
   - Enable PKCE
   - Enable token implicit grant (ID tokens)
   - Add additional redirect URIs for production
4. API permissions:
   - Microsoft Graph → Delegated → Mail.Read
   - Microsoft Graph → Delegated → User.Read
5. Save Application (client) ID

**Implementation Process** (MANDATORY 8-step process):

1. **Capture Start Time**
   ```bash
   echo "Task 1.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/outlook_app_registration.feature
   Feature: Azure AD App Registration
     As a developer
     I want to register the application in Azure AD
     So that users can authenticate with Outlook

     Scenario: Successful app registration
       Given I have access to Azure portal
       When I create a new app registration with PKCE enabled
       Then I should receive a client ID
       And the redirect URI should be configured
       And Mail.Read permission should be granted

     Scenario: Verify PKCE configuration
       Given the app is registered
       When I check authentication settings
       Then PKCE should be enabled
       And no client secret should be required
   ```

3. **Create Test Fixtures**
   ```python
   # tests/fixtures/azure_config_fixtures.py
   @pytest.fixture
   def azure_app_config():
       return {
           "clientId": "test-client-id-guid",
           "authority": "https://login.microsoftonline.com/common",
           "redirectUri": "http://localhost:3000/auth/callback",
           "scopes": ["Mail.Read", "User.Read"]
       }
   ```

4. **Run Red Test**
   ```bash
   pytest tests/features/outlook_app_registration.feature -v
   # Expected: Tests fail (app not registered yet)
   ```

5. **Write Implementation**
   ```javascript
   // apps/static/js/config/outlook_config.js
   export const msalConfig = {
       auth: {
           clientId: process.env.AZURE_CLIENT_ID,
           authority: "https://login.microsoftonline.com/common",
           redirectUri: window.location.origin + "/auth/callback"
       },
       cache: {
           cacheLocation: "localStorage",
           storeAuthStateInCookie: false
       }
   };

   export const loginRequest = {
       scopes: ["Mail.Read", "User.Read"]
   };
   ```

6. **Run Green Test**
   ```bash
   pytest tests/features/outlook_app_registration.feature -v
   # All tests pass - configuration verified
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Configure Azure AD app registration for Outlook

   - Added MSAL configuration with PKCE support
   - Configured Mail.Read and User.Read scopes
   - Set up redirect URIs for OAuth flow
   - Added environment variable for client ID"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 1.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   # Duration calculated and logged
   ```

### Task 1.2: Implement MSAL.js Authentication Service
**Duration**: 3 hours
**Dependencies**: Task 1.1

**Implementation Process**:

1. **Capture Start Time**
   ```bash
   echo "Task 1.2 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/outlook_authentication.feature
   Feature: Outlook Authentication
     As a user
     I want to authenticate with my Outlook account
     So that I can access my emails

     Scenario: Successful login with PKCE
       Given I am not authenticated
       When I click the login button
       Then I should be redirected to Microsoft login
       And PKCE challenge should be generated
       When I enter valid credentials
       Then I should receive an access token
       And the token should be stored in localStorage

     Scenario: Token refresh
       Given I have an expired token
       When the application attempts to use it
       Then it should automatically refresh the token
       And the new token should replace the old one

     Scenario: Logout
       Given I am authenticated
       When I click logout
       Then my tokens should be cleared
       And I should be redirected to home
   ```

3. **Create Test Fixtures**
   ```javascript
   // tests/fixtures/msal_mocks.js
   export const mockMsalInstance = {
       loginPopup: jest.fn().mockResolvedValue({
           accessToken: "mock-access-token",
           account: { username: "user@example.com" }
       }),
       logout: jest.fn(),
       acquireTokenSilent: jest.fn()
   };
   ```

4. **Run Red Test**
   ```bash
   npm test tests/features/outlook_authentication.feature
   # Tests fail - authentication not implemented
   ```

5. **Write Implementation**
   ```javascript
   // apps/static/js/services/outlook_auth.js
   import { PublicClientApplication } from '@azure/msal-browser';
   import { msalConfig, loginRequest } from '../config/outlook_config.js';

   let msalInstance = null;
   let currentAccount = null;

   /**
    * Initialize MSAL instance
    * @returns {Promise<void>}
    */
   export async function initializeMsal() {
       msalInstance = new PublicClientApplication(msalConfig);
       await msalInstance.initialize();

       // Check for existing session
       const accounts = msalInstance.getAllAccounts();
       if (accounts.length > 0) {
           currentAccount = accounts[0];
       }
   }

   /**
    * Login with popup (PKCE flow)
    * @returns {Promise<AuthenticationResult>}
    */
   export async function loginWithPopup() {
       try {
           const response = await msalInstance.loginPopup(loginRequest);
           currentAccount = response.account;
           return response;
       } catch (error) {
           console.error("Login failed:", error);
           throw error;
       }
   }

   /**
    * Get access token (with automatic refresh)
    * @returns {Promise<string>}
    */
   export async function getAccessToken() {
       if (!currentAccount) {
           throw new Error("No authenticated user");
       }

       const tokenRequest = {
           scopes: loginRequest.scopes,
           account: currentAccount
       };

       try {
           const response = await msalInstance.acquireTokenSilent(tokenRequest);
           return response.accessToken;
       } catch (error) {
           // Token expired, try interactive
           const response = await msalInstance.acquireTokenPopup(tokenRequest);
           return response.accessToken;
       }
   }

   /**
    * Logout current user
    * @returns {Promise<void>}
    */
   export async function logout() {
       if (!currentAccount) return;

       await msalInstance.logoutPopup({
           account: currentAccount
       });
       currentAccount = null;
   }

   /**
    * Check if user is authenticated
    * @returns {boolean}
    */
   export function isAuthenticated() {
       return currentAccount !== null;
   }

   /**
    * Get current user info
    * @returns {Object|null}
    */
   export function getCurrentUser() {
       return currentAccount;
   }
   ```

6. **Run Green Test**
   ```bash
   npm test tests/features/outlook_authentication.feature
   # All tests pass - 100% success rate
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement MSAL.js authentication service

   - Added PKCE-based authentication flow
   - Implemented automatic token refresh
   - Created login/logout functions
   - Added session persistence in localStorage"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 1.2 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

### Task 1.3: Create Authentication UI Components
**Duration**: 2 hours
**Dependencies**: Task 1.2

[Similar 8-step process structure for UI implementation]

## Phase 2: Microsoft Graph API Client

**Duration**: 5-6 hours
**Dependencies**: Phase 1
**Risk Level**: Low

### Objectives
- [ ] Implement Graph API wrapper functions
- [ ] Handle pagination and delta sync
- [ ] Implement rate limiting and retry logic
- [ ] Create attachment metadata fetching

### Task 2.1: Create Graph API Client Service
**Duration**: 3 hours

**Implementation Process**:

1. **Capture Start Time**
   ```bash
   echo "Task 2.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/graph_api_client.feature
   Feature: Microsoft Graph API Client
     As a developer
     I want to fetch emails from Microsoft Graph
     So that users can access their Outlook emails

     Scenario: Fetch user emails
       Given I have a valid access token
       When I request emails from Graph API
       Then I should receive an array of email objects
       And each email should have required fields

     Scenario: Handle pagination
       Given there are more than 50 emails
       When I fetch emails with pagination
       Then I should receive all emails across multiple requests
       And the nextLink should be followed automatically

     Scenario: Delta sync
       Given I have a previous delta token
       When I request changes since last sync
       Then I should only receive new or modified emails
       And I should get a new delta token

     Scenario: Rate limit handling
       Given the API returns 429 Too Many Requests
       When I encounter rate limiting
       Then I should wait and retry with exponential backoff
       And eventually succeed when rate limit clears
   ```

3. **Create Test Fixtures**
   ```javascript
   // tests/fixtures/graph_api_mocks.js
   export const mockEmailResponse = {
       value: [
           {
               id: "email-1",
               subject: "Test Email",
               from: { emailAddress: { address: "sender@example.com" }},
               receivedDateTime: "2024-01-15T10:00:00Z",
               bodyPreview: "This is a test email",
               hasAttachments: false
           }
       ],
       "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=50",
       "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/messages/delta?token=abc123"
   };
   ```

4. **Run Red Test**
   ```bash
   npm test tests/features/graph_api_client.feature
   # Tests fail - Graph client not implemented
   ```

5. **Write Implementation**
   ```javascript
   // apps/static/js/services/graph_client.js
   const GRAPH_BASE_URL = 'https://graph.microsoft.com/v1.0';
   const MAX_RETRIES = 3;
   const BATCH_SIZE = 50;

   /**
    * Fetch emails from Microsoft Graph
    * @param {string} accessToken - Valid OAuth token
    * @param {string} deltaToken - Optional delta for incremental sync
    * @param {number} maxEmails - Maximum emails to fetch
    * @returns {Promise<{emails: Array, deltaToken: string}>}
    */
   export async function fetchEmails(accessToken, deltaToken = null, maxEmails = 1000) {
       const emails = [];
       let nextUrl = deltaToken
           ? `${GRAPH_BASE_URL}/me/messages/delta?${new URLSearchParams({$deltatoken: deltaToken})}`
           : `${GRAPH_BASE_URL}/me/messages?${new URLSearchParams({
               $top: BATCH_SIZE,
               $select: 'id,subject,from,receivedDateTime,bodyPreview,body,hasAttachments,isRead,importance',
               $orderby: 'receivedDateTime desc'
           })}`;

       while (nextUrl && emails.length < maxEmails) {
           const response = await fetchWithRetry(nextUrl, accessToken);
           const data = await response.json();

           emails.push(...data.value);

           // Handle pagination
           nextUrl = data['@odata.nextLink'] || null;

           // Store delta token from last page
           if (data['@odata.deltaLink']) {
               const deltaUrl = new URL(data['@odata.deltaLink']);
               const newDeltaToken = deltaUrl.searchParams.get('$deltatoken');
               return { emails, deltaToken: newDeltaToken };
           }
       }

       return { emails, deltaToken: null };
   }

   /**
    * Fetch with retry logic for rate limiting
    * @private
    */
   async function fetchWithRetry(url, accessToken, retryCount = 0) {
       const response = await fetch(url, {
           headers: {
               'Authorization': `Bearer ${accessToken}`,
               'Content-Type': 'application/json'
           }
       });

       if (response.status === 429) {
           if (retryCount >= MAX_RETRIES) {
               throw new Error('Max retries exceeded for rate limiting');
           }

           const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
           console.log(`Rate limited. Waiting ${retryAfter} seconds...`);

           await sleep(retryAfter * 1000);
           return fetchWithRetry(url, accessToken, retryCount + 1);
       }

       if (!response.ok) {
           throw new Error(`Graph API error: ${response.status} ${response.statusText}`);
       }

       return response;
   }

   /**
    * Fetch email attachments metadata
    * @param {string} accessToken - Valid OAuth token
    * @param {string} emailId - Email ID
    * @returns {Promise<Array>}
    */
   export async function fetchAttachments(accessToken, emailId) {
       const url = `${GRAPH_BASE_URL}/me/messages/${emailId}/attachments?$select=id,name,contentType,size`;
       const response = await fetchWithRetry(url, accessToken);
       const data = await response.json();
       return data.value;
   }

   /**
    * Mark email as read in Outlook
    * @param {string} accessToken - Valid OAuth token
    * @param {string} emailId - Email ID
    * @returns {Promise<void>}
    */
   export async function markAsRead(accessToken, emailId) {
       const url = `${GRAPH_BASE_URL}/me/messages/${emailId}`;
       await fetchWithRetry(url, accessToken, 0, {
           method: 'PATCH',
           body: JSON.stringify({ isRead: true })
       });
   }

   /**
    * Search emails using Graph API
    * @param {string} accessToken - Valid OAuth token
    * @param {string} query - Search query
    * @returns {Promise<Array>}
    */
   export async function searchEmails(accessToken, query) {
       const url = `${GRAPH_BASE_URL}/me/messages?${new URLSearchParams({
           $search: `"${query}"`,
           $top: 50,
           $select: 'id,subject,from,receivedDateTime,bodyPreview'
       })}`;

       const response = await fetchWithRetry(url, accessToken);
       const data = await response.json();
       return data.value;
   }

   function sleep(ms) {
       return new Promise(resolve => setTimeout(resolve, ms));
   }
   ```

6. **Run Green Test**
   ```bash
   npm test tests/features/graph_api_client.feature
   # All tests pass - 100% success rate
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement Microsoft Graph API client

   - Added email fetching with pagination
   - Implemented delta sync for incremental updates
   - Added rate limiting with exponential backoff
   - Created attachment and search functions"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 2.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

## Phase 3: Browser Database Schema

**Duration**: 4-5 hours
**Dependencies**: None (can run parallel)
**Risk Level**: Low

### Task 3.1: Create Email Tables Migration
**Duration**: 2 hours

**Implementation Process**:

1. **Capture Start Time**
   ```bash
   echo "Task 3.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/email_schema.feature
   Feature: Email Database Schema
     As a developer
     I want to create email storage tables
     So that emails can be persisted in the browser

     Scenario: Create email tables
       Given a Turso WASM database instance
       When I run the email schema migration
       Then the emails table should exist
       And the email_sync_state table should exist
       And the emails_fts virtual table should exist

     Scenario: Verify zero-trust fields
       Given the email tables exist
       When I check the schema
       Then all tables should have user_id field
       And all tables should have workspace_id field
       And all tables should have created/modified fields
   ```

3. **Create Test Fixtures**
   ```javascript
   // tests/fixtures/database_fixtures.js
   export async function createTestDatabase() {
       const db = await turso.open(':memory:');
       return db;
   }
   ```

4. **Run Red Test**
   ```bash
   npm test tests/features/email_schema.feature
   # Tests fail - schema not created
   ```

5. **Write Implementation**
   ```sql
   -- migrations/003_add_email_tables.sql
   -- ============================================================================
   -- Email Integration Schema
   -- Version: 1.0
   -- Purpose: Add email storage with full-text search
   -- ============================================================================

   -- Emails table
   CREATE TABLE IF NOT EXISTS emails (
       -- Zero-trust required fields
       user_id TEXT NOT NULL,
       workspace_id TEXT NOT NULL,
       created TEXT NOT NULL,
       modified TEXT NOT NULL,
       deleted TEXT,

       -- Email-specific fields
       email_id TEXT PRIMARY KEY,
       outlook_id TEXT NOT NULL UNIQUE,
       thread_id TEXT,
       subject TEXT,
       sender_address TEXT,
       sender_name TEXT,
       recipients_to TEXT,  -- JSON array
       recipients_cc TEXT,  -- JSON array
       recipients_bcc TEXT, -- JSON array
       received_date TEXT NOT NULL,
       body_text TEXT,
       body_html TEXT,
       body_preview TEXT,
       has_attachments INTEGER DEFAULT 0,
       attachment_count INTEGER DEFAULT 0,
       is_read INTEGER DEFAULT 1,
       importance TEXT,
       categories TEXT,     -- JSON array
       folder_id TEXT,
       conversation_id TEXT,

       -- Card link
       card_id TEXT,

       -- Indexes
       FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE SET NULL
   );

   -- Email indexes
   CREATE INDEX idx_emails_user_workspace ON emails(user_id, workspace_id);
   CREATE INDEX idx_emails_received ON emails(received_date DESC);
   CREATE INDEX idx_emails_sender ON emails(sender_address);
   CREATE INDEX idx_emails_thread ON emails(thread_id);
   CREATE INDEX idx_emails_conversation ON emails(conversation_id);
   CREATE INDEX idx_emails_unread ON emails(is_read) WHERE is_read = 0;
   CREATE INDEX idx_emails_attachments ON emails(has_attachments) WHERE has_attachments = 1;

   -- Email sync state table
   CREATE TABLE IF NOT EXISTS email_sync_state (
       -- Zero-trust required fields
       user_id TEXT NOT NULL,
       workspace_id TEXT NOT NULL,
       created TEXT NOT NULL,
       modified TEXT NOT NULL,
       deleted TEXT,

       -- Sync-specific fields
       sync_id TEXT PRIMARY KEY,
       delta_token TEXT,
       last_sync TEXT NOT NULL,
       sync_status TEXT NOT NULL, -- 'success', 'failed', 'in_progress'
       emails_synced INTEGER DEFAULT 0,
       error_message TEXT,

       -- Ensure one active sync per user/workspace
       UNIQUE(user_id, workspace_id, deleted)
   );

   -- Email attachments table
   CREATE TABLE IF NOT EXISTS email_attachments (
       -- Zero-trust required fields
       user_id TEXT NOT NULL,
       workspace_id TEXT NOT NULL,
       created TEXT NOT NULL,
       modified TEXT NOT NULL,
       deleted TEXT,

       -- Attachment-specific fields
       attachment_id TEXT PRIMARY KEY,
       email_id TEXT NOT NULL,
       outlook_attachment_id TEXT NOT NULL,
       name TEXT NOT NULL,
       content_type TEXT,
       size INTEGER,
       is_inline INTEGER DEFAULT 0,
       content_id TEXT,  -- For inline images

       FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE CASCADE
   );

   -- Attachment indexes
   CREATE INDEX idx_attachments_email ON email_attachments(email_id);
   CREATE INDEX idx_attachments_type ON email_attachments(content_type);

   -- Full-text search virtual table
   CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
       subject,
       sender_name,
       body_text,
       body_preview,
       content=emails,
       content_rowid=rowid,
       tokenize='porter unicode61'
   );

   -- Triggers to keep FTS index in sync
   CREATE TRIGGER IF NOT EXISTS emails_fts_insert
   AFTER INSERT ON emails
   BEGIN
       INSERT INTO emails_fts(rowid, subject, sender_name, body_text, body_preview)
       VALUES (new.rowid, new.subject, new.sender_name, new.body_text, new.body_preview);
   END;

   CREATE TRIGGER IF NOT EXISTS emails_fts_update
   AFTER UPDATE ON emails
   BEGIN
       UPDATE emails_fts
       SET subject = new.subject,
           sender_name = new.sender_name,
           body_text = new.body_text,
           body_preview = new.body_preview
       WHERE rowid = new.rowid;
   END;

   CREATE TRIGGER IF NOT EXISTS emails_fts_delete
   AFTER DELETE ON emails
   BEGIN
       DELETE FROM emails_fts WHERE rowid = old.rowid;
   END;

   -- Email tags junction table
   CREATE TABLE IF NOT EXISTS email_tags (
       -- Zero-trust required fields
       user_id TEXT NOT NULL,
       workspace_id TEXT NOT NULL,
       created TEXT NOT NULL,
       modified TEXT NOT NULL,
       deleted TEXT,

       -- Junction fields
       email_id TEXT NOT NULL,
       tag_id TEXT NOT NULL,
       tag_source TEXT NOT NULL, -- 'statistical', 'llm', 'user'
       confidence REAL DEFAULT 1.0,

       PRIMARY KEY (email_id, tag_id),
       FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE CASCADE,
       FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
   );

   -- Email tags indexes
   CREATE INDEX idx_email_tags_email ON email_tags(email_id);
   CREATE INDEX idx_email_tags_tag ON email_tags(tag_id);
   CREATE INDEX idx_email_tags_source ON email_tags(tag_source);
   ```

6. **Run Green Test**
   ```bash
   npm test tests/features/email_schema.feature
   # All tests pass - schema created successfully
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Add email database schema with FTS5

   - Created emails table with zero-trust fields
   - Added email_sync_state for delta tracking
   - Implemented FTS5 full-text search
   - Added attachment and tag junction tables"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 3.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

## Phase 4: Statistical Tagging (Browser)

**Duration**: 6-8 hours
**Dependencies**: None (can run parallel)
**Risk Level**: Medium (algorithm complexity)

### Task 4.1: Implement TF-IDF Tagging
**Duration**: 4 hours

**Implementation Process**:

1. **Capture Start Time**
   ```bash
   echo "Task 4.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/statistical_tagging.feature
   Feature: Statistical Email Tagging
     As a system
     I want to generate tags from email content
     So that emails can be organized spatially

     Scenario: Extract keywords using TF-IDF
       Given an email with subject and body
       When I run TF-IDF analysis
       Then I should get top keywords as tags
       And common words should be filtered out

     Scenario: Named entity recognition
       Given an email containing names and organizations
       When I run NER extraction
       Then I should identify person names
       And I should identify company names
       And I should identify locations

     Scenario: Date and time extraction
       Given an email mentioning dates and times
       When I extract temporal entities
       Then I should create date-based tags
       And I should create deadline tags
   ```

3. **Create Test Fixtures**
   ```javascript
   // tests/fixtures/email_content_fixtures.js
   export const sampleEmail = {
       subject: "Meeting with John from Acme Corp next Tuesday",
       body: "Hi, Let's discuss the Q3 revenue projections. The deadline is March 15th. Best, Sarah"
   };

   export const expectedTags = new Set([
       "#person:john",
       "#company:acme-corp",
       "#topic:meeting",
       "#date:tuesday",
       "#topic:revenue",
       "#quarter:q3",
       "#deadline:march-15",
       "#person:sarah"
   ]);
   ```

4. **Run Red Test**
   ```bash
   npm test tests/features/statistical_tagging.feature
   # Tests fail - tagging not implemented
   ```

5. **Write Implementation**
   ```javascript
   // apps/static/js/services/statistical_tagger.js

   // Common words to exclude (stopwords)
   const STOPWORDS = new Set([
       'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
       'in', 'with', 'to', 'for', 'of', 'as', 'from', 'by', 'that', 'this',
       'it', 'be', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
       'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
   ]);

   // Named entity patterns
   const PATTERNS = {
       email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
       url: /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/g,
       date: /\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b/gi,
       time: /\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?:\s?[ap]m)?\b/gi,
       money: /\$[\d,]+\.?\d*/g,
       phone: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
       quarter: /\bQ[1-4]\b/gi,
       person: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g,
       company: /\b(?:Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co)\b/gi
   };

   /**
    * Generate tags from email content using statistical analysis
    * @param {Object} email - Email object with subject, body, metadata
    * @returns {Set<string>} - Generated tag set
    */
   export function generateStatisticalTags(email) {
       const tags = new Set();
       const text = `${email.subject} ${email.body}`.toLowerCase();

       // Extract keywords using TF-IDF
       const keywords = extractKeywords(text);
       keywords.forEach(keyword => {
           tags.add(`#topic:${keyword}`);
       });

       // Extract named entities
       const entities = extractNamedEntities(email);
       entities.forEach(entity => {
           tags.add(entity);
       });

       // Extract metadata tags
       if (email.from) {
           const sender = email.from.emailAddress.address;
           const domain = sender.split('@')[1];
           tags.add(`#from:${sender}`);
           tags.add(`#domain:${domain}`);
       }

       if (email.hasAttachments) {
           tags.add('#has-attachments');
       }

       if (!email.isRead) {
           tags.add('#unread');
       }

       if (email.importance === 'high') {
           tags.add('#important');
       }

       // Add date-based tags
       const receivedDate = new Date(email.receivedDateTime);
       tags.add(`#year:${receivedDate.getFullYear()}`);
       tags.add(`#month:${receivedDate.toLocaleString('default', { month: 'long' }).toLowerCase()}`);
       tags.add(`#weekday:${receivedDate.toLocaleString('default', { weekday: 'long' }).toLowerCase()}`);

       return tags;
   }

   /**
    * Extract keywords using simplified TF-IDF
    * @private
    */
   function extractKeywords(text) {
       // Tokenize and clean
       const words = text
           .replace(/[^\w\s]/g, ' ')
           .split(/\s+/)
           .filter(word => word.length > 3 && !STOPWORDS.has(word));

       // Calculate term frequency
       const termFreq = {};
       words.forEach(word => {
           termFreq[word] = (termFreq[word] || 0) + 1;
       });

       // Simple IDF (would need corpus in production)
       // For now, prioritize less common words
       const scores = Object.entries(termFreq)
           .map(([word, freq]) => ({
               word,
               score: freq * (1 / Math.log(freq + 2))
           }))
           .sort((a, b) => b.score - a.score)
           .slice(0, 10);

       return scores.map(item => item.word);
   }

   /**
    * Extract named entities from email
    * @private
    */
   function extractNamedEntities(email) {
       const entities = new Set();
       const fullText = `${email.subject} ${email.body}`;

       // Extract emails
       const emails = fullText.match(PATTERNS.email) || [];
       emails.forEach(email => {
           entities.add(`#email:${email.toLowerCase()}`);
       });

       // Extract dates
       const dates = fullText.match(PATTERNS.date) || [];
       dates.forEach(date => {
           entities.add(`#date:${date.toLowerCase().replace(/\s+/g, '-')}`);
       });

       // Extract quarters
       const quarters = fullText.match(PATTERNS.quarter) || [];
       quarters.forEach(quarter => {
           entities.add(`#quarter:${quarter.toUpperCase()}`);
       });

       // Extract monetary amounts
       const amounts = fullText.match(PATTERNS.money) || [];
       amounts.forEach(amount => {
           entities.add(`#amount:${amount}`);
       });

       // Extract potential person names
       const names = fullText.match(PATTERNS.person) || [];
       names.forEach(name => {
           if (!STOPWORDS.has(name.toLowerCase())) {
               entities.add(`#person:${name.toLowerCase().replace(/\s+/g, '-')}`);
           }
       });

       // Look for company indicators
       if (PATTERNS.company.test(fullText)) {
           // Extract company name (simplified)
           const words = fullText.split(/\s+/);
           words.forEach((word, i) => {
               if (PATTERNS.company.test(word)) {
                   const companyName = words.slice(Math.max(0, i-2), i+1).join('-').toLowerCase();
                   entities.add(`#company:${companyName}`);
               }
           });
       }

       return entities;
   }

   /**
    * Calculate email priority/importance
    * @param {Object} email - Email object
    * @returns {number} - Priority score 0-100
    */
   export function calculatePriority(email) {
       let score = 50; // Base score

       // Importance flag
       if (email.importance === 'high') score += 20;
       if (email.importance === 'low') score -= 10;

       // Sender importance (would need whitelist in production)
       if (email.from?.emailAddress?.address?.includes('ceo')) score += 15;
       if (email.from?.emailAddress?.address?.includes('manager')) score += 10;

       // Keywords indicating urgency
       const urgentKeywords = ['urgent', 'asap', 'immediately', 'deadline', 'critical'];
       const text = `${email.subject} ${email.bodyPreview}`.toLowerCase();
       urgentKeywords.forEach(keyword => {
           if (text.includes(keyword)) score += 10;
       });

       // Recency
       const age = Date.now() - new Date(email.receivedDateTime).getTime();
       const daysOld = age / (1000 * 60 * 60 * 24);
       if (daysOld < 1) score += 10;
       if (daysOld > 7) score -= 10;

       return Math.max(0, Math.min(100, score));
   }
   ```

6. **Run Green Test**
   ```bash
   npm test tests/features/statistical_tagging.feature
   # All tests pass - tagging implemented
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement statistical email tagging

   - Added TF-IDF keyword extraction
   - Implemented named entity recognition
   - Created date and metadata tag generation
   - Added email priority calculation"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 4.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

## Phase 5: Email Storage Service

**Duration**: 5-6 hours
**Dependencies**: Phase 3
**Risk Level**: Low

### Task 5.1: Implement Email Storage Operations
**Duration**: 3 hours

**Implementation Process**:

1. **Capture Start Time**
   ```bash
   echo "Task 5.1 Start: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

2. **Create BDD Feature File**
   ```gherkin
   # tests/features/email_storage.feature
   Feature: Email Storage in Browser Database
     As a system
     I want to store emails in Turso WASM
     So that emails persist locally

     Scenario: Store email with zero-trust fields
       Given a valid email object
       When I store it in the database
       Then it should have user_id and workspace_id
       And it should have created and modified timestamps
       And it should be searchable via FTS5

     Scenario: Update existing email
       Given an email exists in the database
       When I receive an updated version
       Then the existing record should be updated
       And the modified timestamp should change

     Scenario: Search emails with FTS5
       Given emails are stored with full text
       When I search for a keyword
       Then matching emails should be returned
       And results should be ranked by relevance
   ```

3. **Create Test Fixtures**
   ```javascript
   // tests/fixtures/storage_fixtures.js
   export const mockStorageContext = {
       userId: "test-user-123",
       workspaceId: "test-workspace-456",
       db: null // Will be initialized in tests
   };
   ```

4. **Run Red Test**
   ```bash
   npm test tests/features/email_storage.feature
   # Tests fail - storage not implemented
   ```

5. **Write Implementation**
   ```javascript
   // apps/static/js/services/email_storage.js
   import { getCurrentUser, getCurrentWorkspace } from './workspace_context.js';

   /**
    * Store email in Turso WASM database
    * @param {Object} db - Turso database instance
    * @param {Object} email - Email to store
    * @param {Set<string>} tags - Generated tags
    * @returns {Promise<string>} - Created email ID
    */
   export async function storeEmail(db, email, tags) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();
       const now = new Date().toISOString();
       const emailId = `email_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

       try {
           await db.execute('BEGIN TRANSACTION');

           // Insert email
           await db.execute({
               sql: `INSERT INTO emails (
                   user_id, workspace_id, created, modified,
                   email_id, outlook_id, thread_id, subject,
                   sender_address, sender_name, recipients_to,
                   received_date, body_text, body_html, body_preview,
                   has_attachments, attachment_count, is_read,
                   importance, conversation_id
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
               args: [
                   userId, workspaceId, now, now,
                   emailId, email.id, email.conversationId, email.subject,
                   email.from?.emailAddress?.address || '',
                   email.from?.emailAddress?.name || '',
                   JSON.stringify(email.toRecipients || []),
                   email.receivedDateTime,
                   email.body?.content || email.bodyPreview || '',
                   email.body?.contentType === 'html' ? email.body.content : '',
                   email.bodyPreview || '',
                   email.hasAttachments ? 1 : 0,
                   email.attachments?.length || 0,
                   email.isRead ? 1 : 0,
                   email.importance || 'normal',
                   email.conversationId
               ]
           });

           // Create card for email
           const cardId = await createEmailCard(db, emailId, email, tags);

           // Update email with card link
           await db.execute({
               sql: 'UPDATE emails SET card_id = ? WHERE email_id = ?',
               args: [cardId, emailId]
           });

           // Store tags
           for (const tag of tags) {
               await storeEmailTag(db, emailId, tag, 'statistical');
           }

           // Store attachments if any
           if (email.attachments) {
               for (const attachment of email.attachments) {
                   await storeAttachment(db, emailId, attachment);
               }
           }

           await db.execute('COMMIT');
           return emailId;

       } catch (error) {
           await db.execute('ROLLBACK');
           throw error;
       }
   }

   /**
    * Create card from email
    * @private
    */
   async function createEmailCard(db, emailId, email, tags) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();
       const now = new Date().toISOString();
       const cardId = `card_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

       const cardName = email.subject || 'Untitled Email';
       const cardDescription = email.bodyPreview || '';
       const tagArray = Array.from(tags);

       await db.execute({
           sql: `INSERT INTO cards (
               user_id, workspace_id, created, modified,
               card_id, name, description, tags
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
           args: [
               userId, workspaceId, now, now,
               cardId, cardName, cardDescription,
               tagArray.join(',')
           ]
       });

       return cardId;
   }

   /**
    * Store email tag association
    * @private
    */
   async function storeEmailTag(db, emailId, tag, source) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();
       const now = new Date().toISOString();

       // First ensure tag exists
       const tagId = await ensureTag(db, tag);

       // Create association
       await db.execute({
           sql: `INSERT OR IGNORE INTO email_tags (
               user_id, workspace_id, created, modified,
               email_id, tag_id, tag_source, confidence
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
           args: [
               userId, workspaceId, now, now,
               emailId, tagId, source, 1.0
           ]
       });
   }

   /**
    * Ensure tag exists in database
    * @private
    */
   async function ensureTag(db, tagName) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();
       const now = new Date().toISOString();
       const tagId = `tag_${tagName.replace('#', '')}_${workspaceId}`;

       await db.execute({
           sql: `INSERT OR IGNORE INTO tags (
               user_id, workspace_id, created, modified,
               tag_id, tag, card_count
           ) VALUES (?, ?, ?, ?, ?, ?, ?)`,
           args: [
               userId, workspaceId, now, now,
               tagId, tagName, 0
           ]
       });

       return tagId;
   }

   /**
    * Search emails using FTS5
    * @param {Object} db - Turso database instance
    * @param {string} query - Search query
    * @param {number} limit - Result limit
    * @returns {Promise<Array>} - Matching emails
    */
   export async function searchEmails(db, query, limit = 50) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();

       const result = await db.execute({
           sql: `
               SELECT e.*,
                      snippet(emails_fts, 0, '<mark>', '</mark>', '...', 32) as snippet
               FROM emails e
               JOIN emails_fts ON e.rowid = emails_fts.rowid
               WHERE emails_fts MATCH ?
                 AND e.user_id = ?
                 AND e.workspace_id = ?
                 AND e.deleted IS NULL
               ORDER BY rank
               LIMIT ?
           `,
           args: [query, userId, workspaceId, limit]
       });

       return result.rows;
   }

   /**
    * Get emails by tag
    * @param {Object} db - Turso database instance
    * @param {string} tag - Tag to filter by
    * @returns {Promise<Array>} - Emails with tag
    */
   export async function getEmailsByTag(db, tag) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();

       const result = await db.execute({
           sql: `
               SELECT DISTINCT e.*
               FROM emails e
               JOIN email_tags et ON e.email_id = et.email_id
               JOIN tags t ON et.tag_id = t.tag_id
               WHERE t.tag = ?
                 AND e.user_id = ?
                 AND e.workspace_id = ?
                 AND e.deleted IS NULL
               ORDER BY e.received_date DESC
           `,
           args: [tag, userId, workspaceId]
       });

       return result.rows;
   }

   /**
    * Update sync state
    * @param {Object} db - Turso database instance
    * @param {string} deltaToken - New delta token
    * @param {number} emailCount - Number of emails synced
    * @param {string} status - Sync status
    * @returns {Promise<void>}
    */
   export async function updateSyncState(db, deltaToken, emailCount, status) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();
       const now = new Date().toISOString();
       const syncId = `sync_${userId}_${workspaceId}`;

       await db.execute({
           sql: `
               INSERT INTO email_sync_state (
                   user_id, workspace_id, created, modified,
                   sync_id, delta_token, last_sync, sync_status, emails_synced
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(sync_id) DO UPDATE SET
                   modified = ?,
                   delta_token = ?,
                   last_sync = ?,
                   sync_status = ?,
                   emails_synced = emails_synced + ?
           `,
           args: [
               userId, workspaceId, now, now,
               syncId, deltaToken, now, status, emailCount,
               now, deltaToken, now, status, emailCount
           ]
       });
   }

   /**
    * Get last sync state
    * @param {Object} db - Turso database instance
    * @returns {Promise<Object|null>} - Sync state or null
    */
   export async function getLastSyncState(db) {
       const userId = getCurrentUser();
       const workspaceId = getCurrentWorkspace();

       const result = await db.execute({
           sql: `
               SELECT * FROM email_sync_state
               WHERE user_id = ?
                 AND workspace_id = ?
                 AND deleted IS NULL
               ORDER BY modified DESC
               LIMIT 1
           `,
           args: [userId, workspaceId]
       });

       return result.rows[0] || null;
   }
   ```

6. **Run Green Test**
   ```bash
   npm test tests/features/email_storage.feature
   # All tests pass - storage implemented
   ```

7. **Commit and Push**
   ```bash
   git add -A
   git commit -m "feat: Implement email storage service

   - Added email storage with zero-trust fields
   - Created email-to-card transformation
   - Implemented FTS5 search functionality
   - Added sync state management"

   git push origin feature/outlook-integration
   ```

8. **Capture End Time**
   ```bash
   echo "Task 5.1 End: $(date '+%Y-%m-%d %H:%M:%S')" >> docs/implementation/outlook-integration-progress.md
   ```

## Phase 6: Email Sync Orchestrator

**Duration**: 6-7 hours
**Dependencies**: Phases 1, 2, 4, 5
**Risk Level**: Medium

### Task 6.1: Implement Sync Workflow
**Duration**: 4 hours

[Complete 8-step implementation process following the same pattern]

## Phase 7: Optional LLM Tagging

**Duration**: 4-5 hours
**Dependencies**: Phase 4
**Risk Level**: Low

### Task 7.1: Create LLM Tagging Endpoint
**Duration**: 3 hours

[Complete 8-step implementation process for server endpoint]

## Phase 8: UI Components

**Duration**: 8-10 hours
**Dependencies**: Phases 1-6
**Risk Level**: Low

### Task 8.1: Create Email List Component
**Duration**: 3 hours

### Task 8.2: Create Email Search Interface
**Duration**: 2 hours

### Task 8.3: Create Card Creation UI
**Duration**: 3 hours

## Module Specifications

### outlook_auth.js
```javascript
// File: apps/static/js/services/outlook_auth.js
// Size: ~400 lines

export async function initializeMsal();
export async function loginWithPopup();
export async function getAccessToken();
export async function logout();
export function isAuthenticated();
export function getCurrentUser();
```

### graph_client.js
```javascript
// File: apps/static/js/services/graph_client.js
// Size: ~500 lines

export async function fetchEmails(accessToken, deltaToken, maxEmails);
export async function fetchAttachments(accessToken, emailId);
export async function markAsRead(accessToken, emailId);
export async function searchEmails(accessToken, query);
```

### statistical_tagger.js
```javascript
// File: apps/static/js/services/statistical_tagger.js
// Size: ~500 lines

export function generateStatisticalTags(email);
export function calculatePriority(email);
```

### email_storage.js
```javascript
// File: apps/static/js/services/email_storage.js
// Size: ~450 lines

export async function storeEmail(db, email, tags);
export async function searchEmails(db, query, limit);
export async function getEmailsByTag(db, tag);
export async function updateSyncState(db, deltaToken, emailCount, status);
export async function getLastSyncState(db);
```

### email_sync.js
```javascript
// File: apps/static/js/services/email_sync.js
// Size: ~400 lines

export async function syncEmails(options);
export async function performDeltaSync();
export async function performFullSync();
export function getSyncStatus();
export function cancelSync();
```

## Server Endpoints

### POST /api/ai/llm-tag

**Request Format**:
```json
{
    "email_content": {
        "subject": "string",
        "body": "string (first 1000 chars)",
        "sender": "string"
    },
    "existing_tags": ["array", "of", "tags"],
    "workspace_id": "string"
}
```

**Response Format**:
```json
{
    "tags": ["array", "of", "generated", "tags"],
    "confidence": 0.95,
    "model": "gpt-4o-mini",
    "cached": false
}
```

**Error Handling**:
- 400: Invalid request format
- 401: Authentication required
- 429: Rate limit exceeded
- 500: LLM service error

**Rate Limiting**:
- 10 requests per minute per user
- Exponential backoff on 429

## Azure App Registration Guide

### Step-by-Step Instructions

1. **Access Azure Portal**
   - Navigate to https://portal.azure.com
   - Sign in with admin account

2. **Create App Registration**
   - Azure Active Directory → App registrations → New registration
   - Name: "MultiCardz Email Integration"
   - Account types: Multitenant + personal
   - Redirect URI: http://localhost:3000/auth/callback (SPA)

3. **Configure Authentication**
   - Authentication → Add platform → Single-page application
   - Enable: Access tokens, ID tokens
   - Enable: PKCE
   - Add production URLs when ready

4. **Set API Permissions**
   - API permissions → Add permission
   - Microsoft Graph → Delegated permissions
   - Select: Mail.Read, User.Read
   - Grant admin consent (if required)

5. **Note Configuration**
   - Copy Application (client) ID
   - Copy Directory (tenant) ID
   - No secret needed (public client)

## Testing Strategy

### BDD Test Scenarios

**Authentication Tests**:
- Successful PKCE login flow
- Token refresh on expiry
- Logout and session cleanup
- Multi-tab session sync

**Email Sync Tests**:
- Initial full sync
- Delta sync for updates
- Rate limit handling
- Network failure recovery
- Large email volume handling

**Tagging Tests**:
- Keyword extraction accuracy
- Named entity recognition
- Priority calculation
- Tag deduplication

**Storage Tests**:
- Zero-trust field validation
- FTS5 search accuracy
- Transaction rollback on error
- Quota management

**UI Tests**:
- Email list rendering
- Search responsiveness
- Card creation from email
- Deep link navigation

### Manual Testing Checklist
- [ ] OAuth login flow works
- [ ] Emails appear in list
- [ ] Search returns results
- [ ] Tags are generated
- [ ] Cards are created
- [ ] Deep links open Outlook
- [ ] Sync status updates
- [ ] Error messages display
- [ ] Logout clears data

## Risk Assessment

### Potential Issues and Mitigations

**Phase 1 Risks**:
- **Issue**: PKCE configuration errors
- **Mitigation**: Detailed Azure setup guide
- **Fallback**: Use implicit flow temporarily

**Phase 2 Risks**:
- **Issue**: Graph API rate limiting
- **Mitigation**: Implement backoff and queuing
- **Fallback**: Reduce batch sizes

**Phase 3 Risks**:
- **Issue**: Browser storage quota
- **Mitigation**: Implement pruning strategy
- **Fallback**: Limit email history

**Phase 4 Risks**:
- **Issue**: Poor tagging accuracy
- **Mitigation**: Iterate on algorithms
- **Fallback**: Rely on LLM tagging

**Phase 5 Risks**:
- **Issue**: Database performance
- **Mitigation**: Add indices, optimize queries
- **Fallback**: Paginate results

**Phase 6 Risks**:
- **Issue**: Sync conflicts
- **Mitigation**: Implement conflict resolution
- **Fallback**: Manual sync trigger

## Configuration Requirements

### Environment Variables
```bash
# .env.example additions
AZURE_CLIENT_ID=your-client-id-here
AZURE_TENANT_ID=common
AZURE_REDIRECT_URI=http://localhost:3000/auth/callback

# Optional LLM configuration
ENABLE_LLM_TAGGING=false
LLM_API_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
```

### Azure Portal Settings
- App registration completed
- API permissions granted
- Redirect URIs configured
- PKCE enabled
- No secrets required

## Implementation Time Summary

### Phase Breakdown
- Phase 1 (Authentication): 6-8 hours
- Phase 2 (Graph API): 5-6 hours
- Phase 3 (Database): 4-5 hours
- Phase 4 (Tagging): 6-8 hours
- Phase 5 (Storage): 5-6 hours
- Phase 6 (Sync): 6-7 hours
- Phase 7 (LLM): 4-5 hours
- Phase 8 (UI): 8-10 hours

**Total Estimate**: 44-55 hours

### Parallel Execution Opportunities
- Phases 3 and 4 can run in parallel (no dependencies)
- UI components can start after Phase 5
- LLM tagging can be deferred post-launch

### Critical Path
1. Phase 1 (Authentication) - blocks all Graph API work
2. Phase 2 (Graph API) - blocks sync implementation
3. Phase 5 (Storage) - blocks UI components
4. Phase 6 (Sync) - blocks full integration

## Success Criteria

### Functional Requirements
- ✅ Users can authenticate with Outlook
- ✅ Emails sync to browser database
- ✅ Tags are generated automatically
- ✅ Full-text search works
- ✅ Cards are created from emails
- ✅ Deep links open source emails
- ✅ Privacy maintained (no server storage)

### Performance Requirements
- ✅ Tag generation <100ms per email
- ✅ Search response <50ms
- ✅ Sync throughput >100 emails/sec
- ✅ Memory usage <150MB for 10K emails

### Quality Requirements
- ✅ Test coverage >90%
- ✅ All BDD scenarios pass
- ✅ No security vulnerabilities
- ✅ Architecture compliance verified

### User Experience Requirements
- ✅ Intuitive authentication flow
- ✅ Clear sync progress indicators
- ✅ Responsive search interface
- ✅ Seamless card creation
- ✅ Helpful error messages

## Post-Implementation Review

### Metrics to Track
- Authentication success rate
- Average sync duration
- Tag generation accuracy
- Search query performance
- User adoption rate
- Error frequency

### Lessons Learned (to be filled)
- Technical challenges encountered
- Process improvements identified
- Architecture decisions validated
- Performance optimizations found

### Future Enhancements
- Shared mailbox support
- Calendar integration
- Contact synchronization
- Teams message import
- Gmail integration
- Attachment preview
- Email composition