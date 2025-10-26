"""
Smart Routing Service.

Provides functions for:
- Detecting referrer sources and routing to appropriate landing pages
- Extracting competitor names from referrer URLs and search queries
- UTM parameter-based routing
- Default fallback routing
"""

import re
from typing import Optional
from urllib.parse import urlparse, parse_qs


# Competitor keyword mapping
COMPETITOR_KEYWORDS = {
    'trello': 'trello-performance',
    'notion': 'notion-performance',
    'asana': 'trello-performance',  # Similar to Trello
    'monday': 'trello-performance',  # Similar to Trello
    'clickup': 'trello-performance',  # Similar to Trello
    'airtable': 'notion-performance',  # Similar to Notion
}

# Domain-based routing
DOMAIN_ROUTING = {
    'trello.com': 'trello-performance',
    'notion.so': 'notion-performance',
    'notion.com': 'notion-performance',
    'asana.com': 'trello-performance',
    'monday.com': 'trello-performance',
    'clickup.com': 'trello-performance',
    'airtable.com': 'notion-performance',
}

# UTM campaign routing patterns
UTM_CAMPAIGN_PATTERNS = {
    'trello': 'trello-performance',
    'notion': 'notion-performance',
    'refugee': 'trello-performance',  # Default for refugees
}

# Default landing page
DEFAULT_LANDING_PAGE = 'cross-platform-operations'


def route_by_referrer(
    referrer_url: Optional[str],
    referrer_domain: Optional[str],
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None
) -> dict:
    """
    Determine the best landing page based on referrer and UTM data.

    Priority:
    1. UTM campaign matching
    2. Referrer domain matching
    3. Search query keyword extraction
    4. Default fallback

    Args:
        referrer_url: Full referrer URL
        referrer_domain: Extracted referrer domain
        utm_source: UTM source parameter
        utm_medium: UTM medium parameter
        utm_campaign: UTM campaign parameter

    Returns:
        dict with 'slug' and 'reason' keys
    """
    # Priority 1: UTM campaign routing
    if utm_campaign:
        slug = _route_by_utm_campaign(utm_campaign)
        if slug:
            return {'slug': slug, 'reason': 'utm_campaign'}

    # Priority 2: Direct referrer domain matching
    if referrer_domain:
        slug = _route_by_domain(referrer_domain)
        if slug:
            return {'slug': slug, 'reason': 'referrer_domain'}

    # Priority 3: Search query keyword extraction
    if referrer_url:
        slug = _route_by_search_query(referrer_url)
        if slug:
            return {'slug': slug, 'reason': 'search_query'}

    # Priority 4: Default routing
    if not referrer_url:
        return {'slug': DEFAULT_LANDING_PAGE, 'reason': 'direct'}

    return {'slug': DEFAULT_LANDING_PAGE, 'reason': 'default'}


def _route_by_utm_campaign(utm_campaign: str) -> Optional[str]:
    """
    Route based on UTM campaign parameter.

    Args:
        utm_campaign: The UTM campaign string

    Returns:
        Landing page slug, or None if no match
    """
    utm_lower = utm_campaign.lower()

    # Check exact patterns
    for pattern, slug in UTM_CAMPAIGN_PATTERNS.items():
        if pattern in utm_lower:
            return slug

    return None


def _route_by_domain(referrer_domain: str) -> Optional[str]:
    """
    Route based on referrer domain.

    Args:
        referrer_domain: The referrer domain

    Returns:
        Landing page slug, or None if no match
    """
    domain_lower = referrer_domain.lower()

    # Check exact domain matches
    for domain, slug in DOMAIN_ROUTING.items():
        if domain in domain_lower:
            return slug

    return None


def _route_by_search_query(referrer_url: str) -> Optional[str]:
    """
    Extract search query and route based on keywords.

    Supports Google, Bing, DuckDuckGo, etc.

    Args:
        referrer_url: Full referrer URL

    Returns:
        Landing page slug, or None if no match
    """
    try:
        parsed = urlparse(referrer_url)

        # Check if it's a search engine
        if not _is_search_engine(parsed.netloc):
            return None

        # Extract query parameter
        query_params = parse_qs(parsed.query)

        # Different search engines use different query parameters
        query_text = None
        if 'q' in query_params:  # Google, DuckDuckGo
            query_text = query_params['q'][0]
        elif 'query' in query_params:  # Bing
            query_text = query_params['query'][0]
        elif 'p' in query_params:  # Yahoo
            query_text = query_params['p'][0]

        if not query_text:
            return None

        query_lower = query_text.lower()

        # Check for competitor keywords
        for keyword, slug in COMPETITOR_KEYWORDS.items():
            if keyword in query_lower:
                return slug

        return None

    except Exception:
        return None


def _is_search_engine(domain: str) -> bool:
    """
    Check if domain is a search engine.

    Args:
        domain: The domain to check

    Returns:
        True if search engine, False otherwise
    """
    search_engines = [
        'google.com',
        'bing.com',
        'yahoo.com',
        'duckduckgo.com',
        'baidu.com',
        'yandex.com',
        'ask.com'
    ]

    domain_lower = domain.lower()
    return any(se in domain_lower for se in search_engines)


def get_landing_page_for_competitor(competitor_name: str) -> Optional[str]:
    """
    Get landing page slug for a competitor name.

    Args:
        competitor_name: The competitor name (e.g., "Trello", "Notion")

    Returns:
        Landing page slug, or None if not found
    """
    competitor_lower = competitor_name.lower()
    return COMPETITOR_KEYWORDS.get(competitor_lower)
