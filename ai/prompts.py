"""
Prompt templates for AI decision making.

Designed to prevent common VLM issues:
1. Ignoring action history
2. Hallucinating English text on non-English pages
3. Defaulting to scroll when uncertain
"""

from typing import Set, List


def build_actor_prompt(
    structure: str,
    goal: str,
    forbidden: Set[str],
    recent_actions: List[str],
    scroll_count: int = 0,
    click_count: int = 0
) -> str:
    """
    Build the actor prompt for VLM decision making.

    Args:
        structure: Session type (fashion, news, etc.)
        goal: Session goal description
        forbidden: Set of element targets that failed/already tried
        recent_actions: List of recent action strings
        scroll_count: Consecutive scroll count
        click_count: Number of clicks on this page
    """
    forbidden_str = ", ".join(forbidden) if forbidden else "none yet"
    recent_str = "\n".join(f"  - {a}" for a in recent_actions[-5:]) if recent_actions else "  (none yet)"

    # Build scroll restriction based on click count
    if click_count < 2:
        scroll_rule = "SCROLL is NOT allowed until you click at least 2 things. You must CLICK first."
    else:
        scroll_rule = "Scroll is allowed, but prefer clicking if you see interesting elements."

    # Build enforcement section (placed at END for higher weight)
    if forbidden:
        enforcement = f"""
CRITICAL - READ THIS:
You already tried clicking: [{', '.join(forbidden)}]
Those elements FAILED or are FORBIDDEN. Clicking them again will FAIL.
You MUST choose something DIFFERENT that is NOT in the forbidden list."""
    else:
        enforcement = ""

    prompt = f"""SESSION: {structure}
GOAL: {goal}

FORBIDDEN ELEMENTS (do NOT click these): {forbidden_str}

RECENT ACTIONS:
{recent_str}

RULES:
1. Look at the screenshot and read the ACTUAL text visible
2. Do NOT assume English - output EXACT text you see (e.g., "HOMBRE" not "Men", "Aceptar" not "Accept")
3. If you see a cookie/consent popup, click the accept button FIRST
4. {scroll_rule}
5. DO NOT click: logos, search icons, cart icons, account icons

RESPOND WITH ONE JSON OBJECT:
{{"action": "click", "target": "EXACT text you see on the element", "reasoning": "why"}}
{{"action": "scroll", "direction": "down", "reasoning": "why"}}
{{"action": "navigate", "text": "website.com", "reasoning": "why"}}
{enforcement}"""

    return prompt


def build_element_verification_prompt(target: str) -> str:
    """
    Prompt to verify what text is actually visible when element not found.

    Used when VLM can't find the target - asks it to list what it actually sees.
    """
    return f"""I asked you to find "{target}" but it was not found.

Look at the screenshot again. List the EXACT text of 3-5 clickable elements you can actually see.
Focus on navigation links, category buttons, or product links.

Respond with JSON:
{{"visible_elements": ["exact text 1", "exact text 2", "exact text 3"]}}"""
