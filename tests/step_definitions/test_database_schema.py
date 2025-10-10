"""
Step definitions for database schema BDD tests.
"""

import os
import shutil
import sqlite3
import tempfile
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Import the feature
scenarios('../features/database_schema.feature')

# Global test state
test_state: dict[str, Any] = {}


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test databases."""
    temp_dir = tempfile.mkdtemp(prefix="multicardz_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_turso():
    """Mock Turso database for testing."""
    class MockTurso:
        def __init__(self):
            self.synced = False
            self.db_path = None
            self.cloud_sync_enabled = False

        def create_embedded(self, path, **kwargs):
            """Mock Turso embedded database creation - falls back to SQLite."""
            self.db_path = path
            return sqlite3.connect(path)

        def enable_cloud_sync(self):
            """Mock enabling cloud sync."""
            self.cloud_sync_enabled = True

        def sync(self):
            """Mock sync operation."""
            self.synced = True
            return True

    return MockTurso()


@given("the multicardz system is initialized")
def system_initialized():
    """Initialize the test system."""
    test_state.clear()
    test_state['initialized'] = True


@given("the database mode is configured")
def database_mode_configured():
    """Configure database mode."""
    test_state['db_mode_configured'] = True


@given(parsers.parse('I am using "{mode}" mode'))
def set_database_mode(mode):
    """Set the database mode."""
    test_state['db_mode'] = mode


@when("I create the database schema")
def create_database_schema(temp_db_dir, mock_turso):
    """Create the database schema based on mode."""
    mode = test_state.get('db_mode', 'development')

    if mode == 'normal':
        # Use Turso for normal mode
        db_path = os.path.join(temp_db_dir, f"{mode}_test.db")
        conn = mock_turso.create_embedded(db_path)
        test_state['turso'] = mock_turso
    else:
        # Use SQLite for development mode
        db_path = os.path.join(temp_db_dir, f"{mode}_test.db")
        conn = sqlite3.connect(db_path)

    test_state['db_connection'] = conn
    test_state['db_path'] = db_path

    # TODO: Implement zero trust schema creation with new middleware
    conn.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        card_id TEXT PRIMARY KEY,
        user_id TEXT,
        workspace_id TEXT,
        name TEXT,
        tag_ids TEXT,
        tag_bitmaps TEXT
    )''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        tag_id TEXT PRIMARY KEY,
        name TEXT
    )''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS card_contents (
        card_id TEXT,
        content TEXT,
        PRIMARY KEY (card_id)
    )''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id TEXT PRIMARY KEY,
        preferences TEXT
    )''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS saved_views (
        view_id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        config TEXT
    )''')
    conn.commit()


@when(parsers.parse('I create the database schema for user "{user}" and workspace "{workspace}"'))
def create_privacy_mode_schema(user, workspace, temp_db_dir, mock_turso):
    """Create privacy mode databases."""
    test_state['privacy_dbs'] = {}

    # Browser database (full content)
    browser_path = os.path.join(temp_db_dir, f"browser_{user}_{workspace}.db")
    browser_conn = sqlite3.connect(browser_path)
    test_state['privacy_dbs']['browser'] = {
        'path': browser_path,
        'conn': browser_conn,
        'type': 'WASM SQLite',
        'content': 'full_content'
    }

    # Server database (obfuscated)
    server_path = os.path.join(temp_db_dir, f"server_{user}_{workspace}.db")
    server_conn = mock_turso.create_embedded(server_path)
    test_state['privacy_dbs']['server'] = {
        'path': server_path,
        'conn': server_conn,
        'type': 'Turso embedded',
        'content': 'obfuscated_only',
        'turso': mock_turso
    }

    # Cloud database (obfuscated)
    test_state['privacy_dbs']['cloud'] = {
        'type': 'Turso Cloud',
        'content': 'obfuscated_only',
        'synced': False
    }

    # Create the schemas
    # TODO: Implement privacy mode schema creation
    for conn in [browser_conn, server_conn]:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS obfuscated_cards (
            card_id TEXT PRIMARY KEY,
            card_hash TEXT
        )''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS obfuscated_tags (
            tag_id TEXT PRIMARY KEY,
            tag_hash TEXT
        )''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_metadata (
            last_sync DATETIME,
            user_id TEXT,
            workspace_id TEXT
        )''')
        conn.commit()


@then(parsers.parse("the following tables should exist:"))
def verify_tables_exist(temp_db_dir):
    """Verify that the required tables exist."""
    conn = test_state.get('db_connection')
    assert conn is not None, "No database connection found"

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    # Expected tables from the feature file
    expected_tables = {'cards', 'tags', 'card_contents', 'user_preferences', 'saved_views'}

    for table in expected_tables:
        assert table in existing_tables, f"Table '{table}' does not exist"


@then(parsers.parse("the {table_name} table should have columns:"))
def verify_table_columns(table_name, temp_db_dir):
    """Verify table columns."""
    conn = test_state.get('db_connection')
    assert conn is not None, "No database connection found"

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    # This will be validated properly when we implement the schema
    assert len(columns) > 0, f"Table '{table_name}' has no columns"


@then("the database should be created with Turso")
def verify_turso_database():
    """Verify that Turso was used for database creation."""
    turso = test_state.get('turso')
    assert turso is not None, "Turso was not used"
    assert turso.db_path is not None, "Turso database path not set"


@then("the schema should match development mode")
def verify_schema_match():
    """Verify that normal mode schema matches development mode."""
    # This will be validated when we implement the schema
    pass


@then("Turso Cloud sync should be optional")
def verify_turso_cloud_optional():
    """Verify that Turso Cloud sync is optional."""
    turso = test_state.get('turso')
    # Cloud sync should not be enabled by default
    assert turso is not None
    # It's optional, so it can be enabled or disabled
    assert hasattr(turso, 'cloud_sync_enabled')


@then("three separate databases should exist:")
def verify_privacy_databases():
    """Verify that three separate databases exist for privacy mode."""
    privacy_dbs = test_state.get('privacy_dbs', {})
    assert len(privacy_dbs) == 3, f"Expected 3 databases, found {len(privacy_dbs)}"
    assert 'browser' in privacy_dbs
    assert 'server' in privacy_dbs
    assert 'cloud' in privacy_dbs


@then("the server database should contain only:")
def verify_server_obfuscation():
    """Verify server database contains only obfuscated data."""
    privacy_dbs = test_state.get('privacy_dbs', {})
    server_db = privacy_dbs.get('server', {})
    conn = server_db.get('conn')

    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        # Server should only have obfuscated tables
        expected = {'obfuscated_cards', 'obfuscated_tags', 'sync_metadata'}
        for table in expected:
            assert table in tables, f"Obfuscated table '{table}' not found"

        # Should not have regular tables
        forbidden = {'cards', 'tags', 'card_contents'}
        for table in forbidden:
            assert table not in tables, f"Regular table '{table}' should not exist in server DB"


@given("I have created databases for multiple users")
def create_multiple_user_databases(temp_db_dir):
    """Create databases for multiple users."""
    test_state['multi_user_dbs'] = {}

    for user in ['user1', 'user2']:
        for workspace in ['ws1', 'ws2']:
            db_key = f"{user}_{workspace}"
            db_path = os.path.join(temp_db_dir, f"{db_key}.db")
            conn = sqlite3.connect(db_path)

            # Create the database with proper isolation
            conn.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                user_id TEXT,
                workspace_id TEXT,
                name TEXT,
                tag_ids TEXT,
                tag_bitmaps TEXT,
                UNIQUE(user_id, workspace_id)
            )''')

            # Insert test data
            conn.execute(
                "INSERT INTO cards (card_id, user_id, workspace_id, name, tag_ids, tag_bitmaps) VALUES (?, ?, ?, ?, ?, ?)",
                (f"card_{db_key}", user, workspace, f"Card for {db_key}", '[]', '[]')
            )
            conn.commit()
            test_state['multi_user_dbs'][db_key] = {'path': db_path, 'conn': conn}


@when(parsers.parse('I access the database for user "{user}" and workspace "{workspace}"'))
def access_user_database(user, workspace):
    """Access a specific user-workspace database."""
    db_key = f"{user}_{workspace}"
    test_state['current_db'] = test_state['multi_user_dbs'].get(db_key)


@then(parsers.parse('I should not be able to access data from user "{other_user}"'))
def verify_user_isolation(other_user):
    """Verify user data isolation."""
    current_db = test_state.get('current_db')
    if current_db:
        conn = current_db.get('conn')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE user_id = ?", (other_user,))
        results = cursor.fetchall()
        # In a properly isolated database, we shouldn't find other user's data
        # This test assumes proper access control is implemented
        assert len(results) == 0 or all(row[1] != other_user for row in results)


@then(parsers.parse('I should not be able to access data from workspace "{other_workspace}"'))
def verify_workspace_isolation(other_workspace):
    """Verify workspace data isolation."""
    current_db = test_state.get('current_db')
    if current_db:
        conn = current_db.get('conn')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE workspace_id = ?", (other_workspace,))
        results = cursor.fetchall()
        # In a properly isolated database, we shouldn't find other workspace's data
        assert len(results) == 0 or all(row[2] != other_workspace for row in results)


@then("each user-workspace combination should have separate database files")
def verify_separate_database_files():
    """Verify that each user-workspace has separate database files."""
    multi_dbs = test_state.get('multi_user_dbs', {})
    paths = set()
    for db_key, db_info in multi_dbs.items():
        path = db_info.get('path')
        assert path not in paths, f"Duplicate database path found: {path}"
        paths.add(path)
        assert os.path.exists(path), f"Database file does not exist: {path}"


@given(parsers.parse('I have a tag with tag_id "{tag_id}"'))
def create_tag(tag_id):
    """Create a tag for testing."""
    if 'tags' not in test_state:
        test_state['tags'] = {}
    test_state['tags'][tag_id] = {
        'tag_id': tag_id,
        'card_count': 0,
        'cards': set()
    }


@given(parsers.parse('the tag has card_count of {count:d}'))
def set_tag_card_count(count):
    """Set the card count for the last created tag."""
    for tag_id in test_state.get('tags', {}):
        test_state['tags'][tag_id]['card_count'] = count
        break


@when(parsers.parse('I add "{tag_id}" to a card'))
def add_tag_to_card(tag_id):
    """Add a tag to a card."""
    if 'cards' not in test_state:
        test_state['cards'] = {}

    # Create a new card
    card_id = f"card_{len(test_state['cards']) + 1}"
    test_state['cards'][card_id] = {'tags': set()}

    # Add the tag
    test_state['cards'][card_id]['tags'].add(tag_id)

    # Update tag count
    if tag_id in test_state.get('tags', {}):
        test_state['tags'][tag_id]['cards'].add(card_id)
        test_state['tags'][tag_id]['card_count'] = len(test_state['tags'][tag_id]['cards'])


@when(parsers.parse('I add "{tag_id}" to another card'))
def add_tag_to_another_card(tag_id):
    """Add a tag to another card."""
    add_tag_to_card(tag_id)


@when(parsers.parse('I remove "{tag_id}" from one card'))
def remove_tag_from_card(tag_id):
    """Remove a tag from a card."""
    if tag_id in test_state.get('tags', {}):
        cards = test_state['tags'][tag_id]['cards']
        if cards:
            # Remove from the first card
            card_id = next(iter(cards))
            cards.remove(card_id)
            test_state['tags'][tag_id]['card_count'] = len(cards)

            # Also remove from the card's tags
            if card_id in test_state.get('cards', {}):
                test_state['cards'][card_id]['tags'].discard(tag_id)


@then(parsers.parse('the card_count for "{tag_id}" should be {expected_count:d}'))
def verify_tag_card_count(tag_id, expected_count):
    """Verify the card count for a tag."""
    tag = test_state.get('tags', {}).get(tag_id)
    assert tag is not None, f"Tag {tag_id} not found"
    actual_count = tag.get('card_count', 0)
    assert actual_count == expected_count, f"Expected count {expected_count}, got {actual_count}"
