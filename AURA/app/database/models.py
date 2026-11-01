from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class ConversationRecord:
    id: str
    title: str
    created_at: str
    updated_at: str
    pinned: bool = False
    archived: bool = False


@dataclass
class MessageRecord:
    id: str
    conversation_id: str
    role: str  # "user", "assistant", "system"
    content: str
    created_at: str
    status: str = "completed"  # "completed", "error", "cancelled"
    metadata_json: Optional[str] = None


@dataclass
class MemoryRecord:
    id: str
    key: str
    content: str
    category: str  # "preference", "fact", "custom"
    created_at: str
    updated_at: str
    source_conversation_id: Optional[str] = None


@dataclass
class DocumentRecord:
    id: str
    filename: str
    file_path: str
    file_type: str  # "pdf", "docx", "txt"
    file_size: int
    extracted_text: str
    summary: Optional[str] = None
    created_at: str = ""


@dataclass
class ReminderRecord:
    id: str
    title: str
    description: str
    due_date: str  # ISO-8601 string
    status: str  # "pending", "completed", "dismissed"
    recurrence: Optional[str] = None
    created_at: str = ""
    notified_at: Optional[str] = None


@dataclass
class AuditEventRecord:
    id: str
    action_name: str
    parameters: str
    status: str  # "requested", "approved", "denied", "executed", "failed"
    result: Optional[str] = None
    timestamp: str = ""
    error_message: Optional[str] = None
