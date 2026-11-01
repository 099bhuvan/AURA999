from datetime import datetime, timedelta
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QDateTimeEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QTextEdit,
    QTabWidget,
    QCheckBox,
)
from PySide6.QtCore import Qt, QDateTime

from app.core.reminder_service import reminder_service
from app.database.models import ReminderRecord
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel


class ReminderDialog(QDialog):
    """Dialog for creating a new reminder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Smart Reminder")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background-color: {Colors.BG_PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g. Deploy production release, Team sync")
        form.addRow("Reminder Title:", self.title_edit)

        self.due_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("yyyy-MM-dd  HH:mm")
        form.addRow("Due Date & Time:", self.due_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Optional detailed description or action items...")
        self.desc_edit.setMaximumHeight(80)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Schedule Reminder")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _validate_and_accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Reminder title cannot be empty.")
            return
        self.accept()

    def get_data(self):
        title = self.title_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip()
        dt_str = self.due_edit.dateTime().toString(Qt.ISODate)
        return title, dt_str, desc


class RemindersPage(QWidget):
    """Smart Reminders interface with SQLite persistence and APScheduler."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_reminders()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_vbox = QVBoxLayout()
        title = QLabel("SMART REMINDERS & SCHEDULER")
        title.setObjectName("pageTitle")
        sub = QLabel("Persistent reminder scheduling with startup recovery and desktop sound notifications")
        sub.setObjectName("pageSubtitle")
        header_vbox.addWidget(title)
        header_vbox.addWidget(sub)
        header_row.addLayout(header_vbox)

        header_row.addStretch()

        self.sound_checkbox = QCheckBox("Audible Alert Sound")
        self.sound_checkbox.setChecked(reminder_service.sound_enabled)
        self.sound_checkbox.toggled.connect(self._on_sound_toggle)
        header_row.addWidget(self.sound_checkbox)

        btn_new_rem = QPushButton("＋ New Reminder")
        btn_new_rem.setObjectName("primaryButton")
        btn_new_rem.clicked.connect(self._open_new_reminder_dialog)
        header_row.addWidget(btn_new_rem)

        main_layout.addLayout(header_row)

        # Tabbed Reminder Lists: Upcoming vs Overdue vs All
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_SUBTLE};
                background: {Colors.BG_PANEL};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background: {Colors.BG_MAIN};
                color: {Colors.TEXT_SECONDARY};
                padding: 8px 16px;
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {Colors.BG_PANEL};
                color: {Colors.CYAN_PRIMARY};
                font-weight: bold;
                border-bottom: 2px solid {Colors.CYAN_PRIMARY};
            }}
        """)

        # Tab 1: Upcoming
        self.upcoming_table = self._create_table()
        self.tabs.addTab(self.upcoming_table, "⏰ Upcoming")

        # Tab 2: Overdue
        self.overdue_table = self._create_table()
        self.tabs.addTab(self.overdue_table, "⚠ Overdue / Alerted")

        # Tab 3: All History
        self.all_table = self._create_table()
        self.tabs.addTab(self.all_table, "📋 All History")

        main_layout.addWidget(self.tabs)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_complete = QPushButton("✔ Mark Completed")
        btn_complete.clicked.connect(self._complete_selected)
        btn_row.addWidget(btn_complete)

        btn_delete = QPushButton("🗑 Delete Reminder")
        btn_delete.setObjectName("dangerButton")
        btn_delete.clicked.connect(self._delete_selected)
        btn_row.addWidget(btn_delete)

        main_layout.addLayout(btn_row)

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Status", "Title", "Due Date & Time", "Description", "ID"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

    def refresh_reminders(self):
        # 1. Upcoming
        upcoming = reminder_service.get_upcoming()
        self._populate_table(self.upcoming_table, upcoming)

        # 2. Overdue
        overdue = reminder_service.get_overdue()
        self._populate_table(self.overdue_table, overdue)

        # 3. All
        all_rems = reminder_service.list_all()
        self._populate_table(self.all_table, all_rems)

    def _populate_table(self, table: QTableWidget, items: list):
        table.setRowCount(len(items))
        for row_idx, r in enumerate(items):
            status_item = QTableWidgetItem(r.status.upper())
            if r.status == "completed":
                status_item.setForeground(Qt.green)
            elif r.status in ("notified", "overdue"):
                status_item.setForeground(Qt.yellow)
            else:
                status_item.setForeground(Qt.cyan)

            title_item = QTableWidgetItem(r.title)
            title_item.setData(Qt.UserRole, r.id)
            due_item = QTableWidgetItem(r.due_date.replace("T", " "))
            desc_item = QTableWidgetItem(r.description or "")
            id_item = QTableWidgetItem(r.id[:8] + "…")

            table.setItem(row_idx, 0, status_item)
            table.setItem(row_idx, 1, title_item)
            table.setItem(row_idx, 2, due_item)
            table.setItem(row_idx, 3, desc_item)
            table.setItem(row_idx, 4, id_item)

    def _open_new_reminder_dialog(self):
        dlg = ReminderDialog(self)
        if dlg.exec() == QDialog.Accepted:
            title, due_iso, desc = dlg.get_data()
            reminder_service.add_reminder(title, due_iso, description=desc)
            self.refresh_reminders()

    def _get_active_selected_id(self) -> Optional[str]:
        cur_table: QTableWidget = self.tabs.currentWidget()
        cur_row = cur_table.currentRow()
        if cur_row < 0:
            return None
        return cur_table.item(cur_row, 1).data(Qt.UserRole)

    def _complete_selected(self):
        rem_id = self._get_active_selected_id()
        if not rem_id:
            QMessageBox.information(self, "Selection Required", "Select a reminder to mark completed.")
            return
        reminder_service.mark_completed(rem_id)
        self.refresh_reminders()

    def _delete_selected(self):
        rem_id = self._get_active_selected_id()
        if not rem_id:
            QMessageBox.information(self, "Selection Required", "Select a reminder to delete.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this reminder permanently?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            reminder_service.delete_reminder(rem_id)
            self.refresh_reminders()

    def _on_sound_toggle(self, checked: bool):
        reminder_service.sound_enabled = checked
