import pytest
from pathlib import Path
from app.database.database import DatabaseService
from app.core.automation_service import AutomationService


@pytest.fixture
def automation_svc(tmp_path: Path):
    db = DatabaseService(tmp_path / "test_auto.db")
    return AutomationService(db)


def test_allowlist_enforcement(automation_svc: AutomationService):
    # Permitted action
    res = automation_svc.execute_action("system_info", {})
    assert res.get("success") is True
    assert "cpu_usage_percent" in res.get("result")

    # Forbidden action
    res_bad = automation_svc.execute_action("format_hard_drive", {})
    assert res_bad.get("success") is False
    assert "not in the approved automation allowlist" in res_bad.get("error")


def test_emergency_stop_circuit(automation_svc: AutomationService):
    automation_svc.trigger_emergency_stop()
    assert automation_svc.is_emergency_stopped is True

    # Action must be denied
    res = automation_svc.execute_action("system_info", {})
    assert res.get("success") is False
    assert "emergency stop is active" in res.get("error").lower()

    # Reset
    automation_svc.reset_emergency_stop()
    assert automation_svc.is_emergency_stopped is False
    res2 = automation_svc.execute_action("system_info", {})
    assert res2.get("success") is True


def test_create_note_action(automation_svc: AutomationService, tmp_path: Path):
    from app.config import config
    config.notes_dir = tmp_path / "notes"
    config.notes_dir.mkdir(parents=True, exist_ok=True)

    params = {"title": "Test Briefing", "content": "Telemetry nominal."}
    res = automation_svc.execute_action("create_note", params, user_confirmed=True)
    assert res.get("success") is True

    created_files = list(config.notes_dir.glob("Test_Briefing_*.txt"))
    assert len(created_files) == 1
    content = created_files[0].read_text(encoding="utf-8")
    assert "Telemetry nominal." in content


def test_url_validation(automation_svc: AutomationService):
    # Invalid protocol
    res_bad = automation_svc.execute_action("open_website", {"url": "file:///c:/secret.txt"})
    assert res_bad.get("success") is False
    assert "http" in res_bad.get("error").lower()
