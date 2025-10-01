"""Template context building functions for workspace isolation.

Pure functions for building Jinja2 template contexts with workspace metadata.
"""
from typing import Dict, Any, Optional
from fastapi import Request


def get_workspace_template_context(
    request: Request,
    workspace_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Build template context with workspace isolation.

    Pure function for context building.

    Args:
        request: FastAPI request object
        workspace_id: Workspace UUID for isolation
        user_id: User UUID for isolation

    Returns:
        Dictionary containing workspace context for templates
    """
    return {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "workspace_name": get_workspace_name(workspace_id),
        "request": request,
        "htmx_enabled": True
    }


def get_workspace_name(workspace_id: str) -> str:
    """
    Get human-readable workspace name.

    Pure function for workspace name resolution.
    In production, would fetch from database.

    Args:
        workspace_id: Workspace UUID

    Returns:
        Human-readable workspace name
    """
    # Would fetch from database in production
    return f"Workspace {workspace_id[:8]}"


def inject_workspace_metadata(
    template_html: str,
    workspace_id: str,
    user_id: str
) -> str:
    """
    Inject workspace metadata into HTML.

    Pure function for HTML modification.
    Adds meta tags for workspace context.

    Args:
        template_html: Rendered HTML template
        workspace_id: Workspace UUID
        user_id: User UUID

    Returns:
        HTML with injected workspace metadata
    """
    # Add metadata to head
    metadata = f"""
    <meta name="workspace-id" content="{workspace_id}">
    <meta name="user-id" content="{user_id}">
    """

    # Inject after <head> tag
    if "<head>" in template_html:
        template_html = template_html.replace(
            "<head>",
            f"<head>\n{metadata}"
        )

    return template_html
