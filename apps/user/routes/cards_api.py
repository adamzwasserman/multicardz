"""
MultiCardz™ Cards API Router
Handles dynamic card rendering with validated input using the complete backend stack.
"""

import json
import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

# Import models
from ..models.render_request import RenderRequest

# Import shared services (adjust paths as needed)
try:
    from apps.shared.services.card_service import CardServiceCompat as CardService
    from apps.shared.services.card_service import create_database_config
    from apps.shared.services.database_storage import (
        create_database_connection,
        load_all_card_summaries,
    )
    from apps.shared.services.set_operations_unified import apply_unified_operations
except ImportError as e:
    logging.warning(f"Could not import shared services: {e}")

# Setup Jinja2 templates
templates_env = Environment(
    loader=FileSystemLoader("apps/static/templates"),
    autoescape=True
)

# Create router
router = APIRouter(prefix="/api", tags=["cards"])

logger = logging.getLogger(__name__)

# Import single source of truth for database path
from apps.shared.config.database import DATABASE_PATH

# Create default database configuration using single source of truth
DEFAULT_DB_CONFIG = create_database_config(
    db_path=DATABASE_PATH,
    enable_foreign_keys=True,
    timeout=30.0,
    check_same_thread=False,
    max_attachment_size_mb=10
)


# ============================================================================
# PURE FUNCTION: Data Layer (Set Operations)
# ============================================================================

def compute_card_sets(
    tags_in_play,
    user_id: str = "default-user",
    workspace_id: str = "default-workspace",
    db_path: Path = DATABASE_PATH
) -> dict:
    """
    Pure function to compute card sets from tag operations.

    Returns data structures, NOT HTML.

    Args:
        tags_in_play: TagsInPlay model with zones and controls
        user_id: User identifier for workspace isolation
        workspace_id: Workspace identifier for data isolation
        db_path: Database path

    Returns:
        dict with keys:
            - filtered_cards: list of cards matching set operations
            - all_cards: list of all cards before filtering
            - dimensional_zones: dict with 'row' and 'column' tags
            - operations: list of operations applied
            - lesson_state: current lesson state
            - metadata: dict with processing info
    """
    start_time = time.perf_counter()

    # Process zones dynamically
    operations = []
    dimensional_zones = {}
    dimensional_tags = []  # Collect all dimensional tags for single union
    union_tags = []  # Collect all union zone tags
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
            # Collect union tags instead of creating operation immediately
            union_tags.extend(zone_data.tags)

        elif behavior == 'intersection' or zone_type == 'intersection':
            operations.append(('intersection', [(tag, 1) for tag in zone_data.tags]))

        elif behavior == 'difference' or behavior == 'exclude':
            exclude_tags.extend(zone_data.tags)

        elif behavior == 'exclusion' or zone_type == 'exclusion':
            # EXCLUSION: Cards with NONE of the specified tags
            operations.append(('exclusion', [(tag, 1) for tag in zone_data.tags]))

        # Dimensional layout (also acts as union for card selection)
        elif zone_type == 'row':
            dimensional_zones['row'] = zone_data.tags
            # Row tags contribute to dimensional card selection
            dimensional_tags.extend(zone_data.tags)

        elif zone_type == 'column':
            dimensional_zones['column'] = zone_data.tags
            # Column tags contribute to dimensional card selection
            dimensional_tags.extend(zone_data.tags)

        # Special behaviors
        elif behavior == 'boost':
            boost_tags.extend(zone_data.tags)

        elif behavior == 'temporal':
            temporal_range = zone_data.metadata.temporalRange
            if temporal_range:
                temporal_filters[temporal_range] = zone_data.tags

    # Merge union tags and dimensional tags into single union operation
    all_union_tags = union_tags + dimensional_tags
    if all_union_tags:
        operations.insert(0, ('union', [(tag, 1) for tag in all_union_tags]))

    # Add exclude operation if needed
    if exclude_tags:
        operations.append(('difference', [(tag, 1) for tag in exclude_tags]))

    # Load and filter cards using shared services
    with create_database_connection(create_database_config(db_path=db_path)) as conn:
        # Load lesson cards specifically for onboarding
        from apps.shared.services.lesson_service import (
            detect_lesson_progression,
            get_default_lesson_state,
        )

        lesson_state = get_default_lesson_state()

        # Check for current lesson from the frontend request
        current_lesson_from_request = tags_in_play.controls.__dict__.get('currentLesson') if hasattr(tags_in_play, 'controls') else None
        if not current_lesson_from_request and hasattr(tags_in_play, '__dict__'):
            current_lesson_from_request = tags_in_play.__dict__.get('currentLesson')

        current_lesson = current_lesson_from_request or lesson_state.get('current_lesson', 1)
        lesson_state['current_lesson'] = current_lesson

        logger.info(f"Loading cards for lesson {current_lesson}")

        # Load cards from new schema (zero-trust)
        cards_query = """
            SELECT card_id, name, tags, created, modified
            FROM cards
            WHERE user_id = ? AND workspace_id = ? AND deleted IS NULL
        """

        cursor = conn.execute(cards_query, (user_id, workspace_id))
        lesson_cards = []

        for row in cursor.fetchall():
            card_id, name, tags_inverted_index, created, modified = row

            logger.info(f"DB READ: card_id={card_id}, name={name}")

            # Parse tags from inverted index and lookup tag names
            tag_names = []
            if tags_inverted_index:
                tag_uuids = tags_inverted_index.split(",")
                placeholders = ",".join("?" * len(tag_uuids))
                tag_cursor = conn.execute(
                    f"SELECT tag FROM tags WHERE tag_id IN ({placeholders}) AND deleted IS NULL",
                    tag_uuids
                )
                tag_names = [row[0] for row in tag_cursor.fetchall()]

            # Create CardSummary-like object
            card = type('CardSummary', (), {
                'id': card_id,
                'title': name,
                'tags': frozenset(tag_names),
                'created_at': created,
                'modified_at': modified,
                'has_attachments': False
            })()
            logger.info(f"CARD OBJECT: id={card.id}, title={card.title}, tags={card.tags}")
            lesson_cards.append(card)

        all_cards = lesson_cards
        logger.info(f"Loaded {len(all_cards)} cards")

        # Apply temporal filters first if present
        if temporal_filters:
            all_cards = apply_temporal_filters(all_cards, temporal_filters)

        # Apply set operations if any
        if operations:
            logger.info(f"Applying {len(operations)} set operations")
            result = apply_unified_operations(
                frozenset(all_cards),
                operations
            )
            filtered_cards = list(result.cards)
            logger.info(f"Set operations completed: {len(filtered_cards)} cards result")
        elif tags_in_play.controls.startWithAllCards:
            filtered_cards = list(all_cards)
            logger.info(f"Showing all cards (lesson-filtered): {len(filtered_cards)}")
        else:
            # When startWithAllCards is false, show cards with "always_visible" tag
            always_visible_cards = [card for card in all_cards if hasattr(card, 'tags') and 'always_visible' in card.tags]
            filtered_cards = always_visible_cards
            logger.info(f"No operations, showing {len(filtered_cards)} always_visible cards")

        # Apply boost ranking if present
        if boost_tags and filtered_cards:
            filtered_cards = apply_boost_ranking(filtered_cards, boost_tags)
            logger.info(f"Applied boost ranking for {len(boost_tags)} boost tags")

        # Detect lesson progression after operations are complete
        current_zone_state = {"zones": {}}
        for zone_type, zone_data in tags_in_play.zones.items():
            current_zone_state["zones"][zone_type] = {"tags": zone_data.tags}

        # Check for lesson progression and update state
        updated_lesson_state, new_criteria = detect_lesson_progression(
            {},  # Previous state not tracked yet, but could be added
            current_zone_state,
            lesson_state
        )

        if new_criteria:
            logger.info(f"Lesson progression detected: {new_criteria}")

    processing_time = (time.perf_counter() - start_time) * 1000

    return {
        'filtered_cards': filtered_cards,
        'all_cards': all_cards,
        'dimensional_zones': dimensional_zones,
        'operations': operations,
        'lesson_state': updated_lesson_state,
        'metadata': {
            'processing_time_ms': processing_time,
            'card_count': len(filtered_cards),
            'total_cards': len(all_cards),
            'operations_count': len(operations)
        }
    }


# ============================================================================
# ROUTE HANDLER: Presentation Layer (HTML Rendering)
# ============================================================================

@router.post("/render/cards", response_class=HTMLResponse)
async def render_cards(request: Request):
    """
    Route handler for card rendering (Presentation Layer).

    This function:
    1. Validates request (Pydantic)
    2. Calls pure compute_card_sets() function (Data Layer)
    3. Renders HTML from data (Presentation Layer)
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

    # Get database path from controls or use default
    db_path = Path(tags_in_play.controls.databasePath) if tags_in_play.controls.databasePath else DATABASE_PATH
    logger.info(f"Using database: {db_path}")

    # CALL PURE FUNCTION: Compute card sets (returns data, not HTML)
    try:
        result = compute_card_sets(
            tags_in_play,
            user_id="default-user",  # TODO: Get from auth
            workspace_id="default-workspace",  # TODO: Get from auth
            db_path=db_path
        )
        filtered_cards = result['filtered_cards']
        dimensional_zones = result['dimensional_zones']
    except Exception as e:
        logger.error(f"Error computing card sets: {str(e)}")
        # Return empty result on error
        filtered_cards = []
        dimensional_zones = {}

    # Render appropriate view - ALWAYS use dimensional grid
    try:
        # Always use dimensional grid (single cell when no row/column tags)
        html = render_dimensional_grid(
            filtered_cards,
            row_tags=dimensional_zones.get('row', []),
            column_tags=dimensional_zones.get('column', []),
            show_expanded=tags_in_play.controls.startWithCardsExpanded,
            show_colors=tags_in_play.controls.showColors,
            color_palette=getattr(tags_in_play.controls, 'colorPalette', 'muji')
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
    logger.info(f"Rendering dimensional grid: {len(cards)} cards, rows={row_tags}, cols={column_tags}")

    # Convert Card objects to template-friendly dicts and compute tag order
    template_cards = []
    all_tags = set()

    for card in cards:
        # Convert frozenset tags to list for template
        tags = list(card.tags) if hasattr(card, 'tags') else []
        card_id = getattr(card, 'id', '')
        card_title = getattr(card, 'title', 'Untitled')

        # Collect all unique tags
        all_tags.update(tags)

        logger.info(f"Card {card_id}: title={card_title}, tags={tags}")

        template_card = {
            'id': card_id,
            'title': card_title,
            'tags': tags,
            'created_at': getattr(card, 'created_at', ''),
            'modified_at': getattr(card, 'modified_at', ''),
        }
        template_cards.append(template_card)

    # Sort tags alphabetically to match frontend tag cloud order
    tag_order = sorted(list(all_tags))

    logger.info(f"Converted {len(template_cards)} cards to template format")
    logger.info(f"Tag order for color assignment (alphabetical): {tag_order}")

    try:
        template = templates_env.get_template('components/dimensional_grid.html')
        html = template.render(
            cards=template_cards,
            row_tags=row_tags or [],
            column_tags=column_tags or [],
            tag_order=tag_order,
            **kwargs
        )
        logger.info(f"Successfully rendered dimensional grid HTML ({len(html)} chars)")
        return html
    except Exception as e:
        logger.error(f"Error rendering dimensional grid: {e}", exc_info=True)
        # Fallback to simple list if template rendering fails
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


# ============================================================================
# Zero-Trust API Routes with Workspace Isolation
# ============================================================================

async def get_workspace_context(
    authorization: str = Header(...),
    x_workspace_id: str = Header(...),
    x_user_id: str = Header(...)
) -> tuple[str, str]:
    """
    Extract and validate workspace context.

    Pure function for context extraction.
    """
    # Validate token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth")

    return x_workspace_id, x_user_id


@router.get("/cards", response_model=list[dict])
async def get_cards(
    context: tuple[str, str] = Depends(get_workspace_context),
    skip: int = 0,
    limit: int = 100
) -> list[dict]:
    """
    Get cards for workspace with isolation.

    Endpoint with automatic workspace scoping.
    """
    start_time = time.perf_counter()
    workspace_id, user_id = context

    try:
        # Import database connection service
        from apps.shared.services.database_connection import get_workspace_connection

        with get_workspace_connection(workspace_id, user_id) as conn:
            cursor = conn.execute(
                """
                SELECT card_id, name, description, tag_ids, created, modified
                FROM cards
                WHERE workspace_id = ? AND user_id = ? AND deleted IS NULL
                ORDER BY created DESC
                LIMIT ? OFFSET ?
                """,
                (workspace_id, user_id, limit, skip)
            )

            cards = []
            for row in cursor:
                cards.append({
                    "card_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "tag_ids": json.loads(row[3]) if row[3] else [],
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "created": row[4],
                    "modified": row[5]
                })

        elapsed = time.perf_counter() - start_time
        if elapsed > 0.1:
            logger.warning(f"Get cards took {elapsed:.3f}s")

        return cards

    except Exception as e:
        logger.error(f"Error getting cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cards", response_model=dict)
async def create_card(
    request: Request,
    context: tuple[str, str] = Depends(get_workspace_context)
) -> dict:
    """
    Create card with automatic workspace assignment.

    Ensures workspace isolation even if not provided.
    """
    workspace_id, user_id = context

    try:
        # Parse card data
        card_data = await request.json()

        # Force workspace context
        card_data["workspace_id"] = workspace_id
        card_data["user_id"] = user_id

        # Import services
        import uuid

        from apps.shared.services.database_connection import get_workspace_connection
        from apps.shared.services.tag_count_maintenance import create_card_with_counts

        # Generate card_id if not provided
        if "card_id" not in card_data:
            card_data["card_id"] = str(uuid.uuid4())

        with get_workspace_connection(workspace_id, user_id) as conn:
            card_id = await create_card_with_counts(
                card_data,
                db_connection=conn
            )

            # Fetch and return created card
            cursor = conn.execute(
                "SELECT card_id, name, description, tag_ids, created, modified FROM cards WHERE card_id = ?",
                (card_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=500, detail="Card created but not found")

            return {
                "card_id": row[0],
                "name": row[1],
                "description": row[2],
                "tag_ids": json.loads(row[3]) if row[3] else [],
                "user_id": user_id,
                "workspace_id": workspace_id,
                "created": row[4],
                "modified": row[5]
            }

    except Exception as e:
        logger.error(f"Error creating card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating card: {str(e)}")


@router.get("/cards/{card_id}", response_model=dict)
async def get_card(
    card_id: str,
    context: tuple[str, str] = Depends(get_workspace_context)
) -> dict:
    """
    Get single card with workspace validation.

    Prevents cross-workspace data access.
    """
    workspace_id, user_id = context

    try:
        from apps.shared.services.database_connection import get_workspace_connection

        with get_workspace_connection(workspace_id, user_id) as conn:
            cursor = conn.execute(
                """
                SELECT card_id, name, description, tag_ids, created, modified
                FROM cards
                WHERE card_id = ? AND workspace_id = ? AND user_id = ?
                """,
                (card_id, workspace_id, user_id)
            )

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Card not found")

            return {
                "card_id": row[0],
                "name": row[1],
                "description": row[2],
                "tag_ids": json.loads(row[3]) if row[3] else [],
                "user_id": user_id,
                "workspace_id": workspace_id,
                "created": row[4],
                "modified": row[5]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting card {card_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Lesson-related endpoints
@router.get("/lessons/options", response_class=HTMLResponse)
async def get_lesson_options(request: Request):
    """Get lesson selector options as HTML."""
    try:
        # Import lesson service functions
        from apps.shared.services.lesson_service import (
            get_default_lesson_state,
            get_lesson_selector_options,
        )

        # Get default lesson state (in production, this would come from user session/database)
        lesson_state = get_default_lesson_state()

        # Check for completed lessons from query params (sent by frontend localStorage)
        completed_param = request.query_params.get('completed')
        if completed_param:
            try:
                import json
                completed_lessons = json.loads(completed_param)
                lesson_state['completed_lessons'] = completed_lessons
                lesson_state['achieved_criteria'] = []

                # Add criteria based on completed lessons
                if 1 in completed_lessons:
                    lesson_state['achieved_criteria'].append('tag_in_union_zone')
                if 2 in completed_lessons:
                    lesson_state['achieved_criteria'].append('two_tags_in_union')
                if 3 in completed_lessons:
                    lesson_state['achieved_criteria'].append('tag_in_intersection')
            except (json.JSONDecodeError, ValueError):
                pass

        options = get_lesson_selector_options(lesson_state)

        # Generate HTML options
        html_options = []
        for option in options:
            selected = 'selected="selected"' if option.get('selected') else ''
            duration = option.get('duration', 60)
            description = option.get('description', '')

            # Format duration for display
            if duration >= 60:
                duration_text = f"{duration//60}m"
            else:
                duration_text = f"{duration}s"

            html_options.append(f'''
                <option value="{option['value']}" {selected} data-duration="{duration}" title="{description}">
                    {option['label']} ({duration_text})
                </option>
            ''')

        return HTMLResponse(''.join(html_options))

    except Exception as e:
        logger.error(f"Error loading lesson options: {str(e)}")
        # Return fallback options
        return HTMLResponse('''
            <option value="1" selected="selected">🔄 Lesson 1: Basic Dragging (30s)</option>
            <option value="production">🚀 Production Mode</option>
        ''')


@router.post("/lessons/switch")
async def switch_lesson(request: Request):
    """Switch to a different lesson."""
    try:
        body = await request.json()
        lesson_id = body.get('lessonId')

        # Import lesson service functions
        from apps.shared.services.lesson_service import (
            change_lesson,
            get_default_lesson_state,
        )

        # Get current lesson state (in production, this would come from user session)
        current_state = get_default_lesson_state()

        # Change lesson
        if lesson_id == "production":
            new_state = change_lesson(current_state, "production")
        else:
            new_state = change_lesson(current_state, int(lesson_id))

        # TODO: Save lesson state to user session/database

        return {"status": "success", "lesson_state": new_state}

    except Exception as e:
        logger.error(f"Error switching lesson: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error switching lesson: {str(e)}")


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
                },
                "exclusion": {
                    "tags": ["deprecated", "archived"],
                    "metadata": {"behavior": "exclusion"}
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


@router.get("/lessons/hint", response_class=HTMLResponse)
async def get_lesson_hint(request: Request):
    """Get current lesson hint text."""
    try:
        from apps.shared.services.lesson_service import (
            create_lesson_hint_text,
            get_default_lesson_state,
        )

        # Get current lesson state
        lesson_state = get_default_lesson_state()

        # Check for completed lessons from query params (sent by frontend localStorage)
        completed_param = request.query_params.get('completed')
        if completed_param:
            try:
                import json
                completed_lessons = json.loads(completed_param)
                lesson_state['completed_lessons'] = completed_lessons
                lesson_state['achieved_criteria'] = []

                # Add criteria based on completed lessons
                if 1 in completed_lessons:
                    lesson_state['achieved_criteria'].append('tag_in_union_zone')
                if 2 in completed_lessons:
                    lesson_state['achieved_criteria'].append('two_tags_in_union')
                if 3 in completed_lessons:
                    lesson_state['achieved_criteria'].append('tag_in_intersection')
            except (json.JSONDecodeError, ValueError):
                pass

        # Get query parameters for current zone state
        zone_union = request.query_params.getlist('union')
        zone_intersection = request.query_params.getlist('intersection')
        zone_exclusion = request.query_params.getlist('exclusion')

        # Build zone state from query params
        zone_state = {
            "zones": {
                "union": {"tags": zone_union},
                "intersection": {"tags": zone_intersection},
                "exclusion": {"tags": zone_exclusion}
            }
        }

        # Create hint text
        hint_text = create_lesson_hint_text(lesson_state, zone_state)

        if hint_text:
            return HTMLResponse(hint_text)
        else:
            return HTMLResponse("drag a <em>tag</em> to a <em>zone</em> to see the cards that have that tag")

    except Exception as e:
        logger.error(f"Error getting lesson hint: {str(e)}")
        return HTMLResponse("drag a <em>tag</em> to a <em>zone</em> to see the cards that have that tag")


@router.post("/cards/update-title")
async def update_card_title(request: Request):
    """Update a card's title."""
    from pydantic import BaseModel
    from apps.shared.repositories import CardRepository

    class UpdateTitleRequest(BaseModel):
        card_id: str
        title: str
        workspace_id: str = "default-workspace"  # TODO: Get from session

    try:
        data = await request.json()
        req = UpdateTitleRequest(**data)

        card_repo = CardRepository()
        success = card_repo.update_title(req.card_id, req.workspace_id, req.title)

        if success:
            return {"success": True, "message": "Title updated"}
        else:
            raise HTTPException(status_code=404, detail="Card not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating card title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/update-content")
async def update_card_content(request: Request):
    """Update a card's description/content."""
    from pydantic import BaseModel
    from apps.shared.repositories import CardRepository

    class UpdateContentRequest(BaseModel):
        card_id: str
        content: str
        workspace_id: str = "default-workspace"  # TODO: Get from session

    try:
        data = await request.json()
        req = UpdateContentRequest(**data)

        card_repo = CardRepository()
        success = card_repo.update_content(req.card_id, req.workspace_id, req.content)

        if success:
            return {"success": True, "message": "Content updated"}
        else:
            raise HTTPException(status_code=404, detail="Card not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating card content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/add-tag")
async def add_tag_to_card(request: Request):
    """Add a tag to a card (using zero-trust inverted index)."""
    from pydantic import BaseModel
    from apps.shared.repositories import CardRepository

    class AddTagRequest(BaseModel):
        card_id: str  # UUID
        tag_id: str  # UUID
        workspace_id: str = "default-workspace"  # TODO: Get from session

    try:
        data = await request.json()
        req = AddTagRequest(**data)

        card_repo = CardRepository()
        success = card_repo.add_tag(req.card_id, req.workspace_id, req.tag_id)

        if success:
            return {"success": True, "message": "Tag added"}
        else:
            return {"success": False, "message": "Card not found or tag already on card"}
    except Exception as e:
        logger.error(f"Error adding tag to card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/remove-tag")
async def remove_tag_from_card(request: Request):
    """Remove a tag from a card (using zero-trust inverted index)."""
    from pydantic import BaseModel
    from apps.shared.repositories import CardRepository

    class RemoveTagRequest(BaseModel):
        card_id: str  # UUID
        tag_id: str  # UUID
        workspace_id: str = "default-workspace"  # TODO: Get from session

    try:
        data = await request.json()
        req = RemoveTagRequest(**data)

        card_repo = CardRepository()
        success = card_repo.remove_tag(req.card_id, req.workspace_id, req.tag_id)

        if success:
            return {"success": True, "message": "Tag removed"}
        else:
            return {"success": False, "message": "Card not found or tag not on card"}
    except Exception as e:
        logger.error(f"Error removing tag from card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/counts")
async def get_tag_counts():
    """Get current card_count for all non-deleted tags."""
    from apps.shared.repositories import TagRepository

    try:
        tag_repo = TagRepository()
        workspace_id = "default-workspace"  # TODO: Get from session
        counts = tag_repo.get_counts(workspace_id)
        return {"counts": counts}
    except Exception as e:
        logger.error(f"Error fetching tag counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/create")
async def create_card(request: Request):
    """Create a new card with tags (using zero-trust schema)."""
    import uuid
    from pydantic import BaseModel
    from apps.shared.repositories import CardRepository

    class CreateCardRequest(BaseModel):
        name: str
        description: str = ""
        tag_ids: list[str] = []  # List of tag UUIDs
        user_id: str = "default-user"  # TODO: Get from auth
        workspace_id: str = "default-workspace"  # TODO: Get from session

    try:
        data = await request.json()
        req = CreateCardRequest(**data)

        card_id = str(uuid.uuid4())
        card_repo = CardRepository()

        # Create card using repository
        card = card_repo.create(
            card_id=card_id,
            name=req.name,
            workspace_id=req.workspace_id,
            tag_ids=req.tag_ids
        )

        return {"success": True, "card_id": card["card_id"], "message": "Card created"}
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/delete")
async def delete_card(request: Request):
    """Delete a card (soft delete by setting deleted timestamp)."""
    from apps.shared.repositories import CardRepository

    data = await request.json()
    card_id = data.get("card_id")
    workspace_id = "default-workspace"  # TODO: Get from session

    try:
        card_repo = CardRepository()
        success = card_repo.soft_delete(card_id, workspace_id)

        if success:
            logger.info(f"Card deleted: {card_id}")
            return {"success": True, "message": "Card deleted"}
        else:
            return {"success": False, "message": "Card not found"}

    except Exception as e:
        logger.error(f"Failed to delete card: {e}")
        return {"success": False, "message": str(e)}


def _flatten_preferences_for_frontend(prefs: dict) -> dict:
    """Flatten nested preferences structure for frontend consumption."""
    view_settings = prefs.get('view_settings') or {}
    theme_settings = prefs.get('theme_settings') or {}
    tag_settings = prefs.get('tag_settings') or {}
    workspace_settings = prefs.get('workspace_settings') or {}

    return {
        'startWithAllCards': view_settings.get('cards_start_visible', True),
        'startWithCardsExpanded': view_settings.get('cards_start_expanded', False),
        'showColors': view_settings.get('show_tag_colors', True),
        'colorPalette': view_settings.get('color_palette', 'muji'),
        'verticalLayout': view_settings.get('tag_layout', 'horizontal') == 'vertical',
        'advancedView': tag_settings.get('separate_user_ai_tags', True),
        'fontSelector': f"font-{theme_settings.get('font_family', 'Inter').lower()}",
        'zoneLayout': workspace_settings.get('zone_layout', {}),
        'collapsedSections': workspace_settings.get('collapsed_sections', []),
        'collapsedRows': workspace_settings.get('collapsed_rows', []),
        'collapsedColumns': workspace_settings.get('collapsed_columns', []),
        'leftControlWidth': workspace_settings.get('left_control_width', 120),
        'rightControlWidth': workspace_settings.get('right_control_width', 120),
    }


@router.get("/user/preferences")
async def get_user_preferences(request: Request):
    """Get user preferences from database."""
    import json
    import sqlite3
    from pathlib import Path

    user_id = "default-user"  # TODO: Get from session/auth
    db_path = Path("/Users/adam/dev/multicardz/data/multicardz_dev.db")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                # Return existing preferences - flatten for frontend
                prefs = json.loads(row[0])
                flattened = _flatten_preferences_for_frontend(prefs)
                logger.info(f"Loaded preferences for user {user_id}: {flattened}")
                return flattened
            else:
                # Return defaults from model
                from apps.shared.models.user_preferences import UserPreferences, ViewSettings, ThemeSettings, TagSettings, WorkspaceSettings

                default_prefs = UserPreferences(
                    user_id=user_id,
                    view_settings=ViewSettings(),
                    theme_settings=ThemeSettings(),
                    tag_settings=TagSettings(),
                    workspace_settings=WorkspaceSettings()
                )

                prefs_dict = default_prefs.model_dump(mode='json')
                flattened = _flatten_preferences_for_frontend(prefs_dict)
                logger.info(f"Returning default preferences for user {user_id}")
                return flattened

    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/preferences")
async def save_user_preferences(request: Request):
    """Save/update user preferences to database."""
    import json
    import sqlite3
    from datetime import datetime
    from pathlib import Path
    from apps.shared.models.user_preferences import UserPreferences, ViewSettings, ThemeSettings, TagSettings, WorkspaceSettings

    user_id = "default-user"  # TODO: Get from session/auth
    db_path = Path("/Users/adam/dev/multicardz/data/multicardz_dev.db")

    try:
        data = await request.json()

        # Map frontend keys to model structure
        frontend_to_model = {
            'startWithAllCards': ('view_settings', 'cards_start_visible'),
            'startWithCardsExpanded': ('view_settings', 'cards_start_expanded'),
            'showColors': ('view_settings', 'show_tag_colors'),
            'colorPalette': ('view_settings', 'color_palette'),
            'verticalLayout': ('view_settings', 'tag_layout'),  # boolean -> "vertical"/"horizontal"
            'advancedView': ('tag_settings', 'separate_user_ai_tags'),
            'fontSelector': ('theme_settings', 'font_family'),
            'zoneLayout': ('workspace_settings', 'zone_layout'),  # dict of zone positions
            'collapsedSections': ('workspace_settings', 'collapsed_sections'),  # list of collapsed section IDs
            'collapsedRows': ('workspace_settings', 'collapsed_rows'),  # list of collapsed row numbers
            'collapsedColumns': ('workspace_settings', 'collapsed_columns'),  # list of collapsed column numbers
            'leftControlWidth': ('workspace_settings', 'left_control_width'),  # left panel width in pixels
            'rightControlWidth': ('workspace_settings', 'right_control_width'),  # right panel width in pixels
        }

        # Load existing preferences or create defaults
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                prefs_dict = json.loads(row[0])
            else:
                # Create default structure
                default_prefs = UserPreferences(
                    user_id=user_id,
                    view_settings=ViewSettings(),
                    theme_settings=ThemeSettings(),
                    tag_settings=TagSettings(),
                    workspace_settings=WorkspaceSettings()
                )
                prefs_dict = default_prefs.model_dump(mode='json')

            # Update with new values
            for frontend_key, value in data.items():
                if frontend_key in frontend_to_model:
                    section, field = frontend_to_model[frontend_key]

                    # Special handling for verticalLayout boolean -> tag_layout string
                    if frontend_key == 'verticalLayout':
                        value = "vertical" if value else "horizontal"

                    # Special handling for fontSelector - extract font name from class
                    if frontend_key == 'fontSelector':
                        # value like "font-inconsolata" -> "Inconsolata"
                        value = value.replace('font-', '').replace('-', ' ').title().replace(' ', '')

                    prefs_dict[section][field] = value
                    logger.info(f"Updated {section}.{field} = {value}")

            # Update timestamp
            prefs_dict['updated_at'] = datetime.utcnow().isoformat()

            # Upsert to database
            prefs_json = json.dumps(prefs_dict)
            cursor.execute("""
                INSERT INTO user_preferences (user_id, preferences_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    preferences_json = excluded.preferences_json,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, prefs_json))
            conn.commit()

            logger.info(f"Saved preferences for user {user_id}")
            return {"success": True, "preferences": prefs_dict}

    except Exception as e:
        logger.error(f"Failed to save user preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

