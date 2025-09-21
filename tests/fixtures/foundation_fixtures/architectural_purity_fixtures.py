import pytest
from typing import Dict, Any, List
import tempfile
import os


@pytest.fixture
def unauthorized_class_examples() -> List[str]:
    """Create examples of unauthorized class usage."""
    return [
        """
class CardManager:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)
        """,
        """
class FilterEngine:
    def filter_cards(self, cards, tags):
        return [card for card in cards if any(tag in card.tags for tag in tags)]
        """,
        """
class StateManager:
    def __init__(self):
        self._state = {}

    def update_state(self, key, value):
        self._state[key] = value
        """
    ]


@pytest.fixture
def authorized_class_examples() -> List[str]:
    """Create examples of authorized class usage."""
    return [
        """
# Pydantic model (authorized)
class CardModel(BaseModel):
    id: str
    title: str
    tags: FrozenSet[str]

    model_config = {"frozen": True}
        """,
        """
# SQLAlchemy model (authorized)
class CardEntity(Base):
    __tablename__ = 'cards'
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
        """,
        """
# Protocol definition (authorized)
class CardProcessor(Protocol):
    def process_cards(self, cards: FrozenSet[CardSummary]) -> FrozenSet[CardSummary]:
        ...
        """,
        """
# Web Component (authorized - browser API requirement)
class TagItem extends HTMLElement:
    connectedCallback() {
        // Minimal class logic, delegates to functions
        const component = TagComponentFactory.create(this);
        TagLifecycle.initialize(component, this);
    }
        """
    ]


@pytest.fixture
def non_compliant_set_operations() -> List[str]:
    """Create examples of non-compliant set operations."""
    return [
        """
def filter_cards_bad(cards, tags):
    # Using list instead of frozenset
    result = []
    for card in cards:
        if any(tag in card.tags for tag in tags):
            result.append(card)
    return result
        """,
        """
def combine_cards_bad(cards_a, cards_b):
    # Using dict instead of set operations
    combined = {}
    for card in cards_a:
        combined[card.id] = card
    for card in cards_b:
        combined[card.id] = card
    return list(combined.values())
        """
    ]


@pytest.fixture
def compliant_set_operations() -> List[str]:
    """Create examples of compliant set operations."""
    return [
        """
def filter_cards_good(cards: FrozenSet[CardSummary], tags: FrozenSet[str]) -> FrozenSet[CardSummary]:
    # Proper frozenset usage
    return frozenset(
        card for card in cards
        if tags.issubset(card.tags)
    )
        """,
        """
def combine_cards_good(
    cards_a: FrozenSet[CardSummary],
    cards_b: FrozenSet[CardSummary]
) -> FrozenSet[CardSummary]:
    # Proper set union
    return cards_a | cards_b
        """
    ]


@pytest.fixture
def pre_commit_hook_configuration() -> Dict[str, Any]:
    """Configuration for pre-commit architectural validation."""
    return {
        "hooks": [
            {
                "id": "validate-no-unauthorized-classes",
                "name": "Validate No Unauthorized Classes",
                "entry": "python scripts/validate_no_classes.py",
                "language": "python",
                "files": r"\.py$",
                "exclude": r"(tests/|migrations/|__pycache__/)"
            },
            {
                "id": "validate-set-theory-compliance",
                "name": "Validate Set Theory Compliance",
                "entry": "python scripts/validate_set_theory.py",
                "language": "python",
                "files": r"\.py$"
            },
            {
                "id": "validate-javascript-web-components",
                "name": "Validate JavaScript Web Components Only",
                "entry": "python scripts/validate_javascript.py",
                "language": "python",
                "files": r"\.js$"
            },
            {
                "id": "validate-pure-functions",
                "name": "Validate Pure Function Architecture",
                "entry": "python scripts/validate_immutability.py",
                "language": "python",
                "files": r"\.py$"
            },
            {
                "id": "validate-performance-benchmarks",
                "name": "Validate Performance Benchmarks",
                "entry": "python scripts/validate_performance.py",
                "language": "python",
                "files": r"(domain/|models/|operations/).*\.py$"
            }
        ],
        "validation_rules": {
            "authorized_classes": [
                "BaseModel",  # Pydantic
                "Base",       # SQLAlchemy
                "Protocol",   # Typing protocols
                "HTMLElement", # Web Components
                "Exception",  # Exception hierarchies
                "Enum"        # Enumerations
            ],
            "required_patterns": {
                "set_operations": r"frozenset\(",
                "immutable_models": r"frozen\s*=\s*True",
                "explicit_dependencies": r"workspace_id:\s*str.*user_id:\s*str"
            },
            "forbidden_patterns": {
                "mutable_defaults": r"def\s+\w+\([^)]*=\s*\[\]",
                "global_state": r"^[A-Z_]+\s*=\s*\{",
                "side_effects": r"(global|nonlocal)\s+\w+"
            }
        }
    }