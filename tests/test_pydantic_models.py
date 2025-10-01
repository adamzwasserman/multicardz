"""BDD tests for Pydantic models with workspace isolation."""

import pytest
from pydantic import ValidationError
from pytest_bdd import given, scenarios, then, when

# Load scenarios from feature file
scenarios('features/pydantic_models.feature')

# Import fixtures


# Scenario: Create valid Card model

@given('I have card data with required fields', target_fixture='card_data_with_required_fields')
def card_data_with_required_fields(valid_card_data):
    """Store valid card data."""
    return valid_card_data


@when('I create a Card model instance', target_fixture='create_card_model')
def create_card_model(card_data_with_required_fields):
    """Attempt to create a Card model - should fail before implementation."""
    try:
        # Import will fail until we implement the model
        from apps.shared.models.zero_trust_models import Card
        return Card(**card_data_with_required_fields)
    except (ImportError, ModuleNotFoundError):
        pytest.fail("Card model not implemented yet")
    except ValidationError as e:
        pytest.fail(f"Validation error: {e}")


@then('the model should validate successfully')
def model_validates_successfully(create_card_model):
    """Verify the model was created successfully."""
    assert create_card_model is not None


@then('UUIDs should be generated automatically')
def uuids_generated_automatically(create_card_model):
    """Verify card_id was auto-generated."""
    assert hasattr(create_card_model, 'card_id')
    assert create_card_model.card_id is not None
    assert len(create_card_model.card_id) > 0


@then('tag arrays should default to empty')
def tag_arrays_default_empty(create_card_model):
    """Verify tag arrays default to empty lists."""
    assert hasattr(create_card_model, 'tag_ids')
    assert create_card_model.tag_ids == []


# Scenario: Validate Tag model with bitmap

@given('I have tag data with bitmap field', target_fixture='tag_data_with_bitmap')
def tag_data_with_bitmap(valid_tag_data):
    """Store valid tag data."""
    return valid_tag_data


@when('I create a Tag model instance', target_fixture='create_tag_model')
def create_tag_model(tag_data_with_bitmap):
    """Attempt to create a Tag model."""
    try:
        from apps.shared.models.zero_trust_models import Tag
        return Tag(**tag_data_with_bitmap)
    except (ImportError, ModuleNotFoundError):
        pytest.fail("Tag model not implemented yet")
    except ValidationError as e:
        pytest.fail(f"Validation error: {e}")


@then('the bitmap should be an integer')
def bitmap_is_integer(create_tag_model):
    """Verify bitmap is an integer."""
    assert hasattr(create_tag_model, 'tag_bitmap')
    assert isinstance(create_tag_model.tag_bitmap, int)


@then('card_count should default to 0')
def card_count_defaults_to_zero(create_tag_model):
    """Verify card_count defaults to 0."""
    assert hasattr(create_tag_model, 'card_count')
    assert create_tag_model.card_count == 0


@then('the model should be frozen')
def model_is_frozen(create_tag_model):
    """Verify the model is immutable (frozen)."""
    with pytest.raises(ValidationError):
        create_tag_model.name = "Modified Name"


# Scenario: Reject invalid workspace isolation

@given('I have card data without workspace_id', target_fixture='card_data_without_workspace')
def card_data_without_workspace(invalid_isolation_data):
    """Store invalid card data."""
    return invalid_isolation_data


@when('I try to create a Card model', target_fixture='try_create_card_without_workspace')
def try_create_card_without_workspace(card_data_without_workspace):
    """Attempt to create Card without workspace_id."""
    try:
        from apps.shared.models.zero_trust_models import Card
        try:
            card = Card(**card_data_without_workspace)
            return {"success": True, "card": card}
        except ValidationError as e:
            return {"success": False, "error": e}
    except (ImportError, ModuleNotFoundError):
        pytest.fail("Card model not implemented yet")


@then('validation should fail')
def validation_should_fail(try_create_card_without_workspace):
    """Verify validation failed."""
    assert try_create_card_without_workspace["success"] is False


@then('error should mention missing workspace_id')
def error_mentions_workspace_id(try_create_card_without_workspace):
    """Verify error message mentions workspace_id."""
    error = try_create_card_without_workspace["error"]
    error_str = str(error)
    assert "workspace_id" in error_str.lower()
