"""
AdsPower browser profile management.

Handles connection to AdsPower local API for browser profile operations.
"""

import requests
from typing import Optional
from dataclasses import dataclass


ADSPOWER_BASE = "http://local.adspower.net:50325"


@dataclass
class BrowserConnection:
    """Connection details for an opened browser profile."""
    profile_id: str
    selenium_port: str
    debug_port: str


class AdsPowerClient:
    """Client for AdsPower local API."""

    def __init__(self, base_url: str = ADSPOWER_BASE, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_connection(self) -> bool:
        """Check if AdsPower is running and accessible."""
        try:
            resp = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def open_profile(self, profile_id: str) -> BrowserConnection:
        """
        Open a browser profile and return connection details.

        Args:
            profile_id: The AdsPower profile/user ID

        Returns:
            BrowserConnection with selenium_port and debug_port

        Raises:
            RuntimeError: If profile fails to open
        """
        resp = requests.get(
            f"{self.base_url}/api/v1/browser/start",
            params={"user_id": profile_id},
            timeout=self.timeout
        )
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Failed to open profile: {data.get('msg', 'Unknown error')}")

        ws_data = data.get("data", {}).get("ws", {})
        return BrowserConnection(
            profile_id=profile_id,
            selenium_port=ws_data.get("selenium", ""),
            debug_port=str(data.get("data", {}).get("debug_port", ""))
        )

    def close_profile(self, profile_id: str) -> bool:
        """
        Close a browser profile.

        Args:
            profile_id: The AdsPower profile/user ID

        Returns:
            True if closed successfully or already closed
        """
        try:
            # Browser close can take longer than other operations
            resp = requests.get(
                f"{self.base_url}/api/v1/browser/stop",
                params={"user_id": profile_id},
                timeout=30
            )
            data = resp.json()
            # code 0 = success, code -1 with "not open" = already closed
            return data.get("code") == 0 or "not open" in data.get("msg", "").lower()
        except requests.RequestException:
            # Even on timeout, check if profile actually closed
            return not self.is_profile_active(profile_id)

    def is_profile_active(self, profile_id: str) -> bool:
        """
        Check if a profile is currently running.

        Args:
            profile_id: The AdsPower profile/user ID

        Returns:
            True if profile is active
        """
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/browser/active",
                params={"user_id": profile_id},
                timeout=self.timeout
            )
            data = resp.json()
            return data.get("data", {}).get("status") == "Active"
        except requests.RequestException:
            return False


def check_adspower() -> tuple[bool, str]:
    """
    Quick check if AdsPower is accessible.

    Returns:
        Tuple of (success, message)
    """
    client = AdsPowerClient()
    if client.check_connection():
        return True, "AdsPower connection OK"
    return False, "AdsPower not accessible. Is it running?"
