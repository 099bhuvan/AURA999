import json
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
import httpx

from app.core.provider_base import AIProviderBase

logger = logging.getLogger("AURA.Ollama")


class OllamaProvider(AIProviderBase):
    """Local offline AI provider using Ollama HTTP API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_availability(self) -> Tuple[bool, str]:
        """Check if local Ollama daemon is reachable and whether model is pulled."""
        try:
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check exact match or base tag match (e.g. llama3.2 vs llama3.2:latest)
                    model_found = any(
                        self.model == m or m.startswith(f"{self.model}:") or self.model.startswith(m)
                        for m in models
                    )
                    if model_found:
                        return True, f"Ollama online with model '{self.model}'."
                    elif models:
                        return False, f"Ollama reachable, but '{self.model}' is not installed. Found: {', '.join(models[:4])}."
                    else:
                        return False, "Ollama is active, but no models installed. Run: ollama run llama3.2"
                return False, f"Ollama returned HTTP status {resp.status_code}."
        except httpx.ConnectError:
            return False, f"Ollama daemon not reachable at {self.base_url}. Ensure Ollama is running."
        except Exception as e:
            return False, f"Ollama check failed: {str(e)}"

    def list_available_models(self) -> List[str]:
        """Return list of locally installed Ollama models."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.warning("Could not list Ollama models: %s", e)
        return []

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """Stream or generate response from local Ollama model."""
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        full_text = []

        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", endpoint, json=payload) as response:
                    if response.status_code != 200:
                        err_body = response.read().decode("utf-8", errors="replace")
                        raise RuntimeError(f"Ollama error ({response.status_code}): {err_body}")

                    for line in response.iter_lines():
                        if cancel_check and cancel_check():
                            logger.info("Generation cancelled by user.")
                            break
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                full_text.append(delta)
                                if stream_callback:
                                    stream_callback(delta)
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Verify that the Ollama service is running on this machine."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama inference error: {str(e)}")

        return "".join(full_text)
