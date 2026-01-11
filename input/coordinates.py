"""
Coordinate translation between image space and screen space.

Handles:
- VLM coordinates (720p image) -> Original image coordinates
- Original image coordinates -> Screen coordinates (window position)
"""

from dataclasses import dataclass
from typing import Tuple

from element.screenshot import Screenshot
from element.vlm_finder import ElementLocation


@dataclass
class ScreenCoordinate:
    """Screen coordinate ready for mouse input."""
    x: int
    y: int
    source: str  # "vlm", "ocr", "css" - for debugging


class CoordinateTranslator:
    """Translates coordinates between image and screen space."""

    def vlm_to_screen(
        self,
        vlm_point: Tuple[int, int],
        screenshot: Screenshot
    ) -> ScreenCoordinate:
        """
        Translate VLM image coordinates to screen coordinates.

        Args:
            vlm_point: (x, y) coordinates in VLM image space (720p)
            screenshot: Screenshot with window position and scale info

        Returns:
            ScreenCoordinate ready for clicking
        """
        vlm_x, vlm_y = vlm_point

        # Scale from VLM size to original window size
        original_x = int(vlm_x * screenshot.scale_factor)
        original_y = int(vlm_y * screenshot.scale_factor)

        # Add window offset to get screen coordinates
        window_left, window_top, _, _ = screenshot.window_rect
        screen_x = window_left + original_x
        screen_y = window_top + original_y

        return ScreenCoordinate(x=screen_x, y=screen_y, source="vlm")

    def element_to_screen(
        self,
        location: ElementLocation,
        screenshot: Screenshot
    ) -> ScreenCoordinate:
        """
        Translate ElementLocation center to screen coordinates.

        Args:
            location: ElementLocation from VLM finder
            screenshot: Screenshot with coordinate metadata

        Returns:
            ScreenCoordinate ready for clicking

        Raises:
            ValueError: If element not found or has no center
        """
        if not location.found or not location.center:
            raise ValueError(f"Element '{location.target}' not found or has no center")

        return self.vlm_to_screen(location.center, screenshot)

    def bbox_to_screen(
        self,
        bbox: Tuple[int, int, int, int],
        screenshot: Screenshot
    ) -> Tuple[ScreenCoordinate, ScreenCoordinate]:
        """
        Translate bounding box corners to screen coordinates.

        Args:
            bbox: (x1, y1, x2, y2) in VLM image space
            screenshot: Screenshot with coordinate metadata

        Returns:
            Tuple of (top_left, bottom_right) ScreenCoordinates
        """
        x1, y1, x2, y2 = bbox
        top_left = self.vlm_to_screen((x1, y1), screenshot)
        bottom_right = self.vlm_to_screen((x2, y2), screenshot)
        return top_left, bottom_right


def translate_to_screen(
    location: ElementLocation,
    screenshot: Screenshot
) -> ScreenCoordinate:
    """
    Quick function to translate element location to screen coordinates.

    Args:
        location: ElementLocation from finder
        screenshot: Screenshot with window info

    Returns:
        ScreenCoordinate ready for clicking
    """
    translator = CoordinateTranslator()
    return translator.element_to_screen(location, screenshot)
