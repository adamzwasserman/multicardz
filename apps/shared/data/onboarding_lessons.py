"""
MultiCardz™ Progressive Onboarding Lesson Data
Contains all lesson cards, tags, and progression logic for teaching users.

Based on Piagetian Learning principles with Muji aesthetic.
"""

from datetime import UTC, datetime
from typing import NamedTuple


class LessonCard(NamedTuple):
    """Structured lesson card data."""
    id: str
    title: str
    content: str
    tags: list[str]
    lesson_number: int
    step_number: int
    success_criteria: str
    next_action: str


class LessonTag(NamedTuple):
    """Structured lesson tag data."""
    name: str
    lesson_number: int
    instruction: str
    zone_target: str


# Lesson 1: Basic Tag Dragging - Appears when "drag me to the SHOW box" is dragged to SHOW
LESSON_1_CARDS = [
    LessonCard(
        id="l1_success",
        title="Good job!",
        content="""<div class="lesson-card">
            <p>Good job! You made these cards appear by dragging the tag into the SHOW box. multicardz will display all cards that have ANY one of the tags in that box.</p>
        </div>""",
        tags=["lesson1", "drag me to the SHOW box", "ANY", "ALL"],
        lesson_number=1,
        step_number=1,
        success_criteria="tag_in_show_zone",
        next_action="drag_second_tag"
    ),

    LessonCard(
        id="l1_instruction",
        title="Next Step",
        content="""<div class="lesson-card">
            <p>Now drag a SECOND tag into the same box.</p>
        </div>""",
        tags=["lesson1", "drag me to the SHOW box"],
        lesson_number=1,
        step_number=2,
        success_criteria="tag_in_show_zone",
        next_action="drag_second_tag"
    ),

    LessonCard(
        id="l1_tech",
        title="Technical Explanation",
        content="""<div class="lesson-card tech-card">
            <p><strong>Technical:</strong> The SHOW box creates a Card set which is the union of all Card sets created by intersections between the Universe of Cards with the Tags (A ∪ B ∪ C...). In this case we have one set: (Universe∩A)</p>
        </div>""",
        tags=["lesson1", "tech-talk"],
        lesson_number=1,
        step_number=1,
        success_criteria="tag_in_show_zone",
        next_action="optional_technical"
    )
]

# Lesson 2: Multiple Tags - Appears when "drag me next" is dragged to SHOW
LESSON_2_CARDS = [
    LessonCard(
        id="l2_success",
        title="Another good job!",
        content="""<div class="lesson-card">
            <p>Another good job! Notice that this card has different tags than the other two. The first two cards have the 'lesson1' and 'drag me to the SHOW box'. This card has 'lesson2' and 'drag me next'. That is because multicardz will display all cards that have ANY one of the tags in the SHOW box.</p>
        </div>""",
        tags=["lesson2", "drag me next", "ANY", "ALL"],
        lesson_number=2,
        step_number=1,
        success_criteria="two_tags_in_show",
        next_action="drag_to_filter"
    ),

    LessonCard(
        id="l2_instruction",
        title="Next Step",
        content="""<div class="lesson-card">
            <p>Now drag the 'ALL' tag to the FILTER box. This will remove the previous instruction cards and show only the new instruction card that has 'lesson2' and 'ALL' tags.</p>
        </div>""",
        tags=["lesson2", "drag me next"],
        lesson_number=2,
        step_number=2,
        success_criteria="two_tags_in_show",
        next_action="drag_to_filter"
    ),

    LessonCard(
        id="l2_tech",
        title="Technical Explanation",
        content="""<div class="lesson-card tech-card">
            <p><strong>Technical:</strong> With two tags in SHOW, you now have (Universe∩A) ∪ (Universe∩B). Each tag first intersects with all cards, then those sets are unioned.</p>
        </div>""",
        tags=["lesson2", "tech-talk"],
        lesson_number=2,
        step_number=1,
        success_criteria="two_tags_in_show",
        next_action="optional_technical"
    )
]

# Lesson 3: Filtering - Appears when "ALL" is dragged to FILTER
LESSON_3_CARDS = [
    LessonCard(
        id="l3_success",
        title="Great work!",
        content="""<div class="lesson-card">
            <p>Great work! You just learned that the FILTER box shows only cards with ALL the required tags. Now click lesson1, then Command+click (Mac) or Control+click (Windows) lesson2, and drag both to the HIDE box.</p>
        </div>""",
        tags=["lesson3", "ALL"],
        lesson_number=3,
        step_number=1,
        success_criteria="tag_in_filter",
        next_action="multi_select_hide"
    ),

    LessonCard(
        id="l3_instruction",
        title="Next Step",
        content="""<div class="lesson-card">
            <p>Notice only lesson3 cards remain. The 'lesson4' tag is waiting in the tag cloud...</p>
        </div>""",
        tags=["lesson3", "ALL"],
        lesson_number=3,
        step_number=2,
        success_criteria="tag_in_filter",
        next_action="discover_lesson4"
    ),

    LessonCard(
        id="l3_tech",
        title="Technical Explanation",
        content="""<div class="lesson-card tech-card">
            <p><strong>Technical:</strong> FILTER reduces the Universe to the intersection of the Universe and all tags in the FILTER drop zone. Cards must belong to ALL specified sets: (Cards∩A) ∩ (Cards∩B) ∩ (Cards∩ALL). This reduces the Universe space available to the SHOW box</p>
        </div>""",
        tags=["lesson3", "ALL", "tech-talk"],
        lesson_number=3,
        step_number=1,
        success_criteria="tag_in_filter",
        next_action="optional_technical"
    )
]

# Lesson 4: Self-Discovery - User must discover how to show these
LESSON_4_CARDS = [
    LessonCard(
        id="l4_success",
        title="Congratulations!",
        content="""<div class="lesson-card">
            <p>Congratulations! You've discovered the core of multicardz - SHOW, FILTER, and HIDE work together to reveal patterns in your data. For advanced techniques, click the Help button (lower left) to access video tutorials, OR create a fresh project from the Project menu to start organizing your own cards and tags.</p>
        </div>""",
        tags=["lesson4"],
        lesson_number=4,
        step_number=1,
        success_criteria="discovered_lesson4",
        next_action="complete_tutorial"
    ),

    LessonCard(
        id="l4_tech",
        title="Technical Explanation",
        content="""<div class="lesson-card tech-card">
            <p><strong>Technical:</strong> Order of operations: 1) Universe Set (all cards), 2) HIDE (exclude Card Sets), 3) FILTER (intersection), 4) SHOW (union of intersections). HIDE is applied first, removing cards before other operations.</p>
        </div>""",
        tags=["lesson4", "tech-talk"],
        lesson_number=4,
        step_number=1,
        success_criteria="discovered_lesson4",
        next_action="optional_technical"
    )
]

# All Lesson Tags (visible in tag cloud from the start)
LESSON_1_TAGS = [
    LessonTag(
        name="drag me to the SHOW box",
        lesson_number=1,
        instruction="👆 Drag me to the SHOW box!",
        zone_target="union"  # Maps to SHOW zone
    ),
    LessonTag(
        name="drag me next",
        lesson_number=2,
        instruction="Drag me to SHOW after the first tag",
        zone_target="union"
    ),
    LessonTag(
        name="ALL",
        lesson_number=3,
        instruction="Drag me to the FILTER box",
        zone_target="intersection"  # Maps to FILTER zone
    ),
    LessonTag(
        name="lesson1",
        lesson_number=1,
        instruction="Lesson 1 cards",
        zone_target="any"
    ),
    LessonTag(
        name="lesson2",
        lesson_number=2,
        instruction="Lesson 2 cards",
        zone_target="any"
    ),
    LessonTag(
        name="lesson3",
        lesson_number=3,
        instruction="Lesson 3 cards",
        zone_target="any"
    ),
    LessonTag(
        name="lesson4",
        lesson_number=4,
        instruction="Lesson 4 cards - discover how to reveal!",
        zone_target="any"
    ),
    LessonTag(
        name="tech-talk",
        lesson_number=0,  # Available in all lessons
        instruction="Reveals technical explanations",
        zone_target="union"
    )
]

LESSON_2_TAGS = []  # All tags available from start
LESSON_3_TAGS = []  # All tags available from start

# Compile all lesson data
ALL_LESSON_CARDS = LESSON_1_CARDS + LESSON_2_CARDS + LESSON_3_CARDS + LESSON_4_CARDS
ALL_LESSON_TAGS = LESSON_1_TAGS  # All 8 tags available from the start

# Lesson progression metadata
LESSON_PROGRESSION = {
    1: {
        "title": "Basic Dragging",
        "duration_seconds": 30,
        "description": "Learn to drag tags to SHOW",
        "success_criteria": ["tag_in_show_zone"],
        "unlocks": [2]
    },
    2: {
        "title": "Multiple Tags",
        "duration_seconds": 45,
        "description": "Use multiple tags in SHOW",
        "success_criteria": ["two_tags_in_show"],
        "unlocks": [3]
    },
    3: {
        "title": "Filtering",
        "duration_seconds": 60,
        "description": "Master FILTER and HIDE",
        "success_criteria": ["tag_in_filter"],
        "unlocks": [4]
    },
    4: {
        "title": "Self-Discovery",
        "duration_seconds": 90,
        "description": "Discover lesson4 cards on your own",
        "success_criteria": ["discovered_lesson4"],
        "unlocks": ["production"]
    }
}


def get_lesson_cards(lesson_number: int) -> list[LessonCard]:
    """Get all cards for a specific lesson."""
    return [card for card in ALL_LESSON_CARDS if card.lesson_number == lesson_number]


def get_lesson_tags(lesson_number: int) -> list[LessonTag]:
    """
    Get all tags for a specific lesson.

    Note: In the new design, ALL 8 tags are available from the start.
    This function returns all tags regardless of lesson_number for compatibility.
    """
    if lesson_number == 1:
        return ALL_LESSON_TAGS
    return []  # All tags already visible from lesson 1


def get_default_lesson_state() -> dict:
    """Get the default lesson state for new users."""
    return {
        "current_lesson": 1,
        "current_step": 1,
        "completed_lessons": [],
        "lesson_progress": {},
        "started_at": datetime.now(UTC).isoformat(),
        "show_hints": True
    }


def validate_lesson_completion(lesson_number: int, user_state: dict) -> bool:
    """Check if a lesson has been completed based on success criteria."""
    lesson_meta = LESSON_PROGRESSION.get(lesson_number)
    if not lesson_meta:
        return False

    criteria = lesson_meta["success_criteria"]
    return all(criterion in user_state.get("achieved_criteria", []) for criterion in criteria)


def get_available_lessons(completed_lessons: list[int]) -> list[int]:
    """Get list of lessons available based on completed lessons."""
    available = [1]  # Lesson 1 always available

    for completed in completed_lessons:
        if completed in LESSON_PROGRESSION:
            unlocks = LESSON_PROGRESSION[completed]["unlocks"]
            for unlock in unlocks:
                if unlock != "production":
                    available.append(unlock)

    # Remove duplicates and sort
    return sorted(list(set(available)))
