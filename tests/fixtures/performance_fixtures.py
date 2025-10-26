import pytest
from typing import List, FrozenSet
import random
import string
from dataclasses import dataclass


@dataclass(frozen=True)
class TestCard:
    card_id: str
    tag_bitmaps: tuple


@pytest.fixture
def large_card_set() -> FrozenSet[TestCard]:
    """Generate 100K test cards."""
    cards = []
    for i in range(100000):
        card = TestCard(
            card_id=f"card-{i:06d}",
            tag_bitmaps=tuple(random.sample(range(1, 100), k=random.randint(1, 10)))
        )
        cards.append(card)
    return frozenset(cards)


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics."""
    import psutil
    import time

    class Monitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.start_cpu = None

        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            self.start_cpu = psutil.cpu_percent()

        def stop(self):
            elapsed = time.perf_counter() - self.start_time
            memory = psutil.Process().memory_info().rss / 1024 / 1024 - self.start_memory
            cpu = psutil.cpu_percent() - self.start_cpu
            return {
                "elapsed": elapsed,
                "memory_mb": memory,
                "cpu_percent": cpu
            }

    return Monitor()
