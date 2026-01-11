"""
Human-like keyboard input using OS-level events.

Uses pynput for OS-level keyboard control.
NEVER use Selenium .send_keys() - only this module for typing.
"""

import random
import time
from typing import Optional

from pynput.keyboard import Key, Controller

from core.logger import Log


class HumanKeyboard:
    """Human-like keyboard control using OS-level events."""

    def __init__(
        self,
        min_delay: float = 0.05,
        max_delay: float = 0.15,
        typo_chance: float = 0.0  # Set > 0 for realistic typos
    ):
        """
        Args:
            min_delay: Minimum delay between keystrokes (seconds)
            max_delay: Maximum delay between keystrokes (seconds)
            typo_chance: Probability of making a typo (0.0-1.0)
        """
        self.keyboard = Controller()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.typo_chance = typo_chance
        self.log = Log.session()  # Using session logger for keyboard

    def _random_delay(self) -> float:
        """Generate random human-like delay between keystrokes."""
        return random.uniform(self.min_delay, self.max_delay)

    def _pause(self) -> None:
        """Pause for a random human-like interval."""
        time.sleep(self._random_delay())

    def type_text(self, text: str, final_enter: bool = False) -> None:
        """
        Type text with human-like delays between characters.

        Args:
            text: Text to type
            final_enter: Whether to press Enter after typing
        """
        self.log.info(f"Typing: '{text[:50]}{'...' if len(text) > 50 else ''}'")

        for char in text:
            self.keyboard.type(char)
            self._pause()

        if final_enter:
            self._pause()
            self.press_key(Key.enter)

    def press_key(self, key: Key) -> None:
        """
        Press a special key.

        Args:
            key: pynput Key to press (e.g., Key.enter, Key.tab)
        """
        self.log.debug(f"Pressing key: {key}")
        self.keyboard.press(key)
        self.keyboard.release(key)

    def hotkey(self, *keys) -> None:
        """
        Press a key combination (hotkey).

        Args:
            keys: Keys to press together (e.g., Key.ctrl, 't' for Ctrl+T)
        """
        key_names = [str(k) for k in keys]
        self.log.info(f"Hotkey: {' + '.join(key_names)}")

        # Press all keys
        for key in keys:
            self.keyboard.press(key)

        # Small delay while held
        time.sleep(0.05)

        # Release in reverse order
        for key in reversed(keys):
            self.keyboard.release(key)

    def new_tab(self) -> None:
        """Open a new browser tab (Ctrl+T)."""
        self.log.info("Opening new tab (Ctrl+T)")
        self.hotkey(Key.ctrl, 't')
        time.sleep(0.3)  # Wait for tab to open

    def close_tab(self) -> None:
        """Close current browser tab (Ctrl+W)."""
        self.log.info("Closing tab (Ctrl+W)")
        self.hotkey(Key.ctrl, 'w')
        time.sleep(0.2)

    def switch_tab_next(self) -> None:
        """Switch to next tab (Ctrl+Tab)."""
        self.log.info("Switching to next tab (Ctrl+Tab)")
        self.hotkey(Key.ctrl, Key.tab)
        time.sleep(0.2)

    def switch_tab_prev(self) -> None:
        """Switch to previous tab (Ctrl+Shift+Tab)."""
        self.log.info("Switching to previous tab (Ctrl+Shift+Tab)")
        self.hotkey(Key.ctrl, Key.shift, Key.tab)
        time.sleep(0.2)

    def focus_address_bar(self) -> None:
        """Focus the browser address bar (Ctrl+L or F6)."""
        self.log.info("Focusing address bar (Ctrl+L)")
        self.hotkey(Key.ctrl, 'l')
        time.sleep(0.2)

    def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL by focusing address bar and typing.

        Args:
            url: URL to navigate to
        """
        self.log.info(f"Navigating to: {url}")
        self.focus_address_bar()
        time.sleep(0.1)
        self.type_text(url, final_enter=True)

    def search_in_address_bar(self, query: str) -> None:
        """
        Search using the address bar (like Google search).

        Args:
            query: Search query
        """
        self.log.info(f"Searching: {query}")
        self.focus_address_bar()
        time.sleep(0.1)
        self.type_text(query, final_enter=True)

    def select_all(self) -> None:
        """Select all text (Ctrl+A)."""
        self.hotkey(Key.ctrl, 'a')

    def copy(self) -> None:
        """Copy selected text (Ctrl+C)."""
        self.hotkey(Key.ctrl, 'c')

    def paste(self) -> None:
        """Paste from clipboard (Ctrl+V)."""
        self.hotkey(Key.ctrl, 'v')

    def escape(self) -> None:
        """Press Escape key."""
        self.press_key(Key.esc)

    def enter(self) -> None:
        """Press Enter key."""
        self.press_key(Key.enter)

    def tab(self) -> None:
        """Press Tab key."""
        self.press_key(Key.tab)

    def backspace(self, count: int = 1) -> None:
        """
        Press Backspace key multiple times.

        Args:
            count: Number of times to press
        """
        for _ in range(count):
            self.press_key(Key.backspace)
            self._pause()

    def scroll_down(self) -> None:
        """Scroll down using Page Down."""
        self.press_key(Key.page_down)

    def scroll_up(self) -> None:
        """Scroll up using Page Up."""
        self.press_key(Key.page_up)


# Convenience functions
def type_text(text: str, enter: bool = False) -> None:
    """Quick function to type text."""
    kb = HumanKeyboard()
    kb.type_text(text, final_enter=enter)


def new_tab() -> None:
    """Quick function to open new tab."""
    kb = HumanKeyboard()
    kb.new_tab()


def navigate(url: str) -> None:
    """Quick function to navigate to URL."""
    kb = HumanKeyboard()
    kb.navigate_to(url)


def search(query: str) -> None:
    """Quick function to search in address bar."""
    kb = HumanKeyboard()
    kb.search_in_address_bar(query)
