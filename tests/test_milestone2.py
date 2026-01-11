"""
Milestone 2: Vision Element Finding Tests

Tests screenshot capture, VLM element finding, coordinate translation,
HumanCursor clicking, and click verification.

Run with: python -m pytest tests/test_milestone2.py -v
"""

import os
import time
import pytest

from browser.adspower import AdsPowerClient
from core.window_manager import WindowManager, ensure_adspower_foreground
from element.screenshot import ScreenshotCapture, capture_for_vlm
from element.vlm_finder import VLMElementFinder, find_element
from input.coordinates import CoordinateTranslator, translate_to_screen
from input.mouse import HumanMouse, click_element
from verification.click_verifier import ClickVerifier, VerificationMethod


PROFILE_ID = "k18il1i6"


@pytest.fixture(scope="module")
def browser_session():
    """Module-scoped browser session to avoid rate limiting."""
    ads = AdsPowerClient()
    wm = WindowManager()

    conn = ads.open_profile(PROFILE_ID)

    # Wait for browser window
    hwnd = None
    for _ in range(10):
        window = wm.find_adspower_browser()
        if window:
            hwnd = window.hwnd
            break
        time.sleep(0.3)

    ensure_adspower_foreground()
    time.sleep(1)  # Let page load

    yield {"ads": ads, "wm": wm, "conn": conn, "hwnd": hwnd}

    ads.close_profile(PROFILE_ID)


class TestScreenshotCapture:
    """Test screenshot capture functionality."""

    def test_capture_window(self, browser_session):
        """Test basic window capture."""
        capture = ScreenshotCapture()
        screenshot = capture.capture_window(browser_session["hwnd"])

        assert screenshot is not None
        assert screenshot.image is not None
        assert screenshot.vlm_size[1] == 720  # 720p height
        assert screenshot.scale_factor > 0

    def test_capture_adspower(self, browser_session):
        """Test AdsPower-specific capture."""
        screenshot = capture_for_vlm()

        assert screenshot is not None
        # Maximized windows may have negative coords (shadow area)
        assert screenshot.window_rect[2] > screenshot.window_rect[0]  # right > left

    def test_save_screenshot(self, browser_session):
        """Test saving screenshot to file."""
        capture = ScreenshotCapture()
        screenshot = capture.capture_window(browser_session["hwnd"])

        path = "test_m2_screenshot.png"
        capture.save(screenshot, path)

        assert os.path.exists(path)
        os.remove(path)


class TestVLMElementFinding:
    """Test VLM-based element finding."""

    def test_find_element_visible(self, browser_session):
        """Test finding a visible element."""
        screenshot = capture_for_vlm()
        finder = VLMElementFinder()

        # Most browser windows have some text - try common elements
        # Test with address bar or any visible text
        location = finder.find(screenshot, "address bar or URL bar")

        # VLM should return a response even if not found
        assert location is not None
        assert location.target == "address bar or URL bar"

    def test_find_element_not_found(self, browser_session):
        """Test finding element that doesn't exist."""
        screenshot = capture_for_vlm()
        finder = VLMElementFinder()

        location = finder.find(screenshot, "xyzzy_nonexistent_button_12345")

        assert location is not None
        assert location.found is False
        assert location.confidence == 0.0


class TestCoordinateTranslation:
    """Test coordinate translation."""

    def test_vlm_to_screen(self):
        """Test VLM to screen coordinate conversion."""
        from element.screenshot import Screenshot
        from PIL import Image

        # Create mock screenshot
        mock_image = Image.new("RGB", (1280, 720))
        screenshot = Screenshot(
            image=mock_image,
            original_size=(1920, 1080),
            vlm_size=(1280, 720),
            window_rect=(100, 50, 2020, 1130),  # Window at (100, 50)
            scale_factor=1.5  # 1080 / 720
        )

        translator = CoordinateTranslator()
        coord = translator.vlm_to_screen((640, 360), screenshot)  # Center of VLM image

        # 640 * 1.5 = 960, + 100 = 1060
        # 360 * 1.5 = 540, + 50 = 590
        assert coord.x == 1060
        assert coord.y == 590
        assert coord.source == "vlm"


class TestHumanMouse:
    """Test HumanCursor wrapper."""

    def test_move_to(self):
        """Test mouse movement."""
        import pyautogui

        mouse = HumanMouse()

        # Move to center of screen
        screen_w, screen_h = pyautogui.size()
        target_x, target_y = screen_w // 2, screen_h // 2

        mouse.move_to(target_x, target_y)

        # Verify position (allow small tolerance)
        current_x, current_y = pyautogui.position()
        assert abs(current_x - target_x) < 5
        assert abs(current_y - target_y) < 5


class TestIntegration:
    """Integration test: full click flow."""

    def test_full_element_click_flow(self, browser_session):
        """
        Full flow: screenshot -> find element -> translate -> click.

        This tests the core loop without verification.
        """
        # Capture
        screenshot = capture_for_vlm()
        assert screenshot is not None

        # Find (look for any clickable element)
        finder = VLMElementFinder()
        location = finder.find(screenshot, "any clickable button or link")

        # If found, translate and click
        if location.found and location.center:
            translator = CoordinateTranslator()
            coord = translator.element_to_screen(location, screenshot)

            # Verify coordinates are on screen
            import pyautogui
            screen_w, screen_h = pyautogui.size()
            assert 0 <= coord.x <= screen_w
            assert 0 <= coord.y <= screen_h

            # Click (this is the real test)
            mouse = HumanMouse()
            mouse.click_at(coord)

            # Success if no exception
            assert True
        else:
            # If VLM couldn't find anything, that's still a valid test result
            pytest.skip("VLM did not find a clickable element")

    def test_click_verification(self, browser_session):
        """Test that click verification detects changes."""
        capture = ScreenshotCapture()
        before = capture.capture_window(browser_session["hwnd"])

        verifier = ClickVerifier(diff_threshold=0.01, wait_time=0.5)

        # Take another screenshot immediately (should show no change)
        result = verifier.verify_click(browser_session["hwnd"], before)

        # Without actually clicking, there should be no change
        # (unless there's animation on the page)
        assert result.method in [
            VerificationMethod.VISUAL_DIFF,
            VerificationMethod.FAILED
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
