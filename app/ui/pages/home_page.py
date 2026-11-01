from datetime import datetime
from typing import Callable, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal

from app.config import config
from app.database import get_db
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel
from app.ui.widgets.aura_core import AuraCoreWidget


class HomePage(QWidget):
    """Futuristic central Home Dashboard for AURA."""

    navigate_requested = Signal(int)
    voice_toggle_requested = Signal()
    open_conversation_requested = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.db = get_db()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(20)

        # Scroll area to allow responsive resizing on smaller displays
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # 1. Header & Dynamic Greeting
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("pageTitle")
        self.greeting_label.setAlignment(Qt.AlignCenter)

        self.sub_greeting = QLabel("Tactical Neural Assistant • Systems nominal • Standby for command")
        self.sub_greeting.setObjectName("pageSubtitle")
        self.sub_greeting.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.greeting_label)
        header_layout.addWidget(self.sub_greeting)
        layout.addLayout(header_layout)

        # 2. Central Core Showcase Area
        core_container = QHBoxLayout()
        core_container.addStretch()

        self.core_widget = AuraCoreWidget(self, size=280)
        core_container.addWidget(self.core_widget)

        core_container.addStretch()
        layout.addLayout(core_container)

        # 3. Core Quick Controls & Mode Indicators
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        controls_layout.addStretch()

        self.voice_action_btn = QPushButton("🎙 START VOICE INTERACTION")
        self.voice_action_btn.setObjectName("primaryButton")
        self.voice_action_btn.setMinimumHeight(40)
        self.voice_action_btn.setMinimumWidth(240)
        self.voice_action_btn.clicked.connect(self.voice_toggle_requested.emit)
        controls_layout.addWidget(self.voice_action_btn)

        btn_chat = QPushButton("💬 OPEN CHAT")
        btn_chat.setMinimumHeight(40)
        btn_chat.clicked.connect(lambda: self.navigate_requested.emit(1))
        controls_layout.addWidget(btn_chat)

        btn_doc = QPushButton("📄 INGEST DOCUMENT")
        btn_doc.setMinimumHeight(40)
        btn_doc.clicked.connect(lambda: self.navigate_requested.emit(4))
        controls_layout.addWidget(btn_doc)

        btn_remind = QPushButton("⏰ NEW REMINDER")
        btn_remind.setMinimumHeight(40)
        btn_remind.clicked.connect(lambda: self.navigate_requested.emit(5))
        controls_layout.addWidget(btn_remind)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # 4. Telemetry and Overview Glass Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(18)

        # Left Card: Recent Neural Conversations
        self.conv_panel = GlassPanel(title="RECENT CONVERSATIONS", border_glow=True)
        self.conv_list = QListWidget()
        self.conv_list.setMinimumHeight(160)
        self.conv_list.itemClicked.connect(self._on_conversation_clicked)
        self.conv_panel.layout.addWidget(self.conv_list)
        cards_layout.addWidget(self.conv_panel)

        # Right Card: Upcoming Reminders
        self.rem_panel = GlassPanel(title="UPCOMING REMINDERS", border_glow=False)
        self.rem_list = QListWidget()
        self.rem_list.setMinimumHeight(160)
        self.rem_panel.layout.addWidget(self.rem_list)
        cards_layout.addWidget(self.rem_panel)

        layout.addLayout(cards_layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.update_greeting()
        self.refresh_data()

    def update_greeting(self, assistant_name: Optional[str] = None):
        name = assistant_name or config.assistant_name
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_str = "Good morning"
        elif 12 <= hour < 17:
            time_str = "Good afternoon"
        elif 17 <= hour < 22:
            time_str = "Good evening"
        else:
            time_str = "Good night"
        
        self.greeting_label.setText(f"{time_str}. I am {name.upper()}.")

    def refresh_data(self):
        """Reload recent conversations and upcoming reminders from SQLite."""
        # Conversations
        self.conv_list.clear()
        try:
            convs = self.db.list_conversations()[:5]
            if not convs:
                item = QListWidgetItem("No recent conversations. Click 'Open Chat' to begin.")
                item.setFlags(Qt.NoItemFlags)
                self.conv_list.addItem(item)
            else:
                for c in convs:
                    item = QListWidgetItem(f"💬  {c.title}")
                    item.setData(Qt.UserRole, c.id)
                    self.conv_list.addItem(item)
        except Exception:
            pass

        # Reminders
        self.rem_list.clear()
        try:
            reminders = self.db.list_reminders(status="pending")[:5]
            if not reminders:
                item = QListWidgetItem("No upcoming reminders. All tasks clear.")
                item.setFlags(Qt.NoItemFlags)
                self.rem_list.addItem(item)
            else:
                for r in reminders:
                    item = QListWidgetItem(f"⏰  {r.title} — {r.due_date}")
                    self.rem_list.addItem(item)
        except Exception:
            pass

    def _on_conversation_clicked(self, item: QListWidgetItem):
        conv_id = item.data(Qt.UserRole)
        if conv_id:
            self.open_conversation_requested.emit(conv_id)
            self.navigate_requested.emit(1)
