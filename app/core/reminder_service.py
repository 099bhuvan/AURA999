import logging
import sys
from datetime import datetime, timezone
from typing import List, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from app.database import get_db, DatabaseService
from app.database.models import ReminderRecord

logger = logging.getLogger("AURA.Reminders")


def play_alert_sound():
    """Play alert sound on Windows systems if available."""
    try:
        if sys.platform == "win32":
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


class ReminderService:
    """Smart Reminder Service with APScheduler and SQLite persistence."""

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or get_db()
        self.scheduler = BackgroundScheduler()
        self.notification_callback: Optional[Callable[[ReminderRecord], None]] = None
        self.sound_enabled: bool = True
        self._started = False

    def start(self):
        """Start scheduler and perform startup recovery."""
        if not self._started:
            self.scheduler.start()
            self._started = True
            self.recover_pending_reminders()

    def stop(self):
        if self._started:
            self.scheduler.shutdown(wait=False)
            self._started = False

    def register_notification_callback(self, callback: Callable[[ReminderRecord], None]):
        self.notification_callback = callback

    def add_reminder(
        self,
        title: str,
        due_date_iso: str,
        description: str = "",
        recurrence: Optional[str] = None
    ) -> ReminderRecord:
        """Create a new reminder and schedule notification job."""
        record = self.db.add_reminder(
            title=title.strip(),
            due_date=due_date_iso,
            description=description.strip(),
            recurrence=recurrence
        )
        self._schedule_job(record)
        return record

    def _schedule_job(self, record: ReminderRecord):
        """Schedule a background execution job for this reminder."""
        try:
            # Parse due date (supporting ISO format with or without timezone)
            due_dt = datetime.fromisoformat(record.due_date)
            # If naive, assume local time
            now = datetime.now() if due_dt.tzinfo is None else datetime.now(timezone.utc)
            
            if due_dt <= now:
                # Already overdue, trigger immediately
                self._trigger_reminder(record.id)
            else:
                self.scheduler.add_job(
                    func=self._trigger_reminder,
                    trigger=DateTrigger(run_date=due_dt),
                    args=[record.id],
                    id=f"rem_{record.id}",
                    replace_existing=True
                )
        except Exception as e:
            logger.error("Failed to schedule reminder '%s': %s", record.title, e)

    def _trigger_reminder(self, reminder_id: str):
        """Called by APScheduler when reminder is due."""
        reminders = self.db.list_reminders()
        record = next((r for r in reminders if r.id == reminder_id), None)
        if not record or record.status != "pending":
            return

        now_iso = datetime.now().isoformat()
        self.db.update_reminder_status(reminder_id, status="notified", notified_at=now_iso)
        record.status = "notified"
        record.notified_at = now_iso

        if self.sound_enabled:
            play_alert_sound()

        if self.notification_callback:
            try:
                self.notification_callback(record)
            except Exception as e:
                logger.error("Error invoking reminder notification callback: %s", e)

    def recover_pending_reminders(self):
        """Startup recovery: inspect pending reminders from past and schedule future ones."""
        reminders = self.db.list_reminders(status="pending")
        now = datetime.now()
        for r in reminders:
            try:
                due_dt = datetime.fromisoformat(r.due_date)
                if due_dt.tzinfo is not None:
                    # Compare timezone-aware
                    now_tz = datetime.now(timezone.utc)
                    is_overdue = due_dt <= now_tz
                else:
                    is_overdue = due_dt <= now

                if is_overdue:
                    logger.info("Startup recovery: Overdue reminder found: '%s'", r.title)
                    self._trigger_reminder(r.id)
                else:
                    self._schedule_job(r)
            except Exception as e:
                logger.warning("Error evaluating reminder %s: %s", r.id, e)

    def list_all(self) -> List[ReminderRecord]:
        return self.db.list_reminders()

    def get_upcoming(self) -> List[ReminderRecord]:
        all_rems = self.db.list_reminders(status="pending")
        now = datetime.now()
        res = []
        for r in all_rems:
            try:
                due_dt = datetime.fromisoformat(r.due_date)
                if due_dt.tzinfo is None and due_dt > now:
                    res.append(r)
                elif due_dt.tzinfo is not None and due_dt > datetime.now(timezone.utc):
                    res.append(r)
            except Exception:
                pass
        return res

    def get_overdue(self) -> List[ReminderRecord]:
        all_rems = [r for r in self.db.list_reminders() if r.status != "completed"]
        now = datetime.now()
        res = []
        for r in all_rems:
            try:
                due_dt = datetime.fromisoformat(r.due_date)
                if due_dt.tzinfo is None and due_dt <= now:
                    res.append(r)
                elif due_dt.tzinfo is not None and due_dt <= datetime.now(timezone.utc):
                    res.append(r)
            except Exception:
                pass
        return res

    def mark_completed(self, reminder_id: str):
        self.db.update_reminder_status(reminder_id, "completed")
        try:
            self.scheduler.remove_job(f"rem_{reminder_id}")
        except Exception:
            pass

    def delete_reminder(self, reminder_id: str):
        self.db.delete_reminder(reminder_id)
        try:
            self.scheduler.remove_job(f"rem_{reminder_id}")
        except Exception:
            pass


reminder_service = ReminderService()
