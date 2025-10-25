/**
 * MultiCardz Conversion Tracking JavaScript
 *
 * Tracks conversion funnel progression:
 * - view: Page loaded
 * - cta_click: CTA button clicked
 * - account_create: Auth0 account created (tracked via webhook)
 * - activate: First card created (tracked via API)
 * - upgrade: Subscription created (tracked via Stripe webhook)
 *
 * Function-based architecture (no classes).
 * Integrates with analytics.js for session management.
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        API_ENDPOINT: '/api/analytics/conversion',
        BATCH_SIZE: 5,
        BATCH_INTERVAL: 5000,  // 5 seconds
        CTA_SELECTOR: '[data-cta]',
        FUNNEL_STAGES: ['view', 'cta_click', 'account_create', 'activate', 'upgrade']
    };

    // State
    let eventQueue = [];
    let batchTimer = null;
    let initialized = false;
    let initRetries = 0;
    const MAX_INIT_RETRIES = 50;  // 5 seconds max wait (50 * 100ms)

    /**
     * Get session ID from localStorage (set by analytics.js)
     */
    function getSessionId() {
        return localStorage.getItem('multicardz_session_id');
    }

    /**
     * Get landing page ID from page data
     */
    function getLandingPageId() {
        // Check for landing page ID in window data
        if (window.LANDING_PAGE_ID) {
            return window.LANDING_PAGE_ID;
        }

        // Check for landing page ID in meta tag
        const metaTag = document.querySelector('meta[name="landing-page-id"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        // Check for landing page ID in page data attribute
        const pageData = document.querySelector('[data-landing-page-id]');
        if (pageData) {
            return pageData.getAttribute('data-landing-page-id');
        }

        return null;
    }

    /**
     * Track a funnel stage event
     */
    function trackFunnelStage(stage, data = {}) {
        const sessionId = getSessionId();
        if (!sessionId) {
            console.warn('ConversionTracking: No session ID found');
            return;
        }

        const event = {
            session_id: sessionId,
            landing_page_id: getLandingPageId(),
            stage: stage,
            timestamp: Date.now(),
            data: data
        };

        eventQueue.push(event);

        // Check if we should submit batch
        if (eventQueue.length >= CONFIG.BATCH_SIZE) {
            flushEvents();
        } else if (!batchTimer) {
            // Start batch timer if not already running
            batchTimer = setTimeout(flushEvents, CONFIG.BATCH_INTERVAL);
        }
    }

    /**
     * Get element position relative to document
     */
    function getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: Math.round(rect.left + window.scrollX),
            y: Math.round(rect.top + window.scrollY)
        };
    }

    /**
     * Extract CTA metadata from button element
     */
    function extractCtaMetadata(element) {
        const ctaId = element.getAttribute('data-cta');
        const buttonText = element.textContent.trim();
        const position = getElementPosition(element);

        return {
            cta_id: ctaId,
            button_text: buttonText,
            position: position,
            href: element.getAttribute('href'),
            tag_name: element.tagName.toLowerCase()
        };
    }

    /**
     * Handle CTA click event
     */
    function handleCtaClick(event) {
        const element = event.target.closest(CONFIG.CTA_SELECTOR);
        if (!element) return;

        const metadata = extractCtaMetadata(element);
        trackFunnelStage('cta_click', metadata);
    }

    /**
     * Submit events to API
     */
    function submitEvents(events) {
        if (events.length === 0) return;

        const payload = {
            events: events
        };

        // Try sendBeacon first (works during page unload)
        if (navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            const success = navigator.sendBeacon(CONFIG.API_ENDPOINT, blob);
            if (success) return;
        }

        // Fallback to fetch
        fetch(CONFIG.API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            keepalive: true  // Keep request alive during page unload
        }).catch(err => {
            console.error('ConversionTracking: Failed to submit events', err);
        });
    }

    /**
     * Flush queued events immediately
     */
    function flushEvents() {
        if (batchTimer) {
            clearTimeout(batchTimer);
            batchTimer = null;
        }

        if (eventQueue.length === 0) return;

        const eventsToSubmit = eventQueue.slice();
        eventQueue = [];

        submitEvents(eventsToSubmit);
    }

    /**
     * Track page view (initial funnel stage)
     */
    function trackPageView() {
        const referrer = document.referrer;
        const urlParams = new URLSearchParams(window.location.search);

        const metadata = {
            url: window.location.href,
            referrer: referrer || null,
            utm_source: urlParams.get('utm_source'),
            utm_medium: urlParams.get('utm_medium'),
            utm_campaign: urlParams.get('utm_campaign'),
            utm_term: urlParams.get('utm_term'),
            utm_content: urlParams.get('utm_content')
        };

        trackFunnelStage('view', metadata);
    }

    /**
     * Initialize conversion tracking
     */
    function init() {
        if (initialized) return;

        const sessionId = getSessionId();
        if (!sessionId) {
            initRetries++;
            if (initRetries > MAX_INIT_RETRIES) {
                console.error('ConversionTracking: Failed to get session ID after max retries. Analytics may not be initialized.');
                return;
            }
            console.warn('ConversionTracking: Waiting for session ID from analytics.js');
            // Retry after a short delay
            setTimeout(init, 100);
            return;
        }

        initialized = true;

        // Track initial page view
        trackPageView();

        // Set up CTA click tracking using event delegation
        document.addEventListener('click', handleCtaClick, true);

        // Flush events before page unload
        window.addEventListener('beforeunload', flushEvents);
    }

    /**
     * Stop conversion tracking (cleanup)
     */
    function stop() {
        document.removeEventListener('click', handleCtaClick, true);
        window.removeEventListener('beforeunload', flushEvents);
        flushEvents();
        initialized = false;
    }

    /**
     * Get queued events (for testing)
     */
    function getQueuedEvents() {
        return eventQueue.slice();
    }

    /**
     * Get queue size (for testing)
     */
    function getQueueSize() {
        return eventQueue.length;
    }

    /**
     * Manual tracking API (for custom events)
     */
    function track(stage, data = {}) {
        if (!CONFIG.FUNNEL_STAGES.includes(stage)) {
            console.warn(`ConversionTracking: Unknown funnel stage "${stage}"`);
        }
        trackFunnelStage(stage, data);
    }

    // Public API
    window.ConversionTracking = {
        init: init,
        stop: stop,
        track: track,
        flush: flushEvents,
        getQueuedEvents: getQueuedEvents,
        getQueueSize: getQueueSize
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
