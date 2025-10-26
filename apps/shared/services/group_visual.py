"""
Group tag visual rendering following Muji design principles.

Provides pure functional rendering of group tags with minimal,
grayscale-based visual distinction using borders, opacity, and subtle textures.
"""

import html
from typing import Optional

from apps.shared.models.database_models import GroupTag


# ============ Visual Style Configuration ============


def get_default_visual_style() -> dict:
    """
    Get default Muji-inspired visual style configuration.

    Returns dict with border, opacity, icon, and pattern settings.
    """
    return {
        'border_style': 'dashed',
        'opacity': 0.95,
        'icon': 'folder-minimal',
        'border_color': 'rgba(0, 0, 0, 0.2)',
        'background_pattern': 'subtle-dots'
    }


def get_nesting_opacity(base_opacity: float, nesting_level: int) -> float:
    """
    Calculate opacity based on nesting depth.

    Each level reduces opacity by 0.05, minimum 0.70.
    """
    reduction = nesting_level * 0.05
    return max(0.70, base_opacity - reduction)


def get_border_style_for_level(nesting_level: int) -> str:
    """
    Get border style based on nesting level.

    Level 0: dashed
    Level 1: dotted
    Level 2: double
    Level 3+: groove
    """
    styles = {
        0: 'dashed',
        1: 'dotted',
        2: 'double',
    }
    return styles.get(nesting_level, 'groove')


# ============ SVG Icon Generation ============


def render_group_icon_svg(is_expanded: bool = False) -> str:
    """
    Render minimal arrow icon for group tags.

    Args:
        is_expanded: Whether group is in expanded state

    Returns:
        SVG markup for icon
    """
    # Simple chevron that rotates 90deg when expanded
    return '''
        <span class="group-icon">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor">
                <path d="M3 5 L6 8 L9 5" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        </span>
    '''


# ============ HTML Rendering ============


def render_group_tag(
    group: GroupTag,
    nesting_level: int = 0,
    is_expanded: bool = False,
    is_selected: bool = False,
    is_dragging: bool = False
) -> str:
    """
    Render group tag as HTML with Muji-inspired styling.

    Pure functional rendering with security (HTML escaping).

    Args:
        group: GroupTag to render
        nesting_level: Current nesting depth (0 = top level)
        is_expanded: Whether group is expanded showing members
        is_selected: Whether group is currently selected
        is_dragging: Whether group is being dragged

    Returns:
        HTML string for group tag element
    """
    # Escape name for security
    safe_name = html.escape(group.name)

    # Build CSS classes
    css_classes = ['tag', 'group-tag']
    if is_selected:
        css_classes.append('selected')
    if is_expanded:
        css_classes.append('expanded')
    if is_dragging:
        css_classes.append('dragging')

    # Build data attributes
    data_attrs = [
        f'data-group-id="{html.escape(group.id)}"',
        f'data-nesting-level="{nesting_level}"',
        f'data-expanded="{str(is_expanded).lower()}"',
        f'data-member-count="{len(group.member_tag_ids)}"',
        'draggable="true"'
    ]

    # ARIA attributes for accessibility
    aria_attrs = [
        f'aria-expanded="{str(is_expanded).lower()}"',
        f'aria-label="Group: {safe_name} with {len(group.member_tag_ids)} members"',
        'role="button"',
        'tabindex="0"'
    ]

    # Icon
    icon_html = render_group_icon_svg(is_expanded) if group.visual_style.get('icon') else ''

    # Member count badge
    count_html = f'<span class="member-count">({len(group.member_tag_ids)})</span>'

    # Combine into final HTML
    return f'''<div class="{' '.join(css_classes)}"
             {' '.join(data_attrs)}
             {' '.join(aria_attrs)}>
            {icon_html}
            <span class="tag-name">{safe_name}</span>
            {count_html}
        </div>'''


def render_group_tag_compact(
    group: GroupTag,
    show_count: bool = True
) -> str:
    """
    Render compact version of group tag for inline display.

    Args:
        group: GroupTag to render
        show_count: Whether to show member count

    Returns:
        Compact HTML string
    """
    safe_name = html.escape(group.name)
    count = f' ({len(group.member_tag_ids)})' if show_count else ''

    return f'<span class="tag group-tag compact" data-group-id="{html.escape(group.id)}">{safe_name}{count}</span>'


# ============ Batch Rendering ============


def render_group_list(
    groups: list[GroupTag],
    nesting_level: int = 0,
    expanded_group_ids: set[str] = None,
    selected_group_ids: set[str] = None
) -> str:
    """
    Render multiple group tags as a list.

    Args:
        groups: List of GroupTags to render
        nesting_level: Current nesting depth
        expanded_group_ids: Set of group IDs that are expanded
        selected_group_ids: Set of group IDs that are selected

    Returns:
        HTML string with all group tags
    """
    expanded_group_ids = expanded_group_ids or set()
    selected_group_ids = selected_group_ids or set()

    rendered_groups = []

    for group in groups:
        is_expanded = group.id in expanded_group_ids
        is_selected = group.id in selected_group_ids

        rendered = render_group_tag(
            group,
            nesting_level=nesting_level,
            is_expanded=is_expanded,
            is_selected=is_selected
        )
        rendered_groups.append(rendered)

    return '\n'.join(rendered_groups)


# ============ JSON Representation ============


def group_to_json_safe(group: GroupTag) -> dict:
    """
    Convert GroupTag to JSON-safe dict for client rendering.

    Returns dict suitable for JSON serialization.
    """
    return {
        'id': group.id,
        'name': group.name,
        'workspace_id': group.workspace_id,
        'member_count': len(group.member_tag_ids),
        'member_ids': list(group.member_tag_ids),
        'parent_group_ids': list(group.parent_group_ids),
        'visual_style': group.visual_style,
        'created_at': group.created_at.isoformat(),
        'created_by': group.created_by
    }


def groups_to_json_safe(groups: list[GroupTag]) -> list[dict]:
    """
    Convert list of GroupTags to JSON-safe list.

    Returns list of dicts suitable for JSON serialization.
    """
    return [group_to_json_safe(g) for g in groups]


# ============ Visual Feedback Helpers ============


def get_drop_feedback_class(
    is_valid_drop: bool,
    is_hovering: bool
) -> str:
    """
    Get CSS class for drop zone visual feedback.

    Args:
        is_valid_drop: Whether drop would be valid
        is_hovering: Whether group is hovering over zone

    Returns:
        CSS class name for drop feedback
    """
    if not is_hovering:
        return ''

    if is_valid_drop:
        return 'group-valid-drop'
    else:
        return 'group-invalid-drop'


def render_expansion_preview(
    group: GroupTag,
    expanded_tag_count: int
) -> str:
    """
    Render tooltip/preview showing what tags will be added.

    Args:
        group: GroupTag being previewed
        expanded_tag_count: Number of tags that will be expanded

    Returns:
        HTML for tooltip preview
    """
    safe_name = html.escape(group.name)

    return f'''
        <div class="group-expansion-preview" role="tooltip">
            <div class="preview-header">
                Group: <strong>{safe_name}</strong>
            </div>
            <div class="preview-body">
                Will add <strong>{expanded_tag_count}</strong> tag(s)
            </div>
        </div>
    '''


# ============ Accessibility Helpers ============


def get_group_aria_description(group: GroupTag, is_expanded: bool) -> str:
    """
    Generate descriptive ARIA label for group tag.

    Args:
        group: GroupTag to describe
        is_expanded: Whether group is expanded

    Returns:
        Descriptive text for screen readers
    """
    state = "expanded" if is_expanded else "collapsed"
    member_text = "member" if len(group.member_tag_ids) == 1 else "members"

    return f"Group {group.name}, {state}, contains {len(group.member_tag_ids)} {member_text}"


def render_keyboard_help() -> str:
    """
    Render keyboard navigation help for group tags.

    Returns:
        HTML with keyboard shortcuts
    """
    return '''
        <div class="group-keyboard-help" role="region" aria-label="Keyboard shortcuts">
            <h3>Group Tag Shortcuts</h3>
            <dl>
                <dt>Space / Enter</dt>
                <dd>Expand/collapse group</dd>

                <dt>Arrow Keys</dt>
                <dd>Navigate between groups</dd>

                <dt>Shift + Click</dt>
                <dd>Multi-select groups</dd>

                <dt>Delete / Backspace</dt>
                <dd>Remove from selection</dd>
            </dl>
        </div>
    '''
