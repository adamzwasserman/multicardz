"""
MultiCardz™ Lesson Service
Pure functional service for managing progressive onboarding lessons.
Follows function-based architecture with explicit state passing.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import json

from ..data.onboarding_lessons import (
    get_lesson_cards,
    get_lesson_tags,
    get_default_lesson_state,
    validate_lesson_completion,
    get_available_lessons,
    LESSON_PROGRESSION,
    LessonCard,
    LessonTag
)


def create_lesson_cards_for_database(lesson_number: int) -> List[Dict[str, Any]]:
    """
    Convert lesson cards to database-compatible format.

    Args:
        lesson_number: Lesson to create cards for

    Returns:
        List of card dictionaries ready for database insertion
    """
    lesson_cards = get_lesson_cards(lesson_number)
    db_cards = []

    for card in lesson_cards:
        db_card = {
            "id": card.id,
            "title": card.title,
            "content": card.content,
            "tags": card.tags,
            "card_type": "lesson",
            "lesson_metadata": {
                "lesson_number": card.lesson_number,
                "step_number": card.step_number,
                "success_criteria": card.success_criteria,
                "next_action": card.next_action
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "modified_at": datetime.now(timezone.utc).isoformat()
        }
        db_cards.append(db_card)

    return db_cards


def create_lesson_tags_for_database(lesson_number: int) -> List[Dict[str, Any]]:
    """
    Convert lesson tags to database-compatible format.

    Args:
        lesson_number: Lesson to create tags for

    Returns:
        List of tag dictionaries ready for database insertion
    """
    lesson_tags = get_lesson_tags(lesson_number)
    db_tags = []

    for tag in lesson_tags:
        db_tag = {
            "name": tag.name,
            "tag_type": "lesson",
            "lesson_metadata": {
                "lesson_number": tag.lesson_number,
                "instruction": tag.instruction,
                "zone_target": tag.zone_target
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        db_tags.append(db_tag)

    return db_tags


def filter_cards_by_lesson_state(
    all_cards: List[Dict],
    lesson_state: Dict,
    zone_state: Dict
) -> List[Dict]:
    """
    Filter cards based on current lesson state and user progress.

    Args:
        all_cards: All available cards
        lesson_state: Current lesson state
        zone_state: Current zone configuration

    Returns:
        Filtered list of cards that should be visible
    """
    current_lesson = lesson_state.get("current_lesson", 1)
    current_step = lesson_state.get("current_step", 1)
    achieved_criteria = lesson_state.get("achieved_criteria", [])

    visible_cards = []

    for card in all_cards:
        # Handle both dict and object card formats
        if hasattr(card, 'card_type'):
            card_type = card.card_type
            lesson_metadata = getattr(card, 'lesson_metadata', None)
        else:
            card_type = card.get("card_type")
            lesson_metadata = card.get("lesson_metadata")

        # Always show non-lesson cards based on zone filtering
        if card_type != "lesson":
            visible_cards.append(card)
            continue

        # Parse lesson metadata if it's a JSON string
        if isinstance(lesson_metadata, str):
            try:
                lesson_meta = json.loads(lesson_metadata)
            except (json.JSONDecodeError, TypeError):
                lesson_meta = {}
        elif isinstance(lesson_metadata, dict):
            lesson_meta = lesson_metadata
        else:
            lesson_meta = {}

        card_lesson = lesson_meta.get("lesson_number")
        card_step = lesson_meta.get("step_number", 1)

        # Show lesson cards for current lesson
        if card_lesson == current_lesson:
            # Check if this step should be visible
            if card_step <= current_step:
                visible_cards.append(card)
                continue

            # Check if success criteria met to show next step
            success_criteria = lesson_meta.get("success_criteria")
            if success_criteria and success_criteria in achieved_criteria:
                visible_cards.append(card)
                continue

    return visible_cards


def detect_lesson_progression(
    previous_state: Dict,
    current_zone_state: Dict,
    lesson_state: Dict
) -> Tuple[Dict, List[str]]:
    """
    Detect if user has achieved lesson progression criteria.

    Args:
        previous_state: Previous zone state
        current_zone_state: Current zone state
        lesson_state: Current lesson state

    Returns:
        Tuple of (updated_lesson_state, list_of_achieved_criteria)
    """
    current_lesson = lesson_state.get("current_lesson", 1)
    achieved_criteria = lesson_state.get("achieved_criteria", [])
    new_criteria = []

    # Detect lesson 1 success: tag in union zone
    if current_lesson == 1:
        union_tags = current_zone_state.get("zones", {}).get("union", {}).get("tags", [])
        if "drag me to first box" in union_tags and "tag_in_union_zone" not in achieved_criteria:
            new_criteria.append("tag_in_union_zone")

    # Detect lesson 2 success: two tags in union zone
    elif current_lesson == 2:
        union_tags = current_zone_state.get("zones", {}).get("union", {}).get("tags", [])
        if len(union_tags) >= 2 and "two_tags_in_union" not in achieved_criteria:
            new_criteria.append("two_tags_in_union")

    # Detect lesson 3 success: tag in intersection zone
    elif current_lesson == 3:
        intersection_tags = current_zone_state.get("zones", {}).get("intersection", {}).get("tags", [])
        if intersection_tags and "tag_in_intersection" not in achieved_criteria:
            new_criteria.append("tag_in_intersection")

        # Also detect experimentation
        if len(intersection_tags) > 0 and union_tags and "experimented_with_zones" not in achieved_criteria:
            new_criteria.append("experimented_with_zones")

    # Update lesson state if criteria achieved
    updated_state = lesson_state.copy()
    if new_criteria:
        updated_state["achieved_criteria"] = achieved_criteria + new_criteria

        # Check if lesson is complete
        if validate_lesson_completion(current_lesson, updated_state):
            completed_lessons = updated_state.get("completed_lessons", [])
            if current_lesson not in completed_lessons:
                updated_state["completed_lessons"] = completed_lessons + [current_lesson]
                updated_state["lesson_completed_at"] = datetime.now(timezone.utc).isoformat()

    return updated_state, new_criteria


def advance_lesson_step(lesson_state: Dict) -> Dict:
    """
    Advance to the next step in current lesson.

    Args:
        lesson_state: Current lesson state

    Returns:
        Updated lesson state
    """
    updated_state = lesson_state.copy()
    current_step = updated_state.get("current_step", 1)
    updated_state["current_step"] = current_step + 1

    return updated_state


def change_lesson(lesson_state: Dict, new_lesson_number: int) -> Dict:
    """
    Change to a different lesson.

    Args:
        lesson_state: Current lesson state
        new_lesson_number: Lesson to switch to

    Returns:
        Updated lesson state
    """
    completed_lessons = lesson_state.get("completed_lessons", [])
    available_lessons = get_available_lessons(completed_lessons)

    if new_lesson_number not in available_lessons and new_lesson_number != "production":
        # Cannot switch to unavailable lesson
        return lesson_state

    updated_state = lesson_state.copy()
    updated_state["current_lesson"] = new_lesson_number
    updated_state["current_step"] = 1
    updated_state["lesson_changed_at"] = datetime.now(timezone.utc).isoformat()

    # Reset achieved criteria for new lesson
    if new_lesson_number != "production":
        updated_state["achieved_criteria"] = []

    return updated_state


def get_lesson_selector_options(lesson_state: Dict) -> List[Dict[str, Any]]:
    """
    Get available lesson options for the lesson selector.

    Args:
        lesson_state: Current lesson state

    Returns:
        List of lesson option dictionaries
    """
    completed_lessons = lesson_state.get("completed_lessons", [])
    available_lessons = get_available_lessons(completed_lessons)
    current_lesson = lesson_state.get("current_lesson", 1)
    achieved_criteria = lesson_state.get("achieved_criteria", [])

    options = []

    # Always show lessons 1-3 for better UX, regardless of completion
    for lesson_num in [1, 2, 3]:
        lesson_meta = LESSON_PROGRESSION.get(lesson_num, {})

        # Determine status based on completion and criteria
        if lesson_num in completed_lessons:
            status = "✅"
        elif lesson_num == current_lesson:
            # Check if current lesson's criteria are met (lesson complete but not marked)
            if lesson_num == 1 and "tag_in_union_zone" in achieved_criteria:
                status = "🎉"  # Completed but user needs to advance
            elif lesson_num == 2 and "two_tags_in_union" in achieved_criteria:
                status = "🎉"
            elif lesson_num == 3 and "tag_in_intersection" in achieved_criteria:
                status = "🎉"
            else:
                status = "🔄"
        elif lesson_num in available_lessons:
            status = "⏳"
        else:
            status = "🔒"

        # Special label for completed lessons that haven't been advanced
        if lesson_num == 1 and "tag_in_union_zone" in achieved_criteria and lesson_num not in completed_lessons:
            label = f"{status} Lesson {lesson_num}: {lesson_meta.get('title', '')} - Complete! Click for Lesson 2"
        elif lesson_num == 2 and "two_tags_in_union" in achieved_criteria and lesson_num not in completed_lessons:
            label = f"{status} Lesson {lesson_num}: {lesson_meta.get('title', '')} - Complete! Click for Lesson 3"
        else:
            label = f"{status} Lesson {lesson_num}: {lesson_meta.get('title', '')}"

        options.append({
            "value": lesson_num,
            "label": label,
            "description": lesson_meta.get('description', ''),
            "duration": lesson_meta.get('duration_seconds', 60),
            "selected": lesson_num == current_lesson,
            "unlocked": lesson_num in available_lessons or lesson_num <= 3  # Always unlock first 3
        })

    # Add remaining lessons from available_lessons if any
    for lesson_num in available_lessons:
        if lesson_num not in [1, 2, 3] and lesson_num != "production":
            lesson_meta = LESSON_PROGRESSION.get(lesson_num, {})
            status = "✅" if lesson_num in completed_lessons else "🔄" if lesson_num == current_lesson else "⏳"

            options.append({
                "value": lesson_num,
                "label": f"{status} Lesson {lesson_num}: {lesson_meta.get('title', '')}",
                "description": lesson_meta.get('description', ''),
                "duration": lesson_meta.get('duration_seconds', 60),
                "selected": lesson_num == current_lesson,
                "unlocked": True
            })

    # Add production mode if unlocked
    if "production" in available_lessons:
        options.append({
            "value": "production",
            "label": "🚀 Production Mode",
            "description": "Use MultiCardz with your own data",
            "selected": current_lesson == "production",
            "unlocked": True
        })

    return sorted(options, key=lambda x: x["value"] if isinstance(x["value"], int) else 999)


def create_lesson_hint_text(lesson_state: Dict, zone_state: Dict) -> Optional[str]:
    """
    Generate contextual hint text based on lesson state.

    Args:
        lesson_state: Current lesson state
        zone_state: Current zone state

    Returns:
        Hint text or None
    """
    current_lesson = lesson_state.get("current_lesson", 1)
    achieved_criteria = lesson_state.get("achieved_criteria", [])

    if not lesson_state.get("show_hints", True):
        return None

    # Lesson 1 hints
    if current_lesson == 1:
        # Check if first drag has been completed (stored in achieved criteria)
        if "tag_in_union_zone" in achieved_criteria:
            # First drag completed, never show hint again
            return None

        union_tags = zone_state.get("zones", {}).get("union", {}).get("tags", [])
        if "drag me to first box" not in union_tags:
            return "drag the blue tag to the box below it to see your first card!"
        else:
            # Tag is in zone, cards should be showing, hide instructional text
            return None

    # Lesson 2 hints
    elif current_lesson == 2:
        union_tags = zone_state.get("zones", {}).get("union", {}).get("tags", [])
        if len(union_tags) == 0:
            return "💡 Try dragging the 'important' tag to the blue union zone to see cards with that tag!"
        elif len(union_tags) == 1:
            return "💡 Great! Now try dragging the 'tutorial' tag to the same blue zone to see UNION operations!"
        elif len(union_tags) >= 2:
            return "🎉 Excellent! You're seeing the UNION of multiple tags. Ready for Lesson 3?"

    # Lesson 3 hints
    elif current_lesson == 3:
        intersection_tags = zone_state.get("zones", {}).get("intersection", {}).get("tags", [])
        if not intersection_tags:
            return "💡 Try dragging the 'urgent' tag to the green INTERSECTION zone!"
        else:
            return "🎉 Perfect! Notice how intersection shows items with ALL the tags."

    return None


def get_lesson_progress_percentage(lesson_state: Dict) -> float:
    """
    Calculate overall lesson progress as percentage.

    Args:
        lesson_state: Current lesson state

    Returns:
        Progress percentage (0.0 to 1.0)
    """
    completed_lessons = lesson_state.get("completed_lessons", [])
    current_lesson = lesson_state.get("current_lesson", 1)

    total_lessons = len(LESSON_PROGRESSION)
    completed_count = len(completed_lessons)

    # Add partial progress for current lesson
    if current_lesson not in completed_lessons and current_lesson in LESSON_PROGRESSION:
        achieved_criteria = lesson_state.get("achieved_criteria", [])
        required_criteria = LESSON_PROGRESSION[current_lesson]["success_criteria"]

        if required_criteria:
            criteria_progress = len(achieved_criteria) / len(required_criteria)
            completed_count += min(criteria_progress, 0.9)  # Max 90% for incomplete lesson

    return completed_count / total_lessons


def serialize_lesson_state(lesson_state: Dict) -> str:
    """Serialize lesson state for storage."""
    return json.dumps(lesson_state, default=str)


def deserialize_lesson_state(lesson_state_json: str) -> Dict:
    """Deserialize lesson state from storage."""
    try:
        return json.loads(lesson_state_json)
    except (json.JSONDecodeError, TypeError):
        return get_default_lesson_state()