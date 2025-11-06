# Anonymous-to-Paid User Tracking System


---
**IMPLEMENTATION STATUS**: PHASED IMPLEMENTATION
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Deferred to auth phase. See consolidated doc 039-2025-11-06-Authentication-Architecture-and-Plan.md
---


## Overview

Complete journey tracking from first anonymous visit through free trial signup to paid conversion using persistent cookies.

## Architecture

### 1. Anonymous User Cookie (`mcz_anon_id`)

**JavaScript** (`analytics.js`):
```javascript
// 90-day persistent cookie
function getOrCreateAnonymousUserId() {
    const cookieName = 'mcz_anon_id';
    const cookieValue = getCookie(cookieName);

    if (cookieValue) {
        return cookieValue;
    }

    // Generate new anonymous user ID
    const anonymousUserId = generateUUID();
    setCookie(cookieName, anonymousUserId, 90); // 90 days

    return anonymousUserId;
}
```

**Result**: Every visitor gets a persistent UUID that survives:
- Multiple sessions
- Browser closes/reopens
- Different pages on the site
- Up to 90 days

### 2. Session Tracking

**On every page load**:
1. Get/create anonymous user ID from cookie
2. Get/create session ID from localStorage
3. Send both to `/api/analytics/session`

**Database** (`analytics_sessions`):
```sql
session_id: UUID (unique per browser session)
user_id: TEXT (stores anonymous_user_id initially)
first_seen: TIMESTAMP
last_seen: TIMESTAMP
utm_source, utm_medium, etc.
```

**Key Insight**: `user_id` column stores the anonymous UUID initially, then gets upgraded to the real Auth0 user ID after signup!

### 3. Signup Conversion

**When user signs up via Auth0**:

**Webhook Payload**:
```json
{
  "user_id": "auth0|abc123",
  "anonymous_user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Backend** (`webhook_service.py`):
```python
# Find ALL sessions with the anonymous_user_id
results = db.execute("""
    SELECT session_id, first_seen
    FROM analytics_sessions
    WHERE user_id = :anonymous_user_id
    ORDER BY first_seen ASC
""", {'anonymous_user_id': anonymous_user_id})

# Update ALL sessions to the real user ID
db.execute("""
    UPDATE analytics_sessions
    SET user_id = :user_id
    WHERE user_id = :anonymous_user_id
""", {
    'user_id': 'auth0|abc123',
    'anonymous_user_id': '550e8400-e29b-41d4-a716-446655440000'
})
```

**Result**: All anonymous sessions are now linked to the real user account!

### 4. Paid Conversion

**When user upgrades to paid** (via Stripe webhook):

**Backend**:
```python
db.execute("""
    INSERT INTO conversion_funnel
    (session_id, user_id, funnel_stage, data)
    VALUES (:session_id, :user_id, 'upgrade', :data)
""")
```

**Result**: Complete attribution from first visit to revenue!

## Complete User Journey Example

### Day 1: Anonymous Visitor
```
1. User visits landing page
2. Cookie mcz_anon_id = "550e8400-..."
3. Session created:
   session_id: "a1b2c3d4-..."
   user_id: "550e8400-..."  (anonymous)
   utm_source: "google"
```

### Day 2: Return Visit
```
1. User returns (same cookie)
2. New session created:
   session_id: "e5f6g7h8-..."
   user_id: "550e8400-..."  (same anonymous ID)
```

### Day 5: Signup
```
1. User signs up → Auth0 webhook
2. Backend finds 2 sessions with user_id="550e8400-..."
3. Updates both:
   user_id: "auth0|abc123"
4. Funnel record created:
   funnel_stage: "signup"
   user_id: "auth0|abc123"
```

### Day 30: Paid Conversion
```
1. User upgrades → Stripe webhook
2. Funnel record created:
   funnel_stage: "upgrade"
   user_id: "auth0|abc123"
```

### Analytics Query
```sql
-- Complete journey for one user
SELECT
    s.first_seen,
    s.utm_source,
    s.utm_medium,
    f.funnel_stage,
    f.created
FROM analytics_sessions s
LEFT JOIN conversion_funnel f ON f.user_id = s.user_id
WHERE s.user_id = 'auth0|abc123'
ORDER BY s.first_seen;

Result:
first_seen          | utm_source | funnel_stage | created
--------------------|------------|--------------|-------------------
2025-01-01 10:00:00 | google     | NULL         | NULL
2025-01-02 14:30:00 | direct     | NULL         | NULL
2025-01-05 09:00:00 | direct     | signup       | 2025-01-05 09:00:00
2025-01-05 09:00:00 | direct     | upgrade      | 2025-01-30 12:00:00
```

**Attribution**: This user came from Google, returned directly, signed up, and converted to paid!

## Benefits

1. **Complete Attribution**: Know exactly where paid customers came from
2. **Multi-Session Tracking**: Track users across days/weeks
3. **A/B Test Attribution**: See which landing page variants convert to paid
4. **Cohort Analysis**: Group users by acquisition source → conversion rate
5. **LTV by Channel**: Calculate customer lifetime value by marketing channel

## Privacy Considerations

- Cookie is first-party (multicardz.com domain)
- No cross-site tracking
- No PII in cookie (just a UUID)
- Compliant with GDPR/CCPA (with proper privacy policy)
- Cookie expires after 90 days

## Integration Points

### Frontend (Your Auth0 signup form)
```javascript
// When user signs up, send anonymous_user_id to Auth0
const analytics = window.multicardzAnalytics();
const anonymousUserId = analytics.anonymousUserId;

// Include in Auth0 metadata or webhook payload
auth0.signup({
  email: email,
  password: password,
  user_metadata: {
    anonymous_user_id: anonymousUserId
  }
});
```

### Auth0 Action (Webhook Trigger)
```javascript
exports.onExecutePostUserRegistration = async (event, api) => {
  const anonymousUserId = event.user.user_metadata.anonymous_user_id;

  await fetch('https://multicardz.com/api/webhooks/auth0/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: event.user.user_id,
      anonymous_user_id: anonymousUserId,
      email: event.user.email,
      created_at: event.user.created_at
    })
  });
};
```

### Stripe (Paid Conversion)
Already implemented via `/api/webhooks/stripe/subscription`

## Queries for Analytics

### Conversion Funnel
```sql
SELECT
    utm_source,
    COUNT(DISTINCT s.user_id) as visitors,
    COUNT(DISTINCT CASE WHEN f.funnel_stage = 'signup' THEN f.user_id END) as signups,
    COUNT(DISTINCT CASE WHEN f.funnel_stage = 'upgrade' THEN f.user_id END) as paid,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.funnel_stage = 'signup' THEN f.user_id END) / COUNT(DISTINCT s.user_id), 2) as signup_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.funnel_stage = 'upgrade' THEN f.user_id END) / COUNT(DISTINCT CASE WHEN f.funnel_stage = 'signup' THEN f.user_id END), 2) as paid_conversion_rate
FROM analytics_sessions s
LEFT JOIN conversion_funnel f ON f.user_id = s.user_id
GROUP BY utm_source;
```

### A/B Test → Paid Conversion
```sql
SELECT
    v.name as variant,
    COUNT(DISTINCT s.user_id) as visitors,
    COUNT(DISTINCT CASE WHEN f.funnel_stage = 'upgrade' THEN f.user_id END) as paid_customers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.funnel_stage = 'upgrade' THEN f.user_id END) / COUNT(DISTINCT s.user_id), 2) as paid_conversion_rate
FROM analytics_sessions s
JOIN a_b_test_variants v ON v.id = s.a_b_variant_id
LEFT JOIN conversion_funnel f ON f.user_id = s.user_id
WHERE s.a_b_variant_id IS NOT NULL
GROUP BY v.name;
```

## Implementation Status

✅ Anonymous cookie tracking (90-day lifespan)
✅ Session creation with anonymous_user_id
✅ Auth0 webhook to link sessions
✅ Stripe webhook for paid conversions
✅ Complete funnel tracking (landing → signup → paid)

## Next Steps

1. **Auth0 Integration**: Add anonymous_user_id to signup payload
2. **Privacy Policy**: Update to mention analytics cookies
3. **Dashboard**: Build analytics dashboard for conversion funnel
4. **Retention Analysis**: Track user engagement post-signup
