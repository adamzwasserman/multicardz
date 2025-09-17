"""FastAPI WebApp Auth0 integration for MultiCardz User Site"""

import json
import os
import pathlib
import sqlite3

# Import centralized logging system
import sys
import time
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from urllib.parse import quote_plus, urlencode

from authlib.integrations.starlette_client import OAuth
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config.database_config import (
    get_database_base_path,
    get_workspace_database_path,
)

# Add the packages/shared/src path to Python path for imports
current_dir = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import checkbox dispatch system
try:
    from backend.models.checkbox import (
        CheckboxDispatchRequest,
        CheckboxDispatchResponse,
    )
    from backend.services.checkbox.dispatcher import dispatch_checkbox
except ImportError as e:
    print(f"Warning: Checkbox dispatch imports not available: {e}")
    dispatch_checkbox = None
    CheckboxDispatchRequest = None
    CheckboxDispatchResponse = None

# Import available services
try:
    from services.lifespan import (
        get_tier_info,
        health_check,
    )
    from services.lifespan import (
        lifespan as tier_aware_lifespan,
    )
except ImportError:
    # Create minimal fallbacks for missing services
    @asynccontextmanager
    async def tier_aware_lifespan(app):
        print("INFO: Using fallback lifespan manager")
        yield

    async def health_check():
        return {"status": "ok", "lifespan": "fallback"}

    def get_tier_info():
        return {"tier": "development", "mode": "fallback"}


try:
    from services.render_optimized import render_card_display_optimized
except ImportError:

    async def render_card_display_optimized(*args, **kwargs):
        return "<div>Render service unavailable</div>"


# Import our new filtering service
try:
    from domain.api_models import (
        PartitionedCard,
        RenderCardsRequest,
        RenderCardsResponse,
    )

    from services.data_access import get_user_cards
    from services.filtering import filter_cards_intersection_first
except ImportError as e:
    print(f"Warning: Could not import filtering services: {e}")

    # Define placeholder functions to prevent undefined name errors
    def filter_cards_intersection_first(*args, **kwargs):
        return set(), None

    def filter_cards_by_intersection(tags):
        return set()

    def filter_cards_by_union(tags, restricted_universe=None):
        return set()

    def partition_cards_by_columns(cards, tags):
        return {}, set()

    def partition_cards_by_rows(cards, tags):
        return {}, set()

    RenderCardsRequest = None
    RenderCardsResponse = None
    PartitionedCard = None
    get_user_cards = None


try:
    from services.logging_config import get_logger

    logger = get_logger(__name__)
    pass  # Centralized logging system loaded successfully
except ImportError:
    pass  # Failed to import centralized logging, using fallback

    # Fallback to simple debug logging
    class FakeLogger:
        def focus(self, message):
            print(f"FOCUS: {message}")  # Enable focus logging

        def info(self, message):
            print(f"INFO: {message}")  # Enable info logging

        def error(self, message):
            print(f"ERROR: {message}")  # Enable error logging

    logger = FakeLogger()

# Create minimal replacements for missing dependencies
try:
    from api.tag_search import router as tag_search_router
except ImportError:
    from fastapi import APIRouter

    tag_search_router = APIRouter()

# Create minimal dependency types
try:
    from dependencies import CustomerID, DatabaseConnection
except ImportError:
    from typing import Annotated

    from fastapi import Depends

    def get_database_connection():
        # Use dynamic database connection based on current selection
        import sqlite3

        global CURRENT_DATABASE
        try:
            db_path = get_workspace_database_path(CURRENT_DATABASE)
            return sqlite3.connect(str(db_path))
        except:
            # Fallback to tutorial database if current selection fails
            tutorial_path = get_workspace_database_path("tutorial_customer")
            return sqlite3.connect(str(tutorial_path))

    def get_customer_id():
        return "tutorial_customer"

    DatabaseConnection = Annotated[object, Depends(get_database_connection)]
    CustomerID = Annotated[str, Depends(get_customer_id)]


# Tutorial tag display mapping
def load_tutorial_tag_display():
    """Load tutorial tag display names for user-friendly interface."""
    try:
        # Navigate from packages/shared/src/backend/core.py to packages/shared/data/customers/
        # Use configuration-based path for tutorial display file
        workspace_path = get_workspace_database_path("tutorial_customer")
        tutorial_display_path = workspace_path.parent / "tutorial_tag_display.json"
        with open(tutorial_display_path) as f:
            data = json.load(f)
            return data.get("tutorial_tag_display", {})
    except Exception as e:
        logger.error(f"Failed to load tutorial tag display: {e}")
        return {}


TUTORIAL_TAG_DISPLAY = load_tutorial_tag_display()

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Environment Configuration
TESTING_MODE = os.getenv("TESTING_MODE", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-key-change-in-production")

# Security check - disable testing in production
if ENVIRONMENT == "production" and TESTING_MODE:
    TESTING_MODE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event with tier-aware initialization."""
    # Use tier-aware lifespan handler
    async with tier_aware_lifespan(app):
        # Legacy index initialization (for backward compatibility)
        try:
            logger.info("Initializing legacy inverted index for compatibility...")
            initialize_inverted_index(expand_dataset=(DATASET_SIZE == "500k"))
            logger.info(f"Legacy index ready with {len(TAG_TO_CARD_IDS)} unique tags")
        except Exception as e:
            logger.warning(f"Legacy index initialization failed: {e}")

        # Check JIT status if available
        if hasattr(sys.flags, "jit"):
            logger.info(
                f"JIT Compiler Status: {'ENABLED' if sys.flags.jit else 'DISABLED'}"
            )
        else:
            logger.info(
                "JIT Compiler: NOT AVAILABLE (Python build without JIT support)"
            )

        yield


app = FastAPI(title="MultiCardz User Site", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET_KEY)

app.include_router(tag_search_router)

templates = Jinja2Templates(
    directory="/Users/adam/dev/cardz/packages/user-site/templates"
)

# Mount static files for CSS
app.mount(
    "/static",
    StaticFiles(directory="/Users/adam/dev/cardz/packages/user-site/static"),
    name="static",
)

# Inverted index for O(1) tag lookups - populated at startup
TAG_TO_CARD_IDS = defaultdict(set)  # {tag: {card_id1, card_id2, ...}}
CARD_ID_TO_CARD = {}  # {card_id: card_dict}
ALL_CARDS = []  # Full card list
_INITIALIZED = False  # One-time initialization flag

# Database switching globals
CURRENT_DATABASE = "tutorial_customer"
DATABASE_BASE_PATH = str(get_database_base_path() / "customers") + "/"


# Load tag data from database with dataset selection
def load_tag_data(expand_dataset=False, dataset_name=None):
    """Load cards and calculate tag counts from database"""
    if dataset_name is None:
        dataset_name = CURRENT_DATASET

    try:
        # Use direct database connection
        try:
            from dependencies import get_database_connection
        except ImportError:
            try:
                # #DISABLED: from .dependencies import get_database_connection  # REMOVED: relative import
                # Use the global fallback function defined at module level
                pass
            except ImportError:
                # Use the already defined fallback function
                pass

        db = get_database_connection()
        try:
            # Get all cards and tags for the specified dataset
            cursor = db.execute(
                """
                SELECT c.id, c.title, c.description, GROUP_CONCAT(t.tag_name, ',') as tags
                FROM cards c
                JOIN datasets d ON c.dataset_id = d.id
                LEFT JOIN tags t ON c.id = t.card_id
                WHERE d.name = ?
                GROUP BY c.id, c.title, c.description
            """,
                (dataset_name,),
            )

            cards_data = cursor.fetchall()

            # Convert to the format expected by the rest of the system
            cards = []
            for row in cards_data:
                card = {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "tags": row[3].split(",") if row[3] else [],
                }
                cards.append(card)
        finally:
            db.close()

        # If 50k mode is enabled, expand the dataset
        if expand_dataset and len(cards) > 10:
            # Keep first 5 and last 5 cards as-is, duplicate the middle cards 1000 times
            first_5 = cards[:5]
            last_5 = cards[-5:]
            middle_cards = cards[5:-5]

            # Create 1000 copies of each middle card
            expanded_cards = first_5[:]
            for card in middle_cards:
                for _ in range(1000):
                    expanded_cards.append(card.copy())
            expanded_cards.extend(last_5)

            cards = expanded_cards

        # Count tags from all cards using SET THEORY for efficient processing
        tag_counter = Counter()
        for card in cards:
            # Convert card tags to set to ensure uniqueness per card, then iterate
            card_tag_set = set(card.get("tags", []))
            for tag in card_tag_set:
                if tag.strip():  # Only count non-empty tags
                    tag_counter[tag] += 1

        return tag_counter
    except Exception as e:
        logger.error(f"Error loading tag data for dataset {dataset_name}: {e}")
        return Counter()


# Load card data from database with dataset selection
def load_card_data(expand_dataset=False, dataset_name=None):
    """Load actual card data (not just tag counts) with optional expansion"""
    if dataset_name is None:
        dataset_name = CURRENT_DATASET

    try:
        # Use direct database connection
        try:
            from dependencies import get_database_connection
        except ImportError:
            try:
                # #DISABLED: from .dependencies import get_database_connection  # REMOVED: relative import
                # Use the global fallback function defined at module level
                pass
            except ImportError:
                # Use the already defined fallback function
                pass

        db = get_database_connection()
        try:
            # Get all cards and tags for the specified dataset
            cursor = db.execute(
                """
                SELECT c.id, c.title, c.description, GROUP_CONCAT(t.tag_name, ',') as tags
                FROM cards c
                JOIN datasets d ON c.dataset_id = d.id
                LEFT JOIN tags t ON c.id = t.card_id
                WHERE d.name = ?
                GROUP BY c.id, c.title, c.description
            """,
                (dataset_name,),
            )

            cards_data = cursor.fetchall()

            # Convert to the format expected by the rest of the system
            cards = []
            for row in cards_data:
                card = {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "tags": row[3].split(",") if row[3] else [],
                }
                cards.append(card)
        finally:
            db.close()

        # If 50k mode is enabled, expand the dataset
        if expand_dataset and len(cards) > 10:
            # Keep first 5 and last 5 cards as-is, duplicate the middle cards 1000 times
            first_5 = cards[:5]
            last_5 = cards[-5:]
            middle_cards = cards[5:-5]

            # Create 1000 copies of each middle card
            expanded_cards = first_5[:]
            for card in middle_cards:
                for _ in range(1000):
                    expanded_cards.append(card.copy())
            expanded_cards.extend(last_5)

            cards = expanded_cards

        return cards
    except Exception as e:
        logger.error(f"Error loading card data for dataset {dataset_name}: {e}")
        return []


# Global dataset state
CURRENT_DATASET = "fintech-pm"  # Default to fintech dataset
DATASET_SIZE = "50"

# Global toggle mode state has been removed as part of unified tag mode implementation

# Load tag counts on startup with default dataset
TAG_COUNTS = load_tag_data(dataset_name=CURRENT_DATASET)


def initialize_inverted_index(expand_dataset=False):
    """Initialize inverted index for O(1) tag lookups.

    This function precomputes tag-to-card mappings at startup,
    eliminating the need for O(N) loops over cards during requests.

    Args:
        expand_dataset: Whether to use 500k expanded dataset
    """
    global TAG_TO_CARD_IDS, CARD_ID_TO_CARD, ALL_CARDS, TAG_COUNTS, _INITIALIZED

    logger.info(f"Initializing inverted index with expand_dataset={expand_dataset}")
    start_time = time.time()

    # Load all cards once using current dataset
    ALL_CARDS = load_card_data(
        expand_dataset=expand_dataset, dataset_name=CURRENT_DATASET
    )

    # Clear existing index
    TAG_TO_CARD_IDS.clear()
    CARD_ID_TO_CARD.clear()

    # Build inverted index
    for card in ALL_CARDS:
        # Convert tags to frozenset for immutability and hashing
        card_tags = frozenset(card.get("tags", []))
        card["tags"] = card_tags  # Store as frozenset in card object

        # Use Python's id() for unique card identification
        card_id = id(card)
        CARD_ID_TO_CARD[card_id] = card

        # Map each tag to this card's ID
        for tag in card_tags:
            TAG_TO_CARD_IDS[tag].add(card_id)

    # Update tag counts
    TAG_COUNTS = load_tag_data(
        expand_dataset=expand_dataset, dataset_name=CURRENT_DATASET
    )

    _INITIALIZED = True

    elapsed = time.time() - start_time
    logger.info(
        f"Inverted index initialized in {elapsed:.2f}s - {len(ALL_CARDS)} cards, {len(TAG_TO_CARD_IDS)} unique tags"
    )

    return len(ALL_CARDS)


oauth = OAuth()

# Mock user data for testing (compatible with templates)
MOCK_USER_DATA = {
    "access_token": "mock_access_token_12345",
    "id_token": "mock_id_token_67890",
    "scope": "openid profile email",
    "expires_in": 86400,
    "token_type": "Bearer",
    "expires_at": int(time.time()) + 86400,
    "userinfo": {
        "given_name": "Test",
        "family_name": "User",
        "nickname": "testuser",
        "name": "Test User",
        "picture": "https://via.placeholder.com/150?text=Test+User",
        "updated_at": "2025-08-06T14:47:40.598Z",
        "email": "test@multicardz.com",
        "email_verified": True,
        "sub": "test-user-123",
    },
}

oauth.register(
    name="auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration",
)


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, connection: DatabaseConnection, customer_id: CustomerID
):
    user = request.session.get("user")

    # Use actual server-side state for toggles instead of hardcoded defaults
    global DATASET_SIZE
    logger.focus(f"HOME ROUTE: DATASET_SIZE = {DATASET_SIZE}")

    # Load zone positions from database for persistence
    zone_layout = {"top": [], "left": [], "right": [], "bottom": []}
    try:
        # Load zones even without authentication for testing
        if True:  # Changed from: if user
            logger.focus(f"DEBUG: Starting zone loading for customer {customer_id}")
            try:
                from services.zone_positioning import (
                    get_all_zones,
                    organize_zones_by_position,
                )
            except ImportError:
                try:
                    pass  # Relative import disabled
                except ImportError:
                    # Fallback functions
                    def get_all_zones(customer_id, connection):
                        return []

                    def organize_zones_by_position(zones):
                        return {"zones": zones}

            zones = get_all_zones(customer_id, connection)
            logger.focus(
                f"DEBUG: get_all_zones returned {len(zones) if zones else 0} zones for customer {customer_id}"
            )
            for zone in zones or []:
                logger.focus(
                    f"DEBUG: Zone {zone.get('zone_id')} at position {zone.get('position')}"
                )

            if zones:
                zone_layout = organize_zones_by_position(zones)
                logger.focus("DEBUG: organize_zones_by_position completed")

            logger.focus(
                f"Loaded zone layout: {[(pos, [z['zone_id'] for z in zones_in_pos]) for pos, zones_in_pos in zone_layout.items() if zones_in_pos]}"
            )
    except Exception as e:
        logger.error(f"Failed to load zone positions: {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continue with default layout

    # Generate initial color style tag (empty since no drop zone tags initially)
    initial_color_style = generate_color_style_tag({}, False)

    # EMERGENCY BYPASS: Provide tutorial tags for frontend display
    emergency_tutorial_tags = [
        "1. Drag me to ANY zone",
        "tutorial",
        "beginner",
        "step-1",
        "python",
        "backend",
        "api",
        "testing",
    ]

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "session": user,
            "pretty": json.dumps(user, indent=4) if user else None,
            # Mode toggle context removed - unified tag mode implementation
            "color_style_tag": initial_color_style,
            # Dataset toggle context - use actual server state
            "dataset_toggle_type": "dataset",
            "dataset_toggle_state": DATASET_SIZE,
            "dataset_toggle_id": "dataset-toggle",
            "dataset_toggle_endpoint": "/api/dataset/toggle",
            "dataset_container_id": "dataset-toggle-container",
            "dataset_toggle_label": "Toggle between 50 and 500k dataset",
            # Current dataset for use cases selector
            "current_dataset": CURRENT_DATASET,
            # Zone layout for persistence
            "zone_layout": zone_layout,
            # Emergency tutorial tags for frontend display
            "available_tags": emergency_tutorial_tags,
        },
    )


@app.get("/callback")
async def callback(request: Request):
    token = await oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return RedirectResponse(url="/")


@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("callback")
    return await oauth.auth0.authorize_redirect(request, redirect_uri)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="https://"
        + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": str(request.url_for("home")),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


# Testing routes (only available in development with TESTING_MODE=true)
@app.get("/test-login")
async def test_login(request: Request):
    """Testing route to bypass Auth0 and set mock session"""
    # Security check - only available in testing mode
    if not TESTING_MODE or ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")

    # Set mock user session
    request.session["user"] = MOCK_USER_DATA

    return RedirectResponse(url="/", status_code=303)


@app.get("/test-logout")
async def test_logout(request: Request):
    """Testing route to clear session"""
    # Security check - only available in testing mode
    if not TESTING_MODE or ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")

    request.session.clear()

    return RedirectResponse(url="/", status_code=303)


@app.get("/test-status")
async def test_status():
    """Show testing configuration status"""
    # Security check - only available in testing mode
    if not TESTING_MODE or ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")

    return JSONResponse(
        {
            "testing_mode": TESTING_MODE,
            "environment": ENVIRONMENT,
            "mock_user_available": bool(MOCK_USER_DATA),
            "warning": "This endpoint only exists in development testing mode",
        }
    )


@app.get("/api/tags/clear")
async def clear_tag_search(
    request: Request,
    used_tags: str = "",
    show_by_count: bool = False,
    show_only_in_use: bool = False,
    size_by_count: bool = False,
    filter_tags: str = "",
    column_tags: str = "",
    toggle_mode: str = "ANY",
):
    """Clear tag search and return all tags except those in use"""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Redirect to search with empty query, maintaining checkbox states
    sort_mode = "count" if show_by_count else "name"
    return await search_tags(
        request,
        q="",
        sort=sort_mode,
        used_tags=used_tags,
        show_only_in_use=show_only_in_use,
        size_by_count=size_by_count,
        filter_tags=filter_tags,
        column_tags=column_tags,
        toggle_mode=toggle_mode,
    )


@app.get("/api/tags/search")
async def search_tags(
    request: Request,
    q: str = "",
    sort: str = "name",
    used_tags: str = "",
    show_only_in_use: bool = False,
    size_by_count: bool = False,
    filter_tags: str = "",
    column_tags: str = "",
    toggle_mode: str = "ANY",
):
    """Search and return filtered tags with counts, excluding tags already in use"""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Parse used tags from JSON state (tags already in drop zones)
    used_tags_set = set()
    if used_tags:
        try:
            # Parse JSON state from frontend
            import json

            state = json.loads(used_tags)
            # Extract all tags currently in play (in drop zones)
            if "tags" in state and "in-play" in state["tags"]:
                for zone_tags in state["tags"]["in-play"].values():
                    if isinstance(zone_tags, list):
                        used_tags_set.update(zone_tags)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback to old comma-separated format
            used_tags_set = {tag.strip() for tag in used_tags.split(",") if tag.strip()}

    # Get current tag counts based on dataset size
    current_tag_counts = load_tag_data(
        expand_dataset=(DATASET_SIZE == "500k"), dataset_name=CURRENT_DATASET
    )
    logger.focus(
        f"Tag search: Using {DATASET_SIZE} mode, {len(current_tag_counts)} unique tags, excluding {len(used_tags_set)} used tags, show_only_in_use={show_only_in_use}, size_by_count={size_by_count}"
    )

    # Apply SET THEORY filtering to tag universe
    if not q:
        # Full universal set of tags, excluding used tags
        filtered_tags = {
            tag: count
            for tag, count in current_tag_counts.items()
            if tag not in used_tags_set
        }
    else:
        # Filtered subset of universal tag set based on search query, excluding used tags
        filtered_tags = {
            tag: count
            for tag, count in current_tag_counts.items()
            if q.lower() in tag.lower() and tag not in used_tags_set
        }

    # If "Show only tags in use" is checked, calculate which tags are in displayed cards
    if show_only_in_use:
        # Parse filter and column tags
        filter_tags_set = {tag.strip() for tag in filter_tags.split(",") if tag.strip()}
        column_tags_set = {tag.strip() for tag in column_tags.split(",") if tag.strip()}

        if filter_tags_set or column_tags_set:
            # Calculate which cards are in play
            in_play_ids = calculate_in_play_set_optimized(
                filter_tags_set, column_tags_set, set(), toggle_mode
            )

            # Collect all tags from in-play cards
            in_play_tags_set = set()
            for card_id in in_play_ids:
                card = CARD_ID_TO_CARD.get(card_id)
                if card:
                    in_play_tags_set.update(card.get("tags", []))

            # Filter to only tags that are in the displayed cards
            filtered_tags = {
                tag: count
                for tag, count in filtered_tags.items()
                if tag in in_play_tags_set
            }

    # Sort tags based on sort parameter or checkbox
    if sort == "count":
        # Sort by count descending, then by name
        sorted_tags = sorted(filtered_tags.items(), key=lambda x: (-x[1], x[0]))
    else:  # sort == "name" or default
        # Sort by name ascending
        sorted_tags = sorted(filtered_tags.items())

    # Generate HTML with id attributes for stateless design
    tags_html = ""

    # Calculate size buckets if sizing by count
    if size_by_count and filtered_tags:
        max_count = max(filtered_tags.values())

        # Define size buckets using integer division
        # Bucket sizes: 0.65rem, 0.75rem, 0.85rem, 0.95rem, 1.05rem, 1.15rem
        size_buckets = [0.65, 0.75, 0.85, 0.95, 1.05, 1.15]
        num_buckets = len(size_buckets)

        # Calculate bucket width using integer division
        # Ensures even distribution across buckets
        bucket_width = max(1, max_count // num_buckets)

    for tag, count in sorted_tags:
        # Apply size scaling if checkbox is checked
        if size_by_count and filtered_tags:
            # Determine bucket using integer division
            bucket_index = min(count // bucket_width, num_buckets - 1)

            # Add micro-adjustment within bucket using modulo for subtle variation
            # This creates slight size differences within same bucket
            micro_adjustment = (count % bucket_width) / bucket_width * 0.05

            font_size = size_buckets[bucket_index] + micro_adjustment
            style = f' style="font-size: {font_size:.2f}rem;"'
        else:
            style = ""

        # Generate sanitized tag name for CSS class (same logic as template)
        sanitized_tag = "".join(c if c.isalnum() else "_" for c in tag)
        tags_html += f'<div class="tag" draggable="true" data-tag="{tag}" id="tag-{tag}" ondragstart="event.dataTransfer.setData(\'tag\', this.dataset.tag)"{style}><span class="tag-dot {sanitized_tag}-dot"></span>{tag} ({count})</div>'

    return HTMLResponse(tags_html)


@app.post("/api/tags/remove-filter")
async def remove_filter_tag(request: Request):
    """Remove a tag from the filter and update cards display"""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    form = await request.form()
    tag_to_remove = form.get("tag", "")
    remaining_tags = form.get("tags", "")  # Get remaining filter tags

    if not tag_to_remove:
        return HTMLResponse("")

    # Parse remaining tags after removal using SET THEORY
    raw_tag_set = {tag.strip() for tag in remaining_tags.split(",") if tag.strip()}
    # Remove the target tag using SET DIFFERENCE
    filter_tags_set = raw_tag_set - {tag_to_remove}
    # Keep as set for SET THEORY operations
    filter_tags = filter_tags_set

    # Start building response HTML - we'll handle moving the element back via JavaScript
    response_html = ""

    # Update card display based on remaining filter tags
    if not filter_tags:
        # No filter tags remaining - clear the display
        response_html += '<div hx-swap-oob="true" id="card-display-zone"></div>'
    else:
        # Filter cards based on remaining tags - reuse logic from filter-stateless
        json_path = (
            pathlib.Path(__file__).parent.parent.parent.parent.parent
            / "data"
            / "mock"
            / "mock-data-cards-tags.json"
        )

        try:
            with open(json_path) as f:
                data = json.load(f)

            # Use unified filtering logic (no mode switching)
            # For compatibility, use union behavior until unified zones implemented
            filter_tags_set = set(filter_tags)
            cards_set = set(data.get("cards", []))

            # Unified filtering: cards contain ANY filter tags (union behavior)
            filtered_cards = {
                card
                for card in cards_set
                if filter_tags_set.intersection(set(card.get("tags", [])))
            }
            # Keep as set for SET THEORY operations

            if not filtered_cards:
                cards_html = f'<div style="padding: 2rem; text-align: center; color: var(--text-dim);">No cards found with any of tags: <strong>{", ".join(sorted(filter_tags))}</strong></div>'
            else:
                cards_html = f'<div style="margin-bottom: 0.5rem; padding: 0.3rem 0.5rem; background: rgba(37, 99, 235, 0.1); border-radius: 0.25rem; color: var(--text-light); font-size: 0.75rem;">Showing {len(filtered_cards)} cards with any of tags: <strong>{", ".join(sorted(filter_tags))}</strong></div>'

                for card in filtered_cards:
                    tags_display = " ".join(
                        f'<span style="background: rgba(255,255,255,0.1); padding: 0.05rem 0.2rem; border-radius: 0.15rem; font-size: 0.65rem;">{t}</span>'
                        for t in card.get("tags", [])
                    )

                    cards_html += f"""
                    <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.25rem; padding: 0.5rem; margin: 0.25rem; display: inline-block; width: 250px; vertical-align: top;">
                        <div style="color: var(--text-light); margin-bottom: 0.2rem; font-size: 0.8rem; font-weight: 600;">{card.get("title", "Untitled")}</div>
                        <div style="color: var(--text-dim); margin-bottom: 0.3rem; font-size: 0.7rem; line-height: 1.2;">{card.get("description", "No description")}</div>
                        <div style="font-size: 0.65rem; color: var(--text-dim);">{tags_display}</div>
                    </div>
                    """

            response_html += (
                f'<div hx-swap-oob="true" id="card-display-zone">{cards_html}</div>'
            )

        except Exception:
            response_html += '<div hx-swap-oob="true" id="card-display-zone"></div>'

    return HTMLResponse(response_html)


@app.post("/api/tags/filter-stateless")
async def filter_by_tags_stateless(request: Request):
    """Stateless filtering using SET THEORY - process complete tag list from DOM

    SET THEORY IMPLEMENTATION:
    - Uses ordered sets to maintain filter tag insertion order
    - Applies union/intersection operations for card filtering
    """
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get complete tag list from form data (comma-separated)
    form = await request.form()
    tags_param = form.get("tags", "")

    if not tags_param:
        return HTMLResponse("")

    # Parse comma-separated tags using SET THEORY
    filter_tags_set = {tag.strip() for tag in tags_param.split(",") if tag.strip()}
    # Keep as set for SET THEORY operations
    filter_tags = filter_tags_set

    if not filter_tags:
        return HTMLResponse("")

    # Load card data and filter by tags
    json_path = (
        pathlib.Path(__file__).parent.parent.parent.parent.parent
        / "data"
        / "mock"
        / "mock-data-cards-tags.json"
    )

    try:
        with open(json_path) as f:
            data = json.load(f)

        # Use unified filtering logic (no mode switching)
        # For compatibility, use union behavior until unified zones implemented
        filter_tag_set = filter_tags
        cards_set = set(data.get("cards", []))

        # Unified filtering: cards contain ANY filter tags (union behavior)
        filtered_cards = {
            card
            for card in cards_set
            if filter_tag_set.intersection(set(card.get("tags", [])))
        }
        # Keep as set for SET THEORY operations

        # Generate filter tags HTML with remove buttons and hidden form inputs
        filter_tags_html = ""
        for filter_tag in filter_tags:
            # Generate sanitized tag name for CSS class (same logic as template)
            sanitized_tag = "".join(c if c.isalnum() else "_" for c in filter_tag)
            filter_tags_html += f"""<div class="filter-tag" id="filter-{filter_tag}">
                <span class="tag-dot {sanitized_tag}-dot"></span>{filter_tag}
                <span class="filter-tag-remove" hx-post="/api/tags/remove-filter" hx-vals='{{"tag":"{filter_tag}"}}' hx-trigger="click" hx-swap="none">×</span>
                <input type="hidden" name="{filter_tag}" value="{filter_tag}">
            </div>"""

        # Generate toggle switch HTML (only show if more than one tag)
        if len(filter_tags) > 1:
            pass

        if not filtered_cards:
            cards_html = f'<div style="padding: 2rem; text-align: center; color: var(--text-dim);">No cards found with any of tags: <strong>{", ".join(sorted(filter_tags))}</strong></div>'
        else:
            # Generate HTML for filtered cards
            cards_html = f'<div style="margin-bottom: 0.5rem; padding: 0.3rem 0.5rem; background: rgba(37, 99, 235, 0.1); border-radius: 0.25rem; color: var(--text-light); font-size: 0.75rem;">Showing {len(filtered_cards)} cards with any of tags: <strong>{", ".join(sorted(filter_tags))}</strong></div>'

            for card in filtered_cards:
                # Create very compact card display
                tags_display = " ".join(
                    f'<span style="background: rgba(255,255,255,0.1); padding: 0.05rem 0.2rem; border-radius: 0.15rem; font-size: 0.65rem;">{t}</span>'
                    for t in card.get("tags", [])
                )

                cards_html += f"""
                <div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.25rem; padding: 0.5rem; margin: 0.25rem; display: inline-block; width: 250px; vertical-align: top;">
                    <div style="color: var(--text-light); margin-bottom: 0.2rem; font-size: 0.8rem; font-weight: 600;">{card.get("title", "Untitled")}</div>
                    <div style="color: var(--text-dim); margin-bottom: 0.3rem; font-size: 0.7rem; line-height: 1.2;">{card.get("description", "No description")}</div>
                    <div style="font-size: 0.65rem; color: var(--text-dim);">{tags_display}</div>
                </div>
                """

        # Return just the cards HTML for stateless operation
        return HTMLResponse(cards_html)

    except Exception as e:
        return HTMLResponse(
            f'<div style="padding: 2rem; text-align: center; color: var(--text-dim);">Error loading cards: {str(e)}</div>'
        )


def calculate_in_play_set(cards, zone_tags, toggle_mode):
    """Calculate In-Play set using global ANY/ALL logic with n-dimensional zone tags.

    Uses polymorphic zone_tags structure to support unlimited dimensions.

    Args:
        cards: List of all cards (dictionaries are unhashable, can't be in sets)
        zone_tags: Dict[str, Set[str]] - Polymorphic dimension->tags mapping
        toggle_mode: "ANY" or "ALL"

    Returns:
        List of cards that match the global ANY/ALL criteria
    """
    try:
        from services.zone_tags import get_all_active_tags
    except ImportError:
        # Fallback function
        def get_all_active_tags(zone_tags_dict):
            all_tags = set()
            for zone_name, tag_set in zone_tags_dict.items():
                all_tags.update(tag_set)
            return all_tags

    # Calculate union of ALL active dimensional tags using SET THEORY
    all_active_tags = get_all_active_tags(zone_tags)

    if not all_active_tags:
        # No active tags - return empty set (no cards shown)
        return []

    # Apply global ANY/ALL logic to ALL active tags using SET THEORY
    if toggle_mode == "ALL":
        # ALL mode: cards must contain ALL active tags (INTERSECTION)
        in_play_cards = []
        for card in cards:
            if all_active_tags.issubset(set(card.get("tags", []))):
                in_play_cards.append(card)
    else:
        # ANY mode: cards must contain ANY active tag (UNION)
        in_play_cards = []
        for card in cards:
            if all_active_tags.intersection(set(card.get("tags", []))):
                in_play_cards.append(card)

    return in_play_cards


def calculate_in_play_set_optimized(zone_tags, toggle_mode):
    """Calculate In-Play set using inverted index for O(M) performance.

    O(M) where M = number of tags, not O(N) where N = number of cards.
    Uses pure set operations on card IDs for maximum performance.

    Args:
        zone_tags: Dict[str, Set[str]] - Polymorphic dimension->tags mapping
        toggle_mode: "ANY" or "ALL"

    Returns:
        Set of card IDs that match the global ANY/ALL criteria
    """
    # Calculate union of ALL active dimensional tags using SET THEORY
    try:
        from services.zone_tags import get_all_active_tags
    except ImportError:
        # Fallback function
        def get_all_active_tags(zone_tags_dict):
            all_tags = set()
            for zone_name, tag_set in zone_tags_dict.items():
                all_tags.update(tag_set)
            return all_tags

    all_active_tags = get_all_active_tags(zone_tags)

    if not all_active_tags:
        # No active tags - return empty set (no cards shown)
        return set()

    if toggle_mode == "ALL":
        # ALL mode: Intersection of all tag sets
        result_ids = None
        for tag in all_active_tags:
            tag_card_ids = TAG_TO_CARD_IDS.get(tag, set())
            if result_ids is None:
                result_ids = tag_card_ids.copy()
            else:
                result_ids &= tag_card_ids  # Pure intersection
                if not result_ids:  # Early exit if no cards match all tags
                    break
    else:  # ANY mode
        # Union of all tag sets
        result_ids = set()
        for tag in all_active_tags:
            result_ids |= TAG_TO_CARD_IDS.get(tag, set())  # Pure union

    return result_ids


def assign_colors_max_distance(tags):
    """Assign colors to tags with maximum perceptual distance.

    Uses LAB color space distances for optimal visual distinction.
    Implements a greedy algorithm that assigns the most distant color
    from all previously assigned colors.

    Args:
        tags (iterable): Tags to assign colors to

    Returns:
        dict: Mapping of tag -> color_index (0-11)
    """
    if not tags:
        return {}

    # RGB values for our 12 colors
    color_rgb = [
        (229, 62, 62),  # red
        (49, 130, 206),  # blue
        (56, 161, 105),  # green
        (128, 90, 213),  # purple
        (221, 107, 32),  # orange
        (11, 197, 234),  # cyan
        (214, 158, 46),  # yellow
        (237, 100, 166),  # pink
        (49, 151, 149),  # teal
        (90, 103, 216),  # indigo
        (101, 163, 13),  # lime
        (245, 158, 11),  # amber
    ]

    def rgb_to_lab(r, g, b):
        """Convert RGB to LAB color space for perceptual distance calculation."""
        # Normalize RGB values
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        # Apply gamma correction
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92

        # Convert to XYZ
        x = (r * 0.4124 + g * 0.3576 + b * 0.1805) * 100
        y = (r * 0.2126 + g * 0.7152 + b * 0.0722) * 100
        z = (r * 0.0193 + g * 0.1192 + b * 0.9505) * 100

        # Normalize for illuminant D65
        x /= 95.047
        y /= 100.000
        z /= 108.883

        # Convert to LAB
        x = x ** (1 / 3) if x > 0.008856 else (7.787 * x) + (16 / 116)
        y = y ** (1 / 3) if y > 0.008856 else (7.787 * y) + (16 / 116)
        z = z ** (1 / 3) if z > 0.008856 else (7.787 * z) + (16 / 116)

        L = (116 * y) - 16
        a = 500 * (x - y)
        b_lab = 200 * (y - z)

        return (L, a, b_lab)

    def color_distance(lab1, lab2):
        """Calculate perceptual distance between two LAB colors."""
        return (
            (lab1[0] - lab2[0]) ** 2
            + (lab1[1] - lab2[1]) ** 2
            + (lab1[2] - lab2[2]) ** 2
        ) ** 0.5

    # Pre-compute LAB values for all colors
    color_lab = [rgb_to_lab(*rgb) for rgb in color_rgb]

    # Sort tags for consistent assignment
    sorted_tags = sorted(tags)
    color_map = {}
    used_colors = []

    for tag in sorted_tags:
        if not used_colors:
            # First tag gets color 0 (red)
            best_color = 0
        else:
            # Find color with maximum minimum distance to all used colors
            best_color = 0
            best_min_distance = 0

            for color_idx in range(12):
                if color_idx in used_colors:
                    continue

                # Calculate minimum distance to all used colors
                min_distance = float("inf")
                for used_color in used_colors:
                    distance = color_distance(
                        color_lab[color_idx], color_lab[used_color]
                    )
                    min_distance = min(min_distance, distance)

                # Choose color with maximum minimum distance
                if min_distance > best_min_distance:
                    best_min_distance = min_distance
                    best_color = color_idx

        color_map[tag] = best_color
        used_colors.append(best_color)

        # Stop if we've used all colors
        if len(used_colors) >= 12:
            break

    # If we have more than 12 tags, cycle through colors starting with most distant
    if len(sorted_tags) > 12:
        remaining_tags = sorted_tags[12:]
        available_colors = list(range(12))

        for i, tag in enumerate(remaining_tags):
            color_map[tag] = available_colors[i % 12]

    return color_map


def generate_color_style_tag(color_map, colors_enabled):
    """
    Generate CSS style tag for color dots with tag-specific classnames.
    Returns HTML for style tag to be OOB injected.
    """
    if not colors_enabled or not color_map:
        # Empty style tag when colors disabled
        return '<style id="dynamic-color-styles"></style>'

    # RGB colors matching the exact backend palette
    color_rgb = [
        "rgb(229, 62, 62)",  # red
        "rgb(49, 130, 206)",  # blue
        "rgb(56, 161, 105)",  # green
        "rgb(128, 90, 213)",  # purple
        "rgb(221, 107, 32)",  # orange
        "rgb(11, 197, 234)",  # cyan
        "rgb(214, 158, 46)",  # yellow
        "rgb(237, 100, 166)",  # pink
        "rgb(49, 151, 149)",  # teal
        "rgb(90, 103, 216)",  # indigo
        "rgb(101, 163, 13)",  # lime
        "rgb(245, 158, 11)",  # amber
    ]

    # Generate CSS rules for each tag
    css_rules = []
    for tag_name, color_index in color_map.items():
        if color_index < len(color_rgb):
            # Sanitize tag name for CSS class (replace special chars with underscore)
            sanitized_tag = "".join(c if c.isalnum() else "_" for c in tag_name)
            css_rules.append(
                f".{sanitized_tag}-dot {{ background-color: {color_rgb[color_index]}; }}"
            )

    css_content = "\n".join(css_rules)
    return f'<style id="dynamic-color-styles">\n{css_content}\n</style>'


def render_dimensional_table(
    zone_tags, in_play_cards, toggle_mode, colors_enabled, color_map
):
    """
    Always generate table - polymorphic for any dimensional combination.

    Implements unified table architecture where ALL dimensional combinations
    render as tables:
    - 0D: 1×1 table (identical to current card_list.html)
    - 1D columns: 1×N table (identical to current columns.html)
    - 1D rows: N×1 table (new functionality)
    - 2D: N×M table (uses existing grid_partitioner.py)

    Args:
        zone_tags: Dict[str, Set[str]] - Polymorphic dimension->tags mapping
        in_play_cards: List[dict] - Cards to render
        toggle_mode: String "ANY" or "ALL"
        colors_enabled: Boolean
        color_map: Dict - Tag to color mapping

    Returns:
        String - HTML for complete dimensional table
    """
    logger.focus("=== STARTING render_dimensional_table ===")
    logger.focus(
        f"Zone dimensions: {list(zone_tags.keys())}, Cards: {len(in_play_cards)}"
    )

    row_tags = list(zone_tags.get("rows", set()))
    column_tags = list(zone_tags.get("columns", set()))

    # Determine table mode based on dimensions present
    if not row_tags and not column_tags:
        # 0D: 1×1 table (should look identical to current card_list.html)
        table_mode = "single_cell"
        row_tags, column_tags = ["all_cards"], ["all_cards"]
    elif not row_tags:
        # 1D columns: 1×N table (should look identical to current columns.html)
        table_mode = "columns_only"
        row_tags = ["all_cards"]
    elif not column_tags:
        # 1D rows: N×1 table (new functionality)
        table_mode = "rows_only"
        column_tags = ["all_cards"]
    else:
        # 2D grid: N×M table (uses existing grid_partitioner.py)
        table_mode = "grid"

    logger.focus(f"Table mode determined: {table_mode}")
    logger.focus(
        f"Effective dimensions: {len(row_tags)} rows × {len(column_tags)} columns"
    )

    # Generate table HTML based on mode
    table_html = generate_table_html(
        in_play_cards,
        row_tags,
        column_tags,
        toggle_mode,
        colors_enabled,
        color_map,
        table_mode,
    )

    logger.focus(f"=== ENDING render_dimensional_table: {len(table_html)} chars ===")
    return table_html


def generate_table_html(
    cards, row_tags, column_tags, toggle_mode, colors_enabled, color_map, table_mode
):
    """Generate HTML table structure for any dimensional combination."""
    logger.focus(f"Generating table HTML for mode: {table_mode}")

    if table_mode == "single_cell":
        # Must look identical to current card_list.html output
        return render_single_cell_table(cards, colors_enabled, color_map, toggle_mode)
    elif table_mode == "columns_only":
        # Must look identical to current columns.html output
        return render_columns_as_table(cards, column_tags, colors_enabled, color_map)
    elif table_mode == "rows_only":
        # New: render as N×1 table
        return render_rows_as_table(cards, row_tags, colors_enabled, color_map)
    else:  # grid mode
        # Use existing grid_partitioner.py service
        return render_2d_grid_table(
            cards, row_tags, column_tags, toggle_mode, colors_enabled, color_map
        )


def render_single_cell_table(cards, colors_enabled, color_map, toggle_mode):
    """Render 1×1 table using dimensional_table.html template."""
    template_context = {
        "table_mode": "single_cell",
        "cards": cards,
        "colors_enabled": colors_enabled,
        "color_map": color_map,
        "toggle_mode": toggle_mode,
        "filter_tags": [],  # For empty state logic
    }
    return templates.get_template("dimensional_table.html").render(**template_context)


def render_columns_as_table(cards, column_tags, colors_enabled, color_map):
    """Render 1×N table using dimensional_table.html template."""
    # Remove "all_cards" placeholder for actual column rendering
    actual_column_tags = [tag for tag in column_tags if tag != "all_cards"]

    if not actual_column_tags:
        # No actual columns, render as single cell
        return render_single_cell_table(cards, colors_enabled, color_map, "ANY")

    # Partition cards into columns using existing logic
    column_cards, other_column_cards = partition_cards_by_columns(
        cards, actual_column_tags
    )

    template_context = {
        "table_mode": "columns_only",
        "column_tags": actual_column_tags,
        "column_cards": column_cards,
        "other_column_cards": other_column_cards,
        "colors_enabled": colors_enabled,
        "color_map": color_map,
        "current_sort": None,  # TODO: Add sorting state when implementing sorting functionality
    }
    return templates.get_template("dimensional_table.html").render(**template_context)


def render_single_card_html(card, colors_enabled, color_map):
    """Render a single card with consistent styling."""
    card_html = f"""<div style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.25rem; padding: 0.5rem; margin: 0.25rem; width: 100%; box-sizing: border-box;">
        <div style="color: var(--text-light); margin-bottom: 0.2rem; font-size: 0.8rem; font-weight: 600;">{card.get("title", "Untitled")}</div>
        <div style="color: var(--text-dim); margin-bottom: 0.3rem; font-size: 0.7rem; line-height: 1.2;">{card.get("description", "No description")}</div>
        <div style="font-size: 0.65rem; color: var(--text-dim);">"""

    # Add tags with color support and matching dots
    for tag in card.get("tags", []):
        # Sanitize tag name for CSS class (same logic as backend)
        sanitized_tag = "".join(c if c.isalnum() else "_" for c in tag)

        if colors_enabled and tag in color_map:
            # Tag matches drop zone - add dot with matching class
            card_html += f'<span class="card-tag-colored-{color_map[tag]}" style="padding: 0.05rem 0.2rem; border-radius: 0.15rem; font-size: 0.65rem;"><span class="tag-dot {sanitized_tag}-dot"></span>{tag}</span>'
        else:
            # No color but still has hidden dot
            card_html += f'<span style="background: rgba(255,255,255,0.1); padding: 0.05rem 0.2rem; border-radius: 0.15rem; font-size: 0.65rem;"><span class="tag-dot {sanitized_tag}-dot"></span>{tag}</span>'

    card_html += """</div>
    </div>"""

    return card_html


def render_rows_as_table(cards, row_tags, colors_enabled, color_map):
    """Render N×1 table using dimensional_table.html template."""
    # Remove "all_cards" placeholder for actual row rendering
    actual_row_tags = [tag for tag in row_tags if tag != "all_cards"]

    if not actual_row_tags:
        # No actual rows, render as single cell
        return render_single_cell_table(cards, colors_enabled, color_map, "ANY")

    # Partition cards into rows using new partitioning function
    row_cards, other_row_cards = partition_cards_by_rows(cards, actual_row_tags)

    template_context = {
        "table_mode": "rows_only",
        "row_tags": actual_row_tags,
        "row_cards": row_cards,
        "other_row_cards": other_row_cards,
        "colors_enabled": colors_enabled,
        "color_map": color_map,
    }
    return templates.get_template("dimensional_table.html").render(**template_context)


# REMOVED: partition_cards_by_columns and partition_cards_by_rows
# These functions duplicated functionality now available in:
# packages/shared/services/set_operations.py -> apply_dimension_partition()
# Use the canonical implementation from set_operations service instead.


def render_2d_grid_table(
    cards, row_tags, column_tags, toggle_mode, colors_enabled, color_map
):
    """Render N×M table using dimensional_table.html template."""
    # Remove "all_cards" placeholder for actual grid rendering
    actual_row_tags = [tag for tag in row_tags if tag != "all_cards"]
    actual_column_tags = [tag for tag in column_tags if tag != "all_cards"]

    # Partition cards into grid cells using intersection logic
    grid_cells = partition_cards_into_grid(
        cards, actual_row_tags, actual_column_tags, toggle_mode
    )

    template_context = {
        "table_mode": "grid",
        "row_tags": actual_row_tags,
        "column_tags": actual_column_tags,
        "grid_cells": grid_cells,
        "toggle_mode": toggle_mode,
        "colors_enabled": colors_enabled,
        "color_map": color_map,
    }
    return templates.get_template("dimensional_table.html").render(**template_context)


def partition_cards_into_grid(cards, row_tags, column_tags, toggle_mode):
    """
    Partition cards into grid cells based on row/column tag intersections.

    IMPORTANT: toggle_mode (ANY/ALL) is already applied to determine which cards are "in play".
    Grid partitioning logic: cards appear in cells where they have BOTH row tag AND column tag.
    Cards that don't match any row tag go to "Other" row.
    Cards that don't match any column tag go to "Other" column.

    Returns grid_cells dict with keys like "row_tag_column_tag".
    """
    grid_cells = {}

    # Add "Other" to row and column tags for unmatched cards
    all_row_tags = row_tags + ["Other"]
    all_column_tags = column_tags + ["Other"]

    # Initialize all possible grid cells (including Other combinations)
    for row_tag in all_row_tags:
        for column_tag in all_column_tags:
            cell_key = f"{row_tag}_{column_tag}"
            grid_cells[cell_key] = []

    # Partition cards into appropriate cells
    for card in cards:
        card_tags = set(card.get("tags", []))

        # Determine which row this card belongs to
        card_row = "Other"  # Default to Other
        for row_tag in row_tags:
            if row_tag in card_tags:
                card_row = row_tag
                break  # Use first matching row tag

        # Determine which column this card belongs to
        card_column = "Other"  # Default to Other
        for column_tag in column_tags:
            if column_tag in card_tags:
                card_column = column_tag
                break  # Use first matching column tag

        # Place card in the intersection cell
        cell_key = f"{card_row}_{card_column}"
        grid_cells[cell_key].append(card)

    return grid_cells


def render_card_display(
    zone_tags,
    toggle_mode,
    colors_enabled,
    render_mode="optimized",
):
    """Unified function to render card display using Jinja2 templates.

    Handles ALL scenarios with n-dimensional zone tags:
    - Filter only: Simple card list
    - Columns only: Multi-column layout
    - Filter + Columns: Multi-column layout with "Other" column
    - Any combination of n dimensions

    Args:
        zone_tags: Dict[str, Set[str]] - Polymorphic dimension->tags mapping
        toggle_mode: String "ANY" or "ALL"
        colors_enabled: Boolean
        render_mode: String "optimized" or "unoptimized"

    Returns:
        dict with 'cards_html', 'filter_tags_html', 'column_tags_html', success status
    """
    logger.focus("=== STARTING render_card_display ===")
    logger.focus(
        f"Parameters: zone_tags={list(zone_tags.keys())}, mode={toggle_mode}, colors={colors_enabled}, render_mode={render_mode}"
    )

    try:
        # Extract specific dimensions from zone_tags
        filter_tags_raw = zone_tags.get("filter", set())
        column_tags_raw = zone_tags.get("columns", set())

        # Check if we have ANY tags at all
        # has_any_tags = any(tags for tags in zone_tags.values())

        # Calculate "IN PLAY" SUPERSETS using SET THEORY (single source of truth)
        try:
            from services.zone_tags import get_all_active_tags
        except ImportError:
            # Fallback function
            def get_all_active_tags(zone_tags_dict):
                all_tags = set()
                for zone_name, tag_set in zone_tags_dict.items():
                    all_tags.update(tag_set)
                return all_tags

        tags_in_play = get_all_active_tags(zone_tags)  # Union of ALL dimensions

        logger.focus(f"Tags_in_play = F ∪ C ∪ R = {tags_in_play}")

        # Choose rendering path based on render_mode and availability
        in_play_ids = None  # Initialize for column partitioning
        use_optimized = render_mode == "optimized" and _INITIALIZED and CARD_ID_TO_CARD

        if use_optimized:
            # Use optimized O(M) algorithm with inverted index
            in_play_ids = calculate_in_play_set_optimized(zone_tags, toggle_mode)
            in_play_cards = [CARD_ID_TO_CARD[card_id] for card_id in in_play_ids]
            logger.focus(
                f"In-Play cards (OPTIMIZED): {len(in_play_cards)} from {len(ALL_CARDS)} total"
            )
        else:
            # Use original O(N) implementation (either forced unoptimized or fallback)
            cards = load_card_data(
                expand_dataset=(DATASET_SIZE == "500k"), dataset_name=CURRENT_DATASET
            )
            in_play_cards = calculate_in_play_set(cards, zone_tags, toggle_mode)
            if render_mode == "unoptimized":
                logger.focus(
                    f"In-Play cards (UNOPTIMIZED - forced): {len(in_play_cards)} from {len(cards)} total"
                )
            else:
                logger.focus(
                    f"In-Play cards (UNOPTIMIZED - fallback): {len(in_play_cards)} from {len(cards)} total"
                )

        # Create color assignment map ONLY for tags in drop zones (not all card tags)
        # Rule: Every tag in a drop zone gets a color using the distance algorithm
        # Rule: Card tags that match drop zone tags get the same color
        drop_zone_tags = set()
        for dimension_tags in zone_tags.values():
            drop_zone_tags.update(dimension_tags)

        color_map = assign_colors_max_distance(drop_zone_tags)
        logger.focus(
            f"Color map generated: {len(color_map)} drop zone tags mapped with maximum distance algorithm"
        )

        # UNIFIED TABLE RENDERER: Always generate tables regardless of dimensional combination
        logger.focus("Using UNIFIED TABLE RENDERER for all dimensional combinations")

        # Call unified table renderer - replaces all conditional logic
        cards_html = render_dimensional_table(
            zone_tags=zone_tags,
            in_play_cards=in_play_cards,
            toggle_mode=toggle_mode,
            colors_enabled=colors_enabled,
            color_map=color_map,
        )

        # Preserve legacy variables for template rendering compatibility
        has_filters = bool(filter_tags_raw)
        has_columns = bool(column_tags_raw)

        # Unified table renderer handles ALL cases - no conditional logic needed

        # Render tag HTML using templates (single source of truth)
        filter_tags_html = ""
        if has_filters:
            filter_context = {
                "filter_tags": filter_tags_raw,
                "tag_counts": TAG_COUNTS,
                "colors_enabled": colors_enabled,
                "color_map": color_map,
            }
            filter_tags_html = templates.get_template("filter_tags.html").render(
                **filter_context
            )

        column_tags_html = ""
        if has_columns:
            column_context = {
                "column_tags_raw": column_tags_raw,
                "tag_counts": TAG_COUNTS,
                "colors_enabled": colors_enabled,
                "color_map": color_map,
            }
            column_tags_html = templates.get_template("column_tags.html").render(
                **column_context
            )

        logger.focus(
            f"Generated HTML - cards: {len(cards_html)} chars, filter_tags: {len(filter_tags_html)} chars, column_tags: {len(column_tags_html)} chars"
        )
        logger.focus(
            f"Cards HTML content (first 200 chars): {cards_html[:200] if cards_html else 'EMPTY'}"
        )
        logger.focus("=== ENDING render_card_display - SUCCESS ===")

        return {
            "success": True,
            "cards_html": cards_html,
            "filter_tags_html": filter_tags_html,
            "column_tags_html": column_tags_html,
            "mode": "columns" if has_columns else "list",
        }

    except Exception as e:
        logger.error(f"Exception in render_card_display: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/tags/filter-from-dom")
async def filter_from_dom(
    request: Request,
    connection: DatabaseConnection,
    customer_id: CustomerID,
):
    """Filter cards based on DOM state using pure functions with dependency injection."""
    logger.focus("=== STARTING filter_from_dom route ===")

    # Check authentication
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get form data
    form = await request.form()
    filter_tags_param = form.get("filter_tags", "")
    column_tags_param = form.get("column_tags", "")
    toggle_mode = form.get("toggle_mode", "ANY")
    colors_enabled = form.get("colors_enabled", "false") == "true"
    render_mode = form.get("render_mode", "optimized")

    logger.focus(
        f"Parameters: filters='{filter_tags_param}', columns='{column_tags_param}', mode={toggle_mode}, colors={colors_enabled}, customer={customer_id}"
    )

    # Parse tags into sets
    filter_tags_raw = {
        tag.strip() for tag in filter_tags_param.split(",") if tag.strip()
    }
    column_tags_param = form.get("column_tags", "")
    column_tags_raw = {
        tag.strip() for tag in column_tags_param.split(",") if tag.strip()
    }

    # Handle empty filter case using template
    if not filter_tags_raw:
        logger.focus("No filter tags - returning empty response")
        response_html = templates.get_template("empty_filter_response.html").render()
        return HTMLResponse(response_html)

    try:
        # Temporarily use working render function until optimized path is fixed
        result = render_card_display(
            filter_tags_raw,
            column_tags_raw,
            set(),  # No row tags from this endpoint
            toggle_mode,
            colors_enabled,
            render_mode,
        )

        if not result["success"]:
            raise Exception(result.get("error", "Unknown error"))

        # CRITICAL: Only return card display HTML, never tags
        template_context = {"cards_html": result["cards_html"]}

        response_html = templates.get_template("cards_only_response.html").render(
            **template_context
        )

        logger.focus(
            "Response generated using optimized pure functions with dependency injection"
        )
        logger.focus("=== ENDING filter_from_dom route - SUCCESS ===")
        return HTMLResponse(response_html)

    except Exception as e:
        logger.error(f"Exception in filter_from_dom: {str(e)}")
        # Use template for error response too
        error_context = {"error_message": str(e)}
        error_response = templates.get_template("error_response.html").render(
            **error_context
        )
        logger.focus("=== ENDING filter_from_dom route - ERROR ===")
        return HTMLResponse(error_response)


# REMOVED: filter_cards_by_intersection and filter_cards_by_union
# These functions duplicated functionality now available in:
# packages/shared/services/filtering.py -> filter_cards_intersection_first()
# packages/shared/services/set_operations.py -> apply_all_mode(), apply_any_mode()
# Use the canonical implementations from service modules instead.


def apply_union_intersection_filtering(
    intersection_tags, union_tags, start_with_all_cards
):
    """Complete filtering logic with start_with_all_cards edge case handling."""
    try:
        from services.inverted_index import TAG_TO_CARD_IDS
    except ImportError:
        try:
            pass  # Relative import disabled
        except ImportError:
            # Fallback: create empty inverted index
            TAG_TO_CARD_IDS = {}

    # CRITICAL: Handle the "no filters" edge case first
    if not intersection_tags and not union_tags:
        if start_with_all_cards:
            # Return all card IDs from the inverted index
            all_card_ids = set()
            for card_ids in TAG_TO_CARD_IDS.values():
                all_card_ids |= card_ids
            return all_card_ids
        else:
            return set()  # Return no cards

    # Step 1: Apply intersection filtering (restricts universe)
    restricted_universe = None
    if intersection_tags:
        restricted_universe = filter_cards_by_intersection(intersection_tags)
        if not restricted_universe:  # No cards match intersection
            return set()

    # Step 2: Apply union filtering to restricted universe
    if union_tags:
        universe = restricted_universe if restricted_universe is not None else None
        return filter_cards_by_union(union_tags, restricted_universe=universe)

    # Only intersection, no union
    return restricted_universe if restricted_universe is not None else set()

    # Removed duplicate @app.post("/api/render/cards") endpoint that was returning HTML tutorial cards
    # This endpoint was providing emergency bypass functionality and is now replaced by
    # the centralized shared service approach for consistent API behavior
    # The large duplicate render_cards function has been removed

    # API endpoint for toggle-mode has been removed as part of unified tag mode implementation
    # All mode-based filtering has been replaced with unified intersection/union tag processing


@app.post("/api/render/toggle")
async def toggle_render_mode(request: Request):
    """Toggle between optimized and unoptimized rendering modes using n-dimensional zone tags."""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    form = await request.form()
    current_render_mode = form.get("render_mode", "unoptimized")
    new_mode = "optimized" if current_render_mode == "unoptimized" else "unoptimized"

    logger.focus(f"Toggling render mode: {current_render_mode} -> {new_mode}")

    try:
        import json

        # Parse n-dimensional zone tags from JSON state - SINGLE SOURCE OF TRUTH
        zone_tags = {}

        # Get the tags-in-play-state field which contains JSON
        state_json = form.get("tags-in-play-state", "{}")
        if state_json:
            try:
                state = json.loads(state_json)

                # JavaScript structure is THE ONLY structure we handle:
                # {"universe": {...}, "tags": {"in-play": {"filter": [...], ...}, "unused": {...}}, "cards": {...}}
                tags_in_play = state.get("tags", {}).get("in-play", {})

                # Build zone_tags dictionary from ALL dimensions found
                for dimension, tag_sequence in tags_in_play.items():
                    if tag_sequence:  # Only add non-empty dimensions
                        # Tags already come clean from JavaScript (no quantities)
                        clean_tags = set()
                        for tag in tag_sequence:
                            if isinstance(tag, str) and tag:
                                clean_tags.add(tag)
                        if clean_tags:
                            zone_tags[dimension] = clean_tags
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON state: {state_json}")
                # Fallback to empty zone_tags
                zone_tags = {}

        toggle_mode = form.get("toggle_mode", "ANY")
        colors_enabled_param = form.get("colors_enabled", "false")
        colors_enabled = colors_enabled_param == "true"

        logger.focus(f"Active zone_tags: {list(zone_tags.keys())} dimensions")

        # Re-render with new render mode using polymorphic function
        result = render_card_display(
            zone_tags,
            toggle_mode,
            colors_enabled,
            new_mode,
        )

        if not result["success"]:
            raise Exception(result.get("error", "Unknown error"))

        # Generate response using template
        template_context = {
            "render_mode": new_mode,
            "toggle_type": "render",
            "toggle_state": new_mode,
            "toggle_id": "render-toggle",
            "toggle_endpoint": "/api/render/toggle",
            "container_id": "render-toggle-container",
            "toggle_label": "Toggle between optimized and unoptimized rendering",
            "cards_html": result["cards_html"],
            "filter_tags_html": result["filter_tags_html"]
            if zone_tags.get("filter")
            else None,
            "column_tags_html": result["column_tags_html"]
            if zone_tags.get("columns")
            else None,
        }

        response_html = templates.get_template("render_toggle_response.html").render(
            **template_context
        )

        logger.focus(
            f"Render mode toggle successful: {current_render_mode} -> {new_mode}"
        )
        return HTMLResponse(response_html)

    except Exception as e:
        logger.error(f"Exception in toggle_render_mode: {str(e)}")
        # Fallback response
        fallback_context = {
            "render_mode": new_mode,
        }
        fallback_html = templates.get_template("render_toggle_response.html").render(
            **fallback_context
        )
        return HTMLResponse(fallback_html)


@app.post("/api/dataset/toggle")
async def toggle_dataset(request: Request):
    """Toggle dataset size 50/500k using unified architecture and templates"""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    form = await request.form()
    dataset_size = int(form.get("dataset_size", "0"))
    # Reverse logic: when frontend sends 1, it wants to GO TO large dataset
    # when frontend sends 0, it wants to GO TO small dataset
    new_size = "500k" if dataset_size == 1 else "50"

    logger.focus(f"Toggling dataset: request={dataset_size} -> {new_size}")

    try:
        # Update global dataset size
        global DATASET_SIZE
        DATASET_SIZE = new_size

        # Refresh inverted index with new dataset size
        logger.info(f"Refreshing inverted index for {new_size} dataset...")
        initialize_inverted_index(expand_dataset=(new_size == "500k"))

        # Reload tag counts with new dataset size (already done in initialize_inverted_index)
        global TAG_COUNTS

        # Parse n-dimensional zone tags from form data
        zone_tags = {}

        # Check for legacy parameters
        filter_tags_param = form.get("filter_tags", "")
        column_tags_param = form.get("column_tags", "")
        row_tags_param = form.get("row_tags", "")

        if filter_tags_param:
            zone_tags["filter"] = {
                tag.strip() for tag in filter_tags_param.split(",") if tag.strip()
            }
        if column_tags_param:
            zone_tags["columns"] = {
                tag.strip() for tag in column_tags_param.split(",") if tag.strip()
            }
        if row_tags_param:
            zone_tags["rows"] = {
                tag.strip() for tag in row_tags_param.split(",") if tag.strip()
            }

        colors_enabled_param = form.get("colors_enabled", "false")
        toggle_mode = form.get("toggle_mode", "ANY")
        colors_enabled = colors_enabled_param == "true"
        render_mode = form.get("render_mode", "optimized")

        logger.focus(f"Active zone_tags: {list(zone_tags.keys())} dimensions")

        # Generate new tag cloud with updated dataset - call search logic directly
        current_tag_counts = load_tag_data(
            expand_dataset=(new_size == "500k"), dataset_name=CURRENT_DATASET
        )
        logger.focus(
            f"Tag cloud refresh: Using {new_size} mode, {len(current_tag_counts)} unique tags"
        )

        # Generate tag cloud HTML directly (no search query, full tag set)
        filtered_tags = current_tag_counts
        sorted_tags = sorted(filtered_tags.items(), key=lambda x: x[0])

        tag_elements = []
        for tag, count in sorted_tags:
            tag_html = templates.get_template("tag.html").render(
                tag=tag, count=count, tag_class="tag", id_prefix="tag"
            )
            tag_elements.append(tag_html)
        tag_cloud_html = "".join(tag_elements)

        # Re-render cards if there are active tags
        cards_html = None
        filter_tags_html = None
        column_tags_html = None

        if zone_tags:
            result = render_card_display(
                zone_tags,
                toggle_mode,
                colors_enabled,
                render_mode,
            )
            if result["success"]:
                cards_html = result["cards_html"]
                filter_tags_html = (
                    result["filter_tags_html"] if zone_tags.get("filter") else None
                )
                column_tags_html = (
                    result["column_tags_html"] if zone_tags.get("columns") else None
                )

        # Generate response using unified template
        template_context = {
            "toggle_type": "dataset",
            "toggle_state": new_size,
            "toggle_id": "dataset-toggle",
            "toggle_endpoint": "/api/dataset/toggle",
            "container_id": "dataset-toggle-container",
            "toggle_label": "Toggle between 50 and 500k dataset",
            "tag_cloud_html": tag_cloud_html,
            "cards_html": cards_html,
            "filter_tags_html": filter_tags_html,
            "column_tags_html": column_tags_html,
        }

        response_html = templates.get_template("dataset_toggle_response.html").render(
            **template_context
        )

        total_tags = sum(len(tags) for tags in zone_tags.values())
        logger.focus(
            f"Dataset toggle successful: {new_size}, active tags: {total_tags}"
        )
        return HTMLResponse(response_html)

    except Exception as e:
        logger.error(f"Exception in toggle_dataset: {str(e)}")
        # Fallback using template
        # Generate basic tag cloud for fallback
        basic_tag_counts = load_tag_data(
            expand_dataset=(new_size == "500k"), dataset_name=CURRENT_DATASET
        )
        basic_sorted_tags = sorted(basic_tag_counts.items(), key=lambda x: x[0])
        basic_tag_elements = []
        for tag, count in basic_sorted_tags:
            basic_tag_elements.append(
                f'<div class="tag" id="tag-{tag}" data-tag="{tag}" draggable="true" '
                f"ondragstart=\"event.dataTransfer.setData('tag', this.dataset.tag)\">{tag} ({count})</div>"
            )
        basic_tag_cloud_html = "".join(basic_tag_elements)

        fallback_context = {
            "toggle_type": "dataset",
            "toggle_state": new_size,
            "toggle_id": "dataset-toggle",
            "toggle_endpoint": "/api/dataset/toggle",
            "container_id": "dataset-toggle-container",
            "toggle_label": "Toggle between 50 and 500k dataset",
            "tag_cloud_html": basic_tag_cloud_html,
            "cards_html": None,
            "filter_tags_html": None,
            "column_tags_html": None,
        }
        fallback_html = templates.get_template("dataset_toggle_response.html").render(
            **fallback_context
        )
        return HTMLResponse(fallback_html)


@app.post("/api/dataset/switch")
async def switch_dataset(request: Request):
    """Switch between different use case datasets (fintech, marketing, content, corporate)"""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Declare globals at the top
    global CURRENT_DATASET, TAG_COUNTS, ALL_CARDS

    form = await request.form()
    new_dataset = form.get("dataset", "fintech-pm")

    # Validate dataset name
    valid_datasets = [
        "fintech-pm",
        "marketing-insights",
        "content-production",
        "corporate-executive",
    ]
    if new_dataset not in valid_datasets:
        new_dataset = "fintech-pm"  # Default fallback

    logger.focus(f"Switching dataset: {CURRENT_DATASET} -> {new_dataset}")

    try:
        # Update global dataset
        CURRENT_DATASET = new_dataset

        # Reload tag counts and cards for new dataset
        TAG_COUNTS = load_tag_data(
            expand_dataset=(DATASET_SIZE == "500k"), dataset_name=new_dataset
        )
        ALL_CARDS = load_card_data(
            expand_dataset=(DATASET_SIZE == "500k"), dataset_name=new_dataset
        )

        # Refresh inverted index with new dataset
        initialize_inverted_index(expand_dataset=(DATASET_SIZE == "500k"))

        logger.info(
            f"Successfully switched to {new_dataset} dataset with {len(TAG_COUNTS)} tags and {len(ALL_CARDS)} cards"
        )

        # Reload the entire page with new dataset
        return RedirectResponse(url="/", status_code=303)

    except Exception as e:
        logger.error(f"Error switching to dataset {new_dataset}: {e}")
        # Return current page with error (could add error messaging later)
        return RedirectResponse(url="/", status_code=303)


# Zone Positioning API Endpoints
@app.post("/api/zones/move")
async def move_zone(
    request: Request, connection: DatabaseConnection, customer_id: CustomerID
):
    """Move zone to new spatial position using arrow buttons."""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        try:
            from services.zone_positioning import (
                calculate_zone_position,
                update_zone_position,
            )
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback functions
                def calculate_zone_position(zone_id, direction):
                    return {"x": 0, "y": 0}

                def update_zone_position(zone_id, position, connection):
                    return True

        form = await request.form()
        zone_id = form.get("zone_id", "")
        direction = form.get("direction", "")

        logger.focus(f"Zone positioning: Moving {zone_id} {direction}")

        # Calculate new position and stack index
        new_position, new_stack_index = calculate_zone_position(
            customer_id, zone_id, direction, connection
        )

        # Update zone position in database
        update_zone_position(
            customer_id, zone_id, new_position, new_stack_index, connection
        )

        logger.focus(
            f"Zone positioned: {zone_id} -> {new_position} (stack: {new_stack_index})"
        )
        logger.focus("About to return JSON response...")

        # Return success with position data for client-side movement
        response_data = {
            "success": True,
            "zone_id": zone_id,
            "direction": direction,
            "new_position": new_position,
            "new_stack_index": new_stack_index,
        }
        logger.focus(f"Returning JSON response: {response_data}")
        return JSONResponse(response_data)

    except Exception as e:
        logger.error(f"Zone move failed: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/zones/layout")
async def get_zone_layout(connection: DatabaseConnection, customer_id: CustomerID):
    """Get current zone layout configuration."""
    try:
        try:
            from services.zone_positioning import (
                get_all_zones,
                organize_zones_by_position,
            )
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback functions
                def get_all_zones(customer_id, connection):
                    return []

                def organize_zones_by_position(zones):
                    return {"zones": zones}

        # Get all zones for customer
        zones = get_all_zones(customer_id, connection)

        # Organize by position
        layout = organize_zones_by_position(zones)

        return JSONResponse(layout)

    except Exception as e:
        logger.error(f"Zone layout failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# View Management API Endpoints


@app.post("/api/views/save")
async def save_view(
    request: Request, connection: DatabaseConnection, customer_id: CustomerID
):
    """Save current grid view configuration."""
    try:
        try:
            from services.view_persistence_functions import (
                save_view_configuration,
            )
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback function
                def save_view_configuration(view_name, config, connection):
                    return {"status": "ok"}

        # Parse request data
        form = await request.form()
        view_name = form.get("view_name", "").strip()
        description = form.get("description", "").strip()
        grid_state_json = form.get("grid_state", "{}")

        # Validate required parameters
        if not view_name:
            return JSONResponse(
                {"success": False, "error": "View name is required"}, status_code=400
            )

        # Parse grid state
        try:
            grid_state = json.loads(grid_state_json)
        except json.JSONDecodeError:
            return JSONResponse(
                {"success": False, "error": "Invalid grid state format"},
                status_code=400,
            )

        # Save view configuration
        result = save_view_configuration(
            customer_id=customer_id,
            view_name=view_name,
            grid_state=grid_state,
            description=description if description else None,
        )

        if result["success"]:
            logger.info(f"View '{view_name}' saved for customer {customer_id}")
            return JSONResponse(result)
        else:
            logger.warning(
                f"Failed to save view '{view_name}' for customer {customer_id}: {result['error']}"
            )
            return JSONResponse(result, status_code=400)

    except Exception as e:
        logger.error(f"Save view endpoint failed: {e}")
        return JSONResponse(
            {"success": False, "error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@app.post("/api/views/recall")
async def recall_view(
    request: Request, connection: DatabaseConnection, customer_id: CustomerID
):
    """Recall a saved grid view configuration."""
    try:
        try:
            from services.view_persistence_functions import (
                load_view_configuration,
            )
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback function
                def load_view_configuration(view_name, connection):
                    return None

        # Parse request data
        form = await request.form()
        view_name = form.get("view_name", "").strip()

        # Validate required parameters
        if not view_name:
            return JSONResponse(
                {"success": False, "error": "View name is required"}, status_code=400
            )

        # Load view configuration
        result = load_view_configuration(customer_id=customer_id, view_name=view_name)

        if result["success"]:
            logger.info(f"View '{view_name}' recalled for customer {customer_id}")
            return JSONResponse(result)
        else:
            logger.warning(
                f"Failed to recall view '{view_name}' for customer {customer_id}: {result['error']}"
            )
            status_code = 404 if "not found" in result["error"].lower() else 400
            return JSONResponse(result, status_code=status_code)

    except Exception as e:
        logger.error(f"Recall view endpoint failed: {e}")
        return JSONResponse(
            {"success": False, "error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@app.get("/api/views/list")
async def list_views(connection: DatabaseConnection, customer_id: CustomerID):
    """List all saved views for the customer."""
    try:
        try:
            from services.view_persistence_functions import list_saved_views
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback function
                def list_saved_views(connection):
                    return []

        # Get pagination parameters from query string
        # Note: For simplicity, we're not implementing pagination in this version
        # but the function supports it for future enhancement

        # List all views for customer
        result = list_saved_views(customer_id=customer_id)

        if result["success"]:
            logger.info(
                f"Listed {result['total_count']} views for customer {customer_id}"
            )
            return JSONResponse(result)
        else:
            logger.warning(
                f"Failed to list views for customer {customer_id}: {result['error']}"
            )
            return JSONResponse(result, status_code=500)

    except Exception as e:
        logger.error(f"List views endpoint failed: {e}")
        return JSONResponse(
            {"success": False, "error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@app.delete("/api/views/delete")
async def delete_view(
    request: Request, connection: DatabaseConnection, customer_id: CustomerID
):
    """Delete a saved view configuration."""
    try:
        try:
            from services.view_persistence_functions import (
                delete_view_configuration,
            )
        except ImportError:
            try:
                pass  # Relative import disabled
            except ImportError:
                # Fallback function
                def delete_view_configuration(view_name, connection):
                    return {"status": "ok"}

        # Parse request data
        form = await request.form()
        view_name = form.get("view_name", "").strip()

        # Validate required parameters
        if not view_name:
            return JSONResponse(
                {"success": False, "error": "View name is required"}, status_code=400
            )

        # Delete view configuration
        result = delete_view_configuration(customer_id=customer_id, view_name=view_name)

        if result["success"]:
            logger.info(f"View '{view_name}' deleted for customer {customer_id}")
            return JSONResponse(result)
        else:
            logger.warning(
                f"Failed to delete view '{view_name}' for customer {customer_id}: {result['error']}"
            )
            status_code = 404 if "not found" in result["error"].lower() else 400
            return JSONResponse(result, status_code=status_code)

    except Exception as e:
        logger.error(f"Delete view endpoint failed: {e}")
        return JSONResponse(
            {"success": False, "error": f"Internal server error: {str(e)}"},
            status_code=500,
        )


@app.get("/health")
async def health_endpoint():
    """Health check endpoint with tier-aware status."""
    try:
        health_status = await health_check()
        return JSONResponse(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)


@app.get("/tier")
async def tier_info_endpoint():
    """Tier information endpoint."""
    try:
        tier_info = get_tier_info()
        return JSONResponse(tier_info)
    except Exception as e:
        logger.error(f"Tier info failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tutorial/tags")
async def get_tutorial_tags():
    """Get tutorial tags with their display names for the frontend."""
    try:
        # Get all tag names from the tutorial database
        connection = get_database_connection()
        cursor = connection.cursor()
        # Handle different schema column names
        try:
            cursor.execute("SELECT DISTINCT tag_name FROM tag_index ORDER BY tag_name")
            raw_tags = [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Try alternative column name
            cursor.execute("SELECT DISTINCT tag FROM tag_index ORDER BY tag")
            raw_tags = [row[0] for row in cursor.fetchall()]
        connection.close()

        # Map to display names
        tutorial_tags = []
        for tag in raw_tags:
            display_name = TUTORIAL_TAG_DISPLAY.get(tag, tag)
            tutorial_tags.append(
                {"tag": tag, "display": display_name, "tutorial": True}
            )

        return JSONResponse(
            {"tags": tutorial_tags, "total": len(tutorial_tags), "tutorial_mode": True}
        )
    except Exception as e:
        logger.error(f"Failed to get tutorial tags: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


def get_dynamic_database_connection():
    """Get database connection based on current selection."""
    import sqlite3

    db_path = get_workspace_database_path(CURRENT_DATABASE)
    return sqlite3.connect(str(db_path))


def get_available_databases():
    """Get list of available customer databases."""

    try:
        from .config.database_config import get_workspace_db_path

        db_path = get_workspace_db_path()
        if not db_path.exists():
            return []

        databases = []
        for db_file in db_path.glob("*.db"):
            db_name = db_file.stem

            # Show tutorial_customer and demo databases only
            allowed_databases = [
                "tutorial_customer",
                "product_manager_demo",
                "marketing_manager_demo",
                "social_media_manager_demo",
                "trello_migration_demo",
                "enterprise_scale_demo",
            ]
            if db_name not in allowed_databases:
                logger.debug(f"Skipping database {db_name} - not in allowed list")
                continue

            logger.debug(f"Processing allowed database: {db_name}")

            # Get basic info about the database
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()

                # Get card count
                cursor.execute("SELECT COUNT(*) FROM cards")
                card_count = cursor.fetchone()[0]

                # Get unique tag count (handle different schema table names)
                try:
                    # Try new schema with tags table
                    cursor.execute("SELECT COUNT(DISTINCT name) FROM tags")
                    tag_count = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    try:
                        # Try old schema with tag_index table
                        cursor.execute("SELECT COUNT(DISTINCT tag_name) FROM tag_index")
                        tag_count = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        # Try alternative column name in tag_index
                        cursor.execute("SELECT COUNT(DISTINCT tag) FROM tag_index")
                        tag_count = cursor.fetchone()[0]

                conn.close()

                db_info = {
                    "name": db_name,
                    "display_name": db_name.replace("_", " ").title(),
                    "card_count": card_count,
                    "tag_count": tag_count,
                    "path": str(db_file),
                }
                databases.append(db_info)
                logger.debug(
                    f"Added database: {db_name} with {card_count} cards, {tag_count} tags"
                )
            except Exception as e:
                logger.warning(f"Could not read database {db_name}: {e}")
                continue

        return sorted(databases, key=lambda x: x["card_count"], reverse=True)
    except Exception as e:
        logger.error(f"Failed to get available databases: {e}")
        return []


@app.get("/api/databases")
async def get_databases():
    """Get list of available customer databases."""
    try:
        databases = get_available_databases()
        return JSONResponse({"databases": databases, "total": len(databases)})
    except Exception as e:
        logger.error(f"Failed to get databases: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# Removed second duplicate @app.post("/api/render/cards") endpoint that used RenderCardsRequest
# This endpoint provided intersection-first filtering but is now replaced by the
# centralized shared service that handles all request types through a unified interface


@app.get("/api/current-database")
async def get_current_database():
    """Get current selected database."""
    try:
        # Get info about current database
        databases = get_available_databases()
        current_db = next(
            (db for db in databases if db["name"] == CURRENT_DATABASE), None
        )

        if not current_db:
            return JSONResponse(
                {"error": "Current database not found"}, status_code=404
            )

        return JSONResponse({"current_database": current_db, "name": CURRENT_DATABASE})
    except Exception as e:
        logger.error(f"Failed to get current database: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/select-database")
async def select_database(request: Request):
    """Switch to a different customer database."""
    global CURRENT_DATABASE

    try:
        body = await request.json()
        new_database = body.get("database_name")

        if not new_database:
            return JSONResponse({"error": "database_name is required"}, status_code=400)

        # Validate database exists
        databases = get_available_databases()
        if not any(db["name"] == new_database for db in databases):
            return JSONResponse(
                {"error": f"Database '{new_database}' not found"}, status_code=404
            )

        # Test connection to new database
        test_connection = None
        try:
            db_path = get_workspace_database_path(new_database)
            test_connection = sqlite3.connect(str(db_path))
            cursor = test_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM cards")
            card_count = cursor.fetchone()[0]
        except Exception as e:
            if test_connection:
                test_connection.close()
            return JSONResponse(
                {"error": f"Cannot connect to database: {str(e)}"}, status_code=500
            )
        finally:
            if test_connection:
                test_connection.close()

        # Switch to new database
        old_database = CURRENT_DATABASE
        CURRENT_DATABASE = new_database

        # Clear any cached data that might be specific to the old database
        global TAG_TO_CARD_IDS
        TAG_TO_CARD_IDS.clear()

        logger.info(f"Switched database from {old_database} to {new_database}")

        return JSONResponse(
            {
                "success": True,
                "old_database": old_database,
                "new_database": new_database,
                "card_count": card_count,
                "message": f"Successfully switched to {new_database}",
            }
        )

    except Exception as e:
        logger.error(f"Failed to switch database: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/database-options", response_class=HTMLResponse)
async def get_database_options():
    """Get database options as HTML for dropdown population."""
    try:
        databases = get_available_databases()
        current_db = CURRENT_DATABASE

        html_options = []
        for db in databases:
            selected = "selected" if db["name"] == current_db else ""
            html_options.append(
                f'<option value="{db["name"]}" {selected}>'
                f"{db['display_name']} ({db['card_count']} cards, {db['tag_count']} tags)"
                f"</option>"
            )

        return HTMLResponse("\n".join(html_options))

    except Exception as e:
        logger.error(f"Failed to get database options: {e}")
        return HTMLResponse('<option value="">Error loading databases</option>')


@app.get("/api/current-database-info", response_class=HTMLResponse)
async def get_current_database_info():
    """Get current database info as HTML."""
    try:
        databases = get_available_databases()
        current_db = next(
            (db for db in databases if db["name"] == CURRENT_DATABASE), None
        )

        if current_db:
            return HTMLResponse(
                f"{current_db['display_name']} ({current_db['card_count']} cards, {current_db['tag_count']} tags)"
            )
        else:
            return HTMLResponse(f"{CURRENT_DATABASE} (unknown)")

    except Exception as e:
        logger.error(f"Failed to get current database info: {e}")
        return HTMLResponse("Error loading database info")


# Project Management API Endpoints
@app.get("/api/v2/projects/list")
async def list_available_projects(user_id: str = "default"):
    """List all available projects for the project dropdown."""
    try:
        from backend.models.projects import ProjectListResponse
        from backend.services.projects import discover_available_projects

        # Discover available projects
        projects = discover_available_projects()

        response = ProjectListResponse(
            projects=projects, count=len(projects), current_workspace=CURRENT_DATABASE
        )

        return response.dict()

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list projects: {str(e)}"
        )


@app.post("/api/v2/projects/switch")
async def switch_project(request: Request):
    """Switch to a different project workspace."""
    global CURRENT_DATABASE, TAG_TO_CARD_IDS

    try:
        from backend.models.projects import ProjectSwitchResponse
        from backend.services.projects import switch_workspace_context

        # Parse request data
        form_data = (
            await request.form()
            if request.headers.get("content-type", "").startswith(
                "application/x-www-form-urlencoded"
            )
            else None
        )
        if form_data:
            workspace_id = form_data.get("workspace_id")
            user_id = form_data.get("user_id", "default")
        else:
            json_data = await request.json()
            workspace_id = json_data.get("workspace_id")
            user_id = json_data.get("user_id", "default")

        if not workspace_id:
            raise HTTPException(status_code=400, detail="workspace_id is required")

        # Get current workspace
        current_workspace = CURRENT_DATABASE

        # Perform workspace switch
        switch_result = switch_workspace_context(
            from_workspace=current_workspace, to_workspace=workspace_id, user_id=user_id
        )

        if not switch_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=switch_result.get("error", "Failed to switch workspace"),
            )

        # Update global database selection
        CURRENT_DATABASE = workspace_id

        # Clear cached data
        TAG_TO_CARD_IDS.clear()

        # Render cards and tags for new workspace
        cards_html = render_cards_for_workspace(workspace_id, user_id)
        tags_html = render_tags_for_workspace(workspace_id, user_id)

        response = ProjectSwitchResponse(
            success=True,
            previous_workspace=switch_result["previous_workspace"],
            new_workspace=switch_result["new_workspace"],
            user_id=switch_result["user_id"],
            project_info=switch_result["project_info"],
            switch_time=switch_result["switch_time"],
            cards_html=cards_html,
            tags_html=tags_html,
        )

        return response.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching project: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to switch project: {str(e)}"
        )


@app.get("/api/v2/projects/current")
async def get_current_project_info(workspace_id: str = None, user_id: str = "default"):
    """Get information about the current project."""
    try:
        from backend.services.projects import (
            discover_available_projects,
            get_current_workspace_info,
        )

        current_workspace = workspace_id or CURRENT_DATABASE
        project_info = get_current_workspace_info(current_workspace, user_id)
        available_projects = discover_available_projects()

        response = {
            "workspace_id": current_workspace,
            "user_id": user_id,
            "project_info": project_info,
            "is_valid": project_info.get("is_valid", True),
            "available_projects_count": len(available_projects),
        }

        return response

    except Exception as e:
        logger.error(f"Error getting current project info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get project info: {str(e)}"
        )


def render_cards_for_workspace(workspace_id: str, user_id: str) -> str:
    """Render cards HTML for a specific workspace."""
    try:
        # Use existing card rendering logic
        with get_database_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM cards ORDER BY id")
            card_ids = [row[0] for row in cursor.fetchall()]

        return render_card_display_optimized(
            card_ids=card_ids,
            tags_to_highlight=[],
            customer_id=workspace_id,
        )
    except Exception as e:
        logger.error(f"Error rendering cards for workspace {workspace_id}: {e}")
        return f"<div>Error loading cards for {workspace_id}</div>"


def render_tags_for_workspace(workspace_id: str, user_id: str) -> str:
    """Render tags HTML for a specific workspace."""
    try:
        # Use existing tag logic
        with get_database_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT DISTINCT tag_name FROM tags ORDER BY tag_name")
            tags = [row[0] for row in cursor.fetchall()]

        if not tags:
            return "<div class='tag-cloud'>No tags available</div>"

        tag_elements = []
        for tag in tags:
            tag_elements.append(f'<span class="tag" data-tag="{tag}">{tag}</span>')

        return f'<div class="tag-cloud">{"".join(tag_elements)}</div>'
    except Exception as e:
        logger.error(f"Error rendering tags for workspace {workspace_id}: {e}")
        return f"<div>Error loading tags for {workspace_id}</div>"


@app.post("/api/v2/checkbox/dispatch")
async def handle_checkbox_dispatch(request: CheckboxDispatchRequest) -> dict:
    """
    Unified checkbox dispatch endpoint for polymorphic checkbox handling.

    This endpoint routes checkbox events to appropriate handlers based on the
    checkbox_id, providing a unified interface for all checkbox interactions.

    Args:
        request: CheckboxDispatchRequest containing checkbox_id, enabled state,
                and context (workspace_id, user_id)

    Returns:
        Dict containing handler result with appropriate HTMX targets and HTML

    Raises:
        HTTPException: 400 if checkbox_id is unknown
        HTTPException: 500 if handler execution fails
    """
    if dispatch_checkbox is None:
        raise HTTPException(
            status_code=500, detail="Checkbox dispatch system not available"
        )

    try:
        # Persist checkbox state to database
        try:
            from backend.services.checkbox.state import persist_checkbox_state

            persist_checkbox_state(request)
        except ImportError:
            logger.warning("Checkbox state persistence not available")

        # Dispatch to appropriate handler
        result = dispatch_checkbox(request)

        # Handle display effects (show/hide cards)
        if result.get("checkbox_effect") in ["display_all", "display_none"]:
            try:
                # Import card rendering function
                from services.render_optimized import render_card_display_optimized

                # Determine what cards to show
                show_all = result.get("checkbox_effect") == "display_all"

                if show_all:
                    # Get all cards for the workspace
                    with get_database_connection() as db:
                        cursor = db.cursor()
                        cursor.execute("SELECT id FROM cards")
                        card_ids = [row[0] for row in cursor.fetchall()]
                else:
                    # No cards to show
                    card_ids = []

                # Render cards HTML
                cards_html = render_card_display_optimized(
                    card_ids=card_ids,
                    tags_to_highlight=[],
                    customer_id=get_customer_id(),
                )

                result["html"] = cards_html
                result["hx_target"] = "#multicardz-display-surface"

            except Exception as e:
                logger.error(
                    f"Error rendering cards for checkbox {request.checkbox_id}: {e}"
                )
                # Continue without HTML rendering
                pass

        # Ensure response structure is consistent
        response = {
            "success": True,
            "checkbox_id": request.checkbox_id,
            "enabled": request.enabled,
            **result,
        }

        return response

    except ValueError as e:
        # Unknown checkbox_id
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handler execution failed
        logger.error(f"Checkbox dispatch error for {request.checkbox_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Handler execution failed: {str(e)}"
        )


# Test comment to trigger auto-reload - RELOAD TEST SUCCESS - TUTORIAL TAGS SCHEMA FIXED
if __name__ == "__main__":
    import uvicorn

    # Log testing mode status on startup
    if TESTING_MODE:
        pass

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8012)))
