"""
Action executor for AI browsing decisions.

Executes BrowsingAction objects using OS-level input modules.
"""

import random
import time
from typing import Optional, Tuple

from ai.actions import BrowsingAction, ActionType, ExecutionResult
from ai.ollama_client import OllamaClient
from element.screenshot import Screenshot, ScreenshotCapture
from element.vlm_finder import VLMElementFinder, ElementLocation
from input.coordinates import CoordinateTranslator, ScreenCoordinate
from input.mouse import HumanMouse
from input.keyboard import HumanKeyboard
from verification.click_verifier import ClickVerifier
from core.window_manager import WindowManager, ensure_adspower_foreground
from core.logger import Log


class ActionExecutor:
    """
    Executes browsing actions using OS-level input.

    Handles the complete flow: find element -> translate coords -> execute input -> verify.
    """

    # Timing constants (in seconds)
    SCROLL_PAUSE_MIN = 0.5
    SCROLL_PAUSE_MAX = 1.5
    ACTION_COOLDOWN_MIN = 0.3
    ACTION_COOLDOWN_MAX = 0.8
    ELEMENT_FIND_TIMEOUT = 10.0
    MAX_FIND_RETRIES = 2

    def __init__(
        self,
        hwnd: int,
        vlm_client: Optional[OllamaClient] = None,
        debug: bool = True
    ):
        """
        Args:
            hwnd: Window handle for browser
            vlm_client: OllamaClient (shared to keep model warm)
            debug: Whether to save debug info
        """
        self.hwnd = hwnd
        self.mouse = HumanMouse()
        self.keyboard = HumanKeyboard()
        self.finder = VLMElementFinder(client=vlm_client, debug=debug)
        self.translator = CoordinateTranslator()
        self.capture = ScreenshotCapture(debug=debug)
        self.verifier = ClickVerifier()
        self.window_manager = WindowManager()
        self.log = Log.session()
        self.debug = debug

    def execute(self, action: BrowsingAction) -> ExecutionResult:
        """
        Execute a browsing action.

        Args:
            action: BrowsingAction to execute

        Returns:
            ExecutionResult with success status and details
        """
        self.log.info(f"Executing: {action}")

        # Ensure window is focused
        if not self._ensure_window_focus():
            return ExecutionResult(
                success=False,
                action=action,
                error="Could not focus browser window"
            )

        # Dispatch to specific handler
        try:
            if action.action_type == ActionType.CLICK:
                result = self._execute_click(action)
            elif action.action_type == ActionType.TYPE:
                result = self._execute_type(action)
            elif action.action_type == ActionType.SCROLL:
                result = self._execute_scroll(action)
            elif action.action_type == ActionType.WAIT:
                result = self._execute_wait(action)
            elif action.action_type == ActionType.NAVIGATE:
                result = self._execute_navigate(action)
            else:
                result = ExecutionResult(
                    success=False,
                    action=action,
                    error=f"Unknown action type: {action.action_type}"
                )
        except Exception as e:
            self.log.error(f"Action execution failed: {e}")
            result = ExecutionResult(
                success=False,
                action=action,
                error=str(e)
            )

        # Apply cooldown after every action
        self._apply_cooldown()

        return result

    def _execute_click(self, action: BrowsingAction) -> ExecutionResult:
        """Execute a click action with element finding and verification."""
        # Find the element
        location, screenshot = self._find_element(action.target)

        if not location or not location.found:
            return ExecutionResult(
                success=False,
                action=action,
                error=f"Could not find element: '{action.target}'"
            )

        # DEBUG: Log element finding results
        self.log.info("=" * 60)
        self.log.info("ELEMENT FINDER DEBUG")
        self.log.info("=" * 60)
        self.log.info(f"TARGET: '{action.target}'")
        self.log.info(f"VLM BBOX: {location.bbox}")
        self.log.info(f"VLM CENTER: {location.center}")
        self.log.info(f"VLM CONFIDENCE: {location.confidence}")
        self.log.info(f"SCREENSHOT SIZE: {screenshot.vlm_size}")
        self.log.info(f"WINDOW RECT: {screenshot.window_rect}")
        self.log.info(f"SCALE FACTOR: {screenshot.scale_factor}")

        # Translate to screen coordinates
        try:
            coord = self.translator.element_to_screen(location, screenshot)
        except ValueError as e:
            return ExecutionResult(
                success=False,
                action=action,
                error=str(e)
            )

        # DEBUG: Log coordinate translation
        self.log.info(f"TRANSLATED SCREEN COORD: ({coord.x}, {coord.y})")
        self.log.info("=" * 60)

        # Execute click with jitter
        actual_x, actual_y = self.mouse.click_with_jitter(coord)
        self.log.info(f"Clicked at ({actual_x}, {actual_y})")

        # Verify click had effect
        verification = self.verifier.verify_click(
            hwnd=self.hwnd,
            before_screenshot=screenshot,
            clicked_target=action.target
        )

        return ExecutionResult(
            success=True,  # Click was executed, even if verification is unclear
            action=action,
            click_coords=(actual_x, actual_y),
            verified=verification.success
        )

    def _execute_type(self, action: BrowsingAction) -> ExecutionResult:
        """Execute a type action."""
        # If we have a target, click it first to focus
        if action.target:
            click_action = BrowsingAction.click(
                target=action.target,
                reasoning=f"Focus for typing: {action.reasoning}"
            )
            click_result = self._execute_click(click_action)
            if not click_result.success:
                return ExecutionResult(
                    success=False,
                    action=action,
                    error=f"Could not click type target: {click_result.error}"
                )
            time.sleep(0.3)  # Brief pause after click

        # Type the text
        self.keyboard.type_text(action.text, final_enter=False)

        return ExecutionResult(
            success=True,
            action=action,
            verified=True
        )

    def _execute_scroll(self, action: BrowsingAction) -> ExecutionResult:
        """Execute scroll with reading pause."""
        # Scroll
        if action.direction == "down":
            self.keyboard.scroll_down()
        else:
            self.keyboard.scroll_up()

        # Human-like pause after scrolling (reading content)
        pause = random.uniform(self.SCROLL_PAUSE_MIN, self.SCROLL_PAUSE_MAX)
        self.log.debug(f"Scroll pause: {pause:.1f}s")
        time.sleep(pause)

        return ExecutionResult(success=True, action=action, verified=True)

    def _execute_wait(self, action: BrowsingAction) -> ExecutionResult:
        """Execute a wait action."""
        duration = action.duration or 3.0
        self.log.info(f"Waiting {duration:.1f}s - {action.reasoning}")
        time.sleep(duration)

        return ExecutionResult(success=True, action=action, verified=True)

    def _execute_navigate(self, action: BrowsingAction) -> ExecutionResult:
        """Execute a navigate action by clicking address bar and typing URL."""
        url = action.text
        self.log.info(f"Navigating to: {url}")

        # Try to find and click the address bar using VLM
        location, screenshot = self._find_element("browser address bar or URL bar")

        if location and location.found:
            # Click on address bar
            try:
                coord = self.translator.element_to_screen(location, screenshot)
                self.mouse.click(coord.x, coord.y)
                self.log.info(f"Clicked address bar at ({coord.x}, {coord.y})")
                time.sleep(0.3)
            except ValueError:
                # Fallback to keyboard shortcut
                self.log.debug("Could not translate address bar coords, using Ctrl+L")
                self.keyboard.focus_address_bar()
                time.sleep(0.2)
        else:
            # Fallback to keyboard shortcut if VLM can't find address bar
            self.log.debug("Address bar not found by VLM, using Ctrl+L")
            self.keyboard.focus_address_bar()
            time.sleep(0.2)

        # Select all existing text and delete it
        self.keyboard.select_all()
        time.sleep(0.1)

        # Type the URL
        self.keyboard.type_text(url, final_enter=True)

        # Wait for page to start loading
        time.sleep(2.0)

        return ExecutionResult(
            success=True,
            action=action,
            verified=True  # Navigation initiated
        )

    def _find_element(
        self,
        target: str
    ) -> Tuple[Optional[ElementLocation], Optional[Screenshot]]:
        """Find element with capture and retries."""
        for attempt in range(self.MAX_FIND_RETRIES):
            # Capture screenshot
            screenshot = self.capture.capture_window(self.hwnd)

            # Find element
            location = self.finder.find(screenshot, target)

            if location.found:
                return location, screenshot

            if attempt < self.MAX_FIND_RETRIES - 1:
                self.log.debug(
                    f"Element '{target}' not found, retrying... "
                    f"(attempt {attempt + 1}/{self.MAX_FIND_RETRIES})"
                )
                time.sleep(0.5)

        return None, None

    def _apply_cooldown(self) -> None:
        """Apply random cooldown between actions."""
        cooldown = random.uniform(self.ACTION_COOLDOWN_MIN, self.ACTION_COOLDOWN_MAX)
        self.log.debug(f"Action cooldown: {cooldown:.1f}s")
        time.sleep(cooldown)

    def _ensure_window_focus(self) -> bool:
        """Ensure browser window is in foreground."""
        # Check if already focused
        if self.window_manager.is_foreground(self.hwnd):
            return True

        # Try to bring to foreground
        self.log.warning("Browser not in foreground, attempting to focus...")
        success = ensure_adspower_foreground()

        if not success:
            self.log.error("Failed to bring browser to foreground")

        return success


def execute_action(
    action: BrowsingAction,
    hwnd: int,
    vlm_client: Optional[OllamaClient] = None
) -> ExecutionResult:
    """
    Quick function to execute a single action.

    Args:
        action: BrowsingAction to execute
        hwnd: Window handle
        vlm_client: Optional shared OllamaClient

    Returns:
        ExecutionResult with outcome
    """
    executor = ActionExecutor(hwnd=hwnd, vlm_client=vlm_client)
    return executor.execute(action)
