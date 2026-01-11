"""
Session planning for structured browsing.

Defines browsing structures (news, YouTube, fashion, forums) and session plans
that guide the AI's browsing behavior.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class BrowsingStructure(Enum):
    """
    Types of browsing sessions the AI can perform.

    Each structure has a distinct starting point and expected behaviors.
    """
    NEWS = "news"
    YOUTUBE = "youtube"
    FASHION = "fashion"
    FORUMS = "forums"
    SHOPPING = "shopping"


# Structure descriptions for AI prompts
STRUCTURE_DESCRIPTIONS = {
    BrowsingStructure.NEWS: (
        "You are browsing news websites. Your goal is to find and read interesting news articles. "
        "Click on headlines that catch your attention, scroll through articles, and explore different "
        "news topics. You might visit multiple news sources to get different perspectives."
    ),
    BrowsingStructure.YOUTUBE: (
        "You are watching YouTube videos. Your goal is to find and watch interesting videos. "
        "Search for topics you're interested in, click on video thumbnails, watch videos by scrolling "
        "through them, and explore recommended videos in the sidebar. Let yourself get drawn into "
        "interesting content."
    ),
    BrowsingStructure.FASHION: (
        "You are browsing fashion websites. Your goal is to explore fashion trends, clothing, and styles. "
        "Look at product images, scroll through galleries, and browse different categories like "
        "men's/women's fashion, accessories, or seasonal collections. You're window shopping, not buying."
    ),
    BrowsingStructure.FORUMS: (
        "You are browsing online forums and discussion boards. Your goal is to read interesting "
        "discussions and threads. Browse different subreddits or forum categories, read comments, "
        "scroll through threads, and explore topics that interest you."
    ),
    BrowsingStructure.SHOPPING: (
        "You are comparison shopping online. Your goal is to research products by reading reviews, "
        "comparing prices, and looking at product details. Browse different product listings, scroll "
        "through reviews, and explore related items. You're researching, not purchasing."
    ),
}

# Starting points for each structure
STRUCTURE_STARTING_POINTS = {
    BrowsingStructure.NEWS: {
        "type": "search",
        "query": "latest news today",
        "fallback_url": "https://news.google.com"
    },
    BrowsingStructure.YOUTUBE: {
        "type": "direct",
        "url": "https://www.youtube.com"
    },
    BrowsingStructure.FASHION: {
        "type": "direct",
        "url": "https://www.zara.com"
    },
    BrowsingStructure.FORUMS: {
        "type": "direct",
        "url": "https://www.reddit.com"
    },
    BrowsingStructure.SHOPPING: {
        "type": "search",
        "query": "best products reviews",
        "fallback_url": "https://www.amazon.com"
    },
}

# Default safety constraints
DEFAULT_SAFETY_CONSTRAINTS = [
    "NEVER click on logout, sign out, or log out buttons",
    "NEVER click on buy, purchase, checkout, or payment buttons",
    "NEVER submit forms with personal information",
    "NEVER close the browser or tabs",
    "NEVER click on delete, remove, or unsubscribe buttons",
    "AVOID clicking on login or sign in unless already logged in",
    "AVOID pop-ups and modal dialogs - close them if they appear",
]


@dataclass
class SessionPlan:
    """
    A plan for a browsing session.

    Attributes:
        structure: The type of browsing session
        duration_minutes: How long the session should run
        persona_id: Optional persona ID (placeholder for Milestone 4)
        constraints: Safety rules the AI must follow
        created_at: When the plan was created
    """
    structure: BrowsingStructure
    duration_minutes: int
    persona_id: Optional[str] = None
    constraints: list[str] = field(default_factory=lambda: DEFAULT_SAFETY_CONSTRAINTS.copy())
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def description(self) -> str:
        """Get the human-readable description for this structure."""
        return STRUCTURE_DESCRIPTIONS.get(
            self.structure,
            f"Browsing the web following {self.structure.value} patterns."
        )

    @property
    def starting_point(self) -> dict:
        """Get the starting point configuration for this structure."""
        return STRUCTURE_STARTING_POINTS.get(
            self.structure,
            {"type": "search", "query": "interesting websites"}
        )

    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds."""
        return self.duration_minutes * 60

    def to_dict(self) -> dict:
        """Convert plan to dictionary for logging."""
        return {
            "structure": self.structure.value,
            "duration_minutes": self.duration_minutes,
            "persona_id": self.persona_id,
            "constraints_count": len(self.constraints),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SessionContext:
    """
    Runtime context during a browsing session.

    Tracks what has happened so far to help the AI make informed decisions.
    """
    plan: SessionPlan
    start_time: datetime = field(default_factory=datetime.now)
    action_history: list[str] = field(default_factory=list)
    current_url: Optional[str] = None
    pages_visited: int = 0
    errors: int = 0

    @property
    def elapsed_seconds(self) -> float:
        """Seconds since session started."""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def remaining_seconds(self) -> float:
        """Seconds remaining in session."""
        return max(0, self.plan.duration_seconds - self.elapsed_seconds)

    @property
    def is_expired(self) -> bool:
        """Whether session time has expired."""
        return self.elapsed_seconds >= self.plan.duration_seconds

    def add_action(self, action_str: str) -> None:
        """Record an action in history (keep last 10)."""
        self.action_history.append(action_str)
        if len(self.action_history) > 10:
            self.action_history.pop(0)

    def get_recent_actions(self, count: int = 5) -> list[str]:
        """Get the most recent actions."""
        return self.action_history[-count:]


def create_plan(
    structure: BrowsingStructure,
    duration_minutes: int = 3,
    persona_id: Optional[str] = None,
    extra_constraints: Optional[list[str]] = None
) -> SessionPlan:
    """
    Create a session plan.

    Args:
        structure: Type of browsing session
        duration_minutes: How long to run (default 3 minutes)
        persona_id: Optional persona ID (placeholder for M4)
        extra_constraints: Additional safety rules to add

    Returns:
        SessionPlan configured for the specified structure
    """
    constraints = DEFAULT_SAFETY_CONSTRAINTS.copy()
    if extra_constraints:
        constraints.extend(extra_constraints)

    return SessionPlan(
        structure=structure,
        duration_minutes=duration_minutes,
        persona_id=persona_id,
        constraints=constraints
    )
