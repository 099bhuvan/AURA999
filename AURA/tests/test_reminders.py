import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.database.database import DatabaseService
from app.core.reminder_service import ReminderService


@pytest.fixture
def reminder_svc(tmp_path: Path):
    db = DatabaseService(tmp_path / "test_rem.db")
    svc = ReminderService(db)
    svc.sound_enabled = False
    return svc


def test_add_and_list_reminders(reminder_svc: ReminderService):
    future_dt = (datetime.now() + timedelta(hours=2)).isoformat()
    rem = reminder_svc.add_reminder("Sync with team", future_dt, description="Discuss architecture")

    assert rem.id is not None
    assert rem.status == "pending"

    all_rems = reminder_svc.list_all()
    assert len(all_rems) == 1
    assert all_rems[0].title == "Sync with team"


def test_upcoming_and_overdue_categorization(reminder_svc: ReminderService):
    past_dt = (datetime.now() - timedelta(minutes=15)).isoformat()
    future_dt = (datetime.now() + timedelta(hours=5)).isoformat()

    reminder_svc.add_reminder("Past Task", past_dt)
    reminder_svc.add_reminder("Future Task", future_dt)

    upcoming = reminder_svc.get_upcoming()
    overdue = reminder_svc.get_overdue()

    assert any(r.title == "Future Task" for r in upcoming)
    assert any(r.title == "Past Task" for r in overdue)


def test_complete_and_delete_reminder(reminder_svc: ReminderService):
    future_dt = (datetime.now() + timedelta(hours=1)).isoformat()
    rem = reminder_svc.add_reminder("To complete", future_dt)

    reminder_svc.mark_completed(rem.id)
    all_rems = reminder_svc.list_all()
    completed = [r for r in all_rems if r.id == rem.id]
    assert completed[0].status == "completed"

    reminder_svc.delete_reminder(rem.id)
    assert len(reminder_svc.list_all()) == 0


def test_startup_recovery(reminder_svc: ReminderService):
    """Test that past pending reminders trigger during recovery."""
    triggered = []

    def mock_cb(r):
        triggered.append(r.id)

    reminder_svc.register_notification_callback(mock_cb)

    past_dt = (datetime.now() - timedelta(hours=3)).isoformat()
    rem = reminder_svc.db.add_reminder("Missed task while offline", past_dt)

    reminder_svc.recover_pending_reminders()
    assert rem.id in triggered
