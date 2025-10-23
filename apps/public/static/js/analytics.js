/**
 * multicardz™ Analytics JavaScript
 *
 * Self-hosted analytics tracking for landing pages.
 * Tracks sessions, page views, clicks, scroll depth, and conversion events.
 *
 * Function-based architecture (no classes).
 */

(function(window) {
    'use strict';

    /**
     * Create or retrieve session ID from localStorage.
     *
     * @returns {string} Session ID (UUID format)
     */
    function getOrCreateSessionId() {
        const storageKey = 'multicardz_session_id';
        let sessionId = localStorage.getItem(storageKey);

        if (!sessionId) {
            // Generate UUID v4
            sessionId = generateUUID();
            localStorage.setItem(storageKey, sessionId);
        }

        return sessionId;
    }

    /**
     * Generate UUID v4.
     *
     * @returns {string} UUID
     */
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Extract UTM parameters from URL.
     *
     * @returns {object} UTM parameters
     */
    function extractUTMParams() {
        const params = new URLSearchParams(window.location.search);

        return {
            utm_source: params.get('utm_source') || null,
            utm_medium: params.get('utm_medium') || null,
            utm_campaign: params.get('utm_campaign') || null,
            utm_term: params.get('utm_term') || null,
            utm_content: params.get('utm_content') || null
        };
    }

    /**
     * Get viewport dimensions.
     *
     * @returns {object} Width and height
     */
    function getViewportDimensions() {
        return {
            viewport_width: window.innerWidth || document.documentElement.clientWidth,
            viewport_height: window.innerHeight || document.documentElement.clientHeight
        };
    }

    /**
     * Create session data object.
     *
     * @param {string} sessionId - Session ID
     * @returns {object} Session data
     */
    function createSessionData(sessionId) {
        const utmParams = extractUTMParams();
        const viewport = getViewportDimensions();

        return {
            session_id: sessionId,
            referrer_url: document.referrer || null,
            ...utmParams,
            user_agent: navigator.userAgent,
            ...viewport,
            timestamp: Date.now()
        };
    }

    /**
     * Track page view event.
     *
     * @param {string} sessionId - Session ID
     * @returns {object} Page view data
     */
    function trackPageView(sessionId) {
        const viewport = getViewportDimensions();

        const pageViewData = {
            session_id: sessionId,
            url: window.location.href,
            referrer: document.referrer || null,
            ...viewport,
            timestamp: Date.now()
        };

        return pageViewData;
    }

    /**
     * Get element position on page.
     *
     * @param {HTMLElement} element - DOM element
     * @returns {object} X and Y coordinates
     */
    function getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        return {
            element_position_x: Math.round(rect.left + scrollLeft),
            element_position_y: Math.round(rect.top + scrollTop)
        };
    }

    /**
     * Get CSS selector for element.
     *
     * @param {HTMLElement} element - DOM element
     * @returns {string} CSS selector
     */
    function getElementSelector(element) {
        // Try ID first
        if (element.id) {
            return '#' + element.id;
        }

        // Try class
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/);
            if (classes.length > 0) {
                return '.' + classes[0];
            }
        }

        // Fall back to tag name
        return element.tagName.toLowerCase();
    }

    /**
     * Track click event.
     *
     * @param {string} sessionId - Session ID
     * @param {HTMLElement} element - Clicked element
     * @param {string} eventType - Event type (default: 'click')
     * @returns {object} Event data
     */
    function trackClickEvent(sessionId, element, eventType = 'click') {
        const position = getElementPosition(element);
        const selector = getElementSelector(element);

        const eventData = {
            session_id: sessionId,
            event_type: eventType,
            element_selector: selector,
            element_text: element.textContent.trim().substring(0, 100),
            ...position,
            timestamp_ms: Date.now()
        };

        return eventData;
    }

    /**
     * Calculate scroll depth percentage.
     *
     * @returns {number} Scroll depth (0-100)
     */
    function calculateScrollDepth() {
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(
            document.body.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.clientHeight,
            document.documentElement.scrollHeight,
            document.documentElement.offsetHeight
        );
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        const scrollableHeight = documentHeight - windowHeight;
        if (scrollableHeight <= 0) {
            return 100;
        }

        const scrollPercent = Math.round((scrollTop / scrollableHeight) * 100);
        return Math.min(100, Math.max(0, scrollPercent));
    }

    /**
     * Event batch buffer and submission.
     */
    let eventBuffer = [];
    let batchTimer = null;
    const BATCH_SIZE = 10;
    const BATCH_INTERVAL_MS = 5000;

    /**
     * Add event to buffer and trigger batch if needed.
     *
     * @param {object} eventData - Event data
     */
    function bufferEvent(eventData) {
        eventBuffer.push(eventData);

        // Trigger batch if size limit reached
        if (eventBuffer.length >= BATCH_SIZE) {
            submitBatch();
        } else if (!batchTimer) {
            // Set timer for time-based batching
            batchTimer = setTimeout(submitBatch, BATCH_INTERVAL_MS);
        }
    }

    /**
     * Submit batched events to API.
     */
    function submitBatch() {
        if (eventBuffer.length === 0) {
            return;
        }

        // Clear timer
        if (batchTimer) {
            clearTimeout(batchTimer);
            batchTimer = null;
        }

        // Get events and clear buffer
        const eventsToSend = eventBuffer.slice();
        eventBuffer = [];

        // Send to API
        sendToAPI('/api/analytics/events/batch', {
            events: eventsToSend,
            count: eventsToSend.length
        });
    }

    /**
     * Send data to analytics API.
     *
     * @param {string} endpoint - API endpoint
     * @param {object} data - Data to send
     */
    function sendToAPI(endpoint, data) {
        // Use sendBeacon if available (more reliable on page unload)
        if (navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
            navigator.sendBeacon(endpoint, blob);
        } else {
            // Fallback to fetch
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                keepalive: true
            }).catch(err => {
                console.error('Analytics API error:', err);
            });
        }
    }

    /**
     * Initialize analytics tracking.
     *
     * @returns {object} Analytics instance
     */
    function MulticardzAnalytics() {
        // Create or retrieve session
        const sessionId = getOrCreateSessionId();
        const sessionData = createSessionData(sessionId);

        // Track page view
        const pageViewData = trackPageView(sessionId);

        // Send session and page view to API
        sendToAPI('/api/analytics/session', sessionData);
        sendToAPI('/api/analytics/page-view', pageViewData);

        // Track scroll depth
        let maxScrollDepth = 0;
        let scrollTimeout = null;

        window.addEventListener('scroll', function() {
            const currentDepth = calculateScrollDepth();

            if (currentDepth > maxScrollDepth) {
                maxScrollDepth = currentDepth;

                // Debounce scroll tracking
                if (scrollTimeout) {
                    clearTimeout(scrollTimeout);
                }

                scrollTimeout = setTimeout(function() {
                    bufferEvent({
                        session_id: sessionId,
                        event_type: 'scroll',
                        scroll_depth: maxScrollDepth,
                        timestamp_ms: Date.now()
                    });
                }, 500);
            }
        });

        // Track clicks on CTA buttons
        document.addEventListener('click', function(event) {
            const target = event.target;

            // Check if clicked element or parent has CTA class
            let ctaElement = target;
            let depth = 0;

            while (ctaElement && depth < 5) {
                if (ctaElement.classList &&
                    (ctaElement.classList.contains('cta-button') ||
                     ctaElement.classList.contains('cta-link') ||
                     ctaElement.hasAttribute('data-event'))) {

                    const eventType = ctaElement.getAttribute('data-event') || 'cta_click';
                    const eventData = trackClickEvent(sessionId, ctaElement, eventType);
                    bufferEvent(eventData);
                    break;
                }

                ctaElement = ctaElement.parentElement;
                depth++;
            }
        });

        // Submit any remaining events before page unload
        window.addEventListener('beforeunload', function() {
            submitBatch();
        });

        // Return public API
        return {
            sessionId: sessionId,
            trackEvent: function(eventType, element) {
                const eventData = trackClickEvent(sessionId, element, eventType);
                bufferEvent(eventData);
            },
            getScrollDepth: function() {
                return maxScrollDepth;
            },
            flushEvents: submitBatch
        };
    }

    // Expose to window
    window.MulticardzAnalytics = MulticardzAnalytics;

})(window);
