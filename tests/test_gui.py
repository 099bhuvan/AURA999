import os
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.config import config
from app.ui.main_window import MainWindow
from app.ui.widgets.aura_core import AuraCoreWidget


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single offscreen QApplication instance for tests."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_creation(qapp):
    """Test full MainWindow initialization, page stacking, and navigation."""
    window = MainWindow()
    assert window is not None
    assert window.pages_stack.count() == 8

    # Test navigation to Chat (index 1)
    window._on_navigate_page(1)
    assert window.pages_stack.currentIndex() == 1

    # Test navigation to Voice (index 2)
    window._on_navigate_page(2)
    assert window.pages_stack.currentIndex() == 2

    # Test navigation to Automation (index 6)
    window._on_navigate_page(6)
    assert window.pages_stack.currentIndex() == 6

    # Test assistant name rename signal
    window._on_assistant_name_changed("JARVIS")
    assert "JARVIS" in window.windowTitle()
    assert window.status_header.name_badge.text() == "◈ JARVIS"

    # Reset
    window._on_assistant_name_changed("AURA")

    # Clean shutdown
    window.close()


def test_aura_core_widget_states(qapp):
    """Test AURA Core widget states and reduced motion."""
    core = AuraCoreWidget(size=200)
    assert core.state == AuraCoreWidget.STATE_IDLE

    core.set_state(AuraCoreWidget.STATE_THINKING)
    assert core.state == AuraCoreWidget.STATE_THINKING

    core.set_state(AuraCoreWidget.STATE_LISTENING)
    assert core.state == AuraCoreWidget.STATE_LISTENING

    core.set_state(AuraCoreWidget.STATE_SPEAKING)
    assert core.state == AuraCoreWidget.STATE_SPEAKING

    core.set_state(AuraCoreWidget.STATE_ERROR)
    assert core.state == AuraCoreWidget.STATE_ERROR

    core.set_audio_level(0.75)
    assert core.target_audio_level == 0.75

    core.set_reduced_motion(True)
    assert core.reduced_motion is True
