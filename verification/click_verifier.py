"""
Click verification to confirm actions had effect.

Checks:
1. URL change detection
2. Visual difference detection
3. Element disappearance (for modals, dropdowns, etc.)
"""

import io
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

from element.screenshot import Screenshot, ScreenshotCapture
from element.vlm_finder import VLMElementFinder


class VerificationMethod(Enum):
    """How the click was verified."""
    URL_CHANGED = "url_changed"
    VISUAL_DIFF = "visual_diff"
    ELEMENT_GONE = "element_gone"
    TIMEOUT = "timeout"
    FAILED = "failed"


@dataclass
class VerificationResult:
    """Result of click verification."""
    success: bool
    method: VerificationMethod
    details: str = ""
    diff_percent: float = 0.0


class ClickVerifier:
    """Verifies that clicks had the expected effect."""

    def __init__(
        self,
        diff_threshold: float = 0.05,
        wait_time: float = 1.0,
        max_wait: float = 5.0
    ):
        """
        Args:
            diff_threshold: Minimum visual difference to count as change (0.0-1.0)
            wait_time: Initial wait time after click
            max_wait: Maximum time to wait for change
        """
        self.diff_threshold = diff_threshold
        self.wait_time = wait_time
        self.max_wait = max_wait
        self.capture = ScreenshotCapture()

    def verify_click(
        self,
        hwnd: int,
        before_screenshot: Screenshot,
        before_url: Optional[str] = None,
        current_url_getter: Optional[callable] = None,
        clicked_target: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify a click had effect.

        Args:
            hwnd: Window handle
            before_screenshot: Screenshot taken before click
            before_url: URL before click (if available)
            current_url_getter: Function to get current URL
            clicked_target: Element that was clicked (for element-gone check)

        Returns:
            VerificationResult indicating if click succeeded
        """
        # Wait for page to respond
        time.sleep(self.wait_time)

        # Check URL change first (fastest)
        if before_url and current_url_getter:
            current_url = current_url_getter()
            if current_url != before_url:
                return VerificationResult(
                    success=True,
                    method=VerificationMethod.URL_CHANGED,
                    details=f"URL changed: {before_url[:50]} -> {current_url[:50]}"
                )

        # Take after screenshot
        after_screenshot = self.capture.capture_window(hwnd)

        # Check visual difference
        diff_percent = self._calculate_diff(
            before_screenshot.image,
            after_screenshot.image
        )

        if diff_percent > self.diff_threshold:
            return VerificationResult(
                success=True,
                method=VerificationMethod.VISUAL_DIFF,
                details=f"Visual diff: {diff_percent:.1%}",
                diff_percent=diff_percent
            )

        # Check if clicked element is gone (for buttons, links)
        if clicked_target:
            finder = VLMElementFinder()
            location = finder.find(after_screenshot, clicked_target)
            if not location.found:
                return VerificationResult(
                    success=True,
                    method=VerificationMethod.ELEMENT_GONE,
                    details=f"Element '{clicked_target}' no longer visible"
                )

        # Wait longer and check again
        elapsed = self.wait_time
        while elapsed < self.max_wait:
            time.sleep(0.5)
            elapsed += 0.5

            after_screenshot = self.capture.capture_window(hwnd)
            diff_percent = self._calculate_diff(
                before_screenshot.image,
                after_screenshot.image
            )

            if diff_percent > self.diff_threshold:
                return VerificationResult(
                    success=True,
                    method=VerificationMethod.VISUAL_DIFF,
                    details=f"Visual diff after {elapsed:.1f}s: {diff_percent:.1%}",
                    diff_percent=diff_percent
                )

        return VerificationResult(
            success=False,
            method=VerificationMethod.FAILED,
            details=f"No change detected after {self.max_wait}s",
            diff_percent=diff_percent
        )

    def _calculate_diff(self, before: Image.Image, after: Image.Image) -> float:
        """
        Calculate visual difference between two screenshots.

        Args:
            before: Screenshot before click
            after: Screenshot after click

        Returns:
            Difference as percentage (0.0 to 1.0)
        """
        # Ensure same size
        if before.size != after.size:
            after = after.resize(before.size, Image.Resampling.LANCZOS)

        # Convert to RGBA for pixelmatch
        before_rgba = before.convert("RGBA")
        after_rgba = after.convert("RGBA")

        # Create diff image
        diff_image = Image.new("RGBA", before_rgba.size)

        # Calculate mismatch
        try:
            mismatch = pixelmatch(
                before_rgba,
                after_rgba,
                diff_image,
                threshold=0.1
            )
        except Exception:
            # Fallback to simple comparison
            return self._simple_diff(before, after)

        total_pixels = before_rgba.size[0] * before_rgba.size[1]
        return mismatch / total_pixels

    def _simple_diff(self, before: Image.Image, after: Image.Image) -> float:
        """Simple pixel difference fallback."""
        before_bytes = before.tobytes()
        after_bytes = after.tobytes()

        if len(before_bytes) != len(after_bytes):
            return 1.0

        diff_count = sum(1 for a, b in zip(before_bytes, after_bytes) if a != b)
        return diff_count / len(before_bytes)


def verify_click_simple(
    hwnd: int,
    before: Screenshot,
    before_url: Optional[str] = None,
    get_url: Optional[callable] = None
) -> bool:
    """
    Quick function to verify a click had effect.

    Args:
        hwnd: Window handle
        before: Screenshot before click
        before_url: URL before click
        get_url: Function to get current URL

    Returns:
        True if click appears to have worked
    """
    verifier = ClickVerifier()
    result = verifier.verify_click(hwnd, before, before_url, get_url)
    return result.success
