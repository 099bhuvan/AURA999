from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSlider,
    QFormLayout,
    QMessageBox,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from app.config import config
from app.database import get_db
from app.core.ai_manager import ai_manager
from app.core.voice_service import voice_service
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel


class SettingsPage(QWidget):
    """System and AI configuration center for AURA."""

    name_changed = Signal(str)
    reduced_motion_changed = Signal(bool)
    mode_changed = Signal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.db = get_db()
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        header = QLabel("SYSTEM & AI CONFIGURATION")
        header.setObjectName("pageTitle")
        sub = QLabel("Customize identity, local Ollama endpoints, online API keys, and voice characteristics")
        sub.setObjectName("pageSubtitle")
        main_layout.addWidget(header)
        main_layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # ---------------------------------------------------------------------
        # Section 1: Assistant Identity
        # ---------------------------------------------------------------------
        identity_panel = GlassPanel(title="ASSISTANT IDENTITY", border_glow=True)
        ip_layout = identity_panel.layout

        form_id = QFormLayout()
        form_id.setSpacing(10)

        self.name_edit = QLineEdit(config.assistant_name)
        self.name_edit.setPlaceholderText("AURA")
        form_id.addRow("Assistant Name:", self.name_edit)

        ip_layout.addLayout(form_id)

        btn_row_id = QHBoxLayout()
        btn_save_name = QPushButton("Update Identity")
        btn_save_name.setObjectName("primaryButton")
        btn_save_name.clicked.connect(self._save_identity)
        btn_row_id.addWidget(btn_save_name)

        btn_reset_name = QPushButton("Reset to Default (AURA)")
        btn_reset_name.clicked.connect(self._reset_identity)
        btn_row_id.addWidget(btn_reset_name)
        btn_row_id.addStretch()

        ip_layout.addLayout(btn_row_id)
        layout.addWidget(identity_panel)

        # ---------------------------------------------------------------------
        # Section 2: AI Routing & Provider Settings
        # ---------------------------------------------------------------------
        ai_panel = GlassPanel(title="NEURAL AI PROVIDER & ROUTING", border_glow=False)
        ai_layout = ai_panel.layout

        form_ai = QFormLayout()
        form_ai.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Automatic (Prefers offline Ollama, fallback to online with notice)",
            "Offline (Strictly local Ollama only — zero external data transfer)",
            "Online (Dedicated external API endpoint)",
        ])
        form_ai.addRow("Execution Mode:", self.mode_combo)

        # Ollama settings
        self.ollama_url_edit = QLineEdit(config.ollama_base_url)
        form_ai.addRow("Ollama Endpoint:", self.ollama_url_edit)

        self.ollama_model_edit = QLineEdit(config.ollama_model)
        form_ai.addRow("Ollama Model Tag:", self.ollama_model_edit)

        # Online settings
        self.online_url_edit = QLineEdit(config.online_base_url)
        form_ai.addRow("Online Base URL:", self.online_url_edit)

        self.online_model_edit = QLineEdit(config.online_model)
        form_ai.addRow("Online Model Name:", self.online_model_edit)

        self.online_key_edit = QLineEdit(config.online_api_key)
        self.online_key_edit.setEchoMode(QLineEdit.Password)
        self.online_key_edit.setPlaceholderText("sk-... (stored securely in memory / .env)")
        
        key_row = QHBoxLayout()
        key_row.addWidget(self.online_key_edit)
        self.btn_show_key = QPushButton("👁 Show")
        self.btn_show_key.setFixedWidth(64)
        self.btn_show_key.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.btn_show_key)
        form_ai.addRow("Online API Key:", key_row)

        ai_layout.addLayout(form_ai)

        # Test Connection Buttons
        btn_test_row = QHBoxLayout()
        btn_test_ollama = QPushButton("🧪 Test Ollama Connection")
        btn_test_ollama.clicked.connect(self._test_ollama)
        btn_test_row.addWidget(btn_test_ollama)

        btn_test_online = QPushButton("🧪 Test Online AI Connection")
        btn_test_online.clicked.connect(self._test_online)
        btn_test_row.addWidget(btn_test_online)

        btn_save_ai = QPushButton("Save AI Configuration")
        btn_save_ai.setObjectName("primaryButton")
        btn_save_ai.clicked.connect(self._save_ai_settings)
        btn_test_row.addWidget(btn_save_ai)

        ai_layout.addLayout(btn_test_row)
        layout.addWidget(ai_panel)

        # ---------------------------------------------------------------------
        # Section 3: Voice, Motion & Performance
        # ---------------------------------------------------------------------
        voice_panel = GlassPanel(title="VOICE, ACCESSIBILITY & PERFORMANCE", border_glow=False)
        vp_layout = voice_panel.layout

        form_perf = QFormLayout()
        form_perf.setSpacing(10)

        self.cb_reduced_motion = QCheckBox("Enable Reduced Motion (optimizes CPU/GPU and simplifies animations)")
        self.cb_reduced_motion.setChecked(config.reduced_motion)
        self.cb_reduced_motion.toggled.connect(self._on_motion_toggle)
        form_perf.addRow("Visual Motion:", self.cb_reduced_motion)

        self.voice_rate_slider = QSlider(Qt.Horizontal)
        self.voice_rate_slider.setRange(100, 260)
        self.voice_rate_slider.setValue(config.speech_rate)
        self.voice_rate_slider.valueChanged.connect(lambda v: voice_service.set_speech_rate(v))
        form_perf.addRow("Speech Rate (Words/Min):", self.voice_rate_slider)

        vp_layout.addLayout(form_perf)
        layout.addWidget(voice_panel)

        # ---------------------------------------------------------------------
        # Section 4: Data Management & Storage
        # ---------------------------------------------------------------------
        data_panel = GlassPanel(title="DATA DIRECTORY & PRIVACY", border_glow=False)
        dp_layout = data_panel.layout

        data_path_label = QLabel(f"Local Storage Directory: {config.data_dir}")
        data_path_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-family: monospace; font-size: 11px;")
        dp_layout.addWidget(data_path_label)

        btn_clear_chats = QPushButton("Purge All Chat History")
        btn_clear_chats.setObjectName("dangerButton")
        btn_clear_chats.clicked.connect(self._purge_all_chats)
        dp_layout.addWidget(btn_clear_chats, alignment=Qt.AlignLeft)

        layout.addWidget(data_panel)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def load_settings(self):
        # Load from DB settings if stored
        saved_name = self.db.get_setting("assistant_name", config.assistant_name)
        self.name_edit.setText(saved_name)
        config.assistant_name = saved_name

        saved_mode = self.db.get_setting("ai_mode", config.ai_mode)
        if saved_mode == "offline":
            self.mode_combo.setCurrentIndex(1)
        elif saved_mode == "online":
            self.mode_combo.setCurrentIndex(2)
        else:
            self.mode_combo.setCurrentIndex(0)

        self.ollama_url_edit.setText(self.db.get_setting("ollama_base_url", config.ollama_base_url))
        self.ollama_model_edit.setText(self.db.get_setting("ollama_model", config.ollama_model))
        self.online_url_edit.setText(self.db.get_setting("online_base_url", config.online_base_url))
        self.online_model_edit.setText(self.db.get_setting("online_model", config.online_model))
        
        # Don't persist API keys in plaintext DB, only populate from runtime config / env
        self.online_key_edit.setText(config.online_api_key)

    def _save_identity(self):
        new_name = self.name_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Assistant name cannot be blank.")
            return

        config.assistant_name = new_name
        self.db.set_setting("assistant_name", new_name)
        self.name_changed.emit(new_name)
        QMessageBox.information(self, "Identity Updated", f"Assistant name updated to '{new_name}'.")

    def _reset_identity(self):
        self.name_edit.setText("AURA")
        self._save_identity()

    def _toggle_key_visibility(self):
        if self.online_key_edit.echoMode() == QLineEdit.Password:
            self.online_key_edit.setEchoMode(QLineEdit.Normal)
            self.btn_show_key.setText("Hide")
        else:
            self.online_key_edit.setEchoMode(QLineEdit.Password)
            self.btn_show_key.setText("👁 Show")

    def _save_ai_settings(self):
        idx = self.mode_combo.currentIndex()
        mode_val = "automatic" if idx == 0 else ("offline" if idx == 1 else "online")

        ollama_url = self.ollama_url_edit.text().strip()
        ollama_model = self.ollama_model_edit.text().strip()
        online_url = self.online_url_edit.text().strip()
        online_model = self.online_model_edit.text().strip()
        online_key = self.online_key_edit.text().strip()

        # Update runtime manager
        ai_manager.update_config(
            mode=mode_val,
            ollama_base_url=ollama_url,
            ollama_model=ollama_model,
            online_api_key=online_key,
            online_base_url=online_url,
            online_model=online_model,
        )

        # Persist non-sensitive settings
        self.db.set_setting("ai_mode", mode_val)
        self.db.set_setting("ollama_base_url", ollama_url)
        self.db.set_setting("ollama_model", ollama_model)
        self.db.set_setting("online_base_url", online_url)
        self.db.set_setting("online_model", online_model)

        self.mode_changed.emit(mode_val)
        QMessageBox.information(self, "Settings Saved", "AI configuration updated successfully.")

    def _test_ollama(self):
        ai_manager.ollama.base_url = self.ollama_url_edit.text().strip().rstrip("/")
        ai_manager.ollama.model = self.ollama_model_edit.text().strip()
        ok, msg = ai_manager.ollama.check_availability()
        if ok:
            QMessageBox.information(self, "Ollama Connection Success", f"✔ {msg}")
        else:
            QMessageBox.warning(self, "Ollama Connection Failed", f"✖ {msg}")

    def _test_online(self):
        ai_manager.online.base_url = self.online_url_edit.text().strip().rstrip("/")
        ai_manager.online.model = self.online_model_edit.text().strip()
        ai_manager.online.api_key = self.online_key_edit.text().strip()
        ok, msg = ai_manager.online.check_availability()
        if ok:
            QMessageBox.information(self, "Online AI Connection Success", f"✔ {msg}")
        else:
            QMessageBox.warning(self, "Online AI Connection Notice", f"✖ {msg}")

    def _on_motion_toggle(self, checked: bool):
        config.reduced_motion = checked
        self.db.set_setting("reduced_motion", "true" if checked else "false")
        self.reduced_motion_changed.emit(checked)

    def _purge_all_chats(self):
        reply = QMessageBox.warning(
            self,
            "Confirm Delete All Chats",
            "This will delete ALL conversations and message records from local SQLite storage.\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM messages")
                conn.execute("DELETE FROM conversations")
                conn.commit()
            QMessageBox.information(self, "Chats Purged", "All chat history has been erased.")
