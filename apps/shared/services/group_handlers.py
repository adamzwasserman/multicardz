"""
Polymorphic drag-drop handlers for group tags.

Integrates group tags with the existing polymorphic dispatch system,
enabling context-aware operations based on drop zones.
"""

from typing import Optional, Protocol
from dataclasses import dataclass

from apps.shared.services.group_storage import (
    add_member_to_group,
    add_multiple_members_to_group,
)
from apps.shared.services.group_expansion import (
    expand_group_recursive,
    apply_group_to_zone,
    apply_group_to_card,
    validate_circular_reference,
    invalidate_expansion_cache,
)


# ============ Operation Result Protocol ============


@dataclass(frozen=True)
class OperationResult:
    """Immutable result from a drag-drop operation."""
    success: bool
    operation_type: str
    affected_tags: frozenset[str] = frozenset()
    updated_zone: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        # Ensure metadata is immutable
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class DropContext:
    """Context information for a drop operation."""
    source_type: str  # 'group', 'tag', 'multi-selection'
    target_type: str  # 'zone', 'card', 'group'
    source_id: str
    target_id: str
    user_id: str
    workspace_id: str
    current_state: frozenset[str] = frozenset()  # Current tags in target
    modifiers: frozenset[str] = frozenset()  # Shift, Ctrl, Alt, etc.


# ============ Handler Protocol ============


class DropHandler(Protocol):
    """Protocol for polymorphic drop handlers."""

    def can_handle(self, context: DropContext) -> bool:
        """Check if this handler can process the drop operation."""
        ...

    def handle(self, context: DropContext) -> OperationResult:
        """Execute the drop operation."""
        ...


# ============ Group → Zone Handlers ============


def handle_group_to_union_zone(context: DropContext) -> OperationResult:
    """
    Handle group dropped on union zone.

    Expands group and performs union with current zone tags.
    """
    try:
        # Expand group to get all member tags
        expanded_tags = expand_group_recursive(context.source_id)

        # Apply to union zone
        updated_tags = context.current_state | expanded_tags

        return OperationResult(
            success=True,
            operation_type='group_expansion_union',
            affected_tags=expanded_tags,
            updated_zone='union',
            metadata={
                'group_id': context.source_id,
                'expanded_count': len(expanded_tags),
                'total_count': len(updated_tags)
            }
        )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='group_expansion_union',
            error_message=str(e)
        )


def handle_group_to_intersection_zone(context: DropContext) -> OperationResult:
    """
    Handle group dropped on intersection zone.

    Expands group and performs intersection with current zone tags.
    """
    try:
        # Expand group
        expanded_tags = expand_group_recursive(context.source_id)

        # Apply intersection
        if context.current_state:
            updated_tags = context.current_state & expanded_tags
        else:
            # If zone is empty, just add the expanded tags
            updated_tags = expanded_tags

        return OperationResult(
            success=True,
            operation_type='group_expansion_intersection',
            affected_tags=expanded_tags,
            updated_zone='intersection',
            metadata={
                'group_id': context.source_id,
                'expanded_count': len(expanded_tags),
                'intersection_count': len(updated_tags)
            }
        )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='group_expansion_intersection',
            error_message=str(e)
        )


def handle_group_to_exclusion_zone(context: DropContext) -> OperationResult:
    """
    Handle group dropped on exclusion zone.

    Expands group and removes those tags from current zone.
    """
    try:
        # Expand group
        expanded_tags = expand_group_recursive(context.source_id)

        # Apply exclusion (remove expanded tags from current set)
        updated_tags = context.current_state - expanded_tags

        return OperationResult(
            success=True,
            operation_type='group_expansion_exclusion',
            affected_tags=expanded_tags,
            updated_zone='exclusion',
            metadata={
                'group_id': context.source_id,
                'removed_count': len(expanded_tags),
                'remaining_count': len(updated_tags)
            }
        )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='group_expansion_exclusion',
            error_message=str(e)
        )


# ============ Group → Card Handler ============


def handle_group_to_card(context: DropContext) -> OperationResult:
    """
    Handle group dropped on card.

    Expands group and adds all member tags to card.
    """
    try:
        # Expand group
        expanded_tags = expand_group_recursive(context.source_id)

        # Apply to card (always union)
        updated_tags = context.current_state | expanded_tags

        return OperationResult(
            success=True,
            operation_type='group_to_card',
            affected_tags=expanded_tags,
            metadata={
                'group_id': context.source_id,
                'card_id': context.target_id,
                'added_count': len(expanded_tags - context.current_state),
                'total_tags': len(updated_tags)
            }
        )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='group_to_card',
            error_message=str(e)
        )


# ============ Tag → Group Handler ============


def handle_tag_to_group(context: DropContext) -> OperationResult:
    """
    Handle regular tag dropped on group.

    Adds tag as a member of the group.
    """
    try:
        # Add tag to group
        success = add_member_to_group(
            context.target_id,  # group_id
            context.source_id,  # tag_id
            context.user_id
        )

        if success:
            # Invalidate cache for this group
            invalidate_expansion_cache(context.target_id)

            return OperationResult(
                success=True,
                operation_type='tag_to_group',
                affected_tags=frozenset([context.source_id]),
                metadata={
                    'group_id': context.target_id,
                    'tag_id': context.source_id
                }
            )
        else:
            return OperationResult(
                success=False,
                operation_type='tag_to_group',
                error_message='Failed to add tag to group'
            )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='tag_to_group',
            error_message=str(e)
        )


# ============ Multi-Selection → Group Handler ============


def handle_multi_selection_to_group(context: DropContext) -> OperationResult:
    """
    Handle multiple selected tags dropped on group.

    Adds all selected tags as members of the group.
    """
    try:
        # Extract selected tag IDs from current_state
        selected_tags = context.current_state

        # Batch add to group
        success, added_ids, error = add_multiple_members_to_group(
            context.target_id,  # group_id
            selected_tags,
            context.user_id
        )

        if success:
            # Invalidate cache for this group
            invalidate_expansion_cache(context.target_id)

            return OperationResult(
                success=True,
                operation_type='multi_selection_to_group',
                affected_tags=added_ids,
                metadata={
                    'group_id': context.target_id,
                    'added_count': len(added_ids),
                    'total_selected': len(selected_tags)
                }
            )
        else:
            return OperationResult(
                success=False,
                operation_type='multi_selection_to_group',
                error_message=error or 'Failed to add tags to group'
            )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='multi_selection_to_group',
            error_message=str(e)
        )


# ============ Group → Group Handler (Nesting) ============


def handle_group_to_group(context: DropContext) -> OperationResult:
    """
    Handle group dropped on another group (creates nesting).

    Validates no circular reference before adding.
    """
    try:
        # Validate no circular reference
        is_valid, error = validate_circular_reference(
            context.target_id,  # parent group
            context.source_id   # child group
        )

        if not is_valid:
            return OperationResult(
                success=False,
                operation_type='group_to_group',
                error_message=error
            )

        # Add source group as member of target group
        success = add_member_to_group(
            context.target_id,  # parent group_id
            context.source_id,  # child group_id
            context.user_id
        )

        if success:
            # Invalidate cache for both groups
            invalidate_expansion_cache(context.target_id)
            invalidate_expansion_cache(context.source_id)

            return OperationResult(
                success=True,
                operation_type='group_to_group',
                affected_tags=frozenset([context.source_id]),
                metadata={
                    'parent_group_id': context.target_id,
                    'child_group_id': context.source_id
                }
            )
        else:
            return OperationResult(
                success=False,
                operation_type='group_to_group',
                error_message='Failed to nest groups'
            )

    except Exception as e:
        return OperationResult(
            success=False,
            operation_type='group_to_group',
            error_message=str(e)
        )


# ============ Handler Registry ============


# Global handler registry
_HANDLER_REGISTRY: dict[tuple[str, str], callable] = {}


def register_drop_handler(
    source_type: str,
    target_type: str,
    handler: callable
) -> None:
    """
    Register a drop handler for source/target type pair.

    Args:
        source_type: Type of dragged element ('group', 'tag', 'multi-selection')
        target_type: Type of drop target ('union-zone', 'card', 'group', etc.)
        handler: Handler function that takes DropContext and returns OperationResult
    """
    key = (source_type, target_type)
    _HANDLER_REGISTRY[key] = handler


def get_drop_handler(
    source_type: str,
    target_type: str
) -> Optional[callable]:
    """
    Get registered handler for source/target type pair.

    Returns handler function or None if not registered.
    """
    key = (source_type, target_type)
    return _HANDLER_REGISTRY.get(key)


def dispatch_drop_operation(context: DropContext) -> OperationResult:
    """
    Dispatch drop operation to appropriate handler.

    Polymorphic dispatch based on source and target types.
    """
    handler = get_drop_handler(context.source_type, context.target_type)

    if handler is None:
        return OperationResult(
            success=False,
            operation_type='unknown',
            error_message=f'No handler for {context.source_type} → {context.target_type}'
        )

    return handler(context)


# ============ Handler Registration ============


def register_all_group_handlers() -> None:
    """Register all group tag handlers with the dispatch system."""

    # Group → Zone handlers
    register_drop_handler('group', 'union-zone', handle_group_to_union_zone)
    register_drop_handler('group', 'intersection-zone', handle_group_to_intersection_zone)
    register_drop_handler('group', 'exclusion-zone', handle_group_to_exclusion_zone)

    # Group → Card handler
    register_drop_handler('group', 'card', handle_group_to_card)

    # Tag → Group handler
    register_drop_handler('tag', 'group', handle_tag_to_group)

    # Multi-selection → Group handler
    register_drop_handler('multi-selection', 'group', handle_multi_selection_to_group)

    # Group → Group handler (nesting)
    register_drop_handler('group', 'group', handle_group_to_group)
