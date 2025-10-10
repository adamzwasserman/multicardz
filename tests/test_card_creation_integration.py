"""
BDD tests for card creation integration with browser database.
"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Load all scenarios from the feature file
scenarios('../tests/features/card_creation_integration.feature')


# ============================================================================
# GIVEN Steps (Test Setup)
# ============================================================================

@given('the browser database is initialized', target_fixture='initialized_browser_db')
def browser_database_initialized(mock_browser_database_initialized):
    """Browser database is initialized and ready."""
    return mock_browser_database_initialized


@given('I am in privacy mode', target_fixture='current_mode')
def in_privacy_mode(privacy_mode_context):
    """Set current mode to privacy."""
    return privacy_mode_context


@given('I am in normal mode', target_fixture='current_mode')
def in_normal_mode(normal_mode_context):
    """Set current mode to normal."""
    return normal_mode_context


@given(parsers.parse('I have row tag "{row_tag}" and column tag "{col_tag}"'), target_fixture='dimensional_tags')
def have_dimensional_tags(row_tag, col_tag):
    """Set dimensional tags for grid cell."""
    return {"row_tag": row_tag, "column_tag": col_tag}


@given('the browser database is unavailable', target_fixture='browser_db_unavailable')
def browser_database_unavailable():
    """Mock unavailable browser database."""
    mock = Mock()
    mock.execute = AsyncMock(side_effect=Exception("Database unavailable"))
    return mock


# ============================================================================
# WHEN Steps (Actions)
# ============================================================================

@when(parsers.parse('I create a new card with name "{name}" and tags "{tags}"'), target_fixture='created_card')
def create_card_with_tags(initialized_browser_db, current_mode, name, tags):
    """Create a new card with specified name and tags."""
    from apps.shared.services.card_creation_integration import create_card_with_routing
    import asyncio

    tag_list = tags.split(',')
    tag_ids = [f"{tag}-uuid" for tag in tag_list]

    result = asyncio.run(create_card_with_routing(
        name=name,
        tags=tag_list,
        tag_ids=tag_ids,
        user_id=current_mode["user_id"],
        workspace_id=current_mode["workspace_id"],
        mode=current_mode["mode"],
        browser_db=initialized_browser_db
    ))

    return result


@when('I create a card from grid cell', target_fixture='created_card')
def create_card_from_grid(initialized_browser_db, current_mode, dimensional_tags):
    """Create card from grid cell with dimensional tags."""
    from apps.shared.services.card_creation_integration import create_card_from_grid_cell
    import asyncio

    result = asyncio.run(create_card_from_grid_cell(
        row_tag=dimensional_tags["row_tag"],
        column_tag=dimensional_tags["column_tag"],
        user_id=current_mode["user_id"],
        workspace_id=current_mode["workspace_id"],
        mode=current_mode["mode"],
        browser_db=initialized_browser_db
    ))

    return result


@when(parsers.parse('I create a card with tags "{tags}"'), target_fixture='created_card')
def create_card_with_bitmap_calc(initialized_browser_db, current_mode, tags, mock_tag_bitmaps):
    """Create card with bitmap calculation."""
    from apps.shared.services.card_creation_integration import create_card_with_routing
    import asyncio

    tag_list = tags.split(',')
    tag_ids = [f"{tag}-uuid" for tag in tag_list]

    result = asyncio.run(create_card_with_routing(
        name="Test Card",
        tags=tag_list,
        tag_ids=tag_ids,
        user_id=current_mode["user_id"],
        workspace_id=current_mode["workspace_id"],
        mode=current_mode["mode"],
        browser_db=initialized_browser_db,
        tag_bitmaps=mock_tag_bitmaps
    ))

    return result


@when('I attempt to create a card', target_fixture='creation_attempt')
def attempt_create_card(browser_db_unavailable, current_mode):
    """Attempt to create card when database is unavailable."""
    from apps.shared.services.card_creation_integration import create_card_with_routing
    import asyncio

    result = asyncio.run(create_card_with_routing(
        name="Test Card",
        tags=["tag1"],
        tag_ids=["tag1-uuid"],
        user_id=current_mode["user_id"],
        workspace_id=current_mode["workspace_id"],
        mode=current_mode["mode"],
        browser_db=browser_db_unavailable
    ))
    return result


@when('I create a new card', target_fixture='created_card')
def create_new_card(initialized_browser_db, current_mode):
    """Create a new card with default values."""
    from apps.shared.services.card_creation_integration import create_card_with_routing
    import asyncio

    result = asyncio.run(create_card_with_routing(
        name="Untitled",
        tags=[],
        tag_ids=[],
        user_id=current_mode["user_id"],
        workspace_id=current_mode["workspace_id"],
        mode=current_mode["mode"],
        browser_db=initialized_browser_db
    ))

    return result


# ============================================================================
# THEN Steps (Assertions)
# ============================================================================

@then('the card should be stored in browser database')
def card_stored_in_browser(created_card, initialized_browser_db):
    """Verify card was stored in browser database."""
    assert created_card.success is True
    assert created_card.storage_location == "browser"
    assert initialized_browser_db.execute.called


@then('the card bitmap should be calculated')
def bitmap_calculated(created_card):
    """Verify card bitmap was calculated."""
    assert hasattr(created_card, "card_bitmap")
    assert isinstance(created_card.card_bitmap, int)


@then('the bitmap should sync to server')
def bitmap_synced_to_server(created_card):
    """Verify bitmap was synced to server."""
    assert created_card.bitmap_synced is True


@then('the card content should not be transmitted to server')
def no_content_transmitted(created_card):
    """Verify no content was sent to server."""
    assert created_card.content_transmitted is False


@then('the card should appear in the grid')
def card_appears_in_grid(created_card):
    """Verify card appears in grid."""
    assert created_card.render_triggered is True


@then('the card should include dimensional tags')
def includes_dimensional_tags(created_card, dimensional_tags):
    """Verify dimensional tags are included."""
    tags = created_card.tags
    assert dimensional_tags["row_tag"] in tags
    assert dimensional_tags["column_tag"] in tags


@then('the card should be stored locally')
def stored_locally(created_card):
    """Verify card stored locally."""
    assert created_card.storage_location in ["browser", "local"]


@then('the card should appear in the correct grid cell')
def appears_in_correct_cell(created_card):
    """Verify card appears in correct grid cell."""
    assert created_card.grid_cell_placement is True


@then('the card should be stored on server')
def stored_on_server(created_card):
    """Verify card stored on server."""
    assert created_card.storage_location == "server"


@then('the card bitmap should be calculated from tag bitmaps')
def bitmap_from_tag_bitmaps(created_card):
    """Verify bitmap calculated from tag bitmaps."""
    assert hasattr(created_card, "card_bitmap")
    # Bitmap should be OR of all tag bitmaps
    assert created_card.card_bitmap > 0


@then('the bitmap should be synced to server')
def bitmap_synced(created_card):
    """Verify bitmap synced to server."""
    assert created_card.bitmap_synced is True


@then('the card content should remain local')
def content_remains_local(created_card):
    """Verify content stays local."""
    assert created_card.content_transmitted is False


@then('I should see an error message')
def see_error_message(creation_attempt):
    """Verify error message is shown."""
    assert creation_attempt.success is False
    assert creation_attempt.error is not None


@then('the UI should remain functional')
def ui_remains_functional(creation_attempt):
    """Verify UI stays functional after error."""
    # Error should be handled gracefully (returned CardCreationResult, not exception)
    from apps.shared.services.card_creation_integration import CardCreationResult
    assert isinstance(creation_attempt, CardCreationResult)


@then('no partial data should be synced')
def no_partial_sync(creation_attempt):
    """Verify no partial data was synced."""
    assert creation_attempt.bitmap_synced is not True


@then('the card should be created successfully')
def card_created_successfully(created_card):
    """Verify card was created successfully."""
    assert created_card.success is True
    assert hasattr(created_card, "card_id")


@then('the card title should be focused for editing')
def title_focused(created_card):
    """Verify card title is focused."""
    assert created_card.title_focused is True


@then('the card should be visible in the grid')
def visible_in_grid(created_card):
    """Verify card is visible in grid."""
    assert created_card.render_triggered is True
