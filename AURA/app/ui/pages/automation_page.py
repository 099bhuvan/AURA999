import json
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QSplitter,
    QTextBrowser,
)
from PySide6.QtCore import Qt

from app.core.automation_service import automation_service
from app.database import get_db
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel


class AutomationPage(QWidget):
    """Windows Desktop Automation interface with security allowlist and audit log."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.db = get_db()
        self._setup_ui()
        self.refresh_audit_log()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_vbox = QVBoxLayout()
        title = QLabel("CONTROLLED DESKTOP AUTOMATION")
        title.setObjectName("pageTitle")
        sub = QLabel("Strict allowlist execution • Emergency safety circuit • Immutable SQLite audit logging")
        sub.setObjectName("pageSubtitle")
        header_vbox.addWidget(title)
        header_vbox.addWidget(sub)
        header_row.addLayout(header_vbox)

        header_row.addStretch()

        # Emergency Stop Banner & Button
        self.btn_emergency_stop = QPushButton("⛔ EMERGENCY STOP")
        self.btn_emergency_stop.setObjectName("dangerButton")
        self.btn_emergency_stop.setMinimumHeight(40)
        self.btn_emergency_stop.setMinimumWidth(160)
        self.btn_emergency_stop.clicked.connect(self._toggle_emergency_stop)
        header_row.addWidget(self.btn_emergency_stop)

        main_layout.addLayout(header_row)

        # Splitter: Left Action Launcher / Right Audit Trail
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Controlled Action Dispatcher
        action_panel = GlassPanel(title="APPROVED ACTION DISPATCHER", border_glow=True)
        action_panel.setFixedWidth(360)
        ap_layout = action_panel.layout

        self.status_banner = QLabel("AUTOMATION READY (SAFETY CIRCUIT ACTIVE)")
        self.status_banner.setStyleSheet(f"""
            color: {Colors.STATUS_ONLINE};
            background: rgba(0, 255, 157, 0.1);
            border: 1px solid rgba(0, 255, 157, 0.3);
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        ap_layout.addWidget(self.status_banner)

        # Action Selector
        ap_layout.addWidget(QLabel("Select Allowlisted Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "system_info",
            "open_application",
            "open_website",
            "create_note",
            "find_files",
            "lock_workstation",
        ])
        self.action_combo.currentTextChanged.connect(self._on_action_changed)
        ap_layout.addWidget(self.action_combo)

        # Parameter Input Fields
        self.param1_label = QLabel("Parameter:")
        self.param1_edit = QLineEdit()
        ap_layout.addWidget(self.param1_label)
        ap_layout.addWidget(self.param1_edit)

        self.param2_label = QLabel("Additional Content:")
        self.param2_edit = QLineEdit()
        ap_layout.addWidget(self.param2_label)
        ap_layout.addWidget(self.param2_edit)

        # Master Toggles
        self.cb_enable_auto = QCheckBox("Enable Desktop Automation")
        self.cb_enable_auto.setChecked(automation_service.is_enabled)
        self.cb_enable_auto.toggled.connect(self._on_enable_toggle)
        ap_layout.addWidget(self.cb_enable_auto)

        self.btn_execute = QPushButton("⚡ Execute Approved Action")
        self.btn_execute.setObjectName("primaryButton")
        self.btn_execute.setMinimumHeight(42)
        self.btn_execute.clicked.connect(self._execute_action)
        ap_layout.addWidget(self.btn_execute)

        # Action execution output console
        ap_layout.addWidget(QLabel("Execution Output:"))
        self.output_browser = QTextBrowser()
        self.output_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: #04060a;
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 6px;
                color: {Colors.CYAN_PRIMARY};
                font-family: 'Consolas', monospace;
                font-size: 11.5px;
            }}
        """)
        self.output_browser.setMinimumHeight(140)
        ap_layout.addWidget(self.output_browser)

        splitter.addWidget(action_panel)

        # Right Column: Audit Log Table
        audit_panel = GlassPanel(title="AUTOMATION AUDIT TRAIL", border_glow=False)
        aud_layout = audit_panel.layout

        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels(["Timestamp", "Status", "Action", "Parameters", "Result / Error"])
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.audit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.audit_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.audit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        aud_layout.addWidget(self.audit_table)

        btn_refresh_audit = QPushButton("🔄 Refresh Audit Log")
        btn_refresh_audit.clicked.connect(self.refresh_audit_log)
        aud_layout.addWidget(btn_refresh_audit, alignment=Qt.AlignRight)

        splitter.addWidget(audit_panel)
        splitter.setSizes([360, 640])

        main_layout.addWidget(splitter)
        self._on_action_changed("system_info")

    def _on_action_changed(self, action_name: str):
        if action_name == "open_application":
            self.param1_label.setText("App Name (notepad, calc, explorer, paint, taskmgr):")
            self.param1_edit.setText("notepad")
            self.param1_edit.show()
            self.param1_label.show()
            self.param2_label.hide()
            self.param2_edit.hide()
        elif action_name == "open_website":
            self.param1_label.setText("Validated URL (must start with https://):")
            self.param1_edit.setText("https://github.com")
            self.param1_edit.show()
            self.param1_label.show()
            self.param2_label.hide()
            self.param2_edit.hide()
        elif action_name == "create_note":
            self.param1_label.setText("Note Title:")
            self.param1_edit.setText("Mission_Briefing")
            self.param1_edit.show()
            self.param1_label.show()
            self.param2_label.setText("Note Content:")
            self.param2_edit.setText("All automated systems confirmed nominal.")
            self.param2_label.show()
            self.param2_edit.show()
        elif action_name == "find_files":
            self.param1_label.setText("Search Pattern (e.g. *.txt, *.pdf):")
            self.param1_edit.setText("*.pdf")
            self.param1_edit.show()
            self.param1_label.show()
            self.param2_label.hide()
            self.param2_edit.hide()
        else:  # system_info or lock_workstation
            self.param1_label.hide()
            self.param1_edit.hide()
            self.param2_label.hide()
            self.param2_edit.hide()

    def _execute_action(self):
        action_name = self.action_combo.currentText()
        params = {}

        if action_name == "open_application":
            params["app_name"] = self.param1_edit.text().strip()
        elif action_name == "open_website":
            params["url"] = self.param1_edit.text().strip()
        elif action_name == "create_note":
            params["title"] = self.param1_edit.text().strip()
            params["content"] = self.param2_edit.text().strip()
        elif action_name == "find_files":
            params["pattern"] = self.param1_edit.text().strip()

        # Check confirmation requirement
        res = automation_service.execute_action(action_name, params, user_confirmed=False)

        if res.get("needs_confirmation"):
            reply = QMessageBox.question(
                self,
                "Confirm Desktop Action",
                f"Action '{action_name}' will modify local files or lock system.\n\n"
                f"Parameters: {json.dumps(params, indent=2)}\n\n"
                "Do you grant permission to execute?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                res = automation_service.execute_action(action_name, params, user_confirmed=True)
            else:
                self.output_browser.setPlainText("Action aborted by user.")
                self.refresh_audit_log()
                return

        if res.get("success"):
            out_str = json.dumps(res.get("result"), indent=2) if isinstance(res.get("result"), (dict, list)) else str(res.get("result"))
            self.output_browser.setPlainText(f"SUCCESS:\n{out_str}")
        else:
            self.output_browser.setPlainText(f"FAILED:\n{res.get('error')}")

        self.refresh_audit_log()

    def _toggle_emergency_stop(self):
        if not automation_service.is_emergency_stopped:
            automation_service.trigger_emergency_stop()
            self.btn_emergency_stop.setText("RESET SAFETY LOCK")
            self.btn_emergency_stop.setObjectName("primaryButton")
            self.btn_emergency_stop.setStyle(self.btn_emergency_stop.style())
            self.status_banner.setText("EMERGENCY STOP ACTIVE — ENGINES LOCKED")
            self.status_banner.setStyleSheet(f"""
                color: #ff3377;
                background: rgba(255, 0, 85, 0.15);
                border: 1px solid rgba(255, 0, 85, 0.5);
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: bold;
            """)
        else:
            automation_service.reset_emergency_stop()
            self.btn_emergency_stop.setText("⛔ EMERGENCY STOP")
            self.btn_emergency_stop.setObjectName("dangerButton")
            self.btn_emergency_stop.setStyle(self.btn_emergency_stop.style())
            self.status_banner.setText("AUTOMATION READY (SAFETY CIRCUIT ACTIVE)")
            self.status_banner.setStyleSheet(f"""
                color: {Colors.STATUS_ONLINE};
                background: rgba(0, 255, 157, 0.1);
                border: 1px solid rgba(0, 255, 157, 0.3);
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: bold;
            """)
        self.refresh_audit_log()

    def _on_enable_toggle(self, checked: bool):
        automation_service.set_enabled(checked)

    def refresh_audit_log(self):
        events = self.db.list_audit_events(limit=50)
        self.audit_table.setRowCount(len(events))

        for row_idx, ev in enumerate(events):
            time_item = QTableWidgetItem(ev.timestamp[:19].replace("T", " "))
            status_item = QTableWidgetItem(ev.status.upper())
            if ev.status == "executed":
                status_item.setForeground(Qt.green)
            elif ev.status == "denied":
                status_item.setForeground(Qt.yellow)
            else:
                status_item.setForeground(Qt.red)

            action_item = QTableWidgetItem(ev.action_name)
            params_item = QTableWidgetItem(ev.parameters)
            res_item = QTableWidgetItem(ev.result or ev.error_message or "")

            self.audit_table.setItem(row_idx, 0, time_item)
            self.audit_table.setItem(row_idx, 1, status_item)
            self.audit_table.setItem(row_idx, 2, action_item)
            self.audit_table.setItem(row_idx, 3, params_item)
            self.audit_table.setItem(row_idx, 4, res_item)
