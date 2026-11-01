import sqlite3
import logging

logger = logging.getLogger("AURA.Database")

MIGRATIONS = [
    # Version 1: Initial Core Schema
    (1, """
    -- Settings table
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    -- Conversations table
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        pinned INTEGER DEFAULT 0,
        archived INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);

    -- Messages table
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'completed',
        metadata_json TEXT,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at ASC);

    -- Memories table
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        key TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'fact',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        source_conversation_id TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
    CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);

    -- Documents metadata table
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        extracted_text TEXT NOT NULL,
        summary TEXT,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC);

    -- Reminders table
    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        recurrence TEXT,
        created_at TEXT NOT NULL,
        notified_at TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_reminders_due_status ON reminders(status, due_date ASC);

    -- Automation Audit Events table
    CREATE TABLE IF NOT EXISTS automation_audit (
        id TEXT PRIMARY KEY,
        action_name TEXT NOT NULL,
        parameters TEXT NOT NULL,
        status TEXT NOT NULL,
        result TEXT,
        timestamp TEXT NOT NULL,
        error_message TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_automation_timestamp ON automation_audit(timestamp DESC);
    """)
]


def run_migrations(conn: sqlite3.Connection):
    """Execute pending schema migrations in an atomic transaction."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()

    cursor.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in cursor.fetchall()}

    for version, script in MIGRATIONS:
        if version not in applied_versions:
            logger.info("Applying database migration version %d...", version)
            try:
                cursor.executescript(script)
                cursor.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
                    (version,)
                )
                conn.commit()
                logger.info("Successfully applied database migration version %d.", version)
            except Exception as e:
                conn.rollback()
                logger.error("Failed to apply migration version %d: %s", version, e)
                raise
