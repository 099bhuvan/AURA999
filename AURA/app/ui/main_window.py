import sys
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QSystemTrayIcon,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction

from app.config import config
from app.database import get_db
from app.core.ai_manager import ai_manager
from app.core.reminder_service import reminder_service
from app.core.automation_service import automation_service
from app.database.models import ReminderRecord
from app.ui.theme import Colors, get_application_stylesheet
from app.ui.widgets.sidebar import Sidebar
from app.ui.widgets.status_widget import StatusHeaderWidget
from app.ui.widgets.aura_core import AuraCoreWidget

from app.ui.pages.home_page import HomePage
from app.ui.pages.chat_page import ChatPage
from app.ui.pages.voice_page import VoicePage
from app.ui.pages.memory_page import MemoryPage
from app.ui.pages.documents_page import DocumentsPage
from app.ui.pages.reminders_page import RemindersPage
from app.ui.pages.automation_page import AutomationPage
from app.ui.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    """Main Application Window for AURA."""

    def __init__(self):
        super().__init__()
        self.db = get_db()
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._start_background_services()

    def _setup_window(self):
        self.setWindowTitle(f"{config.assistant_name.upper()} — Pure Python AI Personal Assistant")
        self.resize(1240, 820)
        self.setMinimumSize(980, 660)
        self.setStyleSheet(get_application_stylesheet())

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        root_layout.addWidget(self.sidebar)

        # 2. Right Content Area (Status Header + Stacked Pages)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Status Header Bar
        self.status_header = StatusHeaderWidget(self)
        content_layout.addWidget(self.status_header)

        # Pages Stack
        self.pages_stack = QStackedWidget(self)

        # Instantiate all 8 major sections
        self.home_page = HomePage(self)
        self.chat_page = ChatPage(self)
        self.voice_page = VoicePage(self)
        self.memory_page = MemoryPage(self)
        self.documents_page = DocumentsPage(self)
        self.reminders_page = RemindersPage(self)
        self.automation_page = AutomationPage(self)
        self.settings_page = SettingsPage(self)

        self.pages_stack.addWidget(self.home_page)       # index 0
        self.pages_stack.addWidget(self.chat_page)       # index 1
        self.pages_stack.addWidget(self.voice_page)      # index 2
        self.pages_stack.addWidget(self.memory_page)     # index 3
        self.pages_stack.addWidget(self.documents_page)  # index 4
        self.pages_stack.addWidget(self.reminders_page)  # index 5
        self.pages_stack.addWidget(self.automation_page) # index 6
        self.pages_stack.addWidget(self.settings_page)   # index 7

        content_layout.addWidget(self.pages_stack)
        root_layout.addWidget(content_container)

    def _connect_signals(self):
        # Sidebar page navigation
        self.sidebar.page_changed.connect(self._on_navigate_page)

        # Home page shortcuts
        self.home_page.navigate_requested.connect(self._on_navigate_page)
        self.home_page.voice_toggle_requested.connect(lambda: self._on_navigate_page(2))
        self.home_page.open_conversation_requested.connect(self.chat_page.switch_to_conversation)

        # Status header actions
        self.status_header.emergency_stop_clicked.connect(self._on_emergency_stop)

        # AI & Voice generation state changes -> drive central AURA core animation
        self.chat_page.generation_state_changed.connect(self._on_ai_state_changed)
        self.voice_page.state_changed.connect(self._on_voice_state_changed)

        # Settings dynamic reactions
        self.settings_page.name_changed.connect(self._on_assistant_name_changed)
        self.settings_page.mode_changed.connect(self._on_ai_mode_changed)
        self.settings_page.reduced_motion_changed.connect(self._on_reduced_motion_changed)

    def _on_navigate_page(self, page_index: int):
        self.pages_stack.setCurrentIndex(page_index)
        self.sidebar.select_page(page_index)

        # Refresh page data if navigating back to home or reminders
        if page_index == 0:
            self.home_page.refresh_data()
        elif page_index == 5:
            self.reminders_page.refresh_reminders()
        elif page_index == 3:
            self.memory_page.refresh_memories()

    def _on_emergency_stop(self):
        automation_service.trigger_emergency_stop()
        self.automation_page.refresh_audit_log()
        QMessageBox.warning(
            self,
            "Emergency Stop Triggered",
            "Automation safety circuit tripped! All desktop operations have been immediately blocked."
        )

    def _on_ai_state_changed(self, state: str):
        # Update home core if visible
        if state == "thinking":
            self.home_page.core_widget.set_state(AuraCoreWidget.STATE_THINKING)
            self.sidebar.update_system_status("PROCESSING AI", Colors.STATUS_THINKING)
        elif state == "error":
            self.home_page.core_widget.set_state(AuraCoreWidget.STATE_ERROR)
            self.sidebar.update_system_status("ERROR ENCOUNTERED", Colors.STATUS_ERROR)
        else:
            self.home_page.core_widget.set_state(AuraCoreWidget.STATE_IDLE)
            self.sidebar.update_system_status("SYSTEM READY", Colors.STATUS_ONLINE)

    def _on_voice_state_changed(self, state: str):
        self.home_page.core_widget.set_state(state)
        if state == "listening":
            self.status_header.set_mic_status("LISTENING", active=True)
            self.sidebar.update_system_status("LISTENING", Colors.STATUS_LISTENING)
        elif state == "speaking":
            self.status_header.set_mic_status("SPEAKING", active=True)
            self.sidebar.update_system_status("SPEAKING", Colors.STATUS_SPEAKING)
        elif state == "thinking":
            self.status_header.set_mic_status("THINKING", active=False)
            self.sidebar.update_system_status("SYNTHESIZING", Colors.STATUS_THINKING)
        else:
            self.status_header.set_mic_status("IDLE", active=False)
            self.sidebar.update_system_status("SYSTEM READY", Colors.STATUS_ONLINE)

    def _on_assistant_name_changed(self, new_name: str):
        self.setWindowTitle(f"{new_name.upper()} — Pure Python AI Personal Assistant")
        self.status_header.set_assistant_name(new_name)
        self.home_page.update_greeting(new_name)

    def _on_ai_mode_changed(self, mode: str):
        self.status_header.set_mode(mode)

    def _on_reduced_motion_changed(self, enabled: bool):
        self.home_page.core_widget.set_reduced_motion(enabled)
        self.voice_page.voice_core.set_reduced_motion(enabled)

    def _start_background_services(self):
        # 1. Register reminder alert callback
        reminder_service.register_notification_callback(self._on_reminder_triggered)
        reminder_service.start()

        # 2. Asynchronous provider availability check on startup
        QTimer.singleShot(1000, self._check_provider_status_async)

    def _check_provider_status_async(self):
        status = ai_manager.check_status()
        ollama_info = status.get("ollama", {})
        if ollama_info.get("ok"):
            self.status_header.set_provider_status(f"OLLAMA ({ollama_info.get('model')})", is_active=True)
        else:
            online_info = status.get("online", {})
            if online_info.get("ok"):
                self.status_header.set_provider_status(f"ONLINE ({online_info.get('model')})", is_active=True)
            else:
                self.status_header.set_provider_status("OFFLINE (NO PROVIDER)", is_active=False)

    def _on_reminder_triggered(self, reminder: ReminderRecord):
        # Notify user with alert box
        QMessageBox.information(
            self,
            f"⏰ REMINDER DUE: {reminder.title}",
            f"Title: {reminder.title}\n\nDescription: {reminder.description or 'No additional details.'}\nDue: {reminder.due_date}"
        )
        self.reminders_page.refresh_reminders()
        self.home_page.refresh_data()

    def closeEvent(self, event):
        # Cleanly stop scheduler
        reminder_service.stop()
        event.accept()
