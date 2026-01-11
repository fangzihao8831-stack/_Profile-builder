"""
Milestone 3 Tests: AI Decision Loop

Tests for:
1. ActionExecutor - action execution with OS-level input
2. BrowsingSession - session management and timing
3. Human-like timing verification

Run with: python -m pytest tests/test_milestone3.py -v -s
"""

import time
import random
import pytest
from unittest.mock import Mock, patch, MagicMock

from ai.actions import BrowsingAction, ActionType, ExecutionResult
from ai.session_planner import BrowsingStructure, SessionPlan, SessionContext, create_plan
from core.logger import setup_logger, Log


# ============================================
# Unit Tests (no real browser required)
# ============================================

class TestBrowsingAction:
    """Test action creation and validation."""

    def test_click_requires_target(self):
        """CLICK action must have target."""
        with pytest.raises(ValueError, match="requires a target"):
            BrowsingAction(action_type=ActionType.CLICK, reasoning="test")

    def test_type_requires_text(self):
        """TYPE action must have text."""
        with pytest.raises(ValueError, match="requires text"):
            BrowsingAction(action_type=ActionType.TYPE, reasoning="test")

    def test_scroll_requires_direction(self):
        """SCROLL action must have direction."""
        with pytest.raises(ValueError, match="requires direction"):
            BrowsingAction(action_type=ActionType.SCROLL, reasoning="test")

    def test_navigate_requires_text(self):
        """NAVIGATE action must have text (URL)."""
        with pytest.raises(ValueError, match="requires text"):
            BrowsingAction(action_type=ActionType.NAVIGATE, reasoning="test")

    def test_wait_allows_no_duration(self):
        """WAIT action can have no duration (uses default)."""
        action = BrowsingAction(action_type=ActionType.WAIT, reasoning="test")
        assert action.duration is None

    def test_from_dict_click(self):
        """Parse click action from dict."""
        data = {
            "action": "click",
            "target": "search button",
            "reasoning": "to search"
        }
        action = BrowsingAction.from_dict(data)
        assert action.action_type == ActionType.CLICK
        assert action.target == "search button"
        assert action.reasoning == "to search"

    def test_from_dict_scroll(self):
        """Parse scroll action from dict."""
        data = {
            "action": "scroll",
            "direction": "down",
            "reasoning": "see more content"
        }
        action = BrowsingAction.from_dict(data)
        assert action.action_type == ActionType.SCROLL
        assert action.direction == "down"

    def test_from_dict_type(self):
        """Parse type action from dict."""
        data = {
            "action": "type",
            "text": "hello world",
            "target": "search box",
            "reasoning": "searching"
        }
        action = BrowsingAction.from_dict(data)
        assert action.action_type == ActionType.TYPE
        assert action.text == "hello world"
        assert action.target == "search box"

    def test_from_dict_wait(self):
        """Parse wait action from dict."""
        data = {
            "action": "wait",
            "duration": 5.0,
            "reasoning": "watching video"
        }
        action = BrowsingAction.from_dict(data)
        assert action.action_type == ActionType.WAIT
        assert action.duration == 5.0

    def test_from_dict_navigate(self):
        """Parse navigate action from dict."""
        data = {
            "action": "navigate",
            "text": "https://example.com",
            "reasoning": "going to site"
        }
        action = BrowsingAction.from_dict(data)
        assert action.action_type == ActionType.NAVIGATE
        assert action.text == "https://example.com"

    def test_factory_methods(self):
        """Test factory methods for action creation."""
        click = BrowsingAction.click("button", "click it")
        assert click.action_type == ActionType.CLICK
        assert click.target == "button"

        scroll = BrowsingAction.scroll("down", "see more")
        assert scroll.action_type == ActionType.SCROLL
        assert scroll.direction == "down"

        wait = BrowsingAction.wait(10.0, "wait a bit")
        assert wait.action_type == ActionType.WAIT
        assert wait.duration == 10.0

        nav = BrowsingAction.navigate("https://test.com", "go there")
        assert nav.action_type == ActionType.NAVIGATE
        assert nav.text == "https://test.com"

        type_action = BrowsingAction.type_text("hello", "typing")
        assert type_action.action_type == ActionType.TYPE
        assert type_action.text == "hello"

    def test_to_dict(self):
        """Test serialization to dict."""
        action = BrowsingAction.click("my button", "because")
        d = action.to_dict()
        assert d["action"] == "click"
        assert d["target"] == "my button"
        assert d["reasoning"] == "because"

    def test_str_representation(self):
        """Test string representation."""
        click = BrowsingAction.click("button", "test")
        assert "CLICK on 'button'" in str(click)

        scroll = BrowsingAction.scroll("down", "test")
        assert "SCROLL down" in str(scroll)


class TestSessionPlan:
    """Test session planning."""

    def test_create_plan_fashion(self):
        """Create fashion browsing plan."""
        plan = create_plan(BrowsingStructure.FASHION, duration_minutes=5)
        assert plan.structure == BrowsingStructure.FASHION
        assert plan.duration_minutes == 5
        assert plan.duration_seconds == 300
        assert "fashion" in plan.description.lower()

    def test_create_plan_news(self):
        """Create news browsing plan."""
        plan = create_plan(BrowsingStructure.NEWS, duration_minutes=3)
        assert plan.structure == BrowsingStructure.NEWS
        assert "news" in plan.description.lower()

    def test_create_plan_youtube(self):
        """Create YouTube browsing plan."""
        plan = create_plan(BrowsingStructure.YOUTUBE, duration_minutes=10)
        assert plan.structure == BrowsingStructure.YOUTUBE
        assert "youtube" in plan.description.lower() or "video" in plan.description.lower()

    def test_session_context_expiry(self):
        """Test session expiry tracking."""
        plan = create_plan(BrowsingStructure.NEWS, duration_minutes=1)
        context = SessionContext(plan=plan)

        # Should not be expired immediately
        assert not context.is_expired
        assert context.remaining_seconds > 0
        assert context.elapsed_seconds < 5  # Just started

    def test_session_context_action_history(self):
        """Test action history tracking."""
        plan = create_plan(BrowsingStructure.FASHION, duration_minutes=3)
        context = SessionContext(plan=plan)

        # Add actions
        context.add_action("CLICK on 'button'")
        context.add_action("SCROLL down")
        context.add_action("WAIT 5s")

        recent = context.get_recent_actions(2)
        assert len(recent) == 2
        assert "SCROLL down" in recent
        assert "WAIT 5s" in recent

    def test_session_context_history_limit(self):
        """Test history is limited to 10 actions."""
        plan = create_plan(BrowsingStructure.FASHION, duration_minutes=3)
        context = SessionContext(plan=plan)

        # Add 15 actions
        for i in range(15):
            context.add_action(f"Action {i}")

        # Should only have 10
        assert len(context.action_history) == 10
        # First 5 should be gone
        assert "Action 0" not in context.action_history
        assert "Action 14" in context.action_history

    def test_starting_points(self):
        """Test starting points are configured."""
        for structure in BrowsingStructure:
            plan = create_plan(structure, duration_minutes=3)
            starting = plan.starting_point
            assert "type" in starting
            assert starting["type"] in ["direct", "search"]


class TestTimingConstants:
    """Verify timing constants are human-like."""

    def test_dwell_time_range(self):
        """Dwell time should be 5-30 seconds."""
        from core.session import BrowsingSession
        assert BrowsingSession.DWELL_TIME_MIN == 5.0
        assert BrowsingSession.DWELL_TIME_MAX == 30.0

    def test_scroll_pause_range(self):
        """Scroll pause should be 2-5 seconds."""
        from ai.action_executor import ActionExecutor
        assert ActionExecutor.SCROLL_PAUSE_MIN == 2.0
        assert ActionExecutor.SCROLL_PAUSE_MAX == 5.0

    def test_action_cooldown_range(self):
        """Action cooldown should be 1-2 seconds."""
        from ai.action_executor import ActionExecutor
        assert ActionExecutor.ACTION_COOLDOWN_MIN == 1.0
        assert ActionExecutor.ACTION_COOLDOWN_MAX == 2.0

    def test_max_consecutive_failures(self):
        """Should stop after 3 consecutive failures."""
        from core.session import BrowsingSession
        assert BrowsingSession.MAX_CONSECUTIVE_FAILURES == 3


class TestExecutionResult:
    """Test execution result tracking."""

    def test_successful_result(self):
        """Test successful result creation."""
        action = BrowsingAction.click("button", "test")
        result = ExecutionResult(
            success=True,
            action=action,
            click_coords=(100, 200),
            verified=True
        )
        assert result.success
        assert result.verified
        assert result.click_coords == (100, 200)
        assert result.error is None

    def test_failed_result(self):
        """Test failed result creation."""
        action = BrowsingAction.click("button", "test")
        result = ExecutionResult(
            success=False,
            action=action,
            error="Element not found"
        )
        assert not result.success
        assert result.error == "Element not found"

    def test_str_representation(self):
        """Test string representation."""
        action = BrowsingAction.scroll("down", "test")
        result = ExecutionResult(success=True, action=action, verified=True)
        s = str(result)
        assert "OK" in s
        assert "verified" in s


# ============================================
# Integration Tests (requires real browser)
# ============================================

PROFILE_ID = "k18il1i6"


@pytest.fixture(scope="module")
def browser_session():
    """Module-scoped browser session for integration tests."""
    from browser.adspower import AdsPowerClient
    from core.window_manager import WindowManager, ensure_adspower_foreground

    setup_logger()
    log = Log.session()
    log.info("=" * 60)
    log.info("STARTING MILESTONE 3 INTEGRATION TESTS")
    log.info("=" * 60)

    ads = AdsPowerClient()
    wm = WindowManager()

    # Open profile
    try:
        ads.open_profile(PROFILE_ID)
    except RuntimeError as e:
        pytest.skip(f"Could not open AdsPower profile: {e}")

    # Wait for window
    hwnd = None
    for _ in range(15):
        window = wm.find_adspower_browser()
        if window:
            hwnd = window.hwnd
            break
        time.sleep(0.5)

    if not hwnd:
        pytest.skip("Browser window not found")

    ensure_adspower_foreground()
    time.sleep(1)

    yield {"ads": ads, "hwnd": hwnd, "log": log}

    # Cleanup - don't close browser so user can inspect
    log.info("Integration tests complete")


class TestActionExecutor:
    """Test action execution with real browser."""

    def test_execute_scroll_down(self, browser_session):
        """Test scroll down execution."""
        from ai.action_executor import ActionExecutor
        from core.window_manager import ensure_adspower_foreground

        ensure_adspower_foreground()

        executor = ActionExecutor(hwnd=browser_session["hwnd"])
        action = BrowsingAction.scroll("down", "looking for content")

        start = time.time()
        result = executor.execute(action)
        elapsed = time.time() - start

        assert result.success
        assert result.action == action
        # Should include pause (2-5s) + cooldown (1-2s) = at least 3s
        assert elapsed >= 3.0, f"Scroll was too fast: {elapsed:.1f}s"

    def test_execute_scroll_up(self, browser_session):
        """Test scroll up execution."""
        from ai.action_executor import ActionExecutor
        from core.window_manager import ensure_adspower_foreground

        ensure_adspower_foreground()

        executor = ActionExecutor(hwnd=browser_session["hwnd"])
        action = BrowsingAction.scroll("up", "going back up")

        result = executor.execute(action)

        assert result.success

    def test_execute_wait(self, browser_session):
        """Test wait execution."""
        from ai.action_executor import ActionExecutor
        from core.window_manager import ensure_adspower_foreground

        ensure_adspower_foreground()

        executor = ActionExecutor(hwnd=browser_session["hwnd"])
        action = BrowsingAction.wait(2.0, "waiting")

        start = time.time()
        result = executor.execute(action)
        elapsed = time.time() - start

        assert result.success
        # Should wait ~2s + cooldown (1-2s) = ~3-4s
        assert elapsed >= 2.5, f"Wait was too short: {elapsed:.1f}s"

    def test_execute_navigate(self, browser_session):
        """Test navigate to URL."""
        from ai.action_executor import ActionExecutor
        from core.window_manager import ensure_adspower_foreground

        ensure_adspower_foreground()

        executor = ActionExecutor(hwnd=browser_session["hwnd"])
        # Use a real fashion search instead of example.com
        action = BrowsingAction.navigate("zara.com", "testing navigation to fashion site")

        result = executor.execute(action)

        assert result.success
        time.sleep(2)  # Wait for page load

    def test_execute_click_not_found(self, browser_session):
        """Test clicking element that doesn't exist."""
        from ai.action_executor import ActionExecutor
        from core.window_manager import ensure_adspower_foreground

        ensure_adspower_foreground()

        executor = ActionExecutor(hwnd=browser_session["hwnd"])
        action = BrowsingAction.click(
            "nonexistent button xyz123",
            "testing not found"
        )

        result = executor.execute(action)

        # Should fail gracefully
        assert not result.success
        assert "Could not find" in result.error


class TestBrowsingSessionShort:
    """Test short browsing sessions."""

    def test_session_initialization(self, browser_session):
        """Test session can initialize."""
        from core.session import BrowsingSession, SessionState

        # Note: This test just checks initialization patterns
        session = BrowsingSession(
            profile_id=PROFILE_ID,
            structure=BrowsingStructure.FASHION,
            duration_minutes=1,
            debug=True
        )

        assert session.state == SessionState.INITIALIZING
        assert session.duration_minutes == 1
        assert session.structure == BrowsingStructure.FASHION

    def test_session_stats_initial(self, browser_session):
        """Test session stats start at zero."""
        from core.session import SessionStats

        stats = SessionStats()

        assert stats.total_actions == 0
        assert stats.successful_actions == 0
        assert stats.failed_actions == 0
        assert stats.clicks == 0
        assert stats.scrolls == 0
        assert stats.total_dwell_time == 0.0


class TestHumanLikeTiming:
    """Verify timing produces human-like behavior."""

    def test_dwell_time_distribution(self):
        """Dwell times should be randomly distributed."""
        from core.session import BrowsingSession

        samples = []
        for _ in range(100):
            dwell = random.uniform(
                BrowsingSession.DWELL_TIME_MIN,
                BrowsingSession.DWELL_TIME_MAX
            )
            samples.append(dwell)

        # Check range
        assert min(samples) >= 5.0
        assert max(samples) <= 30.0

        # Check distribution (should have variety)
        avg = sum(samples) / len(samples)
        assert 10.0 < avg < 25.0  # Roughly centered

    def test_scroll_pause_distribution(self):
        """Scroll pauses should be randomly distributed."""
        from ai.action_executor import ActionExecutor

        samples = []
        for _ in range(100):
            pause = random.uniform(
                ActionExecutor.SCROLL_PAUSE_MIN,
                ActionExecutor.SCROLL_PAUSE_MAX
            )
            samples.append(pause)

        # Check range
        assert min(samples) >= 2.0
        assert max(samples) <= 5.0

    def test_cooldown_distribution(self):
        """Cooldowns should be randomly distributed."""
        from ai.action_executor import ActionExecutor

        samples = []
        for _ in range(100):
            cooldown = random.uniform(
                ActionExecutor.ACTION_COOLDOWN_MIN,
                ActionExecutor.ACTION_COOLDOWN_MAX
            )
            samples.append(cooldown)

        # Check range
        assert min(samples) >= 1.0
        assert max(samples) <= 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
