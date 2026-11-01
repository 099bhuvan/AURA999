import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil

# Ensure app root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import config
from app.database import get_db
from app.core.ai_manager import ai_manager
from app.core.memory_service import memory_service
from app.core.document_service import document_service
from app.core.reminder_service import reminder_service
from app.core.automation_service import automation_service

logger = logging.getLogger("AURA.WebServer")

app = FastAPI(title="AURA - AI Personal Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

db = get_db()


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    chat_mode: Optional[str] = "casual"


class CreateConvRequest(BaseModel):
    title: Optional[str] = "Neural Session"


class RenameConvRequest(BaseModel):
    title: str


class MemoryRequest(BaseModel):
    key: str
    content: str
    category: Optional[str] = "fact"


class ReminderRequest(BaseModel):
    title: str
    due_date: str
    description: Optional[str] = ""


class AutomationRequest(BaseModel):
    action_name: str
    parameters: Optional[Dict[str, Any]] = {}
    confirmed: Optional[bool] = False


class SettingsRequest(BaseModel):
    assistant_name: Optional[str] = None
    ai_mode: Optional[str] = None
    online_api_key: Optional[str] = None
    online_base_url: Optional[str] = None
    online_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None


# -----------------------------------------------------------------------------
# Telemetry & Status API
# -----------------------------------------------------------------------------
@app.get("/api/status")
async def get_status():
    status_ai = ai_manager.check_status()
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()

    return {
        "assistant_name": config.assistant_name,
        "ai_mode": config.ai_mode,
        "ai_status": status_ai,
        "cpu_percent": cpu_percent,
        "ram_percent": mem.percent,
        "automation_enabled": automation_service.is_enabled,
        "emergency_stop": automation_service.is_emergency_stopped,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# -----------------------------------------------------------------------------
# Conversations & Chat API
# -----------------------------------------------------------------------------
@app.get("/api/conversations")
async def list_conversations():
    convs = db.list_conversations()
    if not convs:
        c = db.create_conversation("Primary Session")
        convs = [c]
    return [
        {"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at}
        for c in convs
    ]


@app.post("/api/conversations")
async def create_conversation(req: CreateConvRequest):
    c = db.create_conversation(req.title or "Neural Session")
    return {"id": c.id, "title": c.title, "created_at": c.created_at}


@app.put("/api/conversations/{conv_id}")
async def rename_conversation(conv_id: str, req: RenameConvRequest):
    db.update_conversation_title(conv_id, req.title)
    return {"success": True}


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    db.delete_conversation(conv_id)
    return {"success": True}


@app.get("/api/messages/{conv_id}")
async def get_messages(conv_id: str):
    msgs = db.list_messages(conv_id)
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at, "status": m.status}
        for m in msgs
    ]


@app.post("/api/chat")
async def chat_message(req: ChatRequest):
    """Save user message, retrieve memories, and generate AI response."""
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be blank.")

    # Save user message
    db.add_message(req.conversation_id, role="user", content=user_text)

    # Context memories
    memories = memory_service.get_relevant_memories(user_text)

    # Build messages
    msgs = db.list_messages(req.conversation_id)
    msg_history = [{"role": m.role, "content": m.content} for m in msgs]

    try:
        reply_text, provider_type = ai_manager.generate(
            messages=msg_history,
            memories=memories,
            chat_mode=req.chat_mode or "casual"
        )
        msg_record = db.add_message(req.conversation_id, role="assistant", content=reply_text)
        return {
            "success": True,
            "reply": reply_text,
            "provider": provider_type,
            "message_id": msg_record.id
        }
    except Exception as e:
        logger.error("Chat generation error: %s", e)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# -----------------------------------------------------------------------------
# Long-Term Memory API
# -----------------------------------------------------------------------------
@app.get("/api/memories")
async def list_memories(search: Optional[str] = None):
    mems = memory_service.search_memories(search or "")
    return [
        {"id": m.id, "key": m.key, "content": m.content, "category": m.category, "updated_at": m.updated_at}
        for m in mems
    ]


@app.post("/api/memories")
async def add_memory(req: MemoryRequest):
    mem = memory_service.add_memory(req.key, req.content, req.category or "fact")
    return {"id": mem.id, "key": mem.key, "content": mem.content, "category": mem.category}


@app.put("/api/memories/{mem_id}")
async def update_memory(mem_id: str, req: MemoryRequest):
    memory_service.update_memory(mem_id, req.key, req.content, req.category or "fact")
    return {"success": True}


@app.delete("/api/memories/{mem_id}")
async def delete_memory(mem_id: str):
    memory_service.delete_memory(mem_id)
    return {"success": True}


@app.delete("/api/memories")
async def clear_memories():
    memory_service.clear_all()
    return {"success": True}


# -----------------------------------------------------------------------------
# Document Intelligence API
# -----------------------------------------------------------------------------
@app.get("/api/documents")
async def list_documents():
    docs = document_service.list_documents()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "summary": d.summary,
            "created_at": d.created_at,
            "preview": d.extracted_text[:300]
        }
        for d in docs
    ]


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    temp_dir = config.docs_dir
    temp_path = temp_dir / file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:
        doc = document_service.ingest_document(str(temp_path))
        return {
            "success": True,
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "summary": doc.summary
        }
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/documents/{doc_id}/summarize")
async def summarize_document(doc_id: str):
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    summary = document_service.summarize_document(doc)
    return {"summary": summary}


@app.post("/api/documents/{doc_id}/qa")
async def qa_document(doc_id: str, req: BaseModel):
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    question = getattr(req, "question", "")
    ans = document_service.answer_question(doc, question)
    return {"answer": ans}


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    document_service.delete_document(doc_id)
    return {"success": True}


# -----------------------------------------------------------------------------
# Smart Reminders API
# -----------------------------------------------------------------------------
@app.get("/api/reminders")
async def list_reminders():
    all_rems = reminder_service.list_all()
    upcoming = reminder_service.get_upcoming()
    overdue = reminder_service.get_overdue()
    return {
        "all": [{"id": r.id, "title": r.title, "due_date": r.due_date, "status": r.status, "description": r.description} for r in all_rems],
        "upcoming": [{"id": r.id, "title": r.title, "due_date": r.due_date, "status": r.status} for r in upcoming],
        "overdue": [{"id": r.id, "title": r.title, "due_date": r.due_date, "status": r.status} for r in overdue]
    }


@app.post("/api/reminders")
async def add_reminder(req: ReminderRequest):
    r = reminder_service.add_reminder(req.title, req.due_date, req.description or "")
    return {"id": r.id, "title": r.title, "due_date": r.due_date, "status": r.status}


@app.put("/api/reminders/{rem_id}/complete")
async def complete_reminder(rem_id: str):
    reminder_service.mark_completed(rem_id)
    return {"success": True}


@app.delete("/api/reminders/{rem_id}")
async def delete_reminder(rem_id: str):
    reminder_service.delete_reminder(rem_id)
    return {"success": True}


# -----------------------------------------------------------------------------
# Controlled Desktop Automation API
# -----------------------------------------------------------------------------
@app.get("/api/automation/audit")
async def list_automation_audit():
    events = db.list_audit_events(limit=50)
    return [
        {
            "id": e.id,
            "action_name": e.action_name,
            "parameters": e.parameters,
            "status": e.status,
            "result": e.result or e.error_message,
            "timestamp": e.timestamp
        }
        for e in events
    ]


@app.post("/api/automation/execute")
async def execute_automation(req: AutomationRequest):
    res = automation_service.execute_action(
        req.action_name,
        req.parameters or {},
        user_confirmed=req.confirmed or False
    )
    return res


@app.post("/api/automation/emergency-stop")
async def emergency_stop(active: bool = True):
    if active:
        automation_service.trigger_emergency_stop()
    else:
        automation_service.reset_emergency_stop()
    return {"emergency_stopped": automation_service.is_emergency_stopped}


# -----------------------------------------------------------------------------
# System & AI Settings API
# -----------------------------------------------------------------------------
@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    if req.assistant_name:
        config.assistant_name = req.assistant_name.strip()
        db.set_setting("assistant_name", config.assistant_name)

    if req.ai_mode:
        config.ai_mode = req.ai_mode
        db.set_setting("ai_mode", config.ai_mode)

    ai_manager.update_config(
        mode=req.ai_mode,
        ollama_base_url=req.ollama_base_url,
        ollama_model=req.ollama_model,
        online_api_key=req.online_api_key,
        online_base_url=req.online_base_url,
        online_model=req.online_model
    )

    return {"success": True, "assistant_name": config.assistant_name, "ai_mode": config.ai_mode}


# -----------------------------------------------------------------------------
# Root Web Application Serving
# -----------------------------------------------------------------------------
@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>AURA Neural Server Active. Static files loading...</h2>")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
