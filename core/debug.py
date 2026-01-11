"""
Debug output for human diagnosis.

Saves debug screenshots with timestamps.
"""

from datetime import datetime
from pathlib import Path

from PIL import Image


# Debug output directory
DEBUG_DIR = Path("debug")


def ensure_debug_dir() -> Path:
    """Create debug directory if it doesn't exist."""
    DEBUG_DIR.mkdir(exist_ok=True)
    return DEBUG_DIR


def get_timestamp() -> str:
    """Get current timestamp for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds


def save_debug_screenshot(
    image: Image.Image,
    prefix: str = "screenshot",
    suffix: str = ""
) -> str:
    """
    Save a debug screenshot with timestamp.

    Args:
        image: PIL Image to save
        prefix: Filename prefix
        suffix: Optional suffix before extension

    Returns:
        Path to saved file
    """
    ensure_debug_dir()
    timestamp = get_timestamp()
    suffix_str = f"_{suffix}" if suffix else ""
    filename = f"{prefix}_{timestamp}{suffix_str}.png"
    path = DEBUG_DIR / filename
    image.save(path)
    return str(path)


class DebugVisualizer:
    """Placeholder for debug visualizations - saves screenshots only."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        if enabled:
            ensure_debug_dir()

    def visualize_element_found(self, image, target, bbox, center, confidence, save=True):
        """Save screenshot for debugging (no bbox overlay)."""
        if not self.enabled or not save:
            return None
        path = save_debug_screenshot(image, prefix="vlm_find", suffix=target.replace(" ", "_")[:20])
        return image


# Global debug instance
_debug = None


def get_debugger(enabled: bool = True) -> DebugVisualizer:
    """Get or create global debug visualizer."""
    global _debug
    if _debug is None:
        _debug = DebugVisualizer(enabled=enabled)
    return _debug
