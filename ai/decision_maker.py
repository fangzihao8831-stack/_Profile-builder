"""
AI decision maker for browsing sessions.

Uses VLM to analyze screenshots and decide what action to take next,
based on the session plan and context.
"""

import os
import tempfile
from typing import Optional
from datetime import datetime

from ai.ollama_client import OllamaClient
from ai.actions import BrowsingAction, ActionType
from ai.session_planner import SessionPlan, SessionContext
from core.safety import SafetyChecker, get_safety_checker
from core.logger import Log
from element.screenshot import Screenshot


class DecisionMaker:
    """
    Makes browsing decisions using VLM.

    Takes a screenshot and session context, asks the VLM what action
    a human would naturally take, and returns a structured action.
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        safety_checker: Optional[SafetyChecker] = None,
        debug: bool = True
    ):
        """
        Initialize the decision maker.

        Args:
            client: OllamaClient instance (creates one if not provided)
            safety_checker: SafetyChecker instance (uses global if not provided)
            debug: Whether to save debug info
        """
        self.client = client or OllamaClient()
        self.safety = safety_checker or get_safety_checker()
        self.debug = debug
        self.logger = Log.session()

    def decide(
        self,
        screenshot: Screenshot,
        context: SessionContext
    ) -> BrowsingAction:
        """
        Decide what action to take next.

        Args:
            screenshot: Current browser screenshot
            context: Session context with plan and history

        Returns:
            BrowsingAction to execute

        Raises:
            RuntimeError: If VLM fails to respond or parse
        """
        # Save screenshot temporarily for VLM
        temp_path = self._save_temp_screenshot(screenshot)

        try:
            # Build the prompt
            prompt = self._build_prompt(context)

            self.logger.debug(f"Asking VLM for decision (plan: {context.plan.structure.value})")

            # Ask VLM
            response = self.client.ask(prompt, image_path=temp_path)

            # Parse response into action
            action = self._parse_response(response.content)

            # Safety check
            is_safe, reason = self.safety.is_action_safe(action)
            if not is_safe:
                self.logger.warning(f"Unsafe action blocked: {reason}")
                # Return a safe fallback action
                return BrowsingAction.scroll(
                    direction="down",
                    reasoning=f"Original action blocked for safety: {reason}. Scrolling instead."
                )

            self.logger.info(f"Decision: {action}")
            return action

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _build_prompt(self, context: SessionContext) -> str:
        """Build the decision prompt for VLM."""
        # Get recent actions for context
        recent = context.get_recent_actions(5)
        recent_str = "\n".join(f"  - {a}" for a in recent) if recent else "  (no actions yet)"

        # Time remaining
        remaining = int(context.remaining_seconds)
        minutes = remaining // 60
        seconds = remaining % 60

        # Safety rules
        safety_rules = self.safety.get_safety_rules_prompt()

        prompt = f"""You are a human browsing the web naturally. Your browsing session plan is:

{context.plan.description}

TIME REMAINING: {minutes}m {seconds}s

RECENT ACTIONS:
{recent_str}

{safety_rules}

Look at the current screenshot and decide what a human would naturally do next.
Stay focused on your browsing plan ({context.plan.structure.value}).

Respond with ONLY a JSON object in this exact format:
{{
    "action": "click" or "type" or "scroll" or "wait" or "navigate",
    "target": "description of element to click/type into (required for click/type)",
    "text": "text to type or URL to navigate to (required for type/navigate)",
    "direction": "up" or "down" (required for scroll)",
    "duration": number of seconds (required for wait, usually 1-3),
    "reasoning": "brief explanation of why this action fits your browsing plan"
}}

Examples:
- Click a link: {{"action": "click", "target": "headline about technology news", "reasoning": "interesting news article"}}
- Scroll down: {{"action": "scroll", "direction": "down", "reasoning": "looking for more content"}}
- Watch video: {{"action": "wait", "duration": 5, "reasoning": "watching the video"}}
- Search: {{"action": "type", "target": "search box", "text": "cooking recipes", "reasoning": "searching for content"}}

What is your next action?"""

        return prompt

    def _parse_response(self, content: dict) -> BrowsingAction:
        """Parse VLM response into a BrowsingAction."""
        try:
            return BrowsingAction.from_dict(content)
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse VLM response: {e}")
            self.logger.debug(f"Response content: {content}")
            # Return a safe fallback
            return BrowsingAction.scroll(
                direction="down",
                reasoning=f"Parse error fallback: {e}"
            )

    def _save_temp_screenshot(self, screenshot: Screenshot) -> str:
        """Save screenshot to temp file for VLM."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        temp_dir = tempfile.gettempdir()
        path = os.path.join(temp_dir, f"decision_{timestamp}.png")
        screenshot.image.save(path, "PNG")
        return path


# Convenience function
def decide_action(
    screenshot: Screenshot,
    context: SessionContext,
    client: Optional[OllamaClient] = None
) -> BrowsingAction:
    """
    Quick function to get a browsing decision.

    Args:
        screenshot: Current browser screenshot
        context: Session context
        client: Optional OllamaClient

    Returns:
        BrowsingAction to execute
    """
    maker = DecisionMaker(client=client)
    return maker.decide(screenshot, context)
