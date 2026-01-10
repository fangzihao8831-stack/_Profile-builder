"""
Milestone 1 Foundation Tests

Tests AdsPower, Ollama, and Window Manager integration.
Run with: python -m pytest tests/test_milestone1.py -v
"""

import os
import time
import pytest
import pyautogui

from browser.adspower import AdsPowerClient
from ai.ollama_client import OllamaClient
from core.window_manager import WindowManager, ensure_adspower_foreground


PROFILE_ID = "k18il1i6"


class TestAdsPower:
    """Test AdsPower connection and profile management."""

    def test_connection(self):
        client = AdsPowerClient()
        assert client.check_connection() is True

    def test_open_close_profile(self):
        client = AdsPowerClient()

        # Open
        conn = client.open_profile(PROFILE_ID)
        assert conn.profile_id == PROFILE_ID
        assert conn.debug_port != ""

        # Verify active
        assert client.is_profile_active(PROFILE_ID) is True

        # Close
        closed = client.close_profile(PROFILE_ID)
        assert closed is True
        assert client.is_profile_active(PROFILE_ID) is False


class TestOllama:
    """Test Ollama/Qwen connection."""

    def test_connection(self):
        client = OllamaClient()
        assert client.check_connection() is True

    def test_model_available(self):
        client = OllamaClient()
        assert client.is_model_available() is True

    def test_json_response(self):
        client = OllamaClient()
        response = client.ask('Respond exactly: {"status": "ok"}')
        assert response.content.get("status") == "ok"


class TestWindowManager:
    """Test window management for OS-level input."""

    def test_find_adspower_app(self):
        wm = WindowManager()
        app = wm.find_adspower_app()
        assert app is not None
        assert "AdsPower Browser" in app.title


class TestIntegration:
    """Integration test: open browser, focus, screenshot, ask Qwen."""

    def test_full_flow(self):
        ads = AdsPowerClient()
        wm = WindowManager()
        vlm = OllamaClient()

        # Open profile
        conn = ads.open_profile(PROFILE_ID)
        assert conn.debug_port != ""

        try:
            # Wait for browser window
            window = None
            for _ in range(10):
                window = wm.find_adspower_browser()
                if window:
                    break
                time.sleep(0.3)

            assert window is not None, "Browser window not found"
            assert "SunBrowser" in window.title

            # Bring to foreground (maximized)
            result = ensure_adspower_foreground()
            assert result is not None

            # Take screenshot
            screenshot_path = "test_integration.png"
            pyautogui.screenshot().save(screenshot_path)
            assert os.path.exists(screenshot_path)

            # Ask Qwen what it sees
            response = vlm.ask(
                'How many browser tabs are open? JSON: {"tab_count": <number>}',
                image_path=screenshot_path
            )
            assert "tab_count" in response.content
            assert response.content["tab_count"] >= 1

            # Cleanup screenshot
            os.remove(screenshot_path)

        finally:
            # Always close profile
            ads.close_profile(PROFILE_ID)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
