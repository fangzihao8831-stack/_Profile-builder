"""
Browsing session manager.

Runs the main AI decision loop with human-like timing and behavior.
"""

import random
import time
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field

from ai.actions import BrowsingAction, ActionType, ExecutionResult
from ai.decision_maker import DecisionMaker
from ai.action_executor import ActionExecutor
from ai.session_planner import (
    SessionPlan, SessionContext, BrowsingStructure,
    create_plan, STRUCTURE_STARTING_POINTS
)
from ai.ollama_client import OllamaClient
from browser.adspower import AdsPowerClient
from core.window_manager import WindowManager, ensure_adspower_foreground
from core.logger import Log, setup_logger
from element.screenshot import capture_for_vlm
from input.keyboard import HumanKeyboard


class SessionState(Enum):
    """Current state of the browsing session."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SessionStats:
    """Statistics for the browsing session."""
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    verified_actions: int = 0
    total_dwell_time: float = 0.0
    clicks: int = 0
    scrolls: int = 0
    types: int = 0
    waits: int = 0
    navigations: int = 0
    consecutive_failures: int = 0


class BrowsingSession:
    """
    Manages a complete browsing session.

    Runs the core loop: Screenshot -> AI decides -> Execute -> Verify -> Repeat
    """

    # Timing constants
    DWELL_TIME_MIN = 1.0   # After clicking items
    DWELL_TIME_MAX = 3.0
    ERROR_RETRY_DELAY = 1.0
    MAX_CONSECUTIVE_FAILURES = 5

    def __init__(
        self,
        profile_id: str,
        structure: BrowsingStructure,
        duration_minutes: int = 3,
        debug: bool = True
    ):
        """
        Args:
            profile_id: AdsPower profile ID
            structure: Type of browsing session
            duration_minutes: How long to run
            debug: Whether to save debug output
        """
        self.profile_id = profile_id
        self.structure = structure
        self.duration_minutes = duration_minutes
        self.debug = debug

        self.state = SessionState.INITIALIZING
        self.stats = SessionStats()
        self.plan: Optional[SessionPlan] = None
        self.context: Optional[SessionContext] = None

        # Components (initialized in start())
        self.ads_client: Optional[AdsPowerClient] = None
        self.hwnd: Optional[int] = None
        self.vlm_client: Optional[OllamaClient] = None
        self.decision_maker: Optional[DecisionMaker] = None
        self.executor: Optional[ActionExecutor] = None
        self.keyboard: Optional[HumanKeyboard] = None

        self.log = Log.session()

    def start(self) -> bool:
        """
        Initialize and start the session.

        Returns:
            True if session completed successfully
        """
        setup_logger()
        self.log.info("=" * 60)
        self.log.info("STARTING BROWSING SESSION")
        self.log.info(f"Profile: {self.profile_id}")
        self.log.info(f"Structure: {self.structure.value}")
        self.log.info(f"Duration: {self.duration_minutes} minutes")
        self.log.info("=" * 60)

        try:
            # Initialize components
            if not self._initialize():
                self.state = SessionState.FAILED
                return False

            # Navigate to starting point
            if not self._navigate_to_start():
                self.log.warning("Could not navigate to start, continuing anyway")

            # Run main loop
            self.state = SessionState.RUNNING
            self._run_loop()

            self.state = SessionState.COMPLETED
            return True

        except KeyboardInterrupt:
            self.log.info("Session interrupted by user")
            self.state = SessionState.COMPLETED
            return True

        except Exception as e:
            self.log.error(f"Session failed: {e}")
            self.state = SessionState.FAILED
            return False

        finally:
            self._cleanup()
            self._log_summary()

    def _initialize(self) -> bool:
        """Initialize all components."""
        # Create session plan
        self.plan = create_plan(self.structure, self.duration_minutes)
        self.context = SessionContext(plan=self.plan)

        # Initialize AdsPower client
        self.ads_client = AdsPowerClient()

        # Open browser profile
        self.log.info(f"Opening AdsPower profile: {self.profile_id}")
        try:
            self.ads_client.open_profile(self.profile_id)
        except RuntimeError as e:
            self.log.error(f"Failed to open profile: {e}")
            return False

        # Wait for browser window
        wm = WindowManager()
        for attempt in range(15):
            window = wm.find_adspower_browser()
            if window:
                self.hwnd = window.hwnd
                self.log.info(f"Found browser: '{window.title}'")
                break
            time.sleep(0.5)

        if not self.hwnd:
            self.log.error("Browser window not found")
            return False

        # Bring to foreground
        ensure_adspower_foreground()
        time.sleep(1.0)  # Let browser settle

        # Initialize AI components (shared VLM client)
        self.vlm_client = OllamaClient()
        self.decision_maker = DecisionMaker(
            client=self.vlm_client,
            debug=self.debug
        )
        self.executor = ActionExecutor(
            hwnd=self.hwnd,
            vlm_client=self.vlm_client,
            debug=self.debug
        )
        self.keyboard = HumanKeyboard()

        return True

    def _navigate_to_start(self) -> bool:
        """Navigate to structure starting point."""
        starting = self.plan.starting_point

        if starting.get("type") == "direct":
            # Navigate directly to URL
            url = starting["url"]
            self.log.info(f"Navigating to: {url}")
            self.keyboard.navigate_to(url)
            time.sleep(3.0)  # Wait for page load
            return True

        elif starting.get("type") == "search":
            # Search via address bar
            query = starting["query"]
            self.log.info(f"Searching for: {query}")
            self.keyboard.search_in_address_bar(query)
            time.sleep(3.0)  # Wait for results
            return True

        return False

    def _run_loop(self) -> None:
        """Main decision-action loop."""
        self.log.info("Starting main loop")

        while not self.context.is_expired:
            # Check if too many consecutive failures
            if self.stats.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                self.log.error(
                    f"Too many consecutive failures "
                    f"({self.MAX_CONSECUTIVE_FAILURES}), stopping"
                )
                break

            try:
                # Capture screenshot
                screenshot = capture_for_vlm()
                if not screenshot:
                    self.log.error("Failed to capture screenshot")
                    self.stats.consecutive_failures += 1
                    time.sleep(self.ERROR_RETRY_DELAY)
                    continue

                # Get AI decision
                action = self.decision_maker.decide(screenshot, self.context)
                self.log.info(f"Decision: {action}")

                # Execute with dwell time
                result = self._execute_with_dwell(action)

                # Update stats
                self.stats.total_actions += 1
                if result.success:
                    self.stats.successful_actions += 1
                    self.stats.consecutive_failures = 0
                    if result.verified:
                        self.stats.verified_actions += 1

                    # Track action types
                    if action.action_type == ActionType.CLICK:
                        self.stats.clicks += 1
                    elif action.action_type == ActionType.SCROLL:
                        self.stats.scrolls += 1
                    elif action.action_type == ActionType.TYPE:
                        self.stats.types += 1
                    elif action.action_type == ActionType.WAIT:
                        self.stats.waits += 1
                    elif action.action_type == ActionType.NAVIGATE:
                        self.stats.navigations += 1
                else:
                    self.stats.failed_actions += 1
                    if not self._handle_failure(result):
                        break

                # Add to context history
                self.context.add_action(str(action))

                # Log progress
                remaining = int(self.context.remaining_seconds)
                self.log.debug(f"Time remaining: {remaining}s")

            except Exception as e:
                self.log.error(f"Loop iteration failed: {e}")
                self.stats.consecutive_failures += 1
                time.sleep(self.ERROR_RETRY_DELAY)

        self.log.info("Main loop ended")

    def _execute_with_dwell(self, action: BrowsingAction) -> ExecutionResult:
        """Execute action and apply dwell time for reading."""
        result = self.executor.execute(action)

        if result.success:
            self._apply_dwell_time(result)

        return result

    def _apply_dwell_time(self, result: ExecutionResult) -> None:
        """Apply human-like dwell time after successful actions."""
        action = result.action

        # Different dwell times based on action type
        if action.action_type == ActionType.CLICK:
            # Clicked something - spend time "reading/viewing"
            dwell = random.uniform(self.DWELL_TIME_MIN, self.DWELL_TIME_MAX)
            self.log.debug(f"Dwell time (click): {dwell:.1f}s")
            time.sleep(dwell)
            self.stats.total_dwell_time += dwell

        elif action.action_type == ActionType.WAIT:
            # Explicit wait (watching video, etc.)
            wait_time = action.duration or 3.0
            self.log.debug(f"Wait time: {wait_time:.1f}s")
            time.sleep(wait_time)
            self.stats.total_dwell_time += wait_time

        # SCROLL already has pause built into executor
        # TYPE and NAVIGATE have natural delays

    def _handle_failure(self, result: ExecutionResult) -> bool:
        """
        Handle action failure.

        Returns:
            True if should continue session, False if should stop
        """
        self.stats.consecutive_failures += 1

        self.log.warning(
            f"Action failed ({self.stats.consecutive_failures}/"
            f"{self.MAX_CONSECUTIVE_FAILURES}): {result.error}"
        )

        # Let the AI decide the next action - it will adapt
        return True

    def _cleanup(self) -> None:
        """Clean up resources."""
        self.log.info("Cleaning up session...")
        # Don't close browser - user may want to inspect
        # Just release references
        self.executor = None
        self.decision_maker = None
        self.vlm_client = None

    def _log_summary(self) -> None:
        """Log session summary statistics."""
        total_time = self.context.elapsed_seconds if self.context else 0
        reading_pct = (
            (self.stats.total_dwell_time / total_time * 100)
            if total_time > 0 else 0
        )

        self.log.info("=" * 60)
        self.log.info("SESSION SUMMARY")
        self.log.info("=" * 60)
        self.log.info(f"State: {self.state.value}")
        self.log.info(f"Duration: {total_time:.0f}s ({total_time/60:.1f}m)")
        self.log.info(f"Total actions: {self.stats.total_actions}")
        self.log.info(
            f"Successful: {self.stats.successful_actions} "
            f"({self.stats.successful_actions/max(1, self.stats.total_actions)*100:.0f}%)"
        )
        self.log.info(f"Verified: {self.stats.verified_actions}")
        self.log.info(f"Failed: {self.stats.failed_actions}")
        self.log.info("-" * 40)
        self.log.info(f"Clicks: {self.stats.clicks}")
        self.log.info(f"Scrolls: {self.stats.scrolls}")
        self.log.info(f"Types: {self.stats.types}")
        self.log.info(f"Waits: {self.stats.waits}")
        self.log.info(f"Navigations: {self.stats.navigations}")
        self.log.info("-" * 40)
        self.log.info(f"Total dwell time: {self.stats.total_dwell_time:.0f}s")
        self.log.info(f"Reading %: {reading_pct:.0f}% (target: 60-70%)")
        self.log.info("=" * 60)


def run_session(
    profile_id: str,
    structure: str = "fashion",
    duration_minutes: int = 3,
    debug: bool = True
) -> bool:
    """
    Quick function to run a browsing session.

    Args:
        profile_id: AdsPower profile ID
        structure: Browsing structure name
        duration_minutes: Session duration
        debug: Enable debug output

    Returns:
        True if session completed successfully
    """
    try:
        browsing_structure = BrowsingStructure(structure.lower())
    except ValueError:
        raise ValueError(f"Invalid structure: {structure}")

    session = BrowsingSession(
        profile_id=profile_id,
        structure=browsing_structure,
        duration_minutes=duration_minutes,
        debug=debug
    )
    return session.start()
