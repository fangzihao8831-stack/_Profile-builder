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

            # DEBUG: Log full prompt
            self.logger.info("=" * 60)
            self.logger.info("DECISION MAKER DEBUG")
            self.logger.info("=" * 60)
            self.logger.info(f"PROMPT SENT TO QWEN:\n{prompt}")
            self.logger.info("-" * 60)

            # Ask VLM
            response = self.client.ask(prompt, image_path=temp_path)

            # DEBUG: Log raw response
            self.logger.info(f"QWEN RAW RESPONSE:\n{response.raw}")
            self.logger.info(f"QWEN PARSED CONTENT: {response.content}")
            self.logger.info("-" * 60)

            # Parse response into action
            action = self._parse_response(response.content)
            self.logger.info(f"PARSED ACTION: {action}")

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

        # Build forbidden elements from recent actions
        forbidden = set()
        for action in recent:
            if "CLICK on" in action:
                try:
                    target = action.split("CLICK on '")[1].rstrip("'")
                    forbidden.add(target.lower())
                except:
                    pass

        forbidden_str = ", ".join(forbidden) if forbidden else "none"

        # Get structure-specific goal
        structure = context.plan.structure.value
        goal = context.plan.description

        prompt = f"""SESSION: {structure}
GOAL: {goal}

FORBIDDEN (already tried, skip these): {forbidden_str}

RECENT: {recent_str}

Look at the screenshot. Pick ONE action:

RULES:
1. Cookie/consent popup visible? Click accept button FIRST
2. Click the EXACT text you see (e.g., "HOMBRE" not "Men", "Aceptar" not "Accept")
3. DO NOT click: logos, search icons, cart, account icons
4. DO NOT repeat elements from FORBIDDEN list

JSON response:
{{"action": "click", "target": "exact visible text or element", "reasoning": "why"}}
{{"action": "scroll", "direction": "down", "reasoning": "see more"}}
{{"action": "navigate", "text": "url.com", "reasoning": "go to site"}}"""

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
