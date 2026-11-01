import pytest
from pathlib import Path
from app.database.database import DatabaseService
from app.core.memory_service import MemoryService


@pytest.fixture
def memory_svc(tmp_path: Path):
    db = DatabaseService(tmp_path / "test_mem.db")
    return MemoryService(db)


def test_memory_add_and_list(memory_svc: MemoryService):
    mem = memory_svc.add_memory("Favorite Color", "Deep Electric Cyan", category="preference")
    assert mem.id is not None
    assert mem.key == "Favorite Color"

    all_mems = memory_svc.list_memories()
    assert len(all_mems) == 1
    assert all_mems[0].content == "Deep Electric Cyan"


def test_memory_search(memory_svc: MemoryService):
    memory_svc.add_memory("Python Version", "Prefers Python 3.12 with PySide6", category="fact")
    memory_svc.add_memory("Coffee", "Prefers dark espresso with oat milk", category="preference")

    results = memory_svc.search_memories("Python")
    assert len(results) == 1
    assert results[0].key == "Python Version"

    results_espresso = memory_svc.search_memories("espresso")
    assert len(results_espresso) == 1
    assert results_espresso[0].key == "Coffee"


def test_memory_update_and_delete(memory_svc: MemoryService):
    mem = memory_svc.add_memory("Editor", "VS Code", category="preference")
    memory_svc.update_memory(mem.id, "Editor", "Cursor IDE", category="preference")

    updated = memory_svc.search_memories("Cursor")
    assert len(updated) == 1
    assert updated[0].content == "Cursor IDE"

    memory_svc.delete_memory(mem.id)
    assert len(memory_svc.list_memories()) == 0


def test_memory_relevant_retrieval(memory_svc: MemoryService):
    memory_svc.add_memory("OS", "Windows 11 Professional Workstation", category="fact")
    memory_svc.add_memory("Language", "Prefers Python exclusively", category="preference")

    relevant = memory_svc.get_relevant_memories("How do I configure audio on Windows?")
    assert any("Windows" in r for r in relevant)


def test_memory_clear_all(memory_svc: MemoryService):
    memory_svc.add_memory("Item 1", "Fact 1")
    memory_svc.add_memory("Item 2", "Fact 2")
    assert len(memory_svc.list_memories()) == 2

    memory_svc.clear_all()
    assert len(memory_svc.list_memories()) == 0
