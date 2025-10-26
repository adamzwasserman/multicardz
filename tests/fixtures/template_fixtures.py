import pytest
from jinja2 import DictLoader, Environment


@pytest.fixture
def jinja_env():
    """Jinja2 environment for testing."""
    templates = {
        "card_grid.html": """
        <div class="card-grid" data-workspace="{{ workspace_id }}">
            {% for card in cards %}
            <div class="card" data-card-id="{{ card.card_id }}">
                {{ card.name }}
            </div>
            {% endfor %}
        </div>
        """,
        "tag_filter.html": """
        <div class="tag-filter" data-workspace="{{ workspace_id }}">
            <div id="tagsInPlay"></div>
        </div>
        """
    }
    return Environment(loader=DictLoader(templates))

@pytest.fixture
def workspace_context():
    """Workspace context for templates."""
    return {
        "workspace_id": "test-workspace",
        "workspace_name": "Test Workspace",
        "user_id": "test-user"
    }
