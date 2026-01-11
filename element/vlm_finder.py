"""
VLM-based element finding.

Uses Qwen2.5-VL to locate elements in screenshots and return coordinates.
This is the reliable baseline - always works but slower than OCR.
"""

import os
import tempfile
from dataclasses import dataclass
from typing import Optional, Tuple

from ai.ollama_client import OllamaClient
from element.screenshot import Screenshot
from core.logger import Log
from core.debug import get_debugger


@dataclass
class ElementLocation:
    """Location of an element found by VLM."""
    target: str
    found: bool
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2)
    center: Optional[Tuple[int, int]] = None  # (x, y)
    confidence: float = 0.0
    raw_response: str = ""


FIND_ELEMENT_PROMPT = """Look at this screenshot and find the element: "{target}"

Return a JSON object with these exact fields:
- "found": true if you can see the element, false otherwise
- "target": the element you were asked to find
- "bbox": object with x1, y1, x2, y2 coordinates of the bounding box (pixels from top-left)
- "center": object with x, y coordinates of the center point
- "confidence": your confidence 0.0 to 1.0

Example response if found:
{{"found": true, "target": "Add to Cart", "bbox": {{"x1": 100, "y1": 200, "x2": 200, "y2": 240}}, "center": {{"x": 150, "y": 220}}, "confidence": 0.95}}

Example response if NOT found:
{{"found": false, "target": "Add to Cart", "bbox": null, "center": null, "confidence": 0.0}}

Important:
- Coordinates are in pixels from the top-left corner of the image
- Be precise - the coordinates will be used for clicking
- If you're not confident, set found to false"""


class VLMElementFinder:
    """Finds elements using vision language model."""

    def __init__(self, client: Optional[OllamaClient] = None, debug: bool = True):
        """
        Args:
            client: OllamaClient instance (creates one if not provided)
            debug: Whether to save debug visualizations
        """
        self.client = client or OllamaClient()
        self.debug = debug
        self.debugger = get_debugger(enabled=debug)
        self.log = Log.vlm()

    def find(self, screenshot: Screenshot, target: str) -> ElementLocation:
        """
        Find an element in a screenshot.

        Args:
            screenshot: Screenshot object with image
            target: Element to find (text, description, etc.)

        Returns:
            ElementLocation with coordinates if found
        """
        self.log.info(f"Finding element: '{target}'")

        # Save screenshot to temp file for VLM
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            screenshot.image.save(temp_path)

        try:
            prompt = FIND_ELEMENT_PROMPT.format(target=target)
            self.log.debug(f"Sending to VLM with image: {temp_path}")

            response = self.client.ask(prompt, image_path=temp_path)
            self.log.debug(f"VLM response: {response.raw[:200]}...")

            location = self._parse_response(response.content, response.raw, target)

            # Log result
            if location.found:
                self.log.info(f"FOUND '{target}' at bbox={location.bbox}, center={location.center}, conf={location.confidence:.0%}")
            else:
                self.log.warning(f"NOT FOUND: '{target}'")

            # Save debug visualization
            if self.debug:
                self.debugger.visualize_element_found(
                    image=screenshot.image,
                    target=target,
                    bbox=location.bbox,
                    center=location.center,
                    confidence=location.confidence
                )

            return location

        except Exception as e:
            self.log.error(f"VLM find failed: {e}")
            raise

        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _parse_response(self, content: dict, raw: str, target: str) -> ElementLocation:
        """Parse VLM response into ElementLocation."""
        found = content.get("found", False)

        if not found:
            return ElementLocation(
                target=target,
                found=False,
                confidence=0.0,
                raw_response=raw
            )

        # Parse bounding box
        bbox_data = content.get("bbox", {})
        bbox = None
        if bbox_data and isinstance(bbox_data, dict):
            try:
                bbox = (
                    int(bbox_data.get("x1", 0)),
                    int(bbox_data.get("y1", 0)),
                    int(bbox_data.get("x2", 0)),
                    int(bbox_data.get("y2", 0))
                )
            except (TypeError, ValueError):
                pass

        # Parse center
        center_data = content.get("center", {})
        center = None
        if center_data and isinstance(center_data, dict):
            try:
                center = (
                    int(center_data.get("x", 0)),
                    int(center_data.get("y", 0))
                )
            except (TypeError, ValueError):
                pass

        # If we have bbox but no center, calculate it
        if bbox and not center:
            center = (
                (bbox[0] + bbox[2]) // 2,
                (bbox[1] + bbox[3]) // 2
            )

        confidence = float(content.get("confidence", 0.0))

        return ElementLocation(
            target=target,
            found=True,
            bbox=bbox,
            center=center,
            confidence=confidence,
            raw_response=raw
        )


def find_element(screenshot: Screenshot, target: str) -> ElementLocation:
    """
    Quick function to find an element in a screenshot.

    Args:
        screenshot: Screenshot object
        target: Element to find

    Returns:
        ElementLocation with coordinates
    """
    finder = VLMElementFinder()
    return finder.find(screenshot, target)
