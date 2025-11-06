# Performance Monitoring Standards

**Document Type**: Standards & Guidelines
**Date**: 2025-11-06
**Version**: 1
**Status**: ACTIVE
**Owner**: Engineering Team

---

## Executive Summary

This document establishes performance monitoring standards for the multicardz™ application. The primary objective is to maintain **Lighthouse 100/100 scores** across all categories while enabling rich JavaScript interactions through strategic deferred loading and the genX framework.

### Core Principles

1. **Lighthouse 100 is Non-Negotiable**: All deployments must maintain perfect scores
2. **Deferred Loading First**: JavaScript loads after First Contentful Paint (FCP)
3. **Performance Budget Enforced**: Automated checks block oversized bundles
4. **genX for Complex Interactions**: Framework enables efficiency at scale
5. **Continuous Monitoring**: Real-time alerts on performance degradation

---

## Lighthouse Score Requirements

### Mandatory Thresholds

All four Lighthouse categories must score **100/100**:

| Category | Required Score | Current Score | Status |
|----------|----------------|---------------|--------|
| Performance | 100 | 100 | ✓ |
| Accessibility | 100 | 100 | ✓ |
| Best Practices | 100 | 100 | ✓ |
| SEO | 100 | 100 | ✓ |

### Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor | Current |
|--------|------|-------------------|------|---------|
| FCP (First Contentful Paint) | < 1.8s | 1.8s - 3.0s | > 3.0s | 0.6s ✓ |
| LCP (Largest Contentful Paint) | < 2.5s | 2.5s - 4.0s | > 4.0s | 1.2s ✓ |
| CLS (Cumulative Layout Shift) | < 0.1 | 0.1 - 0.25 | > 0.25 | 0.00 ✓ |
| FID (First Input Delay) | < 100ms | 100ms - 300ms | > 300ms | 12ms ✓ |
| TTI (Time to Interactive) | < 3.8s | 3.8s - 7.3s | > 7.3s | 1.8s ✓ |
| TBT (Total Blocking Time) | < 200ms | 200ms - 600ms | > 600ms | 45ms ✓ |

**Enforcement**: CI/CD pipeline runs Lighthouse on every commit. Scores below thresholds block merge.

---

## Deferred Loading Patterns

### Pattern 1: Script Defer (Recommended)

**When to Use**: All non-critical JavaScript

```html
<!-- GOOD: Deferred loading (doesn't block FCP) -->
<script src="/static/js/app.js" defer></script>
<script src="/static/js/drag-drop.js" defer></script>

<!-- BAD: Synchronous loading (blocks FCP) -->
<script src="/static/js/app.js"></script>
```

**Benefits**:
- HTML parsing continues uninterrupted
- Scripts execute after DOM is ready
- Maintains document order (important for dependencies)

**Metrics Impact**:
```
Before defer:  FCP: 2.1s, LCP: 2.8s, Lighthouse: 87
After defer:   FCP: 0.6s, LCP: 1.2s, Lighthouse: 100
```

---

### Pattern 2: Dynamic Import (Advanced)

**When to Use**: Code splitting, conditional features

```javascript
// Load drag-drop only when user interacts with tags
document.querySelector('.tag').addEventListener('mousedown', async () => {
    const { initDragDrop } = await import('/static/js/drag-drop.js');
    initDragDrop();
}, { once: true });
```

**Benefits**:
- Smallest possible initial bundle
- Features load on-demand
- Reduces Total Blocking Time (TBT)

**Metrics Impact**:
```
Static import:   Initial bundle: 168KB, TBT: 120ms
Dynamic import:  Initial bundle: 28KB,  TBT: 45ms
```

---

### Pattern 3: Intersection Observer (Lazy Loading)

**When to Use**: Below-the-fold features

```javascript
// Load analytics only when user scrolls to footer
const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
        import('/static/js/analytics.js');
        observer.disconnect();
    }
});
observer.observe(document.querySelector('footer'));
```

**Benefits**:
- Zero impact on initial load
- Perfect for analytics, social widgets, ads

**Metrics Impact**:
```
Synchronous analytics: FCP: 0.8s, LCP: 1.4s
Lazy analytics:        FCP: 0.6s, LCP: 1.2s
```

---

### Pattern 4: requestIdleCallback (Non-Critical Tasks)

**When to Use**: Background tasks, preloading

```javascript
// Preload fonts during browser idle time
requestIdleCallback(() => {
    const fonts = ['Mulish', 'Lato', 'Roboto'];
    fonts.forEach(font => {
        document.fonts.load(`1em ${font}`);
    });
});
```

**Benefits**:
- Tasks run when browser has spare cycles
- No impact on user interactions
- Improves perceived performance

---

## genX Usage Guidelines

### When to Use genX

genX is a framework for building reactive, state-driven UIs. Use it when:

1. **Complex State Management**: Multi-step flows, shopping carts, form wizards
2. **Reactive UI**: UI updates automatically when state changes
3. **Server Sync**: Automatic persistence to backend
4. **Performance Critical**: Need optimized DOM updates

### When NOT to Use genX

Use vanilla JavaScript when:

1. **Simple Toggles**: Theme switch, modal open/close
2. **One-Time Actions**: Analytics events, form submission
3. **Static Content**: No state, no interactions
4. **Third-Party Integration**: External scripts (analytics, ads)

---

### Decision Matrix

| Scenario | Use genX? | Rationale | Example |
|----------|-----------|-----------|---------|
| Drag-and-drop system | ✓ Yes | Complex state, multi-element coordination | Tag reordering |
| Tag creation flow | ✓ Yes | Multi-step, validation, server sync | Create tag modal |
| Group management | ✓ Yes | Hierarchical state, reactive UI | Group tags feature |
| Tag selection | ✓ Yes | State-driven, keyboard shortcuts | Multi-select with Shift |
| Theme toggle | ✗ No | Simple class swap, localStorage | Dark/light mode |
| Analytics event | ✗ No | Fire-and-forget, no state | Track button click |
| Modal open/close | ✗ No | Simple class toggle | Settings modal |
| Font preference | ✗ No | Server-rendered, no client state | Font selector |

---

### genX Performance Requirements

1. **Framework Size**: genX core must be < 15KB gzipped
2. **Deferred Loading**: genX loads after FCP (defer attribute)
3. **Progressive Enhancement**: App works without genX (graceful degradation)
4. **Server-Side Rendering**: genX hydrates server HTML (no full re-render)

**Enforcement**: genX bundle size checked in CI/CD pipeline.

---

### genX Code Example

```javascript
// Define reactive state
genX.state = {
    tags: {
        'tag-1': { id: 'tag-1', content: 'Example', selected: false, groupId: null },
        'tag-2': { id: 'tag-2', content: 'Demo', selected: true, groupId: 'group-1' }
    },
    groups: {
        'group-1': { id: 'group-1', name: 'Work', collapsed: false }
    }
};

// Define actions
genX.actions = {
    selectTag(tagId) {
        genX.state.tags[tagId].selected = true;
        // DOM updates automatically, server sync automatic
    },

    moveTagToGroup(tagId, groupId) {
        genX.state.tags[tagId].groupId = groupId;
        // Reactive: UI updates, parent group updates, server syncs
    }
};

// Configure server sync
genX.sync('tags', {
    endpoint: '/api/tags',
    method: 'POST',
    debounce: 500, // Wait 500ms before syncing
    batch: true    // Batch multiple changes
});

// Components auto-update on state change
genX.component('TagList', {
    template: (state) => `
        ${Object.values(state.tags).map(tag => `
            <div class="tag ${tag.selected ? 'selected' : ''}"
                 data-tag-id="${tag.id}">
                ${tag.content}
            </div>
        `).join('')}
    `,
    // Re-renders automatically when state.tags changes
});
```

**Performance Impact**:
```
Vanilla JS (manual DOM updates): 80KB, 2,698 lines
genX (reactive state):            10KB, 350 lines
Reduction:                        87.5% smaller, 87% fewer lines
```

---

## Performance Budget

### Current Budget (November 2025)

| Category | Current | Budget | Status | Notes |
|----------|---------|--------|--------|-------|
| **Total JS** | 168KB | 200KB | ✓ | All deferred |
| **Critical JS** | 0KB | 10KB | ✓ | None on critical path |
| **Total CSS** | 45KB | 50KB | ✓ | Includes font fallbacks |
| **Fonts** | 140KB | 150KB | ✓ | 8 fonts, woff2 format |
| **Images** | 0KB | 100KB | ✓ | SVG only (no raster) |
| **HTML** | 12KB | 20KB | ✓ | Server-rendered |
| **Total Page** | 365KB | 500KB | ✓ | Under budget |

### Future Budget (Post-genX Migration - Target Q2 2026)

| Category | Target | Change | Rationale |
|----------|--------|--------|-----------|
| **Total JS** | 60KB | -64% | genX replaces 168KB vanilla JS with 60KB framework code |
| genX Framework | 15KB | New | Core framework |
| App Code | 20KB | -28% | Replaces app.js (28KB) |
| Drag-Drop | 10KB | -87% | genX-powered, 80KB → 10KB |
| Groups | 5KB | -58% | genX reactive state |
| Analytics | 10KB | -37% | Minimal changes |

**Target Lighthouse Score**: 100/100 (maintained)
**Target FCP**: < 0.5s (improved from 0.6s)
**Target LCP**: < 1.0s (improved from 1.2s)

---

## CI/CD Integration

### Pre-Commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running performance checks..."

# 1. Check bundle sizes
./scripts/check-bundle-size.sh || exit 1

# 2. Run Lighthouse CI (local)
npm run lighthouse:ci || exit 1

# 3. Check for performance regressions
./scripts/check-performance-regression.sh || exit 1

echo "✓ Performance checks passed"
```

---

### GitHub Actions Workflow

```yaml
# .github/workflows/performance.yml
name: Performance Checks

on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v9
        with:
          urls: |
            http://localhost:5000
            http://localhost:5000/tags
          budgetPath: ./lighthouse-budget.json
          uploadArtifacts: true

      - name: Check bundle sizes
        run: |
          npm run bundlesize

      - name: Fail if Lighthouse score < 100
        run: |
          if [ ${{ steps.lighthouse.outputs.score }} -lt 100 ]; then
            echo "Lighthouse score below 100: ${{ steps.lighthouse.outputs.score }}"
            exit 1
          fi
```

---

### Bundle Size Checker

```json
// package.json
{
  "bundlesize": [
    {
      "path": "./apps/static/js/app.js",
      "maxSize": "30 KB"
    },
    {
      "path": "./apps/static/js/drag-drop.js",
      "maxSize": "80 KB",
      "note": "TODO: Reduce to 50KB with genX migration"
    },
    {
      "path": "./apps/static/js/group-tags.js",
      "maxSize": "15 KB"
    },
    {
      "path": "./apps/static/js/analytics.js",
      "maxSize": "20 KB"
    },
    {
      "path": "./apps/static/css/user.css",
      "maxSize": "50 KB"
    }
  ]
}
```

**Enforcement**: `npm run bundlesize` fails if any file exceeds budget.

---

### Lighthouse Budget Configuration

```json
// lighthouse-budget.json
{
  "budgets": [
    {
      "resourceSizes": [
        {
          "resourceType": "script",
          "budget": 200
        },
        {
          "resourceType": "stylesheet",
          "budget": 50
        },
        {
          "resourceType": "font",
          "budget": 150
        },
        {
          "resourceType": "image",
          "budget": 100
        },
        {
          "resourceType": "document",
          "budget": 20
        },
        {
          "resourceType": "total",
          "budget": 500
        }
      ],
      "timings": [
        {
          "metric": "first-contentful-paint",
          "budget": 1800
        },
        {
          "metric": "largest-contentful-paint",
          "budget": 2500
        },
        {
          "metric": "cumulative-layout-shift",
          "budget": 0.1
        },
        {
          "metric": "total-blocking-time",
          "budget": 200
        },
        {
          "metric": "interactive",
          "budget": 3800
        }
      ]
    }
  ]
}
```

---

## Monitoring Dashboard

### Real-Time Metrics (Production)

**Tool**: Custom analytics dashboard at `/admin/performance`

**Metrics Tracked**:

1. **Core Web Vitals (User-Centric)**:
   - FCP: P50, P75, P95, P99
   - LCP: P50, P75, P95, P99
   - CLS: P50, P75, P95, P99
   - FID: P50, P75, P95, P99

2. **JavaScript Performance**:
   - Total bundle size (KB)
   - Parse time (ms)
   - Execution time (ms)
   - Error rate (%)

3. **Network Performance**:
   - DNS lookup time
   - TCP connection time
   - TLS negotiation time
   - Time to First Byte (TTFB)

4. **Resource Loading**:
   - Font load time
   - CSS load time
   - Image load time (if any)
   - Total page weight

---

### Performance Monitoring Code

```javascript
// apps/static/js/performance-monitor.js

// Track Core Web Vitals
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
    fetch('/api/analytics/web-vitals', {
        method: 'POST',
        body: JSON.stringify({
            name: metric.name,
            value: metric.value,
            rating: metric.rating, // 'good', 'needs-improvement', 'poor'
            delta: metric.delta,
            id: metric.id,
            timestamp: Date.now()
        })
    });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);

// Track Long Tasks (blocking main thread)
const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
            fetch('/api/analytics/long-task', {
                method: 'POST',
                body: JSON.stringify({
                    duration: entry.duration,
                    startTime: entry.startTime,
                    attribution: entry.attribution
                })
            });
        }
    }
});
observer.observe({ entryTypes: ['longtask'] });

// Track JavaScript Errors
window.addEventListener('error', (event) => {
    fetch('/api/analytics/error', {
        method: 'POST',
        body: JSON.stringify({
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error?.stack
        })
    });
});

// Track Resource Load Times
window.addEventListener('load', () => {
    const resources = performance.getEntriesByType('resource');
    const slowResources = resources.filter(r => r.duration > 1000);

    if (slowResources.length > 0) {
        fetch('/api/analytics/slow-resources', {
            method: 'POST',
            body: JSON.stringify(slowResources.map(r => ({
                name: r.name,
                duration: r.duration,
                size: r.transferSize
            })))
        });
    }
});
```

**Deployment**: This file loads deferred, after all critical resources.

---

### Dashboard Visualization

```python
# apps/admin/performance_dashboard.py

from flask import render_template, jsonify
from datetime import datetime, timedelta
import statistics

@app.route('/admin/performance')
def performance_dashboard():
    """Performance monitoring dashboard"""

    # Query last 24 hours of metrics
    metrics = db.execute("""
        SELECT metric_name, metric_value, timestamp
        FROM performance_metrics
        WHERE timestamp > ?
        ORDER BY timestamp DESC
    """, [datetime.now() - timedelta(days=1)])

    # Calculate percentiles
    def percentiles(values):
        return {
            'p50': statistics.median(values),
            'p75': statistics.quantiles(values, n=4)[2],
            'p95': statistics.quantiles(values, n=20)[18],
            'p99': statistics.quantiles(values, n=100)[98]
        }

    # Group by metric
    grouped = {}
    for metric in metrics:
        if metric['metric_name'] not in grouped:
            grouped[metric['metric_name']] = []
        grouped[metric['metric_name']].append(metric['metric_value'])

    # Calculate stats
    stats = {}
    for metric_name, values in grouped.items():
        stats[metric_name] = percentiles(values)

    return render_template('admin/performance_dashboard.html', stats=stats)
```

**Access**: Admin users only, `/admin/performance`

---

## Alert Triggers

### Critical Alerts (Immediate Notification)

1. **Lighthouse Score < 95**:
   - **Action**: Block deployment, notify engineering team
   - **Notification**: Slack #engineering, email to tech lead
   - **SLA**: Fix within 1 hour

2. **FCP > 2.0s (P75)**:
   - **Action**: Investigate resource loading
   - **Notification**: Slack #performance
   - **SLA**: Fix within 4 hours

3. **JavaScript Error Rate > 5%**:
   - **Action**: Rollback deployment if recent
   - **Notification**: PagerDuty alert
   - **SLA**: Fix within 1 hour

4. **Bundle Size > 200KB**:
   - **Action**: Block merge to main
   - **Notification**: GitHub PR comment
   - **SLA**: Fix before merge

---

### Warning Alerts (Investigation Required)

5. **LCP > 2.5s (P75)**:
   - **Action**: Review image/font optimization
   - **Notification**: Slack #performance
   - **SLA**: Fix within 1 day

6. **CLS > 0.1 (P75)**:
   - **Action**: Check for dynamic content insertion
   - **Notification**: Slack #performance
   - **SLA**: Fix within 1 day

7. **JavaScript Error Rate > 1%**:
   - **Action**: Review error logs, add tests
   - **Notification**: Slack #engineering
   - **SLA**: Fix within 3 days

8. **Bundle Size > 180KB**:
   - **Action**: Review recent additions, consider code splitting
   - **Notification**: GitHub PR comment
   - **SLA**: Monitor trend

---

### Informational Alerts

9. **New Long Task Detected (> 50ms)**:
   - **Action**: Add to performance backlog
   - **Notification**: Slack #performance (weekly digest)

10. **Slow Resource Load (> 1s)**:
    - **Action**: Review CDN/compression
    - **Notification**: Slack #performance (weekly digest)

---

## Optimization Workflow

### Step 1: Detect Performance Regression

```bash
# Run Lighthouse on production
npm run lighthouse:prod

# Compare with baseline
npm run lighthouse:compare

# Output:
# ❌ Performance score dropped from 100 to 93
# ❌ FCP increased by 400ms (0.6s → 1.0s)
# ✓ LCP unchanged (1.2s)
# ❌ TBT increased by 80ms (45ms → 125ms)
```

---

### Step 2: Identify Root Cause

```bash
# Analyze bundle size changes
npm run bundlesize:diff

# Output:
# apps/static/js/drag-drop.js: +15KB (80KB → 95KB)
# apps/static/js/app.js: +2KB (28KB → 30KB)
```

**Root Cause**: Recent feature added blocking code to drag-drop.js

---

### Step 3: Implement Fix

**Option A: Code Splitting**
```javascript
// Before: Added to drag-drop.js (blocks loading)
import heavyLibrary from 'heavy-library';

function newFeature() {
    heavyLibrary.doSomething();
}

// After: Dynamic import (loads on-demand)
async function newFeature() {
    const { doSomething } = await import('heavy-library');
    doSomething();
}
```

**Option B: Deferred Execution**
```javascript
// Before: Runs immediately
initNewFeature();

// After: Runs after idle
requestIdleCallback(() => {
    initNewFeature();
});
```

**Option C: genX Refactor**
```javascript
// Before: 15KB manual DOM manipulation
function updateTags() {
    // 300 lines of DOM queries and mutations
}

// After: 2KB genX reactive state
genX.state.tags = updatedTags;
// DOM updates automatically
```

---

### Step 4: Verify Fix

```bash
# Run Lighthouse again
npm run lighthouse:local

# Output:
# ✓ Performance score: 100 (restored)
# ✓ FCP: 0.6s (restored)
# ✓ TBT: 45ms (restored)
# ✓ Bundle size: 168KB (reduced from 185KB)
```

---

### Step 5: Deploy and Monitor

```bash
# Deploy to staging
git push origin staging

# Run Lighthouse on staging
npm run lighthouse:staging

# If passing, deploy to production
git push origin main

# Monitor dashboard for 24 hours
# Check /admin/performance for regressions
```

---

## Common Performance Pitfalls

### Pitfall 1: Synchronous Script Loading

```html
<!-- BAD: Blocks HTML parsing -->
<script src="/static/js/app.js"></script>

<!-- GOOD: Deferred loading -->
<script src="/static/js/app.js" defer></script>
```

**Impact**: Synchronous loading delays FCP by 200-500ms.

---

### Pitfall 2: Large Initial Bundle

```javascript
// BAD: Import everything upfront
import { dragDrop } from './drag-drop.js';
import { analytics } from './analytics.js';
import { groupTags } from './group-tags.js';

// GOOD: Import only what's needed
import { init } from './app.js';
// Other modules load dynamically when needed
```

**Impact**: Large bundles increase TBT by 50-100ms per 10KB.

---

### Pitfall 3: Render-Blocking CSS

```html
<!-- BAD: Inline critical CSS not extracted -->
<link rel="stylesheet" href="/static/css/user.css">

<!-- GOOD: Inline critical CSS, defer non-critical -->
<style>
    /* Critical above-the-fold styles */
    body { font-family: system-ui; }
    .header { background: #fff; }
</style>
<link rel="stylesheet" href="/static/css/user.css" media="print" onload="this.media='all'">
```

**Impact**: Render-blocking CSS delays FCP by 100-300ms.

---

### Pitfall 4: No Font Fallback Metrics

```css
/* BAD: Font swap causes layout shift */
@font-face {
    font-family: 'Mulish';
    src: url('/static/fonts/mulish-regular.woff2') format('woff2');
    font-display: swap;
}

/* GOOD: Metrics-matched fallback (zero layout shift) */
@font-face {
    font-family: 'Mulish Fallback';
    src: local('Arial');
    size-adjust: 107.4%;
    ascent-override: 90%;
    descent-override: 22%;
}

@font-face {
    font-family: 'Mulish';
    src: url('/static/fonts/mulish-regular.woff2') format('woff2');
    font-display: swap;
}

.font-avenir {
    font-family: 'Mulish', 'Mulish Fallback', Arial, sans-serif;
}
```

**Impact**: Font swap without metrics increases CLS by 0.05-0.15.

---

### Pitfall 5: Third-Party Scripts (Google Analytics, Facebook Pixel)

```html
<!-- BAD: Synchronous third-party script -->
<script src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>

<!-- GOOD: Deferred, self-hosted analytics -->
<script src="/static/js/analytics.js" defer></script>
```

**Impact**: Third-party scripts can delay FCP by 500-2000ms.

**multicardz™ Policy**: No third-party analytics. All tracking is self-hosted.

---

## Performance Testing Checklist

### Pre-Deployment Checklist

- [ ] Lighthouse score 100/100 on staging
- [ ] FCP < 1.8s on 3G throttling
- [ ] LCP < 2.5s on 3G throttling
- [ ] CLS = 0.00 (no layout shift)
- [ ] TBT < 200ms
- [ ] Bundle sizes within budget
- [ ] No render-blocking resources
- [ ] All scripts deferred or async
- [ ] Font fallback metrics configured
- [ ] No third-party scripts
- [ ] Error rate < 1% in staging
- [ ] Performance dashboard reviewed

### Post-Deployment Checklist

- [ ] Lighthouse score verified in production
- [ ] Dashboard shows no regressions (24 hours)
- [ ] No critical alerts triggered
- [ ] Core Web Vitals unchanged
- [ ] User complaints reviewed (none expected)
- [ ] Rollback plan documented

---

## Reporting

### Weekly Performance Report

**Recipients**: Engineering team, product manager
**Schedule**: Every Monday 9am
**Format**: Email + Slack #performance

**Contents**:
1. **Lighthouse Scores**: Last 7 days average
2. **Core Web Vitals**: P50, P75, P95 trends
3. **Bundle Sizes**: Current vs budget
4. **Top Regressions**: Largest performance drops
5. **Top Improvements**: Largest performance gains
6. **Action Items**: Issues requiring attention

**Example**:
```
Weekly Performance Report (Nov 1-7, 2025)

Lighthouse Scores (7-day avg):
✓ Performance:     100 (unchanged)
✓ Accessibility:   100 (unchanged)
✓ Best Practices:  100 (unchanged)
✓ SEO:             100 (unchanged)

Core Web Vitals (P75):
✓ FCP: 0.62s (target: <1.8s, +0.02s from last week)
✓ LCP: 1.21s (target: <2.5s, +0.01s from last week)
✓ CLS: 0.00  (target: <0.1, unchanged)

Bundle Sizes:
✓ Total JS: 168KB (budget: 200KB)
⚠ drag-drop.js: 80KB (budget: 50KB - TODO: genX migration)

Action Items:
1. Schedule genX migration for drag-drop.js (Q2 2026)
2. Investigate 20ms FCP increase (minor, monitoring)
```

---

### Monthly Performance Review

**Recipients**: All engineering, CTO
**Schedule**: First Monday of each month
**Format**: Presentation + Q&A

**Contents**:
1. **Performance Trends**: 30-day charts
2. **Budget Compliance**: Current vs targets
3. **Optimization Wins**: Recent improvements
4. **Technical Debt**: Performance-related debt
5. **Roadmap**: Upcoming performance initiatives
6. **genX Migration Status**: Progress toward 60KB target

---

## genX Migration Performance Plan

### Phase 1: Proof of Concept (Q1 2026)

**Goal**: Validate genX performance claims

**Tasks**:
1. Migrate group-tags.js to genX (12KB → 5KB target)
2. Measure Lighthouse impact
3. Measure development velocity improvement
4. Document lessons learned

**Success Criteria**:
- Lighthouse score remains 100/100
- Bundle size reduced by 50%+
- Development time reduced by 30%+

---

### Phase 2: Core Features (Q2 2026)

**Goal**: Migrate drag-drop.js and app.js

**Tasks**:
1. Migrate drag-drop.js to genX (80KB → 10KB target)
2. Migrate app.js to genX (28KB → 20KB target)
3. Update performance budget
4. Train team on genX patterns

**Success Criteria**:
- Total JS reduced to ~90KB (from 168KB)
- Lighthouse score remains 100/100
- All team members trained

---

### Phase 3: Full Migration (Q3 2026)

**Goal**: Complete genX adoption

**Tasks**:
1. Migrate remaining JavaScript
2. Achieve 60KB total bundle size
3. Update documentation
4. Retire legacy patterns

**Success Criteria**:
- Total JS: 60KB (64% reduction achieved)
- Lighthouse score: 100/100 (maintained)
- FCP: <0.5s (improved from 0.6s)
- Team velocity: +40% (fewer lines, faster features)

---

## Conclusion

Performance is a feature, not an optimization. These standards ensure multicardz™ maintains its perfect Lighthouse 100/100 scores while enabling rich JavaScript interactions through strategic deferred loading and the genX framework.

**Key Takeaways**:

1. **Lighthouse 100 is mandatory**: All deployments must maintain perfect scores
2. **Defer everything**: JavaScript loads after FCP (critical path is HTML/CSS only)
3. **genX for scale**: Framework enables 64% bundle size reduction
4. **Monitor continuously**: Real-time dashboard catches regressions early
5. **Budget enforcement**: Automated checks block oversized bundles

By following these standards, multicardz™ will maintain world-class performance while scaling feature development.

---

## References

- **Doc 001**: JavaScript Architecture (DOM-as-Authority, deferred loading)
- **Doc 033**: Font Metric Optimization (Zero CLS strategy)
- **Doc 039**: genX Integration Architecture (Migration roadmap)
- **Doc 040**: Current JavaScript Implementation (Baseline metrics)
- **Web Vitals**: https://web.dev/vitals/
- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **genX Framework**: [Internal documentation]

---

**Document Status**: Active Standard
**Review Schedule**: Quarterly (next review February 2026)
**Maintenance Owner**: Performance Team
**Last Updated**: 2025-11-06
