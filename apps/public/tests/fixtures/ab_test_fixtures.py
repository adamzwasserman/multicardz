"""Fixtures for A/B testing tests."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy import text


@pytest.fixture
def sample_ab_test(db_connection):
    """Create a sample A/B test."""
    test_id = uuid4()
    landing_page_a_id = uuid4()
    landing_page_b_id = uuid4()

    # Create test landing pages for the variants
    db_connection.execute(
        text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, subheadline, is_active)
            VALUES
                (:id_a, :slug_a, 'REPLACEMENT', 'Variant A', 'Test Headline A', 'Test Sub A', true),
                (:id_b, :slug_b, 'REPLACEMENT', 'Variant B', 'Test Headline B', 'Test Sub B', true)
        """),
        {
            'id_a': landing_page_a_id,
            'slug_a': 'test-variant-a',
            'id_b': landing_page_b_id,
            'slug_b': 'test-variant-b'
        }
    )

    # Create A/B test
    db_connection.execute(
        text("""
            INSERT INTO a_b_tests (id, name, description, is_active, traffic_split, start_date)
            VALUES (:id, :name, :description, :is_active, CAST(:traffic_split AS jsonb), :start_date)
        """),
        {
            'id': test_id,
            'name': 'Homepage Headline Test',
            'description': 'Testing headline variations',
            'is_active': True,
            'traffic_split': '{"variant_a": 50, "variant_b": 50}',
            'start_date': datetime.now(UTC)
        }
    )

    # Create variants
    variant_a_id = uuid4()
    variant_b_id = uuid4()

    db_connection.execute(
        text("""
            INSERT INTO a_b_test_variants (id, a_b_test_id, variant_name, landing_page_id, weight)
            VALUES
                (:id_a, :test_id, 'variant_a', :page_a, 50),
                (:id_b, :test_id, 'variant_b', :page_b, 50)
        """),
        {
            'id_a': variant_a_id,
            'id_b': variant_b_id,
            'test_id': test_id,
            'page_a': landing_page_a_id,
            'page_b': landing_page_b_id
        }
    )

    db_connection.commit()

    return {
        'test_id': test_id,
        'variant_a_id': variant_a_id,
        'variant_b_id': variant_b_id,
        'landing_page_a_id': landing_page_a_id,
        'landing_page_b_id': landing_page_b_id
    }


@pytest.fixture
def ab_test_70_30(db_connection):
    """Create A/B test with 70/30 split."""
    test_id = uuid4()
    landing_page_a_id = uuid4()
    landing_page_b_id = uuid4()

    # Create test landing pages
    db_connection.execute(
        text("""
            INSERT INTO landing_pages (id, slug, category, name, headline, is_active)
            VALUES
                (:id_a, :slug_a, 'REPLACEMENT', 'Variant A 70', 'Headline A', true),
                (:id_b, :slug_b, 'REPLACEMENT', 'Variant B 30', 'Headline B', true)
        """),
        {
            'id_a': landing_page_a_id,
            'slug_a': 'test-70-variant-a',
            'id_b': landing_page_b_id,
            'slug_b': 'test-70-variant-b'
        }
    )

    # Create A/B test with 70/30 split
    db_connection.execute(
        text("""
            INSERT INTO a_b_tests (id, name, is_active, traffic_split, start_date)
            VALUES (:id, :name, :is_active, CAST(:traffic_split AS jsonb), :start_date)
        """),
        {
            'id': test_id,
            'name': '70/30 Split Test',
            'is_active': True,
            'traffic_split': '{"variant_a": 70, "variant_b": 30}',
            'start_date': datetime.now(UTC)
        }
    )

    # Create variants with 70/30 weights
    variant_a_id = uuid4()
    variant_b_id = uuid4()

    db_connection.execute(
        text("""
            INSERT INTO a_b_test_variants (id, a_b_test_id, variant_name, landing_page_id, weight)
            VALUES
                (:id_a, :test_id, 'variant_a', :page_a, 70),
                (:id_b, :test_id, 'variant_b', :page_b, 30)
        """),
        {
            'id_a': variant_a_id,
            'id_b': variant_b_id,
            'test_id': test_id,
            'page_a': landing_page_a_id,
            'page_b': landing_page_b_id
        }
    )

    db_connection.commit()

    return {
        'test_id': test_id,
        'variant_a_id': variant_a_id,
        'variant_b_id': variant_b_id
    }


@pytest.fixture
def cleanup_ab_tests(db_connection):
    """Clean up A/B test data after tests."""
    yield

    # Clean up in correct order (respecting FK constraints)
    db_connection.execute(text("DELETE FROM analytics_sessions WHERE a_b_variant_id IS NOT NULL"))
    db_connection.execute(text("DELETE FROM a_b_test_variants"))
    db_connection.execute(text("DELETE FROM a_b_tests"))
    db_connection.execute(text("DELETE FROM landing_pages WHERE slug LIKE 'test-%'"))
    db_connection.commit()
