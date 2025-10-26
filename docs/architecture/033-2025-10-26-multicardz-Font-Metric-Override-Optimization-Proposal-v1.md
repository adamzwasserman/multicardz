# multicardz™ Font Metric Override Optimization Proposal

**Document Number**: 033
**Date**: 2025-10-26
**Version**: 1
**Status**: Proposal
**Author**: System Architecture

---

## Executive Summary

This proposal addresses Lighthouse performance warnings regarding font loading strategy. Current implementation uses `font-display: block`, which delays First Contentful Paint (FCP) while custom fonts load. This document proposes a font metric override strategy that achieves:

- **Fast FCP**: Text renders immediately with dimensionally-matched system fonts
- **Zero Layout Shift**: Custom fonts swap in without affecting layout
- **Personalized Experience**: User-selected fonts still apply after FCP
- **Smooth Transition**: Optional CSS transitions for imperceptible font swap

**Expected Performance Impact**: 200-500ms improvement in FCP on slow connections.

---

## Problem Statement

### Current Implementation

The multicardz™ user application loads 7 custom fonts with `font-display: block`:

```css
@font-face {
    font-family: 'Mulish';
    src: url('/static/fonts/mulish-regular.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: block;  /* ← Blocks rendering */
}
```

**Font inventory**:
- Inconsolata (200 weight) - 37KB
- Lato (400 weight) - 23KB
- Libre Franklin (400 weight) - 16KB
- Merriweather Sans (300 weight) - 16KB
- Mulish (400 weight) - 13KB
- Roboto (400 weight) - 15KB
- Work Sans (400 weight) - 20KB

### Why `font-display: block` Is Problematic

**Behavior**:
1. Browser begins parsing HTML
2. Encounters font reference in CSS
3. **Blocks text rendering** until font downloads (up to 3 seconds)
4. Renders text with custom font

**Impact on Core Web Vitals**:
- **FCP delayed**: Text invisible until font loads (200-500ms on 3G)
- **User experience**: Blank page during font download
- **Lighthouse warning**: "Consider setting font-display to swap or optional"

### Why We Used `block` Initially

The `block` value was chosen to prevent **Flash of Unstyled Text (FOUT)** - the jarring visual shift when a system font swaps to a custom font with different dimensions. This is critical for multicardz™ because:

1. **Spatial precision**: Tag positions must not shift
2. **Card layout stability**: Content dimensions affect grid calculations
3. **Professional appearance**: Font swaps feel unpolished

---

## Proposed Solution: Font Metric Overrides

### Core Concept

**Font metric overrides** allow us to adjust a fallback system font to have the **exact same dimensions** as our custom fonts. This means:

1. **Initial render**: Text displays immediately in dimensionally-matched Arial/system-ui
2. **Custom font loads**: Swaps in with `font-display: swap`
3. **Zero layout shift**: Both fonts have identical metrics, so no reflow
4. **Optional transition**: Smooth visual transition for imperceptible swap

### How It Works

#### Step 1: Calculate Metric Adjustments

For each custom font, calculate how the fallback font needs to be adjusted:

```
Mulish metrics:
  - Advance width: X px at 16px
  - Ascent height: Y px
  - Descent depth: Z px
  - Line gap: W px

Arial metrics:
  - Advance width: X' px at 16px
  - Ascent height: Y' px
  - Descent depth: Z' px
  - Line gap: W' px

Adjustments needed:
  - size-adjust: (X / X') × 100%
  - ascent-override: (Y / height) × 100%
  - descent-override: (Z / height) × 100%
  - line-gap-override: (W / height) × 100%
```

#### Step 2: Define Adjusted Fallback Fonts

Create @font-face declarations for dimensionally-matched fallbacks:

```css
/* Fallback font adjusted to match Mulish dimensions */
@font-face {
    font-family: 'Mulish Fallback';
    src: local('Arial');
    size-adjust: 107.4%;      /* Make Arial 7.4% larger */
    ascent-override: 90%;     /* Match ascent to Mulish */
    descent-override: 22%;    /* Match descent to Mulish */
    line-gap-override: 0%;    /* Match line gap to Mulish */
}

/* The actual Mulish font with swap */
@font-face {
    font-family: 'Mulish';
    src: url('/static/fonts/mulish-regular.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: swap;  /* Changed from block */
}
```

#### Step 3: Update Font Stacks

Use fallback in font-family declarations:

```css
.font-avenir,
body.font-avenir {
    font-family: 'Mulish', 'Mulish Fallback', Arial, sans-serif;
}
```

#### Step 4: Add Smooth Transition (Optional)

Make font swap imperceptible with CSS transition:

```css
body {
    transition: font-family 300ms ease-out;
}

/* Or subtle opacity pulse */
@keyframes font-swap {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.98; }
}

.fonts-loaded {
    animation: font-swap 200ms ease-out;
}
```

---

## Technical Implementation

### Option 1: Simple (Recommended)

**What it does**: Pure CSS solution with metric overrides

**Implementation**:
1. Calculate metric overrides for all 7 fonts
2. Add fallback @font-face declarations with overrides
3. Change `font-display: block` → `font-display: swap`
4. Update font-family stacks to include fallback
5. Add CSS transition for smooth swap

**Pros**:
- No JavaScript required
- Fast FCP (text renders immediately)
- Zero layout shift (metrics match exactly)
- Works with server-side font preference loading

**Cons**:
- Users may notice font swap on slow connections (even with transition)
- Slightly more CSS (7 additional @font-face declarations)

**Code changes**: `apps/static/css/user.css` only

### Option 2: Advanced

**What it does**: Post-FCP font loading with Font Loading API

**Implementation**:
1. All of Option 1, plus:
2. Remove custom font classes from initial HTML
3. Use Font Loading API to load fonts after FCP
4. Apply custom font with class toggle
5. Use CSS transition for imperceptible swap

**Pros**:
- Fastest possible FCP (no custom fonts in critical path)
- Most control over swap timing
- Can prioritize fonts (load user's preference first)

**Cons**:
- Requires JavaScript
- More complex implementation
- Falls back to Option 1 if JS fails

**Code changes**: `apps/static/css/user.css` + `apps/static/js/app.js`

---

## Expected Performance Improvements

### Baseline (Current)

```
font-display: block
FCP: 1.2s (font load blocks rendering)
CLS: 0.00 (no shift, but slow FCP)
```

### Option 1 (Metric Overrides)

```
font-display: swap + metric overrides
FCP: 0.7s (text renders immediately)
CLS: 0.00 (metrics match, no shift)
Swap: ~1.2s (custom font replaces fallback)
```

**Improvement**: 500ms faster FCP

### Option 2 (Post-FCP Loading)

```
font-display: swap + post-FCP loading
FCP: 0.6s (system font only)
CLS: 0.00 (metrics match, no shift)
Swap: ~1.5s (custom font loads after FCP)
```

**Improvement**: 600ms faster FCP

---

## Metric Calculation Tools

### Recommended: Fontaine (Automatic)

```bash
# Install
npm install -g fontaine

# Run on font directory
fontaine /Users/adam/dev/multicardz/apps/static/fonts

# Output: JSON with calculated overrides
{
  "Mulish": {
    "fallback": "Arial",
    "sizeAdjust": "107.4%",
    "ascentOverride": "90%",
    "descentOverride": "22%",
    "lineGapOverride": "0%"
  }
}
```

### Alternative: Capsize (Manual)

Online tool at https://seek-oss.github.io/capsize/

1. Upload woff2 file
2. Select fallback font
3. Get calculated metrics

### Manual: FontForge (Expert)

For verification:
1. Open woff2 in FontForge
2. Check Element → Font Info → General → Metrics
3. Calculate overrides manually

---

## Implementation Roadmap

### Phase 1: Calculation (30 minutes)

1. Run Fontaine on all 7 fonts
2. Verify metrics with test page
3. Document overrides in spreadsheet

### Phase 2: CSS Updates (1 hour)

1. Add 7 fallback @font-face declarations
2. Update existing @font-face to use `font-display: swap`
3. Update font-family stacks
4. Add CSS transitions

### Phase 3: Testing (1 hour)

1. Test all 7 fonts with Chrome DevTools
2. Verify zero layout shift with Lighthouse
3. Check FCP improvement
4. Test on slow 3G throttling

### Phase 4: Deployment (30 minutes)

1. Deploy to staging
2. Run Lighthouse audit
3. Verify FCP improvement
4. Deploy to production

**Total estimated time**: 3 hours

---

## Integration with Current Architecture

### Server-Side Font Preference Loading

Current implementation in `apps/user/main.py`:

```python
# Load font preference from database
font_class = theme_settings.get('font_selector', '')
if font_selector and font_selector != 'font-system':
    font_class = font_selector
    font_preload_url = FONT_PRELOAD_MAP.get(font_selector, '')

# Pass to template
"font_class": font_class,
"font_preload_url": font_preload_url,
```

This continues to work with metric overrides:
- Font preference loads server-side ✓
- Correct font class applied to `<body>` ✓
- Font loads with swap instead of block ✓
- Fallback metrics prevent layout shift ✓

### Template Integration

Current `base.html`:

```html
<body class="{% if font_class %}{{ font_class }}{% endif %}">
```

No changes needed - fallback fonts work automatically through font-family stack.

---

## Risk Assessment

### Low Risk
- **CSS-only solution** (Option 1): No JavaScript, works everywhere
- **Backwards compatible**: Falls back gracefully to system fonts
- **Zero layout shift**: Metrics match exactly, no reflow

### Medium Risk
- **Font swap visibility**: Users on slow connections may notice swap
  - **Mitigation**: CSS transition makes swap subtle
  - **Mitigation**: Most users on fast connections won't notice

### Negligible Risk
- **Browser support**: Font metric overrides supported in all modern browsers (Chrome 87+, Safari 14.1+, Firefox 89+)
- **Calculation errors**: Fontaine is battle-tested, metrics verified visually

---

## Success Criteria

### Performance Metrics
- [ ] FCP improved by 200-500ms (measured with Lighthouse)
- [ ] CLS remains 0.00 (no layout shift)
- [ ] Font swap completes within 1.5s on 3G

### Visual Quality
- [ ] Zero visible layout shift during font swap
- [ ] Smooth transition (if using CSS transitions)
- [ ] All 7 fonts render correctly

### Compatibility
- [ ] Works with server-side font preference loading
- [ ] Works with all theme variations (light/dark/earth)
- [ ] Works on all target browsers

---

## Next Steps

1. **Decision**: Choose Option 1 (Simple) or Option 2 (Advanced)
2. **Calculation**: Run Fontaine to calculate metric overrides
3. **Implementation**: Update CSS with overrides
4. **Testing**: Verify FCP improvement and zero layout shift
5. **Deployment**: Ship to production

---

## Appendix A: Example Metric Override CSS

```css
/* Inconsolata Fallback (monospace) */
@font-face {
    font-family: 'Inconsolata Fallback';
    src: local('Courier New');
    size-adjust: 95.2%;
    ascent-override: 92%;
    descent-override: 24%;
    line-gap-override: 0%;
}

@font-face {
    font-family: 'Inconsolata';
    src: url('/static/fonts/inconsolata-regular.woff2') format('woff2');
    font-weight: 200;
    font-style: normal;
    font-display: swap;
}

.font-inconsolata,
body.font-inconsolata {
    font-family: 'Inconsolata', 'Inconsolata Fallback', 'Courier New', monospace;
    transition: font-family 300ms ease-out;
}

/* Lato Fallback */
@font-face {
    font-family: 'Lato Fallback';
    src: local('Arial');
    size-adjust: 102.8%;
    ascent-override: 95%;
    descent-override: 20%;
    line-gap-override: 0%;
}

@font-face {
    font-family: 'Lato';
    src: url('/static/fonts/lato-regular.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}

.font-lato,
body.font-lato {
    font-family: 'Lato', 'Lato Fallback', Arial, sans-serif;
    transition: font-family 300ms ease-out;
}

/* Repeat for remaining 5 fonts... */
```

---

## Appendix B: Font Loading API Example (Option 2)

```javascript
// Load custom fonts after FCP
if ('fonts' in document) {
    // Wait for FCP
    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
                // FCP happened, start loading custom font
                const userFont = document.body.className.match(/font-(\w+)/)?.[1];
                if (userFont && userFont !== 'system') {
                    loadCustomFont(userFont);
                }
            }
        }
    });
    observer.observe({ entryTypes: ['paint'] });
}

function loadCustomFont(fontName) {
    const fontMap = {
        'inconsolata': { family: 'Inconsolata', weight: 200 },
        'lato': { family: 'Lato', weight: 400 },
        'avenir': { family: 'Mulish', weight: 400 },
        // ... etc
    };

    const font = fontMap[fontName];
    if (font) {
        document.fonts.load(`${font.weight} 1em ${font.family}`).then(() => {
            document.body.classList.add('fonts-loaded');
        });
    }
}
```

---

## References

- **Fontaine**: https://github.com/unjs/fontaine
- **Capsize**: https://seek-oss.github.io/capsize/
- **font-display MDN**: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display
- **Font metric overrides**: https://developer.chrome.com/blog/font-fallbacks/
- **Font Loading API**: https://developer.mozilla.org/en-US/docs/Web/API/CSS_Font_Loading_API

---

**Document Status**: Proposal
**Review Required**: Technical Lead
**Implementation Priority**: Medium (Performance optimization)
**Estimated Effort**: 3 hours
**Impact**: High (200-500ms FCP improvement)
