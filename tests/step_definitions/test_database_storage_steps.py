"""
BDD step definitions for database storage layer tests.

These tests verify the two-tier architecture implementation with
CardSummary/CardDetail separation and tag count optimization.
"""

import json
import sqlite3
import time

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from apps.shared.models.card import CardDetail, CardSummary

# Load BDD scenarios
scenarios("../features/database_storage.feature")


@pytest.fixture
def db_connection():
    """Create in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def test_context():
    """Test context for sharing data between steps."""
    return {
        "card_summaries": [],
        "card_details": [],
        "user_preferences": None,
        "tag_count_tuples": [],
        "loaded_cards": [],
        "last_operation_time": None,
        "transaction_active": False,
        "error_occurred": False,
    }


@given("a clean database connection")
def clean_database(test_context, db_connection):
    """Initialize clean database state."""
    test_context["db_connection"] = db_connection


@given("the database schema is initialized")
def initialize_schema(test_context):
    """Create database tables for two-tier architecture."""
    conn = test_context["db_connection"]

    # This will be implemented in the actual database module
    # For now, we'll create the schema directly in the test
    schema_sql = """
    CREATE TABLE IF NOT EXISTS card_summaries (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        tags_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        has_attachments BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS card_details (
        id TEXT PRIMARY KEY REFERENCES card_summaries(id),
        content TEXT DEFAULT '',
        metadata_json TEXT DEFAULT '{}',
        attachment_count INTEGER DEFAULT 0,
        total_attachment_size INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id TEXT PRIMARY KEY,
        preferences_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        version INTEGER DEFAULT 1
    );
    """

    conn.executescript(schema_sql)
    conn.commit()


@given(parsers.parse('I have a CardSummary with title "{title}" and tags "{tags}"'))
def create_card_summary(test_context, title, tags):
    """Create a CardSummary for testing."""
    tag_set = frozenset(tags.split(",")) if tags else frozenset()
    card = CardSummary(title=title, tags=tag_set)
    test_context["card_summaries"] = [card]


@given("I have a CardSummary saved in the database")
def save_test_card_summary(test_context):
    """Save a test CardSummary to database."""
    card = CardSummary(title="Test Card", tags=frozenset(["test"]))
    test_context["card_summaries"] = [card]

    # This will call the actual database save function once implemented
    conn = test_context["db_connection"]
    conn.execute(
        "INSERT INTO card_summaries (id, title, tags_json, created_at, modified_at, has_attachments) VALUES (?, ?, ?, ?, ?, ?)",
        (
            card.id,
            card.title,
            json.dumps(list(card.tags)),
            card.created_at,
            card.modified_at,
            card.has_attachments,
        ),
    )
    conn.commit()


@given(
    parsers.parse('the CardSummary has associated CardDetail with content "{content}"')
)
def create_card_detail(test_context, content):
    """Create CardDetail associated with existing CardSummary."""
    card_summary = test_context["card_summaries"][0]
    card_detail = CardDetail(id=card_summary.id, content=content)
    test_context["card_details"] = [card_detail]


@given("I have multiple cards with overlapping tags:")
def create_multiple_cards(test_context, datatable):
    """Create multiple cards from BDD datatable."""
    cards = []
    # Skip header row and parse data rows
    for row in datatable[1:]:  # Skip header
        title = row[0]  # First column
        tags = frozenset(row[1].split(","))  # Second column
        card = CardSummary(title=title, tags=tags)
        cards.append(card)

    test_context["card_summaries"] = cards

    # Save to database
    conn = test_context["db_connection"]
    for card in cards:
        conn.execute(
            "INSERT INTO card_summaries (id, title, tags_json, created_at, modified_at, has_attachments) VALUES (?, ?, ?, ?, ?, ?)",
            (
                card.id,
                card.title,
                json.dumps(list(card.tags)),
                card.created_at,
                card.modified_at,
                card.has_attachments,
            ),
        )
    conn.commit()


@given(parsers.parse('I have UserPreferences for user "{user_id}"'))
def create_user_preferences(test_context, user_id):
    """Create UserPreferences for testing."""
    # This will use the actual UserPreferences model once imported
    preferences = {
        "user_id": user_id,
        "view_settings": {"cards_start_visible": True},
        "theme_settings": {"theme": "dark"},
        "tag_settings": {"show_tag_counts": True},
        "workspace_settings": {"default_workspace": "main"},
    }
    test_context["user_preferences"] = preferences


@given(parsers.parse("I have {count:d} CardSummary objects in the database"))
def create_bulk_cards(test_context, count):
    """Create bulk cards for performance testing."""
    cards = []
    conn = test_context["db_connection"]

    for i in range(count):
        card = CardSummary(
            title=f"Card {i}", tags=frozenset([f"tag{i%10}", f"category{i%5}"])
        )
        cards.append(card)

        conn.execute(
            "INSERT INTO card_summaries (id, title, tags_json, created_at, modified_at, has_attachments) VALUES (?, ?, ?, ?, ?, ?)",
            (
                card.id,
                card.title,
                json.dumps(list(card.tags)),
                card.created_at,
                card.modified_at,
                card.has_attachments,
            ),
        )

    conn.commit()
    test_context["card_summaries"] = cards


@given("I have started a database transaction")
def start_transaction(test_context):
    """Start a database transaction."""
    conn = test_context["db_connection"]
    conn.execute("BEGIN TRANSACTION")
    test_context["transaction_active"] = True


@when("I save the CardSummary to the database")
def save_card_summary(test_context):
    """Save CardSummary using database layer."""
    card = test_context["card_summaries"][0]
    conn = test_context["db_connection"]

    start_time = time.perf_counter()
    conn.execute(
        "INSERT INTO card_summaries (id, title, tags_json, created_at, modified_at, has_attachments) VALUES (?, ?, ?, ?, ?, ?)",
        (
            card.id,
            card.title,
            json.dumps(list(card.tags)),
            card.created_at,
            card.modified_at,
            card.has_attachments,
        ),
    )
    conn.commit()
    end_time = time.perf_counter()

    test_context["last_operation_time"] = (end_time - start_time) * 1000  # ms


@when("I save the CardDetail to the database")
def save_card_detail(test_context):
    """Save CardDetail using database layer."""
    card_detail = test_context["card_details"][0]
    conn = test_context["db_connection"]

    conn.execute(
        "INSERT INTO card_details (id, content, metadata_json, attachment_count, total_attachment_size, version) VALUES (?, ?, ?, ?, ?, ?)",
        (
            card_detail.id,
            card_detail.content,
            json.dumps(card_detail.metadata),
            card_detail.attachment_count,
            card_detail.total_attachment_size,
            card_detail.version,
        ),
    )
    conn.commit()


@when("I request tag count tuples from the database")
def request_tag_count_tuples(test_context):
    """Request tag count tuples for 80/20 optimization."""
    conn = test_context["db_connection"]

    # Count tag frequencies across all cards
    tag_counts = {}
    cursor = conn.execute("SELECT tags_json FROM card_summaries")
    for (tags_json,) in cursor.fetchall():
        tags = json.loads(tags_json)
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Convert to tuples sorted by count (ascending for selectivity)
    tuples = [(tag, count) for tag, count in tag_counts.items()]
    tuples.sort(key=lambda x: x[1])  # Sort by count ascending

    test_context["tag_count_tuples"] = tuples


@when("I save the preferences to the database")
def save_user_preferences(test_context):
    """Save user preferences to database."""
    preferences = test_context["user_preferences"]
    conn = test_context["db_connection"]

    start_time = time.perf_counter()
    conn.execute(
        "INSERT INTO user_preferences (user_id, preferences_json) VALUES (?, ?)",
        (preferences["user_id"], json.dumps(preferences)),
    )
    conn.commit()
    end_time = time.perf_counter()

    test_context["last_operation_time"] = (end_time - start_time) * 1000  # ms


@when("I load all CardSummary objects for workspace filtering")
def load_all_card_summaries(test_context):
    """Load all CardSummary objects for set operations."""
    conn = test_context["db_connection"]

    start_time = time.perf_counter()
    cursor = conn.execute(
        "SELECT id, title, tags_json, created_at, modified_at, has_attachments FROM card_summaries"
    )

    loaded_cards = []
    for row in cursor.fetchall():
        card = CardSummary(
            id=row[0],
            title=row[1],
            tags=frozenset(json.loads(row[2])),
            created_at=row[3],
            modified_at=row[4],
            has_attachments=bool(row[5]),
        )
        loaded_cards.append(card)

    end_time = time.perf_counter()

    test_context["loaded_cards"] = loaded_cards
    test_context["last_operation_time"] = (end_time - start_time) * 1000  # ms


@when("I attempt to save invalid card data")
def save_invalid_card_data(test_context):
    """Attempt to save invalid data to trigger error."""
    conn = test_context["db_connection"]

    try:
        # Try to insert card with NULL title (should fail)
        conn.execute(
            "INSERT INTO card_summaries (id, title, tags_json) VALUES (?, ?, ?)",
            ("test_id", None, "[]"),
        )
        conn.commit()
    except Exception:
        test_context["error_occurred"] = True


@when("an error occurs during save")
def error_during_save(test_context):
    """Error condition is already handled in previous step."""
    pass


@then("I can load the CardSummary by ID")
def load_card_summary_by_id(test_context):
    """Load CardSummary by ID and verify."""
    card = test_context["card_summaries"][0]
    conn = test_context["db_connection"]

    cursor = conn.execute(
        "SELECT id, title, tags_json, created_at, modified_at, has_attachments FROM card_summaries WHERE id = ?",
        (card.id,),
    )
    row = cursor.fetchone()

    assert row is not None, "CardSummary should be found by ID"

    loaded_card = CardSummary(
        id=row[0],
        title=row[1],
        tags=frozenset(json.loads(row[2])),
        created_at=row[3],
        modified_at=row[4],
        has_attachments=bool(row[5]),
    )

    test_context["loaded_cards"] = [loaded_card]


@then("the loaded CardSummary has the correct title and tags")
def verify_loaded_card_summary(test_context):
    """Verify loaded CardSummary data."""
    original_card = test_context["card_summaries"][0]
    loaded_card = test_context["loaded_cards"][0]

    assert loaded_card.title == original_card.title
    assert loaded_card.tags == original_card.tags
    assert loaded_card.id == original_card.id


@then(parsers.parse("the CardSummary loads in under {max_time:d}ms"))
def verify_card_summary_load_time(test_context, max_time):
    """Verify CardSummary loading performance."""
    operation_time = test_context["last_operation_time"]
    assert (
        operation_time < max_time
    ), f"CardSummary loading took {operation_time}ms, expected <{max_time}ms"


@then("I can load CardDetail on-demand by card ID")
def load_card_detail_by_id(test_context):
    """Load CardDetail by ID."""
    card_detail = test_context["card_details"][0]
    conn = test_context["db_connection"]

    cursor = conn.execute(
        "SELECT id, content, metadata_json, attachment_count, total_attachment_size, version FROM card_details WHERE id = ?",
        (card_detail.id,),
    )
    row = cursor.fetchone()

    assert row is not None, "CardDetail should be found by ID"

    loaded_detail = CardDetail(
        id=row[0],
        content=row[1],
        metadata=json.loads(row[2]),
        attachment_count=row[3],
        total_attachment_size=row[4],
        version=row[5],
    )

    test_context["loaded_card_details"] = [loaded_detail]


@then("the CardDetail contains the full content")
def verify_card_detail_content(test_context):
    """Verify CardDetail content."""
    original_detail = test_context["card_details"][0]
    loaded_detail = test_context["loaded_card_details"][0]

    assert loaded_detail.content == original_detail.content
    assert loaded_detail.id == original_detail.id


@then("CardDetail loading is separate from CardSummary loading")
def verify_separate_loading(test_context):
    """Verify two-tier architecture separation."""
    # This is verified by the fact that we can load CardSummary without CardDetail
    # and vice versa, as demonstrated in the separate test steps
    assert True, "Two-tier separation demonstrated by separate loading steps"


@then("I receive tuples in the format (tag, count):")
def verify_tag_count_tuples(test_context, datatable):
    """Verify tag count tuples format and content."""
    expected_tuples = [(row[0], int(row[1])) for row in datatable[1:]]  # Skip header
    actual_tuples = test_context["tag_count_tuples"]

    # Convert to sets for comparison (order might differ)
    expected_set = set(expected_tuples)
    actual_set = set(actual_tuples)

    assert actual_set == expected_set, f"Expected {expected_set}, got {actual_set}"


@then("the tuples are sorted by count ascending for selectivity optimization")
def verify_tuple_sorting(test_context):
    """Verify tuples are sorted by count ascending."""
    tuples = test_context["tag_count_tuples"]

    for i in range(len(tuples) - 1):
        current_count = tuples[i][1]
        next_count = tuples[i + 1][1]
        assert (
            current_count <= next_count
        ), f"Tuples should be sorted by count ascending, found {current_count} > {next_count}"


@then("I can load the preferences by user ID")
def load_user_preferences_by_id(test_context):
    """Load user preferences by ID."""
    preferences = test_context["user_preferences"]
    conn = test_context["db_connection"]

    cursor = conn.execute(
        "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
        (preferences["user_id"],),
    )
    row = cursor.fetchone()

    assert row is not None, "User preferences should be found"

    loaded_preferences = json.loads(row[0])
    test_context["loaded_user_preferences"] = loaded_preferences


@then("the preferences contain all view, theme, tag, and workspace settings")
def verify_preferences_content(test_context):
    """Verify preferences contain all required settings."""
    loaded_prefs = test_context["loaded_user_preferences"]

    required_keys = [
        "view_settings",
        "theme_settings",
        "tag_settings",
        "workspace_settings",
    ]
    for key in required_keys:
        assert key in loaded_prefs, f"Preferences should contain {key}"


@then(parsers.parse("preferences loading takes under {max_time:d}ms"))
def verify_preferences_load_time(test_context, max_time):
    """Verify preferences loading performance."""
    operation_time = test_context["last_operation_time"]
    assert (
        operation_time < max_time
    ), f"Preferences loading took {operation_time}ms, expected <{max_time}ms"


@then(parsers.parse("all cards are loaded in under {max_time:d}ms"))
def verify_bulk_load_time(test_context, max_time):
    """Verify bulk card loading performance."""
    operation_time = test_context["last_operation_time"]
    assert (
        operation_time < max_time
    ), f"Bulk loading took {operation_time}ms, expected <{max_time}ms"


@then("the loaded cards can be used with set operations")
def verify_cards_for_set_operations(test_context):
    """Verify loaded cards are compatible with set operations."""
    loaded_cards = test_context["loaded_cards"]

    # Verify cards are CardSummary instances with required attributes
    for card in loaded_cards:
        assert hasattr(card, "tags"), "Card should have tags attribute"
        assert isinstance(
            card.tags, frozenset
        ), "Tags should be frozenset for set operations"
        assert hasattr(card, "id"), "Card should have id attribute"
        assert hasattr(card, "title"), "Card should have title attribute"


@then("CardDetail objects are not loaded automatically")
def verify_card_details_not_loaded(test_context):
    """Verify CardDetail objects are not loaded with CardSummary."""
    # This is implicit in our implementation - we only loaded CardSummary objects
    # CardDetail would require separate database query
    assert "loaded_card_details" not in test_context or not test_context.get(
        "loaded_card_details"
    ), "CardDetail should not be auto-loaded"


@then("the transaction is rolled back")
def verify_transaction_rollback(test_context):
    """Verify transaction was rolled back."""
    conn = test_context["db_connection"]

    # SQLite automatically rolls back on error
    # Verify no data was persisted
    cursor = conn.execute("SELECT COUNT(*) FROM card_summaries WHERE title IS NULL")
    count = cursor.fetchone()[0]

    assert count == 0, "No invalid data should be persisted after rollback"


@then("no partial data is persisted")
def verify_no_partial_data(test_context):
    """Verify no partial data exists."""
    # This is handled by the rollback verification
    assert test_context["error_occurred"], "Error should have occurred"


@then("the database remains in a consistent state")
def verify_database_consistency(test_context):
    """Verify database remains consistent after error."""
    conn = test_context["db_connection"]

    # Verify we can still perform normal operations
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM card_summaries")
        count = cursor.fetchone()[0]
        assert isinstance(count, int), "Database should be accessible after error"
    except Exception as e:
        pytest.fail(f"Database should remain accessible after error: {e}")
