"""
BDD tests for multicardz™ models.
"""

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from apps.shared.models import CardSummary, Workspace

# Load scenarios from feature file
scenarios("features/models.feature")


@given(
    parsers.parse('I have card data with title "{title}" and tags "{tags}"'),
    target_fixture="card_data",
)
def card_data(title, tags):
    """Store card data for test."""
    return {"title": title, "tags": frozenset(tags.split(","))}


@given(
    parsers.parse('I have workspace data with name "{name}" and owner "{owner}"'),
    target_fixture="workspace_data",
)
def workspace_data(name, owner):
    """Store workspace data for test."""
    return {"name": name, "owner_id": owner}


@given(
    parsers.parse('I have a card with tags "{tags}"'), target_fixture="card_with_tags"
)
def card_with_tags(tags):
    """Create a card with specific tags."""
    return CardSummary(title="Test Card", tags=frozenset(tags.split(",")))


@when("I create a CardSummary instance", target_fixture="create_card")
def create_card(card_data):
    """Create a CardSummary instance from data."""
    return CardSummary(**card_data)


@when("I create a Workspace instance", target_fixture="create_workspace")
def create_workspace(workspace_data):
    """Create a Workspace instance from data."""
    return Workspace(**workspace_data)


@when("I try to modify the tags", target_fixture="modify_tags")
def modify_tags(card_with_tags):
    """Attempt to modify card tags."""
    try:
        # This should fail due to frozen model
        card_with_tags.tags = frozenset(["modified"])
        return "success"
    except (ValidationError, AttributeError) as e:
        return f"error: {type(e).__name__}"


@then("the card should have the correct title and tags")
def verify_card_data(create_card, card_data):
    """Verify card has correct data."""
    card = create_card
    assert card.title == card_data["title"]
    assert card.tags == card_data["tags"]


@then("the card should be immutable")
def verify_card_immutable(create_card):
    """Verify card cannot be modified."""
    card = create_card
    with pytest.raises((ValidationError, AttributeError)):
        card.title = "Modified Title"


@then("the workspace should have the correct name and owner")
def verify_workspace_data(create_workspace, workspace_data):
    """Verify workspace has correct data."""
    workspace = create_workspace
    assert workspace.name == workspace_data["name"]
    assert workspace.owner_id == workspace_data["owner_id"]


@then("the workspace should be immutable")
def verify_workspace_immutable(create_workspace):
    """Verify workspace cannot be modified."""
    workspace = create_workspace
    with pytest.raises((ValidationError, AttributeError)):
        workspace.name = "Modified Name"


@then("the modification should fail")
def verify_modification_failed(modify_tags):
    """Verify that tag modification failed."""
    result = modify_tags
    assert result.startswith("error:")


@then("the original tags should remain unchanged")
def verify_tags_unchanged(card_with_tags):
    """Verify original tags are preserved."""
    expected_tags = frozenset(["video", "urgent"])
    assert card_with_tags.tags == expected_tags
