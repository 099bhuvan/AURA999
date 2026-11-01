from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple


class AIProviderBase(ABC):
    """Abstract base class for all AI model providers in AURA."""

    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        stream_callback: Optional[Callable[[str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """Generate response from AI provider.
        
        Args:
            messages: List of {'role': 'user'|'assistant'|'system', 'content': str}
            stream_callback: Function called with each streaming token/delta chunk
            cancel_check: Function returning True if generation should abort
            
        Returns:
            The complete generated response string
        """
        pass

    @abstractmethod
    def check_availability(self) -> Tuple[bool, str]:
        """Check if provider endpoint and model are currently reachable and operational."""
        pass

    @abstractmethod
    def list_available_models(self) -> List[str]:
        """Return list of models available through this provider."""
        pass
