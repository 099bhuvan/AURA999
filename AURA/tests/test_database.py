import pytest
from pathlib import Path
from app.database.database import DatabaseService


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_aura.db"
    return DatabaseService(db_file)


def test_database_initialization(temp_db: DatabaseService):
    """Test schema creation and migration versioning."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations")
        versions = [row[0] for row in cursor.fetchall()]
        assert 1 in versions


def test_settings_storage(temp_db: DatabaseService):
    """Test setting and retrieving application configuration."""
    assert temp_db.get_setting("non_existent") is None
    assert temp_db.get_setting("assistant_name", "AURA") == "AURA"

    temp_db.set_setting("assistant_name", "JARVIS")
    assert temp_db.get_setting("assistant_name") == "JARVIS"

    # Update existing setting
    temp_db.set_setting("assistant_name", "AURA_V2")
    assert temp_db.get_setting("assistant_name") == "AURA_V2"


def test_conversation_and_message_crud(temp_db: DatabaseService):
    """Test conversation creation, message threading, and deletion."""
    conv = temp_db.create_conversation("Project Apollo")
    assert conv.id is not None
    assert conv.title == "Project Apollo"

    # Add messages
    m1 = temp_db.add_message(conv.id, role="user", content="Hello AURA")
    m2 = temp_db.add_message(conv.id, role="assistant", content="Greetings Commander.")

    msgs = temp_db.list_messages(conv.id)
    assert len(msgs) == 2
    assert msgs[0].content == "Hello AURA"
    assert msgs[1].content == "Greetings Commander."

    # Rename
    temp_db.update_conversation_title(conv.id, "Project Artemis")
    updated = temp_db.get_conversation(conv.id)
    assert updated.title == "Project Artemis"

    # Delete conversation and ensure cascading message deletion
    temp_db.delete_conversation(conv.id)
    assert temp_db.get_conversation(conv.id) is None
    assert len(temp_db.list_messages(conv.id)) == 0


def test_audit_logging(temp_db: DatabaseService):
    """Test automation audit event recording."""
    event = temp_db.log_audit_event(
        action_name="open_application",
        parameters={"app_name": "notepad"},
        status="executed",
        result="Launched notepad.exe"
    )
    assert event.id is not None
    assert event.status == "executed"

    events = temp_db.list_audit_events()
    assert len(events) >= 1
    assert events[0].action_name == "open_application"
