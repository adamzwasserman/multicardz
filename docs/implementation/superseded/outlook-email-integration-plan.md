# Outlook Email Integration Plan

---
**IMPLEMENTATION STATUS**: PARTIALLY IMPLEMENTED
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Implementation in progress. See implementation/ directory for details.
---


## Collecting Emails to Turso In-Browser Database

**STATUS**: SUPERSEDED
**SUPERSEDED BY**: docs/implementation/028-2025-10-15-multicardz-Outlook-Email-Integration-Implementation-v1.md
**SUPERSEDED DATE**: 2025-10-15
**REASON**: Planning document replaced by formal versioned implementation plan with architecture reference

**Date**: 2025-10-09
**Status**: Planning Phase (Superseded)
**Inspired by**: Superhuman's email client architecture

---

## Executive Summary

This plan outlines the implementation of Outlook email collection and storage in a browser-based Turso database for the multicardz application. The architecture follows Superhuman's approach: OAuth-based authentication, client-side storage, and no server-side email copies.

---

## 1. Research Findings

### 1.1 Superhuman's Architecture

**Key Principles:**
- **OAuth Authentication**: Never stores passwords; uses OAuth tokens with limited scope
- **Client-Side Storage**: Emails stored on user's machine, not on Superhuman's servers
- **Encryption**: Data encrypted at rest and in transit, with sensitive data additionally encrypted at application level
- **Provider Support**: Works with Gmail (via IMAP) and Outlook (via Microsoft Graph API)
- **No IMAP Direct**: Superhuman doesn't support raw IMAP accounts

**Security Model:**
- OAuth provides limited access without seeing passwords
- 2FA authentication flows through OAuth
- All infrastructure runs on Google Cloud Platform

### 1.2 Microsoft Graph API (Current 2024 Standard)

**Important**: Outlook REST API v2.0 was deprecated in November 2020 and decommissioned in March 2024. **Must use Microsoft Graph API**.

**Authentication:**
- OAuth 2.0 Authorization Code Flow with PKCE (Proof Key for Code Exchange)
- Required library: `@azure/msal-browser` (v2.0+, NOT the old `msal` package)
- Required scopes:
  - `User.Read` - Basic user profile
  - `Mail.Read` - Read user's mailbox
  - `Mail.ReadBasic` - Minimum privileged option
  - `Mail.ReadWrite` - If modifying emails needed

**API Endpoints:**
- Primary: `https://graph.microsoft.com/v1.0/me/messages`
- Folder-specific: `https://graph.microsoft.com/v1.0/me/mailFolders/{id}/messages`
- User-specific: `https://graph.microsoft.com/v1.0/users/{id}/messages`

**Query Parameters:**
- `$select` - Choose specific fields (reduce payload)
- `$top` - Page size (1-1000, default 10)
- `$filter` - Filter by criteria (e.g., `receivedDateTime ge {date}`)
- `$orderby` - Sort results (limited $filter + $orderby combinations)

**Pagination:**
- Response includes `@odata.nextLink` URL for next page
- **Critical**: Do NOT try to extract `$skip` value manually, use the full nextLink URL
- Default page size: 10 messages
- Maximum page size: 1000 messages (but may cause gateway timeout)

**Rate Limits:**
- Microsoft Graph has throttling limits
- Must implement exponential backoff for 429 responses
- Recommended: Batch requests when possible

### 1.3 Delta Query for Incremental Sync

**Purpose**: Efficiently sync only changes (additions, deletions, updates) without fetching entire mailbox.

**How It Works:**
1. **Initial Sync**: `GET /me/mailFolders/{folderId}/messages/delta`
   - Returns messages + `@odata.deltaLink` with `deltaToken`
2. **Subsequent Syncs**: Use the deltaLink URL from previous sync
   - Returns only changes since last sync
   - New deltaLink for next sync

**Token Management:**
- State tokens: `skipToken` (pagination) and `deltaToken` (change tracking)
- Token validity: Dependent on internal cache size (not fixed duration)
- Must store deltaToken per folder for incremental sync

**Query Support:**
- Supports: `$select`, `$top`, `$expand`
- Limited `$filter`: Only `receivedDateTime ge/gt {value}`
- Limited `$orderby` support

**Important Limitation:**
- "Sync from now" (`$deltaToken=latest`) is **NOT supported** for Outlook Mail
- Must do initial full sync, cannot skip to current state

### 1.4 MSAL.js Implementation Details

**Package**: `@azure/msal-browser` (current standard for SPAs)

**Key Features:**
- Implements OAuth 2.0 Authorization Code Flow with PKCE
- OpenID Connect compliant
- Handles token acquisition, caching, renewal
- Silent token refresh support
- Multiple authentication flows

**Security Benefits of PKCE:**
- Protection against authorization code interception attacks
- No tokens in browser URL or history
- Refresh token support for long-lived sessions
- Industry standard for public clients (SPAs)

**Configuration Requirements:**
1. Register application in Microsoft Entra (formerly Azure AD)
2. Configure as Single Page Application
3. Add redirect URIs
4. Request API permissions (Mail.Read, etc.)
5. Get client ID

**Basic Flow:**
```javascript
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: 'YOUR_CLIENT_ID',
    authority: 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin
  }
};

const msalInstance = new PublicClientApplication(msalConfig);

// Login
await msalInstance.loginPopup({
  scopes: ['User.Read', 'Mail.Read']
});

// Get token silently
const tokenResponse = await msalInstance.acquireTokenSilent({
  scopes: ['Mail.Read'],
  account: msalInstance.getAllAccounts()[0]
});

// Use token for API calls
const accessToken = tokenResponse.accessToken;
```

### 1.5 Turso In-Browser Database

**Launch**: Recently announced (days ago as of search date)

**Technical Architecture:**
- Complete Rust rewrite of SQLite, compiled to WebAssembly
- Runs in browser via `@tursodatabase/database-wasm`
- Uses OPFS (Origin Private File System) for persistent storage
- **Not just SQLite-to-WASM**: Complete architectural rewrite

**Components:**
1. **Main UI Thread**: Handles all compute operations for queries
2. **Web Worker**: Parallel thread for filesystem operations via synchronous OPFS
3. **Shared Memory**: SharedArrayBuffer for efficient communication
4. **WASM Module**: Compiled to `wasm32-wasip1-threads` target

**API Characteristics:**
- Similar to `better-sqlite3` API
- **All methods are async** (due to OPFS)
- Two connection patterns:
  ```javascript
  // Recommended: connect helper
  const db = await connect("local.db");

  // Alternative: manual connection
  const db = new Database("local.db");
  await db.connect();
  ```

**Storage Options:**
- Named database: `"emails.db"` (persisted in OPFS)
- In-memory: `":memory:"` (ephemeral, reset on reload)

**Bundler Support:**
- Vite: Use `@tursodatabase/database-wasm/vite`
- Turbopack: Use `@tursodatabase/database-wasm/turbopack`
- No bundler: Use CDN (unpkg, jsDelivr) - higher bundle size (base64-encoded WASM)
- Other bundlers: Use default export

**Critical Requirements:**
- **COEP/COOP Headers**: Must be set for SharedArrayBuffer
  ```
  Cross-Origin-Embedder-Policy: require-corp
  Cross-Origin-Opener-Policy: same-origin
  ```
- **Same-Tab Locking**: Synchronous OPFS locks database to specific worker
  - **Cannot open same database from multiple tabs**
  - Important for data integrity

**Performance Characteristics:**
- Compute on main thread (communication overhead too high for worker)
- IO operations on worker thread (OPFS synchronous API)
- Efficient buffer sharing via SharedArrayBuffer

---

## 2. Proposed Architecture

### 2.1 High-Level Flow

```
User → multicardz App → MSAL Auth → Microsoft Graph API
                  ↓
              Turso DB (Browser)
                  ↓
         Local OPFS Storage
```

### 2.2 Component Breakdown

#### A. Frontend Components

**1. Email Account Manager** (`email-account-manager.js`)
- Manage Outlook account connections
- Handle OAuth flow with MSAL
- Store account metadata (email, display name, connection status)

**2. Email Sync Service** (`email-sync-service.js`)
- Coordinate email synchronization
- Implement delta query for incremental sync
- Handle pagination
- Manage sync state (delta tokens)
- Error handling and retry logic

**3. Email Storage Layer** (`email-storage.js`)
- Interface with Turso database
- CRUD operations for emails
- Query emails by criteria
- Full-text search implementation

**4. Email UI Components** (`email-viewer.js`, `email-list.js`)
- Display emails in multicardz interface
- Integrate with card/tag system
- Email preview and full view

**5. Sync Status UI** (`sync-status.js`)
- Show sync progress
- Display connection status
- Error notifications

#### B. Backend Components (Minimal)

**1. OAuth Redirect Handler** (FastAPI endpoint)
- Handle OAuth redirect from Microsoft
- Validate state parameter (CSRF protection)
- No token storage on server (client-side only)

**2. COEP/COOP Header Configuration**
- Middleware to set required headers for SharedArrayBuffer
- Critical for Turso functionality

### 2.3 Data Schema

**Email Table** (Turso SQLite)
```sql
CREATE TABLE emails (
  email_id TEXT PRIMARY KEY,           -- Microsoft Graph message ID
  user_id TEXT NOT NULL,               -- multicardz user ID
  account_email TEXT NOT NULL,         -- Outlook account email

  -- Email metadata
  subject TEXT,
  from_email TEXT,
  from_name TEXT,
  to_recipients TEXT,                  -- JSON array
  cc_recipients TEXT,                  -- JSON array
  bcc_recipients TEXT,                 -- JSON array

  -- Timestamps
  received_datetime TEXT,
  sent_datetime TEXT,
  synced_at TEXT,

  -- Content
  body_preview TEXT,                   -- Short preview
  body_content TEXT,                   -- Full HTML body
  body_type TEXT,                      -- 'html' or 'text'

  -- Flags
  is_read BOOLEAN DEFAULT 0,
  is_flagged BOOLEAN DEFAULT 0,
  has_attachments BOOLEAN DEFAULT 0,
  importance TEXT,                     -- 'low', 'normal', 'high'

  -- Folder
  folder_id TEXT,
  folder_name TEXT,

  -- multicardz integration
  card_id TEXT,                        -- Link to multicardz card
  tags TEXT,                           -- JSON array of tag IDs

  -- Search optimization
  search_text TEXT,                    -- Concatenated searchable fields

  -- Sync tracking
  change_key TEXT,                     -- Microsoft Graph change tracking
  deleted_at TEXT,                     -- Soft delete

  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (card_id) REFERENCES cards(card_id)
);

-- Indexes for performance
CREATE INDEX idx_emails_user_account ON emails(user_id, account_email);
CREATE INDEX idx_emails_received ON emails(received_datetime DESC);
CREATE INDEX idx_emails_folder ON emails(folder_id);
CREATE INDEX idx_emails_card ON emails(card_id);
CREATE INDEX idx_emails_search ON emails(search_text);
CREATE INDEX idx_emails_deleted ON emails(deleted_at);
```

**Email Accounts Table**
```sql
CREATE TABLE email_accounts (
  account_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  account_email TEXT NOT NULL,
  account_name TEXT,
  provider TEXT DEFAULT 'outlook',     -- Future: 'gmail', etc.

  -- OAuth metadata (encrypted)
  token_encrypted TEXT,                -- Encrypted access token
  token_expires_at TEXT,
  encryption_iv TEXT,                  -- Initialization vector for decryption

  -- Sync state
  last_sync_at TEXT,
  delta_tokens TEXT,                   -- JSON map of folder_id -> deltaToken
  sync_status TEXT,                    -- 'active', 'paused', 'error'
  sync_error TEXT,

  -- Settings
  sync_enabled BOOLEAN DEFAULT 1,
  auto_sync_interval INTEGER DEFAULT 300,  -- seconds (5 min default)
  folders_to_sync TEXT,                -- JSON array of folder IDs

  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(user_id),
  UNIQUE(user_id, account_email)
);
```

**Email Attachments Table**
```sql
CREATE TABLE email_attachments (
  attachment_id TEXT PRIMARY KEY,
  email_id TEXT NOT NULL,

  filename TEXT,
  content_type TEXT,
  size INTEGER,

  -- Storage
  content_blob BLOB,                   -- For small attachments
  download_url TEXT,                   -- For large attachments (fetch on-demand)
  is_inline BOOLEAN DEFAULT 0,

  created_at TEXT DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (email_id) REFERENCES emails(email_id) ON DELETE CASCADE
);
```

**Sync Log Table** (for debugging/monitoring)
```sql
CREATE TABLE sync_log (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id TEXT NOT NULL,
  sync_started_at TEXT,
  sync_completed_at TEXT,
  sync_status TEXT,                    -- 'success', 'partial', 'failed'
  emails_fetched INTEGER DEFAULT 0,
  emails_updated INTEGER DEFAULT 0,
  emails_deleted INTEGER DEFAULT 0,
  error_message TEXT,

  FOREIGN KEY (account_id) REFERENCES email_accounts(account_id)
);
```

### 2.4 Security Considerations

**1. Token Storage**
- **Client-Side Only**: Tokens stored in Turso (browser OPFS)
- **Encryption**: Use Web Crypto API to encrypt tokens at rest
- **Key Management**: Derive encryption key from user session (never persisted plainly)
- **No Server Storage**: Backend never sees or stores tokens

**2. Token Encryption Implementation**
```javascript
// Encrypt token before storing
async function encryptToken(token, userKey) {
  const encoder = new TextEncoder();
  const data = encoder.encode(token);

  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encryptedData = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    userKey,
    data
  );

  return {
    encrypted: btoa(String.fromCharCode(...new Uint8Array(encryptedData))),
    iv: btoa(String.fromCharCode(...iv))
  };
}

// Decrypt token when needed
async function decryptToken(encryptedData, iv, userKey) {
  const data = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
  const ivBytes = Uint8Array.from(atob(iv), c => c.charCodeAt(0));

  const decryptedData = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: ivBytes },
    userKey,
    data
  );

  const decoder = new TextDecoder();
  return decoder.decode(decryptedData);
}
```

**3. CSRF Protection**
- Use `state` parameter in OAuth flow
- Validate state on redirect
- Generate cryptographically secure random state

**4. Content Security Policy**
- Restrict script sources
- Allow Microsoft Graph API endpoints
- Enable SharedArrayBuffer (requires COEP/COOP)

**5. Data Privacy**
- Email content never leaves user's browser (except Microsoft → Browser)
- No server-side email storage
- Clear privacy policy

---

## 3. Implementation Phases

### Phase 1: Foundation (Week 1)

**Goals**: Set up basic infrastructure

**Tasks**:
1. **Microsoft Entra (Azure AD) App Registration**
   - Register multicardz as SPA
   - Configure redirect URIs
   - Request API permissions (Mail.Read, User.Read)
   - Document client ID

2. **Install Dependencies**
   ```bash
   npm install @azure/msal-browser
   npm install @tursodatabase/database-wasm
   ```

3. **Backend: COEP/COOP Headers**
   - Add FastAPI middleware for required headers
   - Test SharedArrayBuffer availability

4. **Turso Database Setup**
   - Initialize database connection module
   - Create schema (tables, indexes)
   - Test CRUD operations

5. **MSAL Configuration**
   - Initialize MSAL instance
   - Configure auth parameters
   - Create auth utility functions

**Deliverables**:
- Azure app registration complete
- Turso database initialized with schema
- MSAL auth working (login/logout)
- Backend headers configured

**Testing**:
- Verify SharedArrayBuffer available in browser
- Test Turso connection and basic queries
- Test MSAL login flow (no email fetch yet)

---

### Phase 2: OAuth Flow & Token Management (Week 2)

**Goals**: Complete authentication and secure token storage

**Tasks**:
1. **Email Account Manager Component**
   ```javascript
   class EmailAccountManager {
     async connectOutlookAccount();
     async disconnectAccount(accountId);
     async getConnectedAccounts();
     async refreshToken(accountId);
   }
   ```

2. **Implement OAuth Flow**
   - Popup or redirect flow
   - Handle authorization response
   - Exchange code for tokens
   - Store encrypted tokens in Turso

3. **Token Management**
   - Implement encryption/decryption functions
   - Store tokens securely in email_accounts table
   - Implement token refresh logic
   - Handle token expiration

4. **Account Persistence**
   - Save account metadata to Turso
   - Load accounts on app initialization
   - UI for managing connected accounts

**Deliverables**:
- Complete OAuth flow from button click to stored token
- Token encryption working
- Account management UI
- Token refresh working

**Testing**:
- Test complete auth flow
- Verify token encryption/decryption
- Test token refresh before expiration
- Test multiple account connections

---

### Phase 3: Email Fetching (Week 3)

**Goals**: Fetch emails from Microsoft Graph API

**Tasks**:
1. **Graph API Client**
   ```javascript
   class GraphAPIClient {
     constructor(accessToken);
     async getMessages(folderId, options);
     async getMessageDetails(messageId);
     async getMailFolders();
     async getDeltaMessages(folderId, deltaLink);
   }
   ```

2. **Initial Sync Implementation**
   - Fetch inbox messages (paginated)
   - Handle @odata.nextLink pagination
   - Parse message objects
   - Store in Turso database

3. **Error Handling**
   - Handle 401 (token expired) → refresh token
   - Handle 429 (rate limit) → exponential backoff
   - Handle network errors → retry logic
   - Handle 4xx/5xx errors → user notification

4. **Progress Tracking**
   - Show sync progress (X of Y messages)
   - Estimated time remaining
   - Pause/resume sync

**Deliverables**:
- Initial sync working for inbox
- Pagination working for large mailboxes
- Errors handled gracefully
- Sync progress UI

**Testing**:
- Test with small mailbox (< 100 emails)
- Test with large mailbox (> 1000 emails)
- Test error scenarios (disconnect, rate limit)
- Verify all emails stored correctly

---

### Phase 4: Incremental Sync (Week 4)

**Goals**: Implement delta queries for efficient sync

**Tasks**:
1. **Delta Query Implementation**
   - Store deltaToken per folder
   - Use delta endpoint for subsequent syncs
   - Handle additions, updates, deletions
   - Update local database accordingly

2. **Sync Strategy**
   - Initial sync: Full fetch + store deltaLink
   - Subsequent syncs: Use deltaLink
   - Auto-sync on interval (configurable)
   - Manual sync button

3. **Change Tracking**
   - Detect new emails
   - Detect updated emails (read status, flags)
   - Detect deleted emails (soft delete)
   - Update change_key field

4. **Sync Scheduling**
   - Background sync with Web Workers
   - Configurable interval (default 5 min)
   - Sync on app focus
   - Respect battery/network conditions

**Deliverables**:
- Delta sync working
- Auto-sync on interval
- Change tracking working
- Background sync with Web Worker

**Testing**:
- Send new email → verify auto-sync catches it
- Mark email read → verify sync updates it
- Delete email → verify soft delete
- Test delta token expiration handling

---

### Phase 5: Email Display & Search (Week 5)

**Goals**: Display emails in multicardz interface

**Tasks**:
1. **Email List Component**
   - Display emails in list view
   - Show subject, from, date, preview
   - Unread indicator
   - Sort options (date, from, subject)
   - Filter options (unread, flagged, folder)

2. **Email Detail View**
   - Full email content display
   - HTML rendering (sanitized)
   - Attachment list
   - Actions (mark read, flag, delete)

3. **Search Implementation**
   - Full-text search using SQLite FTS5
   - Search across subject, body, from
   - Search results highlighting
   - Recent searches

4. **Integration with Cards**
   - "Create card from email" button
   - Auto-populate card with email subject/content
   - Link email to existing card
   - Show linked emails in card view

**Deliverables**:
- Email list and detail views
- Search working
- Card integration working
- Basic email actions (read, flag, delete)

**Testing**:
- Test email display with various content types
- Test search with different queries
- Test card creation from email
- Test linking emails to cards

---

### Phase 6: Advanced Features (Week 6)

**Goals**: Add polish and advanced functionality

**Tasks**:
1. **Folder Support**
   - Display folder hierarchy
   - Sync multiple folders
   - Move emails between folders (via API)
   - Folder selection in settings

2. **Attachments**
   - Download and store small attachments
   - On-demand fetch for large attachments
   - Attachment preview
   - Save attachment to card

3. **Email Tags**
   - Auto-tag emails based on rules
   - Manual tagging
   - Tag-based filtering
   - Integration with multicardz tag system

4. **Offline Support**
   - Work with synced emails offline
   - Queue actions for next sync
   - Conflict resolution
   - Offline indicator

5. **Performance Optimization**
   - Virtual scrolling for large email lists
   - Lazy loading of email bodies
   - Database query optimization
   - Memory management

**Deliverables**:
- Folder management working
- Attachment handling complete
- Auto-tagging working
- Offline support functional

**Testing**:
- Test folder sync
- Test attachment download/preview
- Test offline → online sync
- Performance test with 10k+ emails

---

### Phase 7: Polish & Security Audit (Week 7)

**Goals**: Production readiness

**Tasks**:
1. **Security Audit**
   - Review token storage security
   - Review encryption implementation
   - Review API call security
   - Penetration testing
   - Privacy policy review

2. **Error Recovery**
   - Handle corrupted database
   - Reset sync state option
   - Export/import email data
   - Diagnostic tools

3. **User Settings**
   - Sync frequency
   - Folders to sync
   - Storage limits
   - Auto-delete old emails option

4. **Documentation**
   - User guide for connecting Outlook
   - Privacy documentation
   - Troubleshooting guide
   - Developer documentation

5. **Testing & QA**
   - Comprehensive test suite
   - Browser compatibility testing
   - Performance benchmarking
   - User acceptance testing

**Deliverables**:
- Security audit complete
- All edge cases handled
- Settings UI complete
- Documentation complete

**Testing**:
- Security testing
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Load testing
- User testing

---

## 4. Technical Specifications

### 4.1 Browser Requirements

**Minimum Browser Versions** (for SharedArrayBuffer + OPFS):
- Chrome/Edge: 102+
- Firefox: 105+
- Safari: 16.4+

**Feature Detection**:
```javascript
function isTursoSupported() {
  return typeof SharedArrayBuffer !== 'undefined'
    && 'storage' in navigator
    && 'getDirectory' in navigator.storage;
}
```

### 4.2 API Rate Limits

**Microsoft Graph API** (per app, per tenant):
- 10,000 requests per 10 minutes
- Implement token bucket or leaky bucket algorithm
- Exponential backoff on 429 responses
- Request batching for efficiency

**Recommended Strategy**:
- Batch API calls where possible
- Use delta queries to minimize requests
- Cache responses locally
- Respect Retry-After headers

### 4.3 Performance Targets

- **Initial sync**: < 5 seconds for 100 emails
- **Incremental sync**: < 2 seconds for 10 new emails
- **Search**: < 100ms for full-text search on 10k emails
- **Email list render**: < 16ms frame time (60 FPS)
- **Database size**: ~1MB per 1000 emails (without attachments)

### 4.4 Storage Estimates

**Per Email** (approximate):
- Metadata: ~1-2 KB
- Body preview: ~500 bytes
- Full HTML body: ~5-20 KB
- Total per email: ~10-25 KB average

**Capacity Estimates**:
- 1,000 emails: ~10-25 MB
- 10,000 emails: ~100-250 MB
- 100,000 emails: ~1-2.5 GB

**OPFS Limits**:
- No hard limit specified
- Typically several GB available
- Browser may prompt for quota increase
- Should implement storage limit settings

---

## 5. Security & Privacy

### 5.1 Threat Model

**Threats**:
1. Token theft via XSS
2. Token theft via browser extension
3. Token theft via physical access
4. CSRF attacks during OAuth
5. Man-in-the-middle attacks
6. Data exfiltration from database

**Mitigations**:
1. Content Security Policy (CSP)
2. Token encryption at rest
3. Device binding (future enhancement)
4. State parameter validation
5. HTTPS only + HSTS
6. OPFS isolation per origin

### 5.2 Data Privacy

**Principles**:
- **Local-First**: Emails stored only in browser
- **No Server Copies**: Backend never sees email content
- **User Control**: User can disconnect account anytime
- **Transparent**: Clear documentation of data flow
- **Deletion**: Complete data removal on disconnect

**Privacy Policy Requirements**:
- Explain Microsoft OAuth scopes
- Explain local storage model
- Explain no server storage
- Explain encryption
- Provide deletion instructions

### 5.3 Compliance Considerations

**GDPR** (if serving EU users):
- Right to access (export emails)
- Right to deletion (disconnect account)
- Data processing agreement with Microsoft
- Privacy policy disclosure

**CCPA** (if serving California users):
- Disclosure of data collection
- Right to deletion
- Do Not Sell disclosure

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Coverage**:
- Email storage CRUD operations
- Token encryption/decryption
- Graph API client methods
- Delta query parsing
- Search query building

**Tools**: Jest, Vitest

### 6.2 Integration Tests

**Scenarios**:
- Complete OAuth flow
- Initial sync with pagination
- Incremental sync with delta
- Token refresh flow
- Error handling and retries

**Tools**: Playwright, Cypress

### 6.3 E2E Tests

**User Journeys**:
1. Connect Outlook account
2. Wait for initial sync
3. Search for email
4. Create card from email
5. Verify email linked to card

**Tools**: Playwright

### 6.4 Performance Tests

**Metrics**:
- Initial sync time for various mailbox sizes
- Incremental sync time
- Search response time
- Database query performance
- Memory usage over time

**Tools**: Chrome DevTools, Lighthouse

### 6.5 Security Tests

**Checks**:
- Token encryption verification
- CSP compliance
- XSS vulnerability scanning
- HTTPS enforcement
- Token refresh handling

**Tools**: OWASP ZAP, Burp Suite

---

## 7. Deployment Considerations

### 7.1 Backend Changes

**FastAPI Middleware** for COEP/COOP:
```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class COEPCOOPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        return response

app.add_middleware(COEPCOOPMiddleware)
```

**OAuth Redirect Endpoint**:
```python
@app.get("/api/auth/outlook/callback")
async def outlook_callback(
    code: str = Query(...),
    state: str = Query(...),
    session_state: str = Query(None)
):
    # Validate state (CSRF protection)
    # No token exchange on server
    # Return success page that communicates with opener
    return HTMLResponse("""
        <script>
            window.opener.postMessage({
                type: 'oauth_success',
                code: '%s',
                state: '%s'
            }, window.location.origin);
            window.close();
        </script>
    """ % (code, state))
```

### 7.2 Frontend Build

**Bundler Configuration** (Vite):
```javascript
// vite.config.js
export default {
  optimizeDeps: {
    exclude: ['@tursodatabase/database-wasm']
  },
  resolve: {
    alias: {
      '@tursodatabase/database-wasm': '@tursodatabase/database-wasm/vite'
    }
  }
}
```

### 7.3 Environment Variables

```env
# .env.local
VITE_MSAL_CLIENT_ID=your-client-id
VITE_MSAL_AUTHORITY=https://login.microsoftonline.com/common
VITE_MSAL_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_GRAPH_API_ENDPOINT=https://graph.microsoft.com/v1.0
```

---

## 8. Monitoring & Observability

### 8.1 Metrics to Track

**Sync Metrics**:
- Sync success rate
- Sync duration (p50, p95, p99)
- Emails synced per sync
- Delta query success rate
- API error rates

**Performance Metrics**:
- Database query duration
- Search query duration
- Memory usage
- OPFS storage usage
- Token refresh frequency

**User Metrics**:
- Connected accounts per user
- Active email accounts
- Email search frequency
- Card-email linking frequency

### 8.2 Error Tracking

**Client-Side Errors**:
- Log to console (development)
- Send to error tracking service (production)
- Include context (user ID, account ID, action)

**Recommended Tools**:
- Sentry
- LogRocket
- Rollbar

### 8.3 Logging

**Log Levels**:
- DEBUG: Detailed flow (dev only)
- INFO: Major operations (sync start/end)
- WARN: Recoverable errors (rate limit, retry)
- ERROR: Unrecoverable errors (token invalid)

**PII Considerations**:
- Never log email content
- Never log tokens
- Hash email addresses in logs
- Truncate subject lines

---

## 9. Future Enhancements

### 9.1 Phase 8+ Features

**Multi-Provider Support**:
- Gmail integration (IMAP + OAuth)
- Generic IMAP support
- Exchange Server support

**Advanced Email Features**:
- Email composition
- Reply/forward
- Email threading
- Smart filtering
- AI-powered categorization

**Collaboration Features**:
- Share emails with workspace members
- Collaborative email handling
- Assignment and delegation

**Analytics**:
- Email analytics dashboard
- Response time tracking
- Sender/recipient insights

**AI Integration**:
- Email summarization
- Smart replies
- Priority inbox
- Sentiment analysis

### 9.2 Technical Improvements

**Performance**:
- Web Worker for background sync
- IndexedDB fallback for compatibility
- Service Worker for offline
- Lazy loading optimization

**Security**:
- Hardware security key support
- Biometric authentication
- Device attestation
- Encrypted search

**Sync**:
- Push notifications for new emails (via webhooks)
- Real-time sync with WebSockets
- Multi-device sync coordination

---

## 10. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Microsoft API changes | High | Medium | Version API, monitor changelog, graceful degradation |
| Browser compatibility | High | Low | Feature detection, fallback UI, progressive enhancement |
| Token theft | High | Low | Encryption, CSP, security audit |
| Storage quota exceeded | Medium | Medium | Storage limits, old email deletion, user warning |
| Sync conflicts | Medium | Medium | Conflict resolution strategy, last-write-wins |
| Rate limiting | Medium | High | Token bucket, exponential backoff, request batching |
| OPFS browser support | High | Low | Compatibility check, unsupported browser message |
| Performance degradation | Medium | Medium | Virtual scrolling, lazy loading, query optimization |
| OAuth flow breakage | High | Low | Fallback flow, clear error messages, retry mechanism |

---

## 11. Success Criteria

### 11.1 Functional Requirements

- [ ] User can connect Outlook account via OAuth
- [ ] Emails sync automatically from inbox
- [ ] User can search emails
- [ ] User can view email details
- [ ] User can create card from email
- [ ] User can disconnect account (data deleted)
- [ ] Incremental sync works (delta queries)
- [ ] Offline access to synced emails

### 11.2 Performance Requirements

- [ ] Initial sync completes in < 5s for 100 emails
- [ ] Incremental sync completes in < 2s
- [ ] Search returns results in < 100ms
- [ ] UI remains responsive during sync (60 FPS)
- [ ] Database size < 30 KB per email

### 11.3 Security Requirements

- [ ] Tokens encrypted at rest
- [ ] OAuth state parameter validated
- [ ] HTTPS enforced
- [ ] CSP headers configured
- [ ] No email content sent to backend
- [ ] Security audit passed

### 11.4 User Experience Requirements

- [ ] OAuth flow completes in < 3 clicks
- [ ] Sync progress clearly visible
- [ ] Errors explained in plain language
- [ ] Settings accessible and clear
- [ ] Works on major browsers (Chrome, Firefox, Safari, Edge)

---

## 12. Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Foundation | 1 week | Database + Auth setup |
| Phase 2: OAuth & Tokens | 1 week | Complete auth flow |
| Phase 3: Email Fetching | 1 week | Initial sync working |
| Phase 4: Incremental Sync | 1 week | Delta queries working |
| Phase 5: Display & Search | 1 week | Email UI complete |
| Phase 6: Advanced Features | 1 week | Folders, attachments, tags |
| Phase 7: Polish & Audit | 1 week | Production ready |
| **Total** | **7 weeks** | **MVP launch** |

---

## 13. References

### Documentation
- [Microsoft Graph API - Messages](https://learn.microsoft.com/en-us/graph/api/user-list-messages)
- [MSAL.js Documentation](https://learn.microsoft.com/en-us/entra/msal/javascript/)
- [Delta Query Overview](https://learn.microsoft.com/en-us/graph/delta-query-overview)
- [Turso in Browser Launch](https://turso.tech/blog/introducing-turso-in-the-browser)
- [OAuth 2.0 PKCE](https://oauth.net/2/pkce/)

### Libraries
- `@azure/msal-browser`: https://www.npmjs.com/package/@azure/msal-browser
- `@tursodatabase/database-wasm`: https://www.npmjs.com/package/@tursodatabase/database-wasm

### Inspiration
- [Superhuman Architecture](https://superhuman.com)
- [Superhuman Privacy](https://blog.superhuman.com/superhuman-soc-2-compliant-data-privacy/)

---

## Appendix A: Code Examples

### A.1 MSAL Initialization

```javascript
// auth/msal-config.js
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_MSAL_CLIENT_ID,
    authority: 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin + '/auth/callback',
    postLogoutRedirectUri: window.location.origin
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);

await msalInstance.initialize();
```

### A.2 Email Sync Service

```javascript
// services/email-sync-service.js
import { GraphAPIClient } from './graph-api-client.js';
import { EmailStorage } from './email-storage.js';

export class EmailSyncService {
  constructor(msalInstance, tursoDb) {
    this.msal = msalInstance;
    this.db = tursoDb;
    this.storage = new EmailStorage(tursoDb);
  }

  async syncAccount(accountId) {
    // Get account from DB
    const account = await this.storage.getAccount(accountId);

    // Get fresh token
    const tokenResponse = await this.msal.acquireTokenSilent({
      scopes: ['Mail.Read'],
      account: this.msal.getAccountByUsername(account.email)
    });

    const graphClient = new GraphAPIClient(tokenResponse.accessToken);

    // Check if initial sync or incremental
    const deltaToken = account.deltaTokens?.inbox;

    if (deltaToken) {
      // Incremental sync
      await this.incrementalSync(graphClient, account, deltaToken);
    } else {
      // Initial sync
      await this.initialSync(graphClient, account);
    }
  }

  async initialSync(graphClient, account) {
    console.log('Starting initial sync...');

    let nextLink = null;
    let totalFetched = 0;

    do {
      const response = nextLink
        ? await graphClient.getNextPage(nextLink)
        : await graphClient.getMessages('inbox', {
            $select: 'id,subject,from,toRecipients,receivedDateTime,bodyPreview,hasAttachments,isRead',
            $top: 100,
            $orderby: 'receivedDateTime desc'
          });

      // Store emails in Turso
      for (const message of response.value) {
        await this.storage.upsertEmail(account.accountId, message);
        totalFetched++;
      }

      nextLink = response['@odata.nextLink'];

      // Emit progress event
      this.emitProgress({ totalFetched, hasMore: !!nextLink });

    } while (nextLink);

    console.log(`Initial sync complete: ${totalFetched} emails`);
  }

  async incrementalSync(graphClient, account, deltaToken) {
    console.log('Starting incremental sync...');

    const response = await graphClient.getDeltaMessages(deltaToken);

    let added = 0, updated = 0, deleted = 0;

    for (const message of response.value) {
      if (message['@removed']) {
        await this.storage.softDeleteEmail(message.id);
        deleted++;
      } else {
        const existed = await this.storage.emailExists(message.id);
        await this.storage.upsertEmail(account.accountId, message);
        existed ? updated++ : added++;
      }
    }

    // Store new delta token
    await this.storage.updateDeltaToken(
      account.accountId,
      'inbox',
      response['@odata.deltaLink']
    );

    console.log(`Incremental sync complete: +${added} ~${updated} -${deleted}`);
  }

  emitProgress(progress) {
    window.dispatchEvent(new CustomEvent('email-sync-progress', {
      detail: progress
    }));
  }
}
```

### A.3 Turso Email Storage

```javascript
// services/email-storage.js
import { connect } from '@tursodatabase/database-wasm';

export class EmailStorage {
  constructor(db) {
    this.db = db;
  }

  static async initialize() {
    const db = await connect('multicardz-emails.db');

    // Create schema
    await db.exec(`
      CREATE TABLE IF NOT EXISTS emails (
        email_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_email TEXT NOT NULL,
        subject TEXT,
        from_email TEXT,
        from_name TEXT,
        to_recipients TEXT,
        received_datetime TEXT,
        body_preview TEXT,
        body_content TEXT,
        is_read INTEGER DEFAULT 0,
        has_attachments INTEGER DEFAULT 0,
        folder_id TEXT,
        card_id TEXT,
        tags TEXT,
        change_key TEXT,
        synced_at TEXT,
        deleted_at TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_emails_account
        ON emails(account_email, deleted_at);
      CREATE INDEX IF NOT EXISTS idx_emails_received
        ON emails(received_datetime DESC);
    `);

    return new EmailStorage(db);
  }

  async upsertEmail(accountId, message) {
    const email = this.parseGraphMessage(message, accountId);

    await this.db.prepare(`
      INSERT INTO emails (
        email_id, user_id, account_email, subject, from_email, from_name,
        to_recipients, received_datetime, body_preview, is_read,
        has_attachments, change_key, synced_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(email_id) DO UPDATE SET
        subject = excluded.subject,
        is_read = excluded.is_read,
        change_key = excluded.change_key,
        synced_at = CURRENT_TIMESTAMP
    `).run([
      email.id,
      email.userId,
      email.accountEmail,
      email.subject,
      email.fromEmail,
      email.fromName,
      JSON.stringify(email.toRecipients),
      email.receivedDateTime,
      email.bodyPreview,
      email.isRead ? 1 : 0,
      email.hasAttachments ? 1 : 0,
      email.changeKey
    ]);
  }

  parseGraphMessage(message, accountId) {
    return {
      id: message.id,
      userId: 'default-user', // TODO: Get from context
      accountEmail: accountId,
      subject: message.subject || '(no subject)',
      fromEmail: message.from?.emailAddress?.address,
      fromName: message.from?.emailAddress?.name,
      toRecipients: message.toRecipients?.map(r => r.emailAddress) || [],
      receivedDateTime: message.receivedDateTime,
      bodyPreview: message.bodyPreview,
      isRead: message.isRead,
      hasAttachments: message.hasAttachments,
      changeKey: message.changeKey
    };
  }

  async getEmails(accountEmail, limit = 50, offset = 0) {
    const result = await this.db.prepare(`
      SELECT * FROM emails
      WHERE account_email = ? AND deleted_at IS NULL
      ORDER BY received_datetime DESC
      LIMIT ? OFFSET ?
    `).all([accountEmail, limit, offset]);

    return result.rows;
  }

  async searchEmails(accountEmail, query) {
    const result = await this.db.prepare(`
      SELECT * FROM emails
      WHERE account_email = ?
        AND deleted_at IS NULL
        AND (
          subject LIKE ? OR
          body_preview LIKE ? OR
          from_email LIKE ?
        )
      ORDER BY received_datetime DESC
      LIMIT 100
    `).all([
      accountEmail,
      `%${query}%`,
      `%${query}%`,
      `%${query}%`
    ]);

    return result.rows;
  }

  async softDeleteEmail(emailId) {
    await this.db.prepare(`
      UPDATE emails
      SET deleted_at = CURRENT_TIMESTAMP
      WHERE email_id = ?
    `).run([emailId]);
  }

  async emailExists(emailId) {
    const result = await this.db.prepare(`
      SELECT 1 FROM emails WHERE email_id = ? LIMIT 1
    `).get([emailId]);

    return !!result;
  }
}
```

---

## Appendix B: Security Checklist

- [ ] Tokens encrypted with AES-GCM
- [ ] Encryption key derived from user session
- [ ] OAuth state parameter generated with crypto.getRandomValues()
- [ ] State parameter validated on redirect
- [ ] HTTPS enforced (HSTS header)
- [ ] CSP configured (script-src, connect-src)
- [ ] COEP/COOP headers set
- [ ] No tokens in localStorage (use encrypted Turso)
- [ ] No email content logged
- [ ] No PII in error messages
- [ ] Token refresh before expiration
- [ ] Failed auth attempts logged
- [ ] Rate limiting on sync operations
- [ ] Input sanitization for search queries
- [ ] HTML email content sanitized before rendering
- [ ] XSS vulnerability scan passed
- [ ] Dependency vulnerability scan passed (npm audit)
- [ ] Security headers validated (securityheaders.com)
- [ ] Privacy policy reviewed by legal
- [ ] Data deletion verified (disconnect account)

---

**End of Plan**

*This document will be updated as implementation progresses and new insights are gained.*
