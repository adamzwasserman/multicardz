/**
 * multicardz™ Mouse Tracking JavaScript
 *
 * Records mouse movements and clicks for session replay.
 * Implements efficient sampling and batching for minimal performance impact.
 *
 * Function-based architecture (no classes).
 */

(function(window) {
    'use strict';

    /**
     * Configuration for mouse tracking.
     */
    const DEFAULT_SAMPLE_RATE_MS = 100;  // 10 samples per second
    const DEFAULT_BATCH_SIZE = 50;       // Send every 50 positions
    const DEFAULT_BATCH_INTERVAL_MS = 10000;  // Or every 10 seconds

    /**
     * Check if user has Do Not Track enabled.
     *
     * @returns {boolean} True if DNT is enabled
     */
    function isDoNotTrackEnabled() {
        return navigator.doNotTrack === '1' ||
               window.doNotTrack === '1' ||
               navigator.msDoNotTrack === '1';
    }

    /**
     * Get scroll offsets for document-relative coordinates.
     *
     * @returns {object} Scroll X and Y offsets
     */
    function getScrollOffsets() {
        return {
            scrollX: window.pageXOffset || document.documentElement.scrollLeft || 0,
            scrollY: window.pageYOffset || document.documentElement.scrollTop || 0
        };
    }

    /**
     * Convert viewport coordinates to document-relative coordinates.
     *
     * @param {number} viewportX - X coordinate in viewport
     * @param {number} viewportY - Y coordinate in viewport
     * @returns {object} Document-relative coordinates
     */
    function viewportToDocumentCoords(viewportX, viewportY) {
        const scroll = getScrollOffsets();

        return {
            x: Math.round(viewportX + scroll.scrollX),
            y: Math.round(viewportY + scroll.scrollY)
        };
    }

    /**
     * Create compact mouse position object.
     *
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @param {number} timestamp - Timestamp in milliseconds
     * @param {boolean} isClick - Whether this is a click event
     * @returns {object} Mouse position object
     */
    function createMousePosition(x, y, timestamp, isClick = false) {
        const position = {
            x: x,
            y: y,
            t: timestamp  // Shortened key for bandwidth efficiency
        };

        if (isClick) {
            position.c = 1;  // Mark as click
        }

        return position;
    }

    /**
     * Initialize mouse tracking.
     *
     * @param {object} options - Configuration options
     * @returns {object} Mouse tracking instance
     */
    function MulticardzMouseTracking(options = {}) {
        // Configuration
        const sampleRate = options.sampleRate || DEFAULT_SAMPLE_RATE_MS;
        const batchSize = options.batchSize || DEFAULT_BATCH_SIZE;
        const batchInterval = options.batchInterval || DEFAULT_BATCH_INTERVAL_MS;
        const sessionId = options.sessionId;
        const pageViewId = options.pageViewId;

        // Check privacy settings
        const respectDNT = options.respectDoNotTrack !== false;
        if (respectDNT && isDoNotTrackEnabled()) {
            console.log('Mouse tracking disabled: Do Not Track is enabled');
            return {
                enabled: false,
                stop: function() {},
                flush: function() {}
            };
        }

        // State
        let enabled = true;
        let positionBuffer = [];
        let lastSampleTime = 0;
        let batchTimer = null;

        /**
         * Sample mouse position (throttled).
         *
         * @param {MouseEvent} event - Mouse event
         */
        function sampleMousePosition(event) {
            if (!enabled) return;

            const currentTime = Date.now();

            // Throttle sampling based on sample rate
            if (currentTime - lastSampleTime < sampleRate) {
                return;
            }

            lastSampleTime = currentTime;

            // Convert to document coordinates
            const coords = viewportToDocumentCoords(event.clientX, event.clientY);

            // Add to buffer
            const position = createMousePosition(coords.x, coords.y, currentTime);
            positionBuffer.push(position);

            // Check if batch should be sent
            if (positionBuffer.length >= batchSize) {
                sendBatch();
            } else if (!batchTimer) {
                // Start timer for time-based batching
                batchTimer = setTimeout(sendBatch, batchInterval);
            }
        }

        /**
         * Track mouse click.
         *
         * @param {MouseEvent} event - Click event
         */
        function trackClick(event) {
            if (!enabled) return;

            const currentTime = Date.now();

            // Convert to document coordinates
            const coords = viewportToDocumentCoords(event.clientX, event.clientY);

            // Add click to buffer (marked as click)
            const clickPosition = createMousePosition(coords.x, coords.y, currentTime, true);
            positionBuffer.push(clickPosition);

            // Clicks may trigger immediate batch (optional)
            // For now, follow normal batching rules
        }

        /**
         * Send batched mouse positions to API.
         */
        function sendBatch() {
            if (positionBuffer.length === 0) {
                return;
            }

            // Clear timer
            if (batchTimer) {
                clearTimeout(batchTimer);
                batchTimer = null;
            }

            // Get positions and clear buffer
            const positionsToSend = positionBuffer.slice();
            positionBuffer = [];

            // Send to API
            const data = {
                session_id: sessionId,
                page_view_id: pageViewId,
                positions: positionsToSend,
                timestamp: Date.now()
            };

            sendToAPI('/api/analytics/mouse-tracking', data);
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
                    console.error('Mouse tracking API error:', err);
                });
            }
        }

        /**
         * Stop mouse tracking.
         */
        function stop() {
            enabled = false;

            // Flush any remaining positions
            sendBatch();

            // Remove event listeners
            document.removeEventListener('mousemove', sampleMousePosition);
            document.removeEventListener('click', trackClick);

            // Clear timer
            if (batchTimer) {
                clearTimeout(batchTimer);
                batchTimer = null;
            }
        }

        // Attach event listeners
        document.addEventListener('mousemove', sampleMousePosition, { passive: true });
        document.addEventListener('click', trackClick, { passive: true });

        // Flush on page unload
        window.addEventListener('beforeunload', function() {
            sendBatch();
        });

        // Public API
        return {
            enabled: true,
            stop: stop,
            flush: sendBatch,
            getBufferSize: function() {
                return positionBuffer.length;
            },
            getSampleRate: function() {
                return sampleRate;
            }
        };
    }

    // Expose to window
    window.MulticardzMouseTracking = MulticardzMouseTracking;

})(window);
