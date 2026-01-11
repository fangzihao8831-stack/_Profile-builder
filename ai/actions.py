"""
Action schema for AI-driven browsing decisions.

Defines the structured actions the AI can take during a browsing session.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Literal


class ActionType(Enum):
    """Types of actions the AI can take."""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"


@dataclass
class BrowsingAction:
    """
    A structured action decided by the AI.

    Attributes:
        action_type: The type of action to perform
        target: Element description for click/type actions (e.g., "search button", "video thumbnail")
        text: Text to type or URL to navigate to
        direction: Scroll direction ("up" or "down")
        duration: Wait duration in seconds
        reasoning: AI's explanation for why this action fits the session plan
    """
    action_type: ActionType
    reasoning: str
    target: Optional[str] = None
    text: Optional[str] = None
    direction: Optional[Literal["up", "down"]] = None
    duration: Optional[float] = None

    def __post_init__(self):
        """Validate action has required fields for its type."""
        if self.action_type == ActionType.CLICK and not self.target:
            raise ValueError("CLICK action requires a target")
        if self.action_type == ActionType.TYPE and not self.text:
            raise ValueError("TYPE action requires text")
        if self.action_type == ActionType.SCROLL and not self.direction:
            raise ValueError("SCROLL action requires direction")
        if self.action_type == ActionType.NAVIGATE and not self.text:
            raise ValueError("NAVIGATE action requires text (URL)")

    @classmethod
    def click(cls, target: str, reasoning: str) -> "BrowsingAction":
        """Create a click action."""
        return cls(
            action_type=ActionType.CLICK,
            target=target,
            reasoning=reasoning
        )

    @classmethod
    def type_text(cls, text: str, reasoning: str, target: Optional[str] = None) -> "BrowsingAction":
        """Create a type action."""
        return cls(
            action_type=ActionType.TYPE,
            text=text,
            target=target,
            reasoning=reasoning
        )

    @classmethod
    def scroll(cls, direction: Literal["up", "down"], reasoning: str) -> "BrowsingAction":
        """Create a scroll action."""
        return cls(
            action_type=ActionType.SCROLL,
            direction=direction,
            reasoning=reasoning
        )

    @classmethod
    def wait(cls, duration: float, reasoning: str) -> "BrowsingAction":
        """Create a wait action."""
        return cls(
            action_type=ActionType.WAIT,
            duration=duration,
            reasoning=reasoning
        )

    @classmethod
    def navigate(cls, url: str, reasoning: str) -> "BrowsingAction":
        """Create a navigate action."""
        return cls(
            action_type=ActionType.NAVIGATE,
            text=url,
            reasoning=reasoning
        )

    @classmethod
    def from_dict(cls, data: dict) -> "BrowsingAction":
        """
        Parse action from VLM JSON response.

        Expected format:
        {
            "action": "click|type|scroll|wait|navigate",
            "target": "element description",
            "text": "text to type or URL",
            "direction": "up|down",
            "duration": 2.0,
            "reasoning": "why this action"
        }
        """
        action_str = data.get("action", "").lower()

        try:
            action_type = ActionType(action_str)
        except ValueError:
            raise ValueError(f"Unknown action type: {action_str}")

        return cls(
            action_type=action_type,
            target=data.get("target"),
            text=data.get("text"),
            direction=data.get("direction"),
            duration=data.get("duration"),
            reasoning=data.get("reasoning", "No reasoning provided")
        )

    def to_dict(self) -> dict:
        """Convert action to dictionary for logging/debugging."""
        return {
            "action": self.action_type.value,
            "target": self.target,
            "text": self.text,
            "direction": self.direction,
            "duration": self.duration,
            "reasoning": self.reasoning
        }

    def __str__(self) -> str:
        """Human-readable action description."""
        if self.action_type == ActionType.CLICK:
            return f"CLICK on '{self.target}'"
        elif self.action_type == ActionType.TYPE:
            preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
            return f"TYPE '{preview}'"
        elif self.action_type == ActionType.SCROLL:
            return f"SCROLL {self.direction}"
        elif self.action_type == ActionType.WAIT:
            return f"WAIT {self.duration}s"
        elif self.action_type == ActionType.NAVIGATE:
            return f"NAVIGATE to '{self.text}'"
        return f"UNKNOWN ACTION: {self.action_type}"


@dataclass
class ExecutionResult:
    """
    Result of executing an action.

    Attributes:
        success: Whether the action was executed successfully
        action: The action that was executed
        error: Error message if failed
        click_coords: Actual screen coordinates clicked (if click action)
        verified: Whether the action effect was verified
    """
    success: bool
    action: BrowsingAction
    error: Optional[str] = None
    click_coords: Optional[tuple[int, int]] = None
    verified: bool = False

    def __str__(self) -> str:
        status = "OK" if self.success else "FAILED"
        verified = " (verified)" if self.verified else ""
        if self.error:
            return f"[{status}] {self.action} - {self.error}"
        return f"[{status}] {self.action}{verified}"
