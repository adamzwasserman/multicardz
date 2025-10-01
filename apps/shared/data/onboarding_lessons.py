"""
MultiCardz™ Progressive Onboarding Lesson Data
Contains all lesson cards, tags, and progression logic for teaching users.
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


# Lesson 1: Basic Tag Dragging (30 seconds)
LESSON_1_CARDS = [
    LessonCard(
        id="lesson1_success",
        title="Great Job! 🎯",
        content="""<div class="lesson-card success-card">
            <h3>🎯 Congratulations! You discovered the magic! ✨</h3>
            <p>When you dragged that tag, MultiCardz instantly showed you matching cards. This is <strong>spatial filtering</strong> - no typing, just drag and discover!</p>

            <div class="lesson-achievement">
                <p>✅ <strong>You've mastered:</strong> Basic tag dragging and card discovery!</p>
            </div>
        </div>""",
        tags=["lesson:1", "step:success", "lesson1_completed", "drag me to first box"],
        lesson_number=1,
        step_number=2,
        success_criteria="tag_in_union_zone",
        next_action="continue_learning"
    ),

    LessonCard(
        id="lesson1_next_step",
        title="Ready for More Tags? 🏷️",
        content="""<div class="lesson-card next-step-card">
            <h3>🏷️ Now let's try multiple tags!</h3>
            <p>Real information has multiple tags. Look at the tag cloud - you now have a new <code>important</code> tag to work with!</p>

            <div class="lesson-instruction highlight-action">
                <h4>👆 NEXT STEP:</h4>
                <p><strong>Drag the <code>important</code> tag to the same blue ANY zone.</strong></p>
                <p>Watch how the ANY zone shows you cards that have <em>either</em> tag!</p>
            </div>

            <div class="concept-explanation">
                <p><em>💡 The ANY zone shows items with "this OR that" - any of the tags you put there.</em></p>
            </div>
        </div>""",
        tags=["lesson:1", "step:next", "lesson1_completed", "drag me to first box"],
        lesson_number=1,
        step_number=3,
        success_criteria="tag_in_union_zone",
        next_action="drag_important_tag"
    )
]

LESSON_1_TAGS = [
    LessonTag(
        name="drag me to first box",
        lesson_number=1,
        instruction="👆 Drag me to the blue ANY zone! 👇",
        zone_target="union"
    ),
    LessonTag(
        name="important",
        lesson_number=1,
        instruction="💡 Drag me to the ANY zone too!",
        zone_target="union"
    ),
    LessonTag(
        name="urgent",
        lesson_number=1,
        instruction="🚨 Drag me to the green ALL zone!",
        zone_target="intersection"
    )
]

# Lesson 2: Card Revelation and Lesson Navigation (45 seconds)
LESSON_2_CARDS = [
    LessonCard(
        id="lesson2_any_success",
        title="ANY Zone Mastered! 🔗",
        content="""<div class="lesson-card any-success-card">
            <h3>🔗 Excellent! You just used the ANY zone with multiple tags!</h3>
            <p>Notice how you now see cards that have <em>either</em> tag. The ANY zone shows items with "this OR that" - any of the tags you put there.</p>

            <div class="concepts-learned">
                <h4>What you've learned:</h4>
                <ul>
                    <li>✅ Tags control what cards appear</li>
                    <li>✅ ANY zone = "show me everything with any of these tags"</li>
                    <li>✅ Physical movement = logical operations</li>
                </ul>
            </div>
        </div>""",
        tags=["lesson:2", "step:any_success", "important"],
        lesson_number=1,
        step_number=4,
        success_criteria="two_tags_in_union",
        next_action="continue_to_all"
    ),

    LessonCard(
        id="lesson2_all_intro",
        title="Try the ALL Zone! 🎯",
        content="""<div class="lesson-card all-intro-card">
            <h3>🎯 Now let's learn about the ALL zone!</h3>
            <p>The ALL zone is different from the ANY zone. Look for the green ALL zone below.</p>

            <div class="lesson-instruction highlight-action">
                <h4>👆 NEXT STEP:</h4>
                <p><strong>Drag the new <code>urgent</code> tag to the green ALL zone.</strong></p>
                <p>Watch how the ALL zone shows only items that have <em>all</em> the tags you put there!</p>
            </div>

            <div class="concept-explanation">
                <p><em>💡 The ALL zone shows items with "this AND that" - items must have every tag you put there.</em></p>
            </div>
        </div>""",
        tags=["lesson:2", "step:all_intro", "important"],
        lesson_number=1,
        step_number=5,
        success_criteria="two_tags_in_union",
        next_action="drag_to_all"
    ),

    LessonCard(
        id="lesson2_all_success",
        title="ALL Zone Mastered! 🎯",
        content="""<div class="lesson-card all-success-card">
            <h3>🎯 Perfect! You just used the ALL zone!</h3>
            <p>Notice how the results changed - now you only see items that have <em>both</em> tags. The ALL zone shows items with "this AND that".</p>

            <div class="concepts-learned">
                <h4>Compare the zones:</h4>
                <ul>
                    <li>🔵 ANY zone = "this OR that" (broader results)</li>
                    <li>🟢 ALL zone = "this AND that" (narrower, more specific results)</li>
                </ul>
            </div>
        </div>""",
        tags=["lesson:3", "step:all_success", "urgent", "important"],
        lesson_number=1,
        step_number=6,
        success_criteria="tag_in_intersection",
        next_action="continue_to_none"
    ),

    LessonCard(
        id="lesson2_none_intro",
        title="Try the NONE Zone! 🚫",
        content="""<div class="lesson-card none-intro-card">
            <h3>🚫 Finally, let's try the NONE zone!</h3>
            <p>The NONE zone is for filtering OUT things you don't want to see.</p>

            <div class="lesson-instruction highlight-action">
                <h4>👆 FINAL STEP:</h4>
                <p><strong>Move one of your tags from the ANY zone to the red NONE zone.</strong></p>
                <p>Watch how items with that tag disappear from your results!</p>
            </div>

            <div class="concept-explanation">
                <p><em>💡 The NONE zone shows items "NOT this" - items that don't have the tags you put there.</em></p>
            </div>
        </div>""",
        tags=["lesson:3", "step:none_intro", "urgent", "important"],
        lesson_number=1,
        step_number=7,
        success_criteria="tag_in_intersection",
        next_action="drag_to_none"
    )
]

LESSON_2_TAGS = []

# Lesson 3: Dimensional Layout Demo (columns and rows)
LESSON_3_CARDS = [
    LessonCard(
        id="lesson3_intersection_intro",
        title="Master Intersection Operations 🎯",
        content="""<div class="lesson-card intersection-intro-card">
            <h3>🎯 Time to learn INTERSECTION operations!</h3>
            <p>Union was "this OR that" - now learn "this AND that".</p>
            <div class="zone-explanation">
                <p>Notice the different colored zones:</p>
                <ul>
                    <li><span class="union-color">🔵 Union Zone</span> = "show me items with ANY of these tags"</li>
                    <li><span class="intersection-color">🟢 Intersection Zone</span> = "show me items with ALL of these tags"</li>
                </ul>
            </div>
            <div class="lesson-instruction">
                <p><strong>Try this:</strong> Drag the <code>urgent</code> tag to the green <strong>intersection zone</strong>.</p>
            </div>
        </div>""",
        tags=["lesson:3", "step:intro", "lesson3_started"],
        lesson_number=3,
        step_number=1,
        success_criteria="lesson_3_selected",
        next_action="drag_to_intersection"
    ),

    LessonCard(
        id="lesson3_intersection_example",
        title="See the Difference? 🔍",
        content="""<div class="lesson-card intersection-example-card">
            <h3>🔍 This card has BOTH tags!</h3>
            <p>This card appeared because it has <strong>both</strong> the tags you placed in the intersection zone.</p>
            <div class="comparison">
                <div class="union-example">
                    <h4>Union Zone (Blue): "OR" logic</h4>
                    <p>Shows items with <em>any</em> of the tags</p>
                </div>
                <div class="intersection-example">
                    <h4>Intersection Zone (Green): "AND" logic</h4>
                    <p>Shows items with <em>all</em> of the tags</p>
                </div>
            </div>
            <div class="lesson-instruction">
                <p><strong>Experiment:</strong> Try moving tags between zones and watch how the results change!</p>
            </div>
        </div>""",
        tags=["lesson:3", "step:example", "urgent", "important"],
        lesson_number=3,
        step_number=2,
        success_criteria="tag_in_intersection",
        next_action="experiment_with_zones"
    ),

    LessonCard(
        id="lesson3_mastery",
        title="You're Getting It! 🧠",
        content="""<div class="lesson-card mastery-card">
            <h3>🧠 You're mastering spatial tag manipulation!</h3>
            <div class="skills-learned">
                <h4>Skills unlocked:</h4>
                <ul>
                    <li>✅ <strong>Union operations</strong> (ANY matching tags)</li>
                    <li>✅ <strong>Intersection operations</strong> (ALL matching tags)</li>
                    <li>✅ <strong>Dynamic filtering</strong> by moving tags</li>
                    <li>✅ <strong>Visual logic</strong> instead of complex queries</li>
                </ul>
            </div>
            <div class="real-world">
                <p><strong>Real-world example:</strong> Find emails that are both "urgent" AND "from-boss" by dragging both tags to the intersection zone!</p>
            </div>
            <div class="lesson-instruction">
                <p><strong>Ready for Lesson 4?</strong> Learn about EXCLUSION operations - how to hide things you don't want!</p>
            </div>
        </div>""",
        tags=["lesson:3", "step:mastery", "urgent", "tutorial"],
        lesson_number=3,
        step_number=3,
        success_criteria="experimented_with_zones",
        next_action="select_lesson_4"
    )
]

LESSON_3_TAGS = [
    LessonTag(
        name="urgent",
        lesson_number=3,
        instruction="🚨 Drag me to the green intersection zone",
        zone_target="intersection"
    ),
    LessonTag(
        name="project_alpha",
        lesson_number=3,
        instruction="📋 I represent a project tag",
        zone_target="any"
    ),
    LessonTag(
        name="work",
        lesson_number=3,
        instruction="💼 I categorize work items",
        zone_target="any"
    )
]

# Continue with lessons 4-7...
LESSON_4_CARDS = [
    LessonCard(
        id="lesson4_exclusion_intro",
        title="Master Exclusion Operations 🚫",
        content="""<div class="lesson-card exclusion-intro-card">
            <h3>🚫 Sometimes you want to EXCLUDE things!</h3>
            <p>You've learned to include with Union and Intersection. Now learn to exclude with the Exclusion zone.</p>
            <div class="exclusion-explanation">
                <p><strong>Exclusion Zone</strong> = "show me items that do NOT have these tags"</p>
                <p>This is incredibly powerful for filtering out noise and distractions.</p>
            </div>
            <div class="lesson-instruction">
                <p><strong>Try this:</strong> Drag the <code>spam</code> tag to the red <strong>exclusion zone</strong>.</p>
                <p>Watch how items tagged with "spam" disappear from your results!</p>
            </div>
        </div>""",
        tags=["lesson:4", "step:intro", "lesson4_started"],
        lesson_number=4,
        step_number=1,
        success_criteria="lesson_4_selected",
        next_action="drag_to_exclusion"
    )
    # Additional lesson 4-7 cards would continue here...
]

# Compile all lesson data
ALL_LESSON_CARDS = LESSON_1_CARDS + LESSON_2_CARDS + LESSON_3_CARDS + LESSON_4_CARDS
ALL_LESSON_TAGS = LESSON_1_TAGS + LESSON_2_TAGS + LESSON_3_TAGS

# Lesson progression metadata
LESSON_PROGRESSION = {
    1: {
        "title": "Basic Dragging",
        "duration_seconds": 30,
        "description": "Learn to drag tags to zones",
        "success_criteria": ["tag_in_union_zone"],
        "unlocks": [2]
    },
    2: {
        "title": "Card Revelation",
        "duration_seconds": 45,
        "description": "Understand how tags reveal cards",
        "success_criteria": ["two_tags_in_union"],
        "unlocks": [3]
    },
    3: {
        "title": "Union Operations",
        "duration_seconds": 90,
        "description": "Master OR logic with multiple tags",
        "success_criteria": ["experimented_with_zones"],
        "unlocks": [4]
    },
    4: {
        "title": "Intersection Operations",
        "duration_seconds": 90,
        "description": "Master AND logic",
        "success_criteria": ["tag_in_intersection"],
        "unlocks": [5]
    },
    5: {
        "title": "Exclusion Operations",
        "duration_seconds": 75,
        "description": "Learn to filter out unwanted items",
        "success_criteria": ["tag_in_exclusion"],
        "unlocks": [6]
    },
    6: {
        "title": "Advanced Features",
        "duration_seconds": 120,
        "description": "Temporal filters and dimensions",
        "success_criteria": ["used_advanced_feature"],
        "unlocks": [7]
    },
    7: {
        "title": "Real-world Workflow",
        "duration_seconds": 180,
        "description": "Complete workflow example",
        "success_criteria": ["completed_workflow"],
        "unlocks": ["production"]
    }
}


def get_lesson_cards(lesson_number: int) -> list[LessonCard]:
    """Get all cards for a specific lesson."""
    return [card for card in ALL_LESSON_CARDS if card.lesson_number == lesson_number]


def get_lesson_tags(lesson_number: int) -> list[LessonTag]:
    """Get all tags for a specific lesson."""
    return [tag for tag in ALL_LESSON_TAGS if tag.lesson_number == lesson_number]


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
            available.extend(LESSON_PROGRESSION[completed]["unlocks"])

    # Remove duplicates and filter valid lessons
    available = list(set(available))
    return [lesson for lesson in available if lesson in LESSON_PROGRESSION or lesson == "production"]
