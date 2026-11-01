import json
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
import httpx

from app.core.provider_base import AIProviderBase

logger = logging.getLogger("AURA.OnlineAI")


class OnlineProvider(AIProviderBase):
    """Online AI provider connecting to standard OpenAI-compatible chat endpoints."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_availability(self) -> Tuple[bool, str]:
        """Check if API key is present and endpoint is reachable."""
        if not self.api_key:
            return False, "Online API key is not configured. Please add your key in Settings or .env."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AURA-AI-Assistant/1.0"
        }

        # Check /models or quick ping
        models_endpoint = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(models_endpoint, headers=headers)
                if resp.status_code == 200:
                    return True, f"Online AI operational ({self.model})."
                elif resp.status_code == 401:
                    return False, "Authentication failed: Invalid Online API key."
                elif resp.status_code == 404:
                    # Some custom endpoints don't support /models, test dummy
                    return True, f"Endpoint reachable ({self.model})."
                else:
                    return False, f"Provider responded with HTTP {resp.status_code}."
        except httpx.ConnectError:
            return False, f"Could not connect to online endpoint: {self.base_url}."
        except Exception as e:
            return False, f"Online check error: {str(e)}"

    def list_available_models(self) -> List[str]:
        """Return list of models if supported by the provider."""
        if not self.api_key:
            return [self.model]
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(f"{self.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("id") for m in data.get("data", []) if "id" in m]
        except Exception:
            pass
        return [self.model]

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """Stream or generate response from online AI provider."""
        if not self.api_key:
            raise ValueError(
                "Online API key is missing. Configure ONLINE_API_KEY in Settings or .env."
            )

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AURA-AI-Assistant/1.0",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
        }

        full_text = []

        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    if response.status_code == 401:
                        raise ValueError("Online AI request failed: Invalid API Key (HTTP 401).")
                    elif response.status_code == 429:
                        raise RuntimeError("Online AI rate limit exceeded or quota exhausted (HTTP 429).")
                    elif response.status_code != 200:
                        err_body = response.read().decode("utf-8", errors="replace")
                        raise RuntimeError(f"Online AI HTTP error ({response.status_code}): {err_body}")

                    for line in response.iter_lines():
                        if cancel_check and cancel_check():
                            logger.info("Generation cancelled by user.")
                            break
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[len("data: "):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                full_text.append(delta)
                                if stream_callback:
                                    stream_callback(delta)
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to online AI endpoint: {self.base_url}")
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(f"Online AI connection error: {str(e)}")

        return "".join(full_text)
