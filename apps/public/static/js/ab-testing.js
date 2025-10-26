/**
 * multicardz" A/B Testing JavaScript
 *
 * Handles:
 * - Fetching assigned variant for session
 * - Rendering variant content
 * - Tracking CTA clicks
 */

(function(window) {
    'use strict';

    /**
     * Initialize A/B testing for disclaimer.
     */
    async function initABTest() {
        // Get or create session ID (from analytics.js)
        const sessionId = window.multicardzAnalytics ?
            window.multicardzAnalytics().sessionId :
            localStorage.getItem('multicardz_session_id');

        if (!sessionId) {
            console.warn('A/B Testing: No session ID available');
            return;
        }

        // Get active tests
        try {
            const testsResponse = await fetch('/api/ab-test/active-tests');
            if (!testsResponse.ok) {
                console.error('Failed to fetch active tests');
                return;
            }

            const testsData = await testsResponse.json();
            const tests = testsData.tests;

            if (!tests || tests.length === 0) {
                console.log('A/B Testing: No active tests');
                return;
            }

            // Get the first active test (disclaimer test)
            const test = tests[0];
            const testId = test.id;
            const elementSelector = test.element_selector;

            // Get assigned variant
            const variantResponse = await fetch(
                `/api/ab-test/test/${testId}/variant?session_id=${sessionId}`
            );

            if (!variantResponse.ok) {
                console.error('Failed to fetch variant');
                return;
            }

            const variant = await variantResponse.json();

            // Render the variant
            renderVariant(elementSelector, variant);

            // Set up CTA click tracking
            setupCTATracking(sessionId, variant.variant_id);

        } catch (error) {
            console.error('A/B Testing error:', error);
        }
    }

    /**
     * Render variant content into the target element.
     *
     * @param {string} selector - CSS selector for target element
     * @param {object} variant - Variant data with content
     */
    function renderVariant(selector, variant) {
        const targetElement = document.querySelector(selector);

        if (!targetElement) {
            console.warn(`A/B Testing: Element not found: ${selector}`);
            return;
        }

        // Render HTML content from variant
        const html = variant.content.html || '';
        targetElement.innerHTML = html;

        // Show the element (in case it was hidden)
        targetElement.style.display = 'block';

        console.log(`A/B Testing: Rendered ${variant.variant_name}`);
    }

    /**
     * Set up click tracking for CTA links.
     *
     * @param {string} sessionId - Session ID
     * @param {string} variantId - Variant ID
     */
    function setupCTATracking(sessionId, variantId) {
        // Listen for clicks on CTA links with data-event="ab_features_cta"
        document.addEventListener('click', async function(event) {
            const target = event.target;

            // Check if clicked element or parent has the CTA event attribute
            let ctaElement = target;
            let depth = 0;

            while (ctaElement && depth < 5) {
                const eventType = ctaElement.getAttribute('data-event');

                if (eventType === 'ab_features_cta') {
                    // Track the conversion
                    await trackConversion(sessionId, variantId);

                    // Let the default link behavior happen (navigate to /features)
                    break;
                }

                ctaElement = ctaElement.parentElement;
                depth++;
            }
        });
    }

    /**
     * Track a conversion event (CTA click).
     *
     * @param {string} sessionId - Session ID
     * @param {string} variantId - Variant ID
     */
    async function trackConversion(sessionId, variantId) {
        try {
            const response = await fetch('/api/ab-test/conversion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    variant_id: variantId
                })
            });

            if (response.ok) {
                console.log('A/B Testing: Conversion tracked');
            } else {
                console.error('A/B Testing: Failed to track conversion');
            }
        } catch (error) {
            console.error('A/B Testing: Error tracking conversion:', error);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initABTest);
    } else {
        // DOM is already ready
        initABTest();
    }

    // Expose for debugging
    window.multicardzABTest = {
        init: initABTest
    };

})(window);
