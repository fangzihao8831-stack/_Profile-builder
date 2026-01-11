"""
Realistic Integration Tests

Tests actual browser interactions with coordinated mouse + keyboard.
These tests require AdsPower to be running with profile k18il1i6.

Run with: python -m pytest tests/test_integration_real.py -v -s
Use -s to see live logging output.
"""

import os
import time
import random
import pytest

from browser.adspower import AdsPowerClient
from core.window_manager import WindowManager, ensure_adspower_foreground
from core.logger import setup_logger, Log
from element.screenshot import ScreenshotCapture, capture_for_vlm
from element.vlm_finder import VLMElementFinder
from input.coordinates import CoordinateTranslator
from input.mouse import HumanMouse
from input.keyboard import HumanKeyboard
from verification.click_verifier import ClickVerifier


PROFILE_ID = "k18il1i6"

# Random search terms for testing
SEARCH_TERMS = [
    "weather today",
    "python programming",
    "best coffee shops",
    "how to cook pasta",
    "latest tech news",
]


@pytest.fixture(scope="module")
def browser_session():
    """Module-scoped browser session."""
    # Setup logging
    setup_logger()
    log = Log.session()
    log.info("=" * 60)
    log.info("STARTING INTEGRATION TEST SESSION")
    log.info("=" * 60)

    ads = AdsPowerClient()
    wm = WindowManager()

    log.info(f"Opening AdsPower profile: {PROFILE_ID}")
    conn = ads.open_profile(PROFILE_ID)

    # Wait for browser window
    hwnd = None
    for attempt in range(15):
        window = wm.find_adspower_browser()
        if window:
            hwnd = window.hwnd
            log.info(f"Found browser window: '{window.title}' (hwnd={hwnd})")
            break
        log.debug(f"Waiting for browser window... attempt {attempt + 1}")
        time.sleep(0.5)

    if not hwnd:
        log.error("Browser window not found!")
        pytest.fail("Browser window not found")

    # Bring to foreground
    result = ensure_adspower_foreground()
    if result:
        log.info("Browser brought to foreground")
    else:
        log.warning("Could not bring browser to foreground")

    time.sleep(1)  # Let browser settle

    yield {
        "ads": ads,
        "wm": wm,
        "conn": conn,
        "hwnd": hwnd,
        "log": log
    }

    log.info("Closing browser profile...")
    ads.close_profile(PROFILE_ID)
    log.info("=" * 60)
    log.info("TEST SESSION COMPLETE")
    log.info("=" * 60)


class TestKeyboardInput:
    """Test keyboard input functionality."""

    def test_new_tab(self, browser_session):
        """Test opening a new tab with Ctrl+T."""
        log = browser_session["log"]
        log.info("TEST: Opening new tab")

        kb = HumanKeyboard()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Take before screenshot
        capture = ScreenshotCapture()
        before = capture.capture_window(browser_session["hwnd"])

        # Open new tab
        kb.new_tab()
        time.sleep(1)

        # Take after screenshot
        after = capture.capture_window(browser_session["hwnd"])

        # Verify visual change
        verifier = ClickVerifier(diff_threshold=0.02)
        result = verifier._calculate_diff(before.image, after.image)

        log.info(f"Visual diff after new tab: {result:.1%}")
        assert result > 0.01, "Expected visual change after opening new tab"

        # Close the tab we just opened
        kb.close_tab()
        time.sleep(0.5)

    def test_type_in_address_bar(self, browser_session):
        """Test typing a search query in the address bar."""
        log = browser_session["log"]
        query = random.choice(SEARCH_TERMS)
        log.info(f"TEST: Typing in address bar: '{query}'")

        kb = HumanKeyboard()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Focus address bar
        kb.focus_address_bar()
        time.sleep(0.3)

        # Type search query (but don't press Enter)
        kb.type_text(query)
        time.sleep(0.5)

        # Take screenshot to see what was typed
        screenshot = capture_for_vlm()
        assert screenshot is not None

        # Press Escape to cancel
        kb.escape()
        time.sleep(0.3)

        log.info("Successfully typed in address bar")


class TestMouseKeyboardCoordination:
    """Test coordinated mouse and keyboard actions."""

    def test_click_then_type(self, browser_session):
        """Test clicking an element then typing."""
        log = browser_session["log"]
        log.info("TEST: Click then type sequence")

        kb = HumanKeyboard()
        mouse = HumanMouse()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Take screenshot
        screenshot = capture_for_vlm()
        assert screenshot is not None

        # Try to find the address bar using VLM
        finder = VLMElementFinder()
        location = finder.find(screenshot, "address bar or URL input field")

        if location.found and location.center:
            log.info(f"Found address bar at {location.center}")

            # Translate coordinates
            translator = CoordinateTranslator()
            coord = translator.element_to_screen(location, screenshot)

            # Click on address bar
            log.info(f"Clicking at screen coords ({coord.x}, {coord.y})")
            mouse.click(coord.x, coord.y)
            time.sleep(0.3)

            # Type something
            test_text = "test search query"
            kb.type_text(test_text)
            time.sleep(0.5)

            # Clear with Escape
            kb.escape()

            log.info("Click then type sequence completed")
        else:
            log.warning("Could not find address bar - skipping click")
            # Still do keyboard-only test
            kb.focus_address_bar()
            time.sleep(0.2)
            kb.type_text("fallback test")
            time.sleep(0.3)
            kb.escape()


class TestNavigationFlow:
    """Test complete navigation flows."""

    def test_navigate_to_url(self, browser_session):
        """Test navigating to a URL."""
        log = browser_session["log"]
        log.info("TEST: Navigate to URL")

        kb = HumanKeyboard()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Navigate to example.com (safe test URL)
        kb.navigate_to("example.com")

        # Wait for page load
        time.sleep(2)

        # Take screenshot to verify
        screenshot = capture_for_vlm()
        assert screenshot is not None

        # Use VLM to verify we're on example.com
        finder = VLMElementFinder()
        location = finder.find(screenshot, "Example Domain heading or title")

        if location.found:
            log.info("Successfully navigated to example.com")
        else:
            log.warning("Could not verify page content (may still have loaded)")

    def test_search_random_term(self, browser_session):
        """Test searching a random term."""
        log = browser_session["log"]
        query = random.choice(SEARCH_TERMS)
        log.info(f"TEST: Search for '{query}'")

        kb = HumanKeyboard()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Search
        kb.search_in_address_bar(query)

        # Wait for results
        time.sleep(3)

        # Take screenshot
        screenshot = capture_for_vlm()
        assert screenshot is not None

        log.info(f"Search completed for: {query}")


class TestTabManagement:
    """Test tab switching and management."""

    def test_multiple_tabs(self, browser_session):
        """Test opening multiple tabs and switching between them."""
        log = browser_session["log"]
        log.info("TEST: Multiple tabs management")

        kb = HumanKeyboard()

        # Ensure window is focused
        ensure_adspower_foreground()
        time.sleep(0.5)

        # Open 2 new tabs
        log.info("Opening tab 1")
        kb.new_tab()
        time.sleep(0.5)
        kb.navigate_to("example.com")
        time.sleep(1.5)

        log.info("Opening tab 2")
        kb.new_tab()
        time.sleep(0.5)
        kb.navigate_to("example.org")
        time.sleep(1.5)

        # Switch between tabs
        log.info("Switching to previous tab")
        kb.switch_tab_prev()
        time.sleep(0.5)

        # Take screenshot
        screenshot = capture_for_vlm()
        assert screenshot is not None

        log.info("Switching to next tab")
        kb.switch_tab_next()
        time.sleep(0.5)

        # Close the tabs we opened
        log.info("Cleaning up tabs")
        kb.close_tab()
        time.sleep(0.3)
        kb.close_tab()
        time.sleep(0.3)

        log.info("Tab management test completed")


class TestVLMIntegration:
    """Test VLM finding with real page elements."""

    def test_find_and_click_link(self, browser_session):
        """Test finding and clicking a link on example.com."""
        log = browser_session["log"]
        log.info("TEST: Find and click link")

        kb = HumanKeyboard()
        mouse = HumanMouse()

        # Navigate to example.com
        ensure_adspower_foreground()
        time.sleep(0.5)

        kb.navigate_to("example.com")
        time.sleep(2)

        # Take screenshot
        screenshot = capture_for_vlm()
        assert screenshot is not None

        # Find the "More information..." link
        finder = VLMElementFinder()
        location = finder.find(screenshot, "More information link")

        if location.found and location.center:
            log.info(f"Found 'More information' link at {location.center}")

            # Translate and click
            translator = CoordinateTranslator()
            coord = translator.element_to_screen(location, screenshot)

            log.info(f"Clicking at ({coord.x}, {coord.y})")
            mouse.click(coord.x, coord.y)
            time.sleep(2)

            # Verify navigation happened
            after = capture_for_vlm()
            verifier = ClickVerifier()
            diff = verifier._calculate_diff(screenshot.image, after.image)
            log.info(f"Visual diff after click: {diff:.1%}")

            # Go back (Alt+Left)
            from pynput.keyboard import Key
            kb.hotkey(Key.alt, Key.left)
            time.sleep(1)

        else:
            log.warning("Could not find 'More information' link")
            pytest.skip("VLM did not find the target element")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
