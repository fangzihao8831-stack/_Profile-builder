"""
Safety checks for browsing actions.

Prevents the AI from taking dangerous actions like:
- Logging out
- Making purchases
- Submitting forms
- Deleting content
"""

from typing import Optional
import re

from ai.actions import BrowsingAction, ActionType


class SafetyChecker:
    """
    Checks if actions are safe to execute.

    Uses pattern matching on action targets and text to detect potentially
    dangerous operations.
    """

    # Patterns that indicate dangerous click targets
    DANGEROUS_CLICK_PATTERNS = [
        # Logout/signout
        r"\blog\s*out\b",
        r"\bsign\s*out\b",
        r"\bsign\s*off\b",
        r"\bexit\s*account\b",

        # Purchase/payment
        r"\bbuy\s*now\b",
        r"\bpurchase\b",
        r"\bcheckout\b",
        r"\bcheck\s*out\b",
        r"\bpay\s*now\b",
        r"\bpayment\b",
        r"\bplace\s*order\b",
        r"\bconfirm\s*order\b",
        r"\bcomplete\s*purchase\b",
        r"\badd\s*to\s*cart\b",  # Could lead to purchase flow

        # Form submission
        r"\bsubmit\b",
        r"\bconfirm\b",
        r"\bsend\s*message\b",
        r"\bpost\s*comment\b",

        # Deletion
        r"\bdelete\b",
        r"\bremove\b",
        r"\bunsubscribe\b",
        r"\bcancel\s*subscription\b",

        # Account changes
        r"\bchange\s*password\b",
        r"\bupdate\s*email\b",
        r"\bdelete\s*account\b",
        r"\bclose\s*account\b",
    ]

    # Patterns for dangerous URLs
    DANGEROUS_URL_PATTERNS = [
        r"/logout",
        r"/signout",
        r"/sign-out",
        r"/checkout",
        r"/payment",
        r"/purchase",
        r"/delete",
        r"/unsubscribe",
        r"/account/close",
    ]

    # Domains that should never be navigated to
    BLOCKED_DOMAINS = [
        "paypal.com",
        "stripe.com",
        "pay.google.com",
        "payments.",
    ]

    def __init__(self):
        """Initialize with compiled regex patterns for performance."""
        self._click_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_CLICK_PATTERNS
        ]
        self._url_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_URL_PATTERNS
        ]

    def is_action_safe(self, action: BrowsingAction) -> tuple[bool, Optional[str]]:
        """
        Check if an action is safe to execute.

        Args:
            action: The action to check

        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        if action.action_type == ActionType.CLICK:
            return self._check_click_safe(action.target)

        elif action.action_type == ActionType.TYPE:
            return self._check_type_safe(action.text)

        elif action.action_type == ActionType.NAVIGATE:
            return self._check_url_safe(action.text)

        # SCROLL and WAIT are always safe
        return True, None

    def _check_click_safe(self, target: str) -> tuple[bool, Optional[str]]:
        """Check if a click target is safe."""
        if not target:
            return True, None

        target_lower = target.lower()

        for pattern in self._click_patterns:
            if pattern.search(target_lower):
                return False, f"Dangerous click target detected: '{target}' matches pattern"

        return True, None

    def _check_type_safe(self, text: str) -> tuple[bool, Optional[str]]:
        """Check if text being typed is safe."""
        if not text:
            return True, None

        # Check for credit card patterns (simple check)
        if re.search(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", text):
            return False, "Text appears to contain credit card number"

        # Check for SSN patterns
        if re.search(r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b", text):
            return False, "Text appears to contain SSN"

        return True, None

    def _check_url_safe(self, url: str) -> tuple[bool, Optional[str]]:
        """Check if a URL is safe to navigate to."""
        if not url:
            return True, None

        url_lower = url.lower()

        # Check blocked domains
        for domain in self.BLOCKED_DOMAINS:
            if domain in url_lower:
                return False, f"Blocked domain: {domain}"

        # Check dangerous URL patterns
        for pattern in self._url_patterns:
            if pattern.search(url_lower):
                return False, f"Dangerous URL pattern detected in: {url}"

        return True, None

    def check_url_safe(self, url: str) -> bool:
        """Simple check if URL is safe (returns just bool)."""
        is_safe, _ = self._check_url_safe(url)
        return is_safe

    def get_safety_rules_prompt(self) -> str:
        """Get safety rules formatted for AI prompt."""
        return """
SAFETY RULES - You MUST follow these:
1. NEVER click on logout, sign out, or exit account buttons
2. NEVER click on buy, purchase, checkout, or payment buttons
3. NEVER click on add to cart buttons
4. NEVER click on submit, confirm order, or place order buttons
5. NEVER click on delete, remove, or unsubscribe buttons
6. NEVER type credit card numbers, SSNs, or passwords
7. NEVER navigate to payment or checkout URLs
8. AVOID clicking on login prompts - just browse as guest
9. If a popup appears, look for a close/X button or scroll away

If you see any of these, choose a different action like scrolling or clicking something else.
"""


# Module-level instance for convenience
_checker = None


def get_safety_checker() -> SafetyChecker:
    """Get the global safety checker instance."""
    global _checker
    if _checker is None:
        _checker = SafetyChecker()
    return _checker


def is_action_safe(action: BrowsingAction) -> tuple[bool, Optional[str]]:
    """Check if an action is safe using the global checker."""
    return get_safety_checker().is_action_safe(action)
