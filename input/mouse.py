"""
Human-like mouse control using HumanCursor.

OS-level mouse movement with bezier curves for natural appearance.
NEVER use Selenium .click() - only this module for clicking.
"""

import random
import time
from typing import Optional, Tuple

from humancursor import SystemCursor

from input.coordinates import ScreenCoordinate
from core.logger import Log


class HumanMouse:
    """Human-like mouse control using OS-level events."""

    def __init__(self):
        """Initialize with SystemCursor for OS-level control."""
        self.cursor = SystemCursor()
        self.log = Log.mouse()

    def move_to(self, x: int, y: int) -> None:
        """
        Move mouse to coordinates with human-like bezier curve.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
        """
        self.log.debug(f"Moving to ({x}, {y})")
        self.cursor.move_to([x, y])

    def click(self, x: int, y: int) -> None:
        """
        Click at coordinates with human-like movement.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
        """
        self.log.info(f"CLICK at ({x}, {y})")
        self.cursor.click_on([x, y])

    def click_at(self, coord: ScreenCoordinate) -> None:
        """
        Click at a ScreenCoordinate.

        Args:
            coord: ScreenCoordinate to click
        """
        self.click(coord.x, coord.y)

    def click_with_jitter(
        self,
        coord: ScreenCoordinate,
        jitter_px: int = 3
    ) -> Tuple[int, int]:
        """
        Click with small random offset for more human-like behavior.

        Args:
            coord: ScreenCoordinate to click
            jitter_px: Max random offset in pixels

        Returns:
            Actual (x, y) clicked
        """
        jitter_x = random.randint(-jitter_px, jitter_px)
        jitter_y = random.randint(-jitter_px, jitter_px)

        actual_x = coord.x + jitter_x
        actual_y = coord.y + jitter_y

        self.click(actual_x, actual_y)
        return actual_x, actual_y

    def double_click(self, x: int, y: int) -> None:
        """
        Double click at coordinates.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate
        """
        self.cursor.click_on([x, y], clicks=2)

    def right_click(self, x: int, y: int) -> None:
        """
        Right click at coordinates.

        Note: HumanCursor may not support right-click directly,
        falls back to pyautogui for this.
        """
        import pyautogui
        self.move_to(x, y)
        pyautogui.rightClick()


def click_element(coord: ScreenCoordinate, jitter: bool = True) -> Tuple[int, int]:
    """
    Quick function to click at a screen coordinate.

    Args:
        coord: ScreenCoordinate to click
        jitter: If True, add small random offset

    Returns:
        Actual (x, y) clicked
    """
    mouse = HumanMouse()
    if jitter:
        return mouse.click_with_jitter(coord)
    else:
        mouse.click_at(coord)
        return coord.x, coord.y
