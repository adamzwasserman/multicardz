# tests/fixtures/bitmap_fixtures.py

import pyroaring
import pytest


@pytest.fixture
def sample_bitmaps() -> dict[str, pyroaring.BitMap]:
    """Sample bitmaps for testing."""
    return {
        "tag1": pyroaring.BitMap([1, 2, 3, 4, 5]),
        "tag2": pyroaring.BitMap([3, 4, 5, 6, 7]),
        "tag3": pyroaring.BitMap([5, 6, 7, 8, 9]),
        "tag4": pyroaring.BitMap([1, 5, 9, 10])
    }

@pytest.fixture
def sample_cards() -> frozenset:
    """Sample cards for testing."""
    from collections import namedtuple
    Card = namedtuple('Card', ['card_id', 'tag_bitmaps'])

    return frozenset([
        Card("card1", [1]),
        Card("card2", [1]),
        Card("card3", [1, 2]),
        Card("card4", [1, 2]),
        Card("card5", [1, 2, 3, 4])
    ])

@pytest.fixture
def performance_threshold() -> float:
    """Performance threshold in seconds."""
    return 0.05  # 50ms
