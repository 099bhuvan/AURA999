import re
from typing import List, Optional, Set
from app.database import get_db, DatabaseService
from app.database.models import MemoryRecord


class MemoryService:
    """Dedicated service for managing user-approved long-term memories."""

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or get_db()
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        val = self.db.get_setting("memory_enabled", "true")
        return val.lower() in ("true", "1", "yes")

    def set_enabled(self, enabled: bool):
        self.db.set_setting("memory_enabled", "true" if enabled else "false")

    def add_memory(
        self,
        key: str,
        content: str,
        category: str = "fact",
        source_conversation_id: Optional[str] = None
    ) -> MemoryRecord:
        """Store an explicitly user-approved memory."""
        cleaned_key = key.strip()
        cleaned_content = content.strip()
        if not cleaned_key:
            raise ValueError("Memory key cannot be empty.")
        if not cleaned_content:
            raise ValueError("Memory content cannot be empty.")
        return self.db.add_memory(
            key=cleaned_key,
            content=cleaned_content,
            category=category,
            source_conversation_id=source_conversation_id
        )

    def list_memories(self, category: Optional[str] = None) -> List[MemoryRecord]:
        return self.db.list_memories(category=category)

    def search_memories(self, query: str) -> List[MemoryRecord]:
        if not query or not query.strip():
            return self.list_memories()
        return self.db.search_memories(query.strip())

    def update_memory(self, memory_id: str, key: str, content: str, category: str):
        if not key.strip() or not content.strip():
            raise ValueError("Memory key and content cannot be blank.")
        self.db.update_memory(memory_id, key.strip(), content.strip(), category)

    def delete_memory(self, memory_id: str):
        self.db.delete_memory(memory_id)

    def clear_all(self):
        """Purge all stored memories upon explicit user request."""
        self.db.clear_all_memories()

    def get_relevant_memories(self, user_text: str, max_results: int = 5) -> List[str]:
        """Retrieve relevant memories matching keywords in user text for context injection."""
        if not self.is_enabled:
            return []

        all_memories = self.list_memories()
        if not all_memories:
            return []

        # Extract search words (length >= 3)
        words: Set[str] = set(re.findall(r"\b\w{3,}\b", user_text.lower()))
        if not words:
            # Return general user preferences by default
            prefs = [m for m in all_memories if m.category == "preference"]
            return [f"{m.key}: {m.content}" for m in prefs[:max_results]]

        scored = []
        for mem in all_memories:
            mem_text = f"{mem.key} {mem.content}".lower()
            matches = sum(1 for w in words if w in mem_text)
            if matches > 0 or mem.category == "preference":
                scored.append((matches, mem))

        # Sort by relevance match count descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f"{mem.key}: {mem.content}" for _, mem in scored[:max_results]]


memory_service = MemoryService()
