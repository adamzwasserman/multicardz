"""
BDD tests for MultiCardz™ two-tier card model system.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when

from apps.shared.models import Attachment, CardDetail, CardSummary, UserTier

# Load scenarios from feature file
scenarios("features/card_models.feature")


@given(
    parsers.parse('I have card summary data with title "{title}" and tags "{tags}"'),
    target_fixture="card_summary_data",
)
def card_summary_data(title, tags):
    """Store card summary data for test."""
    return {"title": title, "tags": frozenset(tags.split(","))}


@given(
    parsers.parse(
        'I have card detail data with id "{card_id}" and content "{content}"'
    ),
    target_fixture="card_detail_data",
)
def card_detail_data(card_id, content):
    """Store card detail data for test."""
    return {"id": card_id, "content": content}


@given(
    parsers.parse(
        'I have attachment data with filename "{filename}" and size {size:d}'
    ),
    target_fixture="attachment_data",
)
def attachment_data(filename, size):
    """Store attachment data for test."""
    return {
        "card_id": "CARD1234",
        "filename": filename,
        "content_type": "application/pdf",
        "size_bytes": size,
        "data": b"fake pdf data",
    }


@given(
    parsers.parse(
        'I have user tier data for tier "{tier}" with storage quota {quota:d}GB'
    ),
    target_fixture="user_tier_data",
)
def user_tier_data(tier, quota):
    """Store user tier data for test."""
    return {
        "user_id": "USER123",
        "tier": tier,
        "max_attachment_size_mb": 25,
        "total_storage_quota_gb": quota,
    }


@given(
    parsers.parse("I have a UserTier with {quota:d}GB quota and {usage:d}GB usage"),
    target_fixture="user_tier_with_usage",
)
def user_tier_with_usage(quota, usage):
    """Create UserTier with specific quota and usage."""
    usage_bytes = usage * 1024 * 1024 * 1024  # Convert GB to bytes
    return UserTier(
        user_id="USER123",
        tier="pro",
        max_attachment_size_mb=25,
        total_storage_quota_gb=quota,
        current_storage_bytes=usage_bytes,
    )


@when("I create a CardSummary instance", target_fixture="create_card_summary")
def create_card_summary(card_summary_data):
    """Create a CardSummary instance from data."""
    return CardSummary(**card_summary_data)


@when("I create a CardDetail instance", target_fixture="create_card_detail")
def create_card_detail(card_detail_data):
    """Create a CardDetail instance from data."""
    return CardDetail(**card_detail_data)


@when("I create an Attachment instance", target_fixture="create_attachment")
def create_attachment(attachment_data):
    """Create an Attachment instance from data."""
    return Attachment(**attachment_data)


@when("I create a UserTier instance", target_fixture="create_user_tier")
def create_user_tier(user_tier_data):
    """Create a UserTier instance from data."""
    return UserTier(**user_tier_data)


@when("I check the storage calculations", target_fixture="storage_calculations")
def storage_calculations(user_tier_with_usage):
    """Check storage calculation properties."""
    return {
        "quota_bytes": user_tier_with_usage.storage_quota_bytes,
        "usage_percentage": user_tier_with_usage.storage_usage_percentage,
        "attachment_limit_bytes": user_tier_with_usage.attachment_size_limit_bytes,
    }


@then("the card summary should have the correct data")
def verify_card_summary_data(create_card_summary, card_summary_data):
    """Verify card summary has correct data."""
    card = create_card_summary
    assert card.title == card_summary_data["title"]
    assert card.tags == card_summary_data["tags"]
    assert isinstance(card.id, str)
    assert len(card.id) == 8


@then("the card summary should be immutable")
def verify_card_summary_immutable(create_card_summary):
    """Verify card summary cannot be modified."""
    card = create_card_summary
    with pytest.raises((ValidationError, AttributeError)):
        card.title = "Modified Title"


@then("the card summary should have timestamps")
def verify_card_summary_timestamps(create_card_summary):
    """Verify card summary has timestamp fields."""
    card = create_card_summary
    assert isinstance(card.created_at, datetime)
    assert isinstance(card.modified_at, datetime)
    assert isinstance(card.has_attachments, bool)


@then("the card detail should have the correct data")
def verify_card_detail_data(create_card_detail, card_detail_data):
    """Verify card detail has correct data."""
    card = create_card_detail
    assert card.id == card_detail_data["id"]
    assert card.content == card_detail_data["content"]
    assert isinstance(card.metadata, dict)
    assert card.version == 1


@then("the card detail should be immutable")
def verify_card_detail_immutable(create_card_detail):
    """Verify card detail cannot be modified."""
    card = create_card_detail
    with pytest.raises((ValidationError, AttributeError)):
        card.content = "Modified Content"


@then("the card detail should have version tracking")
def verify_card_detail_version(create_card_detail):
    """Verify card detail has version tracking."""
    card = create_card_detail
    assert card.version >= 1
    assert card.attachment_count >= 0
    assert card.total_attachment_size >= 0


@then("the attachment should have the correct metadata")
def verify_attachment_data(create_attachment, attachment_data):
    """Verify attachment has correct metadata."""
    attachment = create_attachment
    assert attachment.filename == attachment_data["filename"]
    assert attachment.card_id == attachment_data["card_id"]
    assert attachment.size_bytes == attachment_data["size_bytes"]
    assert attachment.content_type == attachment_data["content_type"]
    assert isinstance(attachment.uploaded_at, datetime)


@then("the attachment should be immutable")
def verify_attachment_immutable(create_attachment):
    """Verify attachment cannot be modified."""
    attachment = create_attachment
    with pytest.raises((ValidationError, AttributeError)):
        attachment.filename = "modified.pdf"


@then("the user tier should have correct storage limits")
def verify_user_tier_limits(create_user_tier, user_tier_data):
    """Verify user tier has correct storage limits."""
    tier = create_user_tier
    assert tier.tier == user_tier_data["tier"]
    assert tier.total_storage_quota_gb == user_tier_data["total_storage_quota_gb"]
    assert tier.max_attachment_size_mb == user_tier_data["max_attachment_size_mb"]


@then("the user tier should calculate storage usage percentage")
def verify_user_tier_calculations(create_user_tier):
    """Verify user tier calculations work."""
    tier = create_user_tier
    assert hasattr(tier, "storage_quota_bytes")
    assert hasattr(tier, "storage_usage_percentage")
    assert hasattr(tier, "attachment_size_limit_bytes")


@then("the user tier should be immutable")
def verify_user_tier_immutable(create_user_tier):
    """Verify user tier cannot be modified."""
    tier = create_user_tier
    with pytest.raises((ValidationError, AttributeError)):
        tier.tier = "elite"


@then("the quota should be correctly converted to bytes")
def verify_quota_conversion(storage_calculations):
    """Verify quota is correctly converted to bytes."""
    expected_bytes = 10 * 1024 * 1024 * 1024  # 10GB in bytes
    assert storage_calculations["quota_bytes"] == expected_bytes


@then("the usage percentage should be 50%")
def verify_usage_percentage(storage_calculations):
    """Verify usage percentage is calculated correctly."""
    assert storage_calculations["usage_percentage"] == 50.0
