"""
MultiCardz™ Cards API Router
Handles dynamic card rendering with validated input using the complete backend stack.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Tuple
import time
import logging

# Import models
from ..models.render_request import RenderRequest, TagsInPlay, ZoneData

# Import shared services (adjust paths as needed)
try:
    from apps.shared.services.set_operations_unified import apply_unified_operations
    from apps.shared.services.database_storage import (
        create_database_connection,
        load_all_card_summaries
    )
    from apps.shared.services.card_service import CardServiceCompat as CardService
except ImportError as e:
    logging.warning(f"Could not import shared services: {e}")

# Setup Jinja2 templates
templates_env = Environment(
    loader=FileSystemLoader("apps/static/templates"),
    autoescape=True
)

# Create router
router = APIRouter(prefix="/api/v2", tags=["cards"])

logger = logging.getLogger(__name__)


@router.post("/render/cards", response_class=HTMLResponse)
async def render_cards(request: Request):
    """
    Dynamic card rendering with fully validated input.
    Handles any number of zones with different behaviors.
    """
    start_time = time.perf_counter()

    try:
        # Parse and validate with Pydantic
        body = await request.json()
        render_request = RenderRequest(**body)
        tags_in_play = render_request.tagsInPlay
    except Exception as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    logger.info(f"Processing {len(tags_in_play.zones)} zones")

    # Process zones dynamically
    operations = []
    dimensional_zones = {}
    boost_tags = []
    exclude_tags = []
    temporal_filters = {}

    for zone_type, zone_data in tags_in_play.zones.items():
        if not zone_data.tags:  # Skip empty zones
            continue

        behavior = zone_data.metadata.behavior
        logger.debug(f"Processing zone {zone_type} with behavior {behavior} and {len(zone_data.tags)} tags")

        # Standard set operations
        if behavior == 'union' or zone_type == 'union':
            operations.append(('union', [(tag, 1) for tag in zone_data.tags]))

        elif behavior == 'intersection' or zone_type == 'intersection':
            operations.append(('intersection', [(tag, 1) for tag in zone_data.tags]))

        elif behavior == 'difference' or behavior == 'exclude':
            exclude_tags.extend(zone_data.tags)

        # Dimensional layout
        elif zone_type == 'row':
            dimensional_zones['row'] = zone_data.tags

        elif zone_type == 'column':
            dimensional_zones['column'] = zone_data.tags

        # Special behaviors
        elif behavior == 'boost':
            boost_tags.extend(zone_data.tags)

        elif behavior == 'temporal':
            temporal_range = zone_data.metadata.temporalRange
            if temporal_range:
                temporal_filters[temporal_range] = zone_data.tags

    # Add exclude operation if needed
    if exclude_tags:
        operations.append(('difference', [(tag, 1) for tag in exclude_tags]))

    try:
        # Load and filter cards using shared services
        with create_database_connection() as conn:
            all_cards = load_all_card_summaries(conn)

            # Apply temporal filters first if present
            if temporal_filters:
                all_cards = apply_temporal_filters(all_cards, temporal_filters)

            # Apply set operations if any
            if operations:
                logger.info(f"Applying {len(operations)} set operations")
                result = apply_unified_operations(
                    frozenset(all_cards),
                    operations,
                    processing_mode='auto'  # Let backend auto-select optimal mode
                )
                filtered_cards = list(result.cards)
                logger.info(f"Set operations completed: {len(filtered_cards)} cards result")
            elif tags_in_play.controls.startWithAllCards:
                filtered_cards = list(all_cards)
                logger.info(f"Showing all cards: {len(filtered_cards)}")
            else:
                filtered_cards = []
                logger.info("No operations and startWithAllCards=False, showing empty result")

            # Apply boost ranking if present
            if boost_tags and filtered_cards:
                filtered_cards = apply_boost_ranking(filtered_cards, boost_tags)
                logger.info(f"Applied boost ranking for {len(boost_tags)} boost tags")

    except Exception as e:
        logger.error(f"Error processing cards: {str(e)}")
        # Return empty result on error
        filtered_cards = []

    # Render appropriate view
    try:
        if dimensional_zones.get('row') or dimensional_zones.get('column'):
            html = render_dimensional_grid(
                filtered_cards,
                row_tags=dimensional_zones.get('row', []),
                column_tags=dimensional_zones.get('column', []),
                show_expanded=tags_in_play.controls.startWithCardsExpanded,
                show_colors=tags_in_play.controls.showColors
            )
        else:
            # Standard card grid
            template = templates_env.get_template('components/card_display.html')
            html = template.render(
                cards=filtered_cards,
                show_expanded=tags_in_play.controls.startWithCardsExpanded,
                show_colors=tags_in_play.controls.showColors,
                card_count=len(filtered_cards)
            )
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        # Fallback to simple HTML
        html = f"""
        <div class="card-container">
            <p>Found {len(filtered_cards)} cards</p>
            {render_simple_card_list(filtered_cards)}
        </div>
        """

    processing_time = (time.perf_counter() - start_time) * 1000
    logger.info(f"Request completed in {processing_time:.2f}ms")

    return HTMLResponse(html)


def apply_temporal_filters(cards, temporal_filters):
    """Apply temporal range filters to cards."""
    from datetime import datetime, timedelta

    if not temporal_filters:
        return cards

    filtered = []
    now = datetime.now()

    for card in cards:
        # Check if card has a date attribute
        card_date = getattr(card, 'created_at', None) or getattr(card, 'modified_at', None)
        if not card_date:
            continue

        for range_type, required_tags in temporal_filters.items():
            # Check if card has any of the required tags
            card_tags = getattr(card, 'tags', [])
            if isinstance(card_tags, str):
                # Handle JSON string tags
                import json
                try:
                    card_tags = json.loads(card_tags)
                except:
                    card_tags = []

            if not any(tag in card_tags for tag in required_tags):
                continue

            # Apply temporal filter
            if range_type == 'today':
                if card_date.date() == now.date():
                    filtered.append(card)
            elif range_type == 'week':
                if card_date >= now - timedelta(days=7):
                    filtered.append(card)
            elif range_type == 'month':
                if card_date.month == now.month and card_date.year == now.year:
                    filtered.append(card)

    return filtered if temporal_filters else cards


def apply_boost_ranking(cards, boost_tags):
    """Apply boost ranking to prioritize cards with certain tags."""
    def boost_score(card):
        score = 0
        card_tags = getattr(card, 'tags', [])
        if isinstance(card_tags, str):
            # Handle JSON string tags
            import json
            try:
                card_tags = json.loads(card_tags)
            except:
                card_tags = []

        for tag in boost_tags:
            if tag in card_tags:
                score += 10  # Boost weight
        return score

    # Sort by boost score (highest first), then by original order
    return sorted(cards, key=lambda card: (boost_score(card), 0), reverse=True)


def render_dimensional_grid(cards, row_tags=None, column_tags=None, **kwargs):
    """Render cards in a dimensional grid layout."""
    # This is a placeholder - implement dimensional rendering as needed
    try:
        template = templates_env.get_template('components/dimensional_grid.html')
        return template.render(
            cards=cards,
            row_tags=row_tags or [],
            column_tags=column_tags or [],
            **kwargs
        )
    except:
        # Fallback to simple list if dimensional template not found
        return render_simple_card_list(cards)


def render_simple_card_list(cards):
    """Simple fallback card rendering."""
    if not cards:
        return '<p class="empty-state">No cards to display</p>'

    html_parts = ['<div class="card-grid">']

    for card in cards[:100]:  # Limit for performance
        title = getattr(card, 'title', 'Untitled')
        card_id = getattr(card, 'id', '')
        tags = getattr(card, 'tags', [])

        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except:
                tags = []

        html_parts.append(f'''
        <div class="card" data-card-id="{card_id}">
            <h4 class="card-title">{title}</h4>
            <div class="card-tags">
                {" ".join(f'<span class="tag">{tag}</span>' for tag in tags[:5])}
            </div>
        </div>
        ''')

    html_parts.append('</div>')
    return ''.join(html_parts)


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for the cards API."""
    return {"status": "healthy", "service": "cards_api"}


# View restoration endpoint
@router.get("/views/{view_id}/restore")
async def restore_view(view_id: str):
    """
    Restore a saved view by returning its tagsInPlay configuration.
    The frontend JavaScript will rearrange tags based on this data.
    """
    # TODO: Load from database/storage based on view_id
    # For now, return example saved view
    example_saved_view = {
        "tagsInPlay": {
            "zones": {
                "union": {
                    "tags": ["javascript", "python"],
                    "metadata": {"behavior": "union"}
                },
                "intersection": {
                    "tags": ["react"],
                    "metadata": {"behavior": "intersection"}
                }
            },
            "controls": {
                "startWithAllCards": True,
                "showColors": True,
                "startWithCardsExpanded": False
            }
        }
    }

    logger.info(f"Restoring view {view_id}")
    return example_saved_view