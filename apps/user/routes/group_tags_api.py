"""Group Tags API routes for creation, modification, and expansion operations."""

import logging

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, HTTPException

from apps.shared.config.database import DATABASE_PATH
from apps.shared.services.group_expansion import (
    GroupExpansionCache,
    expand_group_recursive,
    get_expansion_statistics,
    validate_circular_reference,
)
from apps.shared.services.group_handlers import (
    DropContext,
    dispatch_drop_operation,
)
from apps.shared.services.group_storage import (
    add_member_to_group,
    add_multiple_members_to_group,
    create_group,
    delete_group,
    get_group_by_id,
    get_groups_by_workspace,
    remove_member_from_group,
    validate_group_name,
    validate_no_self_reference,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["group-tags"])

# Initialize global expansion cache
expansion_cache = GroupExpansionCache(max_size=1024, ttl_seconds=300)


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateGroupRequest(BaseModel):
    """Request model for group creation."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    workspace_id: str = Field(..., description="Workspace ID")
    user_id: str = Field(..., description="User ID creating the group")
    member_tag_ids: tuple[str, ...] = Field(
        default_factory=tuple, description="Initial member tag IDs"
    )
    visual_style: dict = Field(default_factory=dict, description="Visual style config")


class CreateGroupResponse(BaseModel):
    """Response model for group creation."""

    model_config = ConfigDict(frozen=True)

    success: bool
    group_id: str
    message: str | None = None


class AddMemberRequest(BaseModel):
    """Request model for adding member to group."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    member_tag_id: str
    user_id: str


class AddMultipleMembersRequest(BaseModel):
    """Request model for adding multiple members to group."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    member_tag_ids: tuple[str, ...] = Field(..., description="Member tag IDs")
    user_id: str


class RemoveMemberRequest(BaseModel):
    """Request model for removing member from group."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    member_tag_id: str
    user_id: str


class ExpandGroupRequest(BaseModel):
    """Request model for group expansion."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    use_cache: bool = True


class ExpandGroupResponse(BaseModel):
    """Response model for group expansion."""

    model_config = ConfigDict(frozen=True)

    success: bool
    group_id: str
    expanded_tag_ids: tuple[str, ...] = Field(..., description="Expanded tag IDs")
    depth: int
    cached: bool
    message: str | None = None


class DropOperationRequest(BaseModel):
    """Request model for polymorphic drop operation."""

    model_config = ConfigDict(frozen=True)

    source_type: str  # 'tag', 'group', 'multi-selection'
    source_id: str
    target_type: (
        str  # 'union-zone', 'intersection-zone', 'exclusion-zone', 'card', 'group'
    )
    target_id: str
    workspace_id: str
    user_id: str
    current_zone_tags: tuple[str, ...] = Field(default_factory=tuple)


class DropOperationResponse(BaseModel):
    """Response model for drop operation."""

    model_config = ConfigDict(frozen=True)

    success: bool
    operation_type: str
    result_tag_ids: tuple[str, ...] = Field(..., description="Result tag IDs")
    message: str | None = None


class GroupInfoResponse(BaseModel):
    """Response model for group information."""

    model_config = ConfigDict(frozen=True)

    group_id: str
    name: str
    workspace_id: str
    created_by: str
    member_count: int
    member_tag_ids: tuple[str, ...] = Field(..., description="Member tag IDs")
    visual_style: dict
    max_nesting_depth: int


class WorkspaceGroupsResponse(BaseModel):
    """Response model for workspace groups listing."""

    model_config = ConfigDict(frozen=True)

    success: bool
    groups: tuple[GroupInfoResponse, ...] = Field(..., description="Groups")
    total_count: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/create", response_model=CreateGroupResponse)
async def create_group_endpoint(request: CreateGroupRequest) -> CreateGroupResponse:
    """
    Create a new group tag.

    Args:
        request: Group creation request with name, workspace, initial members

    Returns:
        CreateGroupResponse with success status and group_id
    """
    logger.info(
        f"Creating group: {request.name} in workspace {request.workspace_id} "
        f"with {len(request.member_tag_ids)} members"
    )

    try:
        # Validate group name
        is_valid, error_msg = validate_group_name(
            request.name, request.workspace_id, DATABASE_PATH
        )
        if not is_valid:
            return CreateGroupResponse(
                success=False, group_id="", message=f"Validation error: {error_msg}"
            )

        # Convert member list to frozenset
        member_tag_ids = frozenset(request.member_tag_ids)

        # Check for self-reference in members (if any member is the group being created)
        for member_id in member_tag_ids:
            is_valid, error_msg = validate_no_self_reference(None, member_id)
            if not is_valid and member_id.startswith("group_"):
                # Validate no circular references for group members
                is_valid, error_msg = validate_circular_reference(
                    None, member_id, DATABASE_PATH
                )
                if not is_valid:
                    return CreateGroupResponse(
                        success=False, group_id="", message=error_msg
                    )

        # Create the group
        group_id = create_group(
            name=request.name,
            workspace_id=request.workspace_id,
            created_by=request.user_id,
            member_tag_ids=member_tag_ids,
            visual_style=request.visual_style if request.visual_style else None,
            db_path=DATABASE_PATH,
        )

        logger.info(f"Group created successfully: {request.name} (ID: {group_id})")

        return CreateGroupResponse(
            success=True, group_id=group_id, message="Group created successfully"
        )

    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        return CreateGroupResponse(
            success=False, group_id="", message=f"Failed to create group: {str(e)}"
        )


@router.post("/add-member")
async def add_member_endpoint(request: AddMemberRequest):
    """
    Add a member (tag or group) to an existing group.

    Args:
        request: Member addition request with group_id and member_tag_id

    Returns:
        Success status and message
    """
    logger.info(f"Adding member {request.member_tag_id} to group {request.group_id}")

    try:
        # Validate no circular reference
        is_valid, error_msg = validate_circular_reference(
            request.group_id, request.member_tag_id, DATABASE_PATH
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Add member
        success = add_member_to_group(
            group_id=request.group_id,
            member_tag_id=request.member_tag_id,
            added_by=request.user_id,
            db_path=DATABASE_PATH,
        )

        if success:
            # Invalidate cache for this group
            expansion_cache.invalidate_group(request.group_id)

            logger.info(
                f"Member {request.member_tag_id} added to group {request.group_id}"
            )
            return {"success": True, "message": "Member added successfully"}
        else:
            return {"success": False, "message": "Failed to add member"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add member: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/add-members")
async def add_multiple_members_endpoint(request: AddMultipleMembersRequest):
    """
    Add multiple members to a group in a batch operation.

    Args:
        request: Batch member addition request

    Returns:
        Success status with count of members added
    """
    logger.info(
        f"Adding {len(request.member_tag_ids)} members to group {request.group_id}"
    )

    try:
        # Validate all members
        for member_id in request.member_tag_ids:
            is_valid, error_msg = validate_circular_reference(
                request.group_id, member_id, DATABASE_PATH
            )
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed for {member_id}: {error_msg}",
                )

        # Add all members
        success, added_count = add_multiple_members_to_group(
            group_id=request.group_id,
            member_tag_ids=frozenset(request.member_tag_ids),
            added_by=request.user_id,
            db_path=DATABASE_PATH,
        )

        if success:
            # Invalidate cache
            expansion_cache.invalidate_group(request.group_id)

            logger.info(f"{added_count} members added to group {request.group_id}")
            return {
                "success": True,
                "members_added": added_count,
                "message": f"Added {added_count} members successfully",
            }
        else:
            return {"success": False, "message": "Failed to add members"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add members: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/remove-member")
async def remove_member_endpoint(request: RemoveMemberRequest):
    """
    Remove a member from a group.

    Args:
        request: Member removal request

    Returns:
        Success status and message
    """
    logger.info(
        f"Removing member {request.member_tag_id} from group {request.group_id}"
    )

    try:
        success = remove_member_from_group(
            group_id=request.group_id,
            member_tag_id=request.member_tag_id,
            db_path=DATABASE_PATH,
        )

        if success:
            # Invalidate cache
            expansion_cache.invalidate_group(request.group_id)

            logger.info(
                f"Member {request.member_tag_id} removed from group {request.group_id}"
            )
            return {"success": True, "message": "Member removed successfully"}
        else:
            return {"success": False, "message": "Failed to remove member"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove member: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/expand", response_model=ExpandGroupResponse)
async def expand_group_endpoint(request: ExpandGroupRequest) -> ExpandGroupResponse:
    """
    Expand a group to all its member tags recursively.

    Args:
        request: Expansion request with group_id

    Returns:
        ExpandGroupResponse with expanded tag IDs and statistics
    """
    logger.info(f"Expanding group {request.group_id} (use_cache={request.use_cache})")

    try:
        if request.use_cache:
            # Use cached expansion
            expanded_tags = expansion_cache.expand_with_cache(
                request.group_id, DATABASE_PATH
            )
            cached = True
        else:
            # Direct expansion without cache
            expanded_tags = expand_group_recursive(
                request.group_id, db_path=DATABASE_PATH
            )
            cached = False

        # Get expansion statistics
        stats = get_expansion_statistics(request.group_id, DATABASE_PATH)

        logger.info(
            f"Group {request.group_id} expanded to {len(expanded_tags)} tags "
            f"(depth={stats['max_depth']}, cached={cached})"
        )

        return ExpandGroupResponse(
            success=True,
            group_id=request.group_id,
            expanded_tag_ids=tuple(expanded_tags),
            depth=stats["max_depth"],
            cached=cached,
            message=f"Expanded to {len(expanded_tags)} tags",
        )

    except Exception as e:
        logger.error(f"Failed to expand group: {e}")
        return ExpandGroupResponse(
            success=False,
            group_id=request.group_id,
            expanded_tag_ids=(),
            depth=0,
            cached=False,
            message=f"Expansion failed: {str(e)}",
        )


@router.post("/drop", response_model=DropOperationResponse)
async def drop_operation_endpoint(
    request: DropOperationRequest,
) -> DropOperationResponse:
    """
    Handle polymorphic drop operation for groups.

    Supports:
    - Group → Zone (union, intersection, exclusion)
    - Group → Card (add all members as tags)
    - Tag → Group (add tag as member)
    - Multi-selection → Group (batch add)
    - Group → Group (nest groups)

    Args:
        request: Drop operation request with source, target, and context

    Returns:
        DropOperationResponse with result tag IDs
    """
    logger.info(
        f"Drop operation: {request.source_type} ({request.source_id}) → "
        f"{request.target_type} ({request.target_id})"
    )

    try:
        # Build drop context
        context = DropContext(
            source_type=request.source_type,
            source_id=request.source_id,
            target_type=request.target_type,
            target_id=request.target_id,
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            current_zone_tags=frozenset(request.current_zone_tags),
            db_path=DATABASE_PATH,
        )

        # Dispatch to appropriate handler
        result = dispatch_drop_operation(context, expansion_cache)

        logger.info(
            f"Drop operation completed: {result.operation_type} → "
            f"{len(result.result_tag_ids)} tags"
        )

        return DropOperationResponse(
            success=result.success,
            operation_type=result.operation_type,
            result_tag_ids=tuple(result.result_tag_ids),
            message=result.message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drop operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/{group_id}", response_model=GroupInfoResponse)
async def get_group_info(group_id: str) -> GroupInfoResponse:
    """
    Get information about a specific group.

    Args:
        group_id: Group ID to retrieve

    Returns:
        GroupInfoResponse with group details
    """
    logger.info(f"Fetching info for group {group_id}")

    try:
        group = get_group_by_id(group_id, DATABASE_PATH)

        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

        return GroupInfoResponse(
            group_id=group.id,
            name=group.name,
            workspace_id=group.workspace_id,
            created_by=group.created_by,
            member_count=len(group.member_tag_ids),
            member_tag_ids=tuple(group.member_tag_ids),
            visual_style=group.visual_style,
            max_nesting_depth=group.max_nesting_depth,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/workspace/{workspace_id}", response_model=WorkspaceGroupsResponse)
async def get_workspace_groups(workspace_id: str) -> WorkspaceGroupsResponse:
    """
    Get all groups for a workspace.

    Args:
        workspace_id: Workspace ID to query

    Returns:
        WorkspaceGroupsResponse with list of groups
    """
    logger.info(f"Fetching groups for workspace {workspace_id}")

    try:
        groups = get_groups_by_workspace(workspace_id, DATABASE_PATH)

        group_infos = tuple(
            GroupInfoResponse(
                group_id=g.id,
                name=g.name,
                workspace_id=g.workspace_id,
                created_by=g.created_by,
                member_count=len(g.member_tag_ids),
                member_tag_ids=tuple(g.member_tag_ids),
                visual_style=g.visual_style,
                max_nesting_depth=g.max_nesting_depth,
            )
            for g in groups
        )

        logger.info(f"Found {len(groups)} groups in workspace {workspace_id}")

        return WorkspaceGroupsResponse(
            success=True, groups=group_infos, total_count=len(groups)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workspace groups: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{group_id}")
async def delete_group_endpoint(group_id: str):
    """
    Delete a group (memberships are cascade deleted).

    Args:
        group_id: Group ID to delete

    Returns:
        Success status and message
    """
    logger.info(f"Deleting group {group_id}")

    try:
        success = delete_group(group_id, DATABASE_PATH)

        if success:
            # Invalidate cache
            expansion_cache.invalidate_group(group_id)

            logger.info(f"Group {group_id} deleted successfully")
            return {"success": True, "message": "Group deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete group"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete group: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get expansion cache statistics.

    Returns:
        Cache performance metrics
    """
    stats = expansion_cache.get_statistics()
    return {"success": True, "cache_stats": stats}


@router.post("/cache/invalidate/{group_id}")
async def invalidate_cache_endpoint(group_id: str):
    """
    Manually invalidate cache for a specific group.

    Args:
        group_id: Group ID to invalidate

    Returns:
        Success status
    """
    expansion_cache.invalidate_group(group_id)
    logger.info(f"Cache invalidated for group {group_id}")
    return {"success": True, "message": f"Cache invalidated for {group_id}"}


@router.post("/cache/clear")
async def clear_cache_endpoint():
    """
    Clear the entire expansion cache.

    Returns:
        Success status
    """
    expansion_cache.clear()
    logger.info("Expansion cache cleared")
    return {"success": True, "message": "Cache cleared"}
