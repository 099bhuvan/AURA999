import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.config import config
from app.database.migrations import run_migrations
from app.database.models import (
    ConversationRecord,
    MessageRecord,
    MemoryRecord,
    DocumentRecord,
    ReminderRecord,
    AuditEventRecord,
)


def get_utc_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


class DatabaseService:
    """SQLite Database Service providing thread-safe operations and repository methods."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else config.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=15.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def init_database(self):
        """Run migrations on startup."""
        with self.get_connection() as conn:
            run_migrations(conn)

    # -------------------------------------------------------------------------
    # Settings CRUD
    # -------------------------------------------------------------------------
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value, now))
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # -------------------------------------------------------------------------
    # Conversations CRUD
    # -------------------------------------------------------------------------
    def create_conversation(self, title: str = "New Conversation") -> ConversationRecord:
        conv_id = str(uuid.uuid4())
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (id, title, created_at, updated_at, pinned, archived)
                VALUES (?, ?, ?, ?, 0, 0)
            """, (conv_id, title, now, now))
            conn.commit()
        return ConversationRecord(
            id=conv_id,
            title=title,
            created_at=now,
            updated_at=now,
            pinned=False,
            archived=False
        )

    def list_conversations(self, include_archived: bool = False) -> List[ConversationRecord]:
        query = "SELECT id, title, created_at, updated_at, pinned, archived FROM conversations"
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY pinned DESC, updated_at DESC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [
                ConversationRecord(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    pinned=bool(row["pinned"]),
                    archived=bool(row["archived"]),
                )
                for row in cursor.fetchall()
            ]

    def get_conversation(self, conv_id: str) -> Optional[ConversationRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at, updated_at, pinned, archived FROM conversations WHERE id = ?",
                (conv_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ConversationRecord(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                pinned=bool(row["pinned"]),
                archived=bool(row["archived"]),
            )

    def update_conversation_title(self, conv_id: str, title: str):
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conv_id)
            )
            conn.commit()

    def delete_conversation(self, conv_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Messages CRUD
    # -------------------------------------------------------------------------
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageRecord:
        msg_id = str(uuid.uuid4())
        now = get_utc_iso()
        meta_json = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, created_at, status, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (msg_id, conversation_id, role, content, now, status, meta_json))
            # Also touch conversation updated_at
            cursor.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
            conn.commit()
        return MessageRecord(
            id=msg_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=now,
            status=status,
            metadata_json=meta_json
        )

    def list_messages(self, conversation_id: str) -> List[MessageRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, conversation_id, role, content, created_at, status, metadata_json
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """, (conversation_id,))
            return [
                MessageRecord(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                    status=row["status"],
                    metadata_json=row["metadata_json"]
                )
                for row in cursor.fetchall()
            ]

    # -------------------------------------------------------------------------
    # Memories CRUD
    # -------------------------------------------------------------------------
    def add_memory(
        self,
        key: str,
        content: str,
        category: str = "fact",
        source_conversation_id: Optional[str] = None
    ) -> MemoryRecord:
        mem_id = str(uuid.uuid4())
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (id, key, content, category, created_at, updated_at, source_conversation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mem_id, key, content, category, now, now, source_conversation_id))
            conn.commit()
        return MemoryRecord(
            id=mem_id,
            key=key,
            content=content,
            category=category,
            created_at=now,
            updated_at=now,
            source_conversation_id=source_conversation_id
        )

    def list_memories(self, category: Optional[str] = None) -> List[MemoryRecord]:
        query = "SELECT id, key, content, category, created_at, updated_at, source_conversation_id FROM memories"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY updated_at DESC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [
                MemoryRecord(
                    id=row["id"],
                    key=row["key"],
                    content=row["content"],
                    category=row["category"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    source_conversation_id=row["source_conversation_id"]
                )
                for row in cursor.fetchall()
            ]

    def search_memories(self, query_str: str) -> List[MemoryRecord]:
        like_pattern = f"%{query_str.strip()}%"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, key, content, category, created_at, updated_at, source_conversation_id
                FROM memories
                WHERE key LIKE ? OR content LIKE ?
                ORDER BY updated_at DESC
            """, (like_pattern, like_pattern))
            return [
                MemoryRecord(
                    id=row["id"],
                    key=row["key"],
                    content=row["content"],
                    category=row["category"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    source_conversation_id=row["source_conversation_id"]
                )
                for row in cursor.fetchall()
            ]

    def update_memory(self, memory_id: str, key: str, content: str, category: str):
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories
                SET key = ?, content = ?, category = ?, updated_at = ?
                WHERE id = ?
            """, (key, content, category, now, memory_id))
            conn.commit()

    def delete_memory(self, memory_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()

    def clear_all_memories(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories")
            conn.commit()

    # -------------------------------------------------------------------------
    # Documents Metadata CRUD
    # -------------------------------------------------------------------------
    def add_document(
        self,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        extracted_text: str,
        summary: Optional[str] = None
    ) -> DocumentRecord:
        doc_id = str(uuid.uuid4())
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (id, filename, file_path, file_type, file_size, extracted_text, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, filename, file_path, file_type, file_size, extracted_text, summary, now))
            conn.commit()
        return DocumentRecord(
            id=doc_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text,
            summary=summary,
            created_at=now
        )

    def list_documents(self, limit: int = 50) -> List[DocumentRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_type, file_size, extracted_text, summary, created_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [
                DocumentRecord(
                    id=row["id"],
                    filename=row["filename"],
                    file_path=row["file_path"],
                    file_type=row["file_type"],
                    file_size=row["file_size"],
                    extracted_text=row["extracted_text"],
                    summary=row["summary"],
                    created_at=row["created_at"]
                )
                for row in cursor.fetchall()
            ]

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, file_path, file_type, file_size, extracted_text, summary, created_at
                FROM documents
                WHERE id = ?
            """, (doc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentRecord(
                id=row["id"],
                filename=row["filename"],
                file_path=row["file_path"],
                file_type=row["file_type"],
                file_size=row["file_size"],
                extracted_text=row["extracted_text"],
                summary=row["summary"],
                created_at=row["created_at"]
            )

    def delete_document(self, doc_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Reminders CRUD
    # -------------------------------------------------------------------------
    def add_reminder(
        self,
        title: str,
        due_date: str,
        description: str = "",
        recurrence: Optional[str] = None
    ) -> ReminderRecord:
        rem_id = str(uuid.uuid4())
        now = get_utc_iso()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (id, title, description, due_date, status, recurrence, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """, (rem_id, title, description, due_date, recurrence, now))
            conn.commit()
        return ReminderRecord(
            id=rem_id,
            title=title,
            description=description,
            due_date=due_date,
            status="pending",
            recurrence=recurrence,
            created_at=now
        )

    def list_reminders(self, status: Optional[str] = None) -> List[ReminderRecord]:
        query = "SELECT id, title, description, due_date, status, recurrence, created_at, notified_at FROM reminders"
        params = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY due_date ASC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [
                ReminderRecord(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    due_date=row["due_date"],
                    status=row["status"],
                    recurrence=row["recurrence"],
                    created_at=row["created_at"],
                    notified_at=row["notified_at"]
                )
                for row in cursor.fetchall()
            ]

    def update_reminder_status(self, rem_id: str, status: str, notified_at: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if notified_at:
                cursor.execute(
                    "UPDATE reminders SET status = ?, notified_at = ? WHERE id = ?",
                    (status, notified_at, rem_id)
                )
            else:
                cursor.execute(
                    "UPDATE reminders SET status = ? WHERE id = ?",
                    (status, rem_id)
                )
            conn.commit()

    def update_reminder(self, rem_id: str, title: str, description: str, due_date: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders
                SET title = ?, description = ?, due_date = ?
                WHERE id = ?
            """, (title, description, due_date, rem_id))
            conn.commit()

    def delete_reminder(self, rem_id: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Automation Audit Events
    # -------------------------------------------------------------------------
    def log_audit_event(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AuditEventRecord:
        event_id = str(uuid.uuid4())
        now = get_utc_iso()
        param_str = json.dumps(parameters)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO automation_audit (id, action_name, parameters, status, result, timestamp, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_id, action_name, param_str, status, result, now, error_message))
            conn.commit()
        return AuditEventRecord(
            id=event_id,
            action_name=action_name,
            parameters=param_str,
            status=status,
            result=result,
            timestamp=now,
            error_message=error_message
        )

    def list_audit_events(self, limit: int = 100) -> List[AuditEventRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, action_name, parameters, status, result, timestamp, error_message
                FROM automation_audit
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [
                AuditEventRecord(
                    id=row["id"],
                    action_name=row["action_name"],
                    parameters=row["parameters"],
                    status=row["status"],
                    result=row["result"],
                    timestamp=row["timestamp"],
                    error_message=row["error_message"]
                )
                for row in cursor.fetchall()
            ]


_db_instance: Optional[DatabaseService] = None


def get_db() -> DatabaseService:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
    return _db_instance
