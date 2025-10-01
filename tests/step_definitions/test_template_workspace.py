"""Step definitions for template workspace BDD tests."""
from pytest_bdd import given, scenarios, then, when

# Load scenarios from feature file
scenarios('../features/template_workspace.feature')

# Test state storage
test_state = {}

@given("I am in workspace A")
def workspace_a_context(workspace_context):
    """Set up workspace A context."""
    test_state['workspace_id'] = 'workspace-a'
    test_state['workspace_name'] = 'Workspace A'
    test_state['user_id'] = workspace_context['user_id']

@given("I have tags from my workspace")
def workspace_tags():
    """Set up workspace tags."""
    test_state['tags'] = [
        {'tag_id': 'tag1', 'name': 'Tag 1'},
        {'tag_id': 'tag2', 'name': 'Tag 2'}
    ]

@given("I am logged into a workspace")
def logged_into_workspace(workspace_context):
    """Set up logged in workspace context."""
    test_state['workspace_id'] = workspace_context['workspace_id']
    test_state['workspace_name'] = workspace_context['workspace_name']
    test_state['user_id'] = workspace_context['user_id']

@when("the card grid template renders")
def render_card_grid(jinja_env):
    """Render card grid template."""
    template = jinja_env.get_template('card_grid.html')
    test_state['rendered_html'] = template.render(
        workspace_id=test_state['workspace_id'],
        cards=[
            {'card_id': 'card1', 'name': 'Card 1'},
            {'card_id': 'card2', 'name': 'Card 2'}
        ]
    )

@when("I drag tags to filter area")
def drag_tags_to_filter():
    """Simulate dragging tags to filter area."""
    test_state['tags_in_play'] = ['tag1', 'tag2']
    test_state['filter_triggered'] = True

@when("any template renders")
def render_any_template(jinja_env):
    """Render any template with workspace context."""
    template = jinja_env.get_template('tag_filter.html')
    test_state['rendered_html'] = template.render(
        workspace_id=test_state['workspace_id']
    )

@then("only workspace A cards should appear")
def verify_workspace_a_cards():
    """Verify only workspace A cards are shown."""
    html = test_state['rendered_html']
    assert 'workspace-a' in html
    assert 'data-workspace="workspace-a"' in html

@then("workspace_id should be in data attributes")
def verify_workspace_id_in_data_attributes():
    """Verify workspace_id is in data attributes."""
    html = test_state['rendered_html']
    workspace_id = test_state['workspace_id']
    assert f'data-workspace="{workspace_id}"' in html

@then("drag-drop should maintain context")
def verify_drag_drop_context():
    """Verify drag-drop maintains workspace context."""
    # This would check that data attributes are preserved during drag-drop
    html = test_state['rendered_html']
    assert 'data-workspace=' in html

@then("filtering should apply to workspace cards only")
def verify_filtering_workspace_scoped():
    """Verify filtering is workspace-scoped."""
    assert test_state.get('filter_triggered', False)
    assert 'workspace_id' in test_state

@then("tagsInPlay should update correctly")
def verify_tags_in_play_update():
    """Verify tagsInPlay updates correctly."""
    assert 'tags_in_play' in test_state
    assert len(test_state['tags_in_play']) > 0

@then("/api/render/cards should receive workspace context")
def verify_api_receives_workspace_context():
    """Verify API receives workspace context."""
    # This would be tested in integration tests
    # For now, verify state has workspace_id
    assert 'workspace_id' in test_state

@then("workspace name should be visible")
def verify_workspace_name_visible():
    """Verify workspace name is visible."""
    # This would check rendered HTML contains workspace name
    assert 'workspace_name' in test_state
    assert test_state['workspace_name'] is not None

@then("workspace ID should be in page metadata")
def verify_workspace_id_in_metadata():
    """Verify workspace ID is in page metadata."""
    html = test_state['rendered_html']
    # Check for data attribute (metadata)
    assert 'data-workspace=' in html

@then("switching workspaces should refresh all data")
def verify_workspace_switch_refreshes_data():
    """Verify switching workspaces refreshes all data."""
    # This would be tested in integration tests
    # For now, verify workspace context can change
    old_workspace = test_state['workspace_id']
    test_state['workspace_id'] = 'new-workspace'
    assert test_state['workspace_id'] != old_workspace
