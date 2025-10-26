"""Tag count auto-maintenance functions with atomic transactions."""

import json


async def increment_tag_counts(
    tag_ids: list[str],
    workspace_id: str,
    user_id: str,
    *,
    db_connection
) -> None:
    """
    Increment tag counts atomically.

    Pure function with transactional safety.
    """
    if not tag_ids:
        return

    await db_connection.execute("BEGIN TRANSACTION")

    try:
        for tag_id in tag_ids:
            await db_connection.execute(
                """
                UPDATE tags
                SET card_count = card_count + 1,
                    modified = CURRENT_TIMESTAMP
                WHERE tag_id = ? AND workspace_id = ? AND user_id = ?
                """,
                (tag_id, workspace_id, user_id)
            )

        await db_connection.execute("COMMIT")

    except Exception as e:
        await db_connection.execute("ROLLBACK")
        raise ValueError(f"Failed to increment counts: {e}")


async def decrement_tag_counts(
    tag_ids: list[str],
    workspace_id: str,
    user_id: str,
    *,
    db_connection
) -> None:
    """
    Decrement tag counts with floor at 0.

    Pure function ensuring counts never go negative.
    """
    if not tag_ids:
        return

    await db_connection.execute("BEGIN TRANSACTION")

    try:
        for tag_id in tag_ids:
            await db_connection.execute(
                """
                UPDATE tags
                SET card_count = MAX(0, card_count - 1),
                    modified = CURRENT_TIMESTAMP
                WHERE tag_id = ? AND workspace_id = ? AND user_id = ?
                """,
                (tag_id, workspace_id, user_id)
            )

        await db_connection.execute("COMMIT")

    except Exception as e:
        await db_connection.execute("ROLLBACK")
        raise ValueError(f"Failed to decrement counts: {e}")


async def update_tag_counts_on_reassignment(
    card_id: str,
    old_tag_ids: list[str],
    new_tag_ids: list[str],
    workspace_id: str,
    user_id: str,
    *,
    db_connection
) -> None:
    """
    Update counts when card tags change.

    Atomic operation using set difference.
    """
    old_set = set(old_tag_ids)
    new_set = set(new_tag_ids)

    tags_removed = old_set - new_set
    tags_added = new_set - old_set

    await db_connection.execute("BEGIN TRANSACTION")

    try:
        # Decrement removed tags
        if tags_removed:
            await decrement_tag_counts(
                list(tags_removed),
                workspace_id,
                user_id,
                db_connection=db_connection
            )

        # Increment added tags
        if tags_added:
            await increment_tag_counts(
                list(tags_added),
                workspace_id,
                user_id,
                db_connection=db_connection
            )

        # Update card's tag arrays
        await db_connection.execute(
            """
            UPDATE cards
            SET tag_ids = ?,
                modified = CURRENT_TIMESTAMP
            WHERE card_id = ? AND workspace_id = ? AND user_id = ?
            """,
            (json.dumps(list(new_set)), card_id, workspace_id, user_id)
        )

        await db_connection.execute("COMMIT")

    except Exception as e:
        await db_connection.execute("ROLLBACK")
        raise ValueError(f"Failed to update tag counts: {e}")


async def create_card_with_counts(
    card_data: dict,
    *,
    db_connection
) -> str:
    """
    Create card and update tag counts atomically.

    Returns card_id on success.
    """
    card_id = card_data.get("card_id")
    tag_ids = card_data.get("tag_ids", [])
    workspace_id = card_data["workspace_id"]
    user_id = card_data["user_id"]

    await db_connection.execute("BEGIN TRANSACTION")

    try:
        # Insert card
        await db_connection.execute(
            """
            INSERT INTO cards (
                card_id, name, description, user_id, workspace_id,
                tag_ids, created, modified
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                card_id, card_data["name"], card_data.get("description"),
                user_id, workspace_id, json.dumps(tag_ids)
            )
        )

        # Increment tag counts
        if tag_ids:
            await increment_tag_counts(
                tag_ids, workspace_id, user_id,
                db_connection=db_connection
            )

        await db_connection.execute("COMMIT")
        return card_id

    except Exception as e:
        await db_connection.execute("ROLLBACK")
        raise ValueError(f"Failed to create card: {e}")
