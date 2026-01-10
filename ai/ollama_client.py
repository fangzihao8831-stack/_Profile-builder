"""
Ollama client for Qwen2.5-VL-7B vision model.

Handles communication with locally running Ollama for AI decisions.
"""

import json
from typing import Any, Optional
from dataclasses import dataclass

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None


DEFAULT_MODEL = "qwen2.5vl:7b"


@dataclass
class VLMResponse:
    """Response from the vision language model."""
    content: dict[str, Any]
    raw: str


class OllamaClient:
    """Client for Ollama API with Qwen2.5-VL model."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        if not OLLAMA_AVAILABLE:
            return False
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def is_model_available(self) -> bool:
        """Check if the configured model is available."""
        if not OLLAMA_AVAILABLE:
            return False
        try:
            models = ollama.list()
            model_list = models.get("models", []) if isinstance(models, dict) else getattr(models, "models", [])

            for m in model_list:
                # Handle both dict and object response formats
                # Ollama returns 'model' attribute, not 'name'
                name = m.get("model", m.get("name", "")) if isinstance(m, dict) else getattr(m, "model", getattr(m, "name", ""))
                # Check for both qwen2.5vl and qwen2.5-vl variants
                if "qwen2.5vl" in name.lower() or "qwen2.5-vl" in name.lower():
                    return True
            return False
        except Exception:
            return False

    def ask(self, prompt: str, image_path: Optional[str] = None) -> VLMResponse:
        """
        Send a prompt to the VLM and get a JSON response.

        Args:
            prompt: The text prompt
            image_path: Optional path to image for vision tasks

        Returns:
            VLMResponse with parsed content and raw response

        Raises:
            RuntimeError: If API call fails or response is invalid
        """
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("ollama package not installed")

        messages = [{
            "role": "user",
            "content": prompt,
        }]

        if image_path:
            messages[0]["images"] = [image_path]

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "keep_alive": -1,  # Keep in VRAM indefinitely
                },
                format="json"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {e}")

        raw_content = response.get("message", {}).get("content", "")
        if isinstance(response, dict):
            raw_content = response.get("message", {}).get("content", "")
        else:
            raw_content = getattr(getattr(response, "message", {}), "content", "")

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response: {e}\nRaw: {raw_content}")

        return VLMResponse(content=parsed, raw=raw_content)

    def warm_up(self) -> bool:
        """
        Warm up the model by sending a simple request.
        This loads the model into VRAM if not already loaded.

        Returns:
            True if warm-up successful
        """
        try:
            self.ask("Respond with: {\"status\": \"ready\"}")
            return True
        except Exception:
            return False


def check_ollama() -> tuple[bool, str]:
    """
    Quick check if Ollama and Qwen2.5-VL are available.

    Returns:
        Tuple of (success, message)
    """
    if not OLLAMA_AVAILABLE:
        return False, "ollama package not installed. Run: pip install ollama"

    client = OllamaClient()

    if not client.check_connection():
        return False, "Ollama not accessible. Is it running?"

    if not client.is_model_available():
        return False, f"Model {DEFAULT_MODEL} not found. Run: ollama pull {DEFAULT_MODEL}"

    return True, f"Ollama + {DEFAULT_MODEL} OK"
