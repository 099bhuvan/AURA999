import pytest
from app.core.ai_manager import AIManager
from app.core.online_provider import OnlineProvider
from app.core.ollama_provider import OllamaProvider


def test_missing_online_credentials():
    """Verify clean exception when online key is missing."""
    online = OnlineProvider(api_key="", base_url="https://api.openai.com/v1")
    ok, msg = online.check_availability()
    assert not ok
    assert "not configured" in msg.lower() or "missing" in msg.lower()

    with pytest.raises(ValueError) as exc:
        online.generate_response([{"role": "user", "content": "hi"}])
    assert "missing" in str(exc.value).lower()


def test_ollama_unavailable_behavior():
    """Verify clear error when Ollama daemon is unreachable."""
    ollama = OllamaProvider(base_url="http://localhost:99999", model="llama3.2")
    ok, msg = ollama.check_availability()
    assert not ok
    assert "not reachable" in msg.lower() or "check failed" in msg.lower()

    with pytest.raises(RuntimeError) as exc:
        ollama.generate_response([{"role": "user", "content": "hi"}])
    assert "cannot connect to ollama" in str(exc.value).lower()


def test_ai_manager_system_prompt_builder():
    mgr = AIManager()
    memories = ["User prefers dark theme", "Primary language is Python"]
    doc_context = "Project Alpha is a satellite communication platform."

    prompt = mgr.build_system_prompt(memories=memories, document_context=doc_context)
    assert "AURA" in prompt or "assistant" in prompt
    assert "User prefers dark theme" in prompt
    assert "satellite communication platform" in prompt


def test_ai_manager_offline_mode_resolution():
    mgr = AIManager()
    mgr.mode = "offline"
    # Point to invalid Ollama
    mgr.ollama.base_url = "http://localhost:59999"

    with pytest.raises(RuntimeError) as exc:
        mgr.resolve_provider()
    assert "offline mode active, but local ollama is unavailable" in str(exc.value).lower()


def test_ai_manager_online_mode_resolution():
    mgr = AIManager()
    mgr.mode = "online"
    mgr.online.api_key = ""

    with pytest.raises(RuntimeError) as exc:
        mgr.resolve_provider()
    assert "online mode active, but provider is unavailable" in str(exc.value).lower()
