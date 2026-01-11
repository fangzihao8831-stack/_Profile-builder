"""
Screenshot capture for element finding.

Captures browser window screenshots and resizes for VLM processing.
Uses OS-level screenshot (pyautogui) for reliable capture.
"""

import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import pyautogui
from PIL import Image

from core.window_manager import WindowManager, WindowInfo
from core.logger import Log
from core.debug import save_debug_screenshot


VLM_TARGET_HEIGHT = 720  # 720p for VLM input


@dataclass
class Screenshot:
    """Captured screenshot with metadata for coordinate translation."""
    image: Image.Image
    original_size: Tuple[int, int]  # (width, height) before resize
    vlm_size: Tuple[int, int]  # (width, height) after resize
    window_rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    scale_factor: float  # original / vlm (for coord translation)


class ScreenshotCapture:
    """Captures and prepares screenshots for VLM processing."""

    def __init__(self, vlm_height: int = VLM_TARGET_HEIGHT, debug: bool = True):
        """
        Args:
            vlm_height: Target height for VLM input (maintains aspect ratio)
            debug: Whether to save debug screenshots
        """
        self.vlm_height = vlm_height
        self.window_manager = WindowManager()
        self.debug = debug
        self.log = Log.screenshot()

    def capture_window(self, hwnd: int) -> Screenshot:
        """
        Capture a window screenshot and prepare for VLM.

        Args:
            hwnd: Window handle to capture

        Returns:
            Screenshot object with image and coordinate metadata
        """
        # Get window position
        rect = self.window_manager.get_window_rect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top

        self.log.info(f"Capturing window hwnd={hwnd} at rect={rect} ({width}x{height})")

        # Check if window is actually in foreground
        is_fg = self.window_manager.is_foreground(hwnd)
        if not is_fg:
            self.log.warning(f"Window is NOT in foreground! Screenshot may capture wrong content.")

        # Capture the region
        image = pyautogui.screenshot(region=(left, top, width, height))
        original_size = image.size

        # Resize for VLM (maintain aspect ratio)
        vlm_image, vlm_size = self._resize_for_vlm(image)

        scale_factor = original_size[1] / vlm_size[1]

        self.log.debug(f"Captured {original_size} -> resized to {vlm_size}, scale={scale_factor:.2f}")

        screenshot = Screenshot(
            image=vlm_image,
            original_size=original_size,
            vlm_size=vlm_size,
            window_rect=rect,
            scale_factor=scale_factor
        )

        # Save debug screenshot
        if self.debug:
            path = save_debug_screenshot(vlm_image, prefix="capture")
            self.log.debug(f"Debug screenshot saved: {path}")

        return screenshot

    def capture_adspower(self, profile_name: Optional[str] = None) -> Optional[Screenshot]:
        """
        Capture screenshot of AdsPower browser window.

        Args:
            profile_name: Optional profile name to match

        Returns:
            Screenshot if window found, None otherwise
        """
        self.log.info(f"Looking for AdsPower browser (profile={profile_name})")

        window = self.window_manager.find_adspower_browser(profile_name)
        if not window:
            self.log.error("AdsPower browser window not found!")
            return None

        self.log.info(f"Found window: '{window.title}' hwnd={window.hwnd}")

        # Ensure foreground before capture
        if not self.window_manager.ensure_foreground(window.hwnd):
            self.log.error("Failed to bring window to foreground!")
            return None

        return self.capture_window(window.hwnd)

    def _resize_for_vlm(self, image: Image.Image) -> Tuple[Image.Image, Tuple[int, int]]:
        """
        Resize image to target height for VLM, maintaining aspect ratio.

        Args:
            image: Original PIL Image

        Returns:
            Tuple of (resized_image, (width, height))
        """
        original_width, original_height = image.size

        # Calculate new dimensions maintaining aspect ratio
        scale = self.vlm_height / original_height
        new_width = int(original_width * scale)
        new_height = self.vlm_height

        # Use LANCZOS for high quality downscaling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized, (new_width, new_height)

    def save(self, screenshot: Screenshot, path: str, save_vlm: bool = True) -> str:
        """
        Save screenshot to file.

        Args:
            screenshot: Screenshot object to save
            path: File path to save to
            save_vlm: If True, save VLM-sized image; if False, save original

        Returns:
            Path to saved file
        """
        screenshot.image.save(path)
        return path


def capture_for_vlm(profile_name: Optional[str] = None) -> Optional[Screenshot]:
    """
    Quick function to capture AdsPower browser for VLM processing.

    Args:
        profile_name: Optional profile name to match

    Returns:
        Screenshot ready for VLM, or None if window not found
    """
    capture = ScreenshotCapture()
    return capture.capture_adspower(profile_name)
