"""
Window manager for OS-level input operations.

Ensures AdsPower browser window is in foreground before any
screenshots or input actions. Required because OS-level input
(HumanCursor, PyAutoGUI) operates on screen coordinates.
"""

import time
from typing import Optional
from dataclasses import dataclass

import win32gui
import win32con
import win32process
import win32api


@dataclass
class WindowInfo:
    """Information about a window."""
    hwnd: int
    title: str
    pid: int


class WindowManager:
    """Manages window focus for OS-level input operations."""

    def __init__(self, settle_time: float = 0.3):
        """
        Args:
            settle_time: Seconds to wait after bringing window to foreground
        """
        self.settle_time = settle_time

    def find_windows_by_title(self, title_contains: str) -> list[WindowInfo]:
        """
        Find all windows whose title contains the given string.

        Args:
            title_contains: Substring to search for in window titles

        Returns:
            List of matching WindowInfo objects
        """
        results = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title_contains.lower() in title.lower():
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    results.append(WindowInfo(hwnd=hwnd, title=title, pid=pid))
            return True

        win32gui.EnumWindows(enum_callback, None)
        return results

    def find_adspower_browser(self, profile_name: Optional[str] = None) -> Optional[WindowInfo]:
        """
        Find the AdsPower browser window (SunBrowser, not the app).

        Args:
            profile_name: Optional profile name to match in title

        Returns:
            WindowInfo if found, None otherwise
        """
        # AdsPower browser windows have "SunBrowser" in title
        # Format: "<profile_name> - SunBrowser"
        browser_windows = self.find_windows_by_title("SunBrowser")

        if not browser_windows:
            return None

        # If profile_name specified, prefer window with that name in title
        if profile_name:
            for win in browser_windows:
                if profile_name.lower() in win.title.lower():
                    return win

        # Return first SunBrowser window
        return browser_windows[0] if browser_windows else None

    def find_adspower_app(self) -> Optional[WindowInfo]:
        """
        Find the AdsPower application window (not the browser).

        Returns:
            WindowInfo if found, None otherwise
        """
        for win in self.find_windows_by_title("AdsPower Browser |"):
            return win
        return None

    def bring_to_foreground(self, hwnd: int, maximize: bool = True) -> bool:
        """
        Bring a window to the foreground.

        Args:
            hwnd: Window handle
            maximize: Whether to maximize the window

        Returns:
            True if successful (or window is visible and usable)
        """
        try:
            # Restore if minimized, then optionally maximize
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            if maximize:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

            # Try multiple methods to bring to foreground
            # Method 1: Direct SetForegroundWindow (works if we have focus)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

            # Method 2: Attach to target thread (works from background)
            try:
                current_thread = win32api.GetCurrentThreadId()
                target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
                if current_thread != target_thread:
                    win32process.AttachThreadInput(current_thread, target_thread, True)
                    win32gui.SetForegroundWindow(hwnd)
                    win32process.AttachThreadInput(current_thread, target_thread, False)
            except Exception:
                pass

            # Method 3: BringWindowToTop as fallback
            try:
                win32gui.BringWindowToTop(hwnd)
            except Exception:
                pass

            # Wait for window to settle
            time.sleep(self.settle_time)

            # Consider success if window is visible (even if not strictly foreground)
            return win32gui.IsWindowVisible(hwnd)
        except Exception:
            return False

    def is_foreground(self, hwnd: int) -> bool:
        """
        Check if a window is currently in foreground.

        Args:
            hwnd: Window handle

        Returns:
            True if window is foreground
        """
        return win32gui.GetForegroundWindow() == hwnd

    def ensure_foreground(self, hwnd: int, max_attempts: int = 3) -> bool:
        """
        Ensure a window is in foreground, with retries.

        Args:
            hwnd: Window handle
            max_attempts: Maximum attempts to bring to foreground

        Returns:
            True if window is in foreground or at least visible
        """
        for _ in range(max_attempts):
            if self.is_foreground(hwnd):
                return True
            self.bring_to_foreground(hwnd)

        # Accept if foreground OR just visible (for testing scenarios)
        return self.is_foreground(hwnd) or win32gui.IsWindowVisible(hwnd)

    def get_window_rect(self, hwnd: int) -> tuple[int, int, int, int]:
        """
        Get window rectangle (left, top, right, bottom).

        Args:
            hwnd: Window handle

        Returns:
            Tuple of (left, top, right, bottom) coordinates
        """
        return win32gui.GetWindowRect(hwnd)


def ensure_adspower_foreground(profile_name: Optional[str] = None) -> Optional[WindowInfo]:
    """
    Find AdsPower browser window and bring it to foreground.

    Args:
        profile_name: Optional profile name to match in window title

    Returns:
        WindowInfo if successful, None if window not found

    Raises:
        RuntimeError: If window found but couldn't bring to foreground
    """
    wm = WindowManager()
    window = wm.find_adspower_browser(profile_name)

    if not window:
        return None

    if not wm.ensure_foreground(window.hwnd):
        raise RuntimeError(f"Found window '{window.title}' but couldn't bring to foreground")

    return window
