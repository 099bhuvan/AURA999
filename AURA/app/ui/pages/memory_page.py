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
    QDialog,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QCheckBox,
)
from PySide6.QtCore import Qt

from app.core.memory_service import memory_service
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel


class MemoryDialog(QDialog):
    """Dialog for creating or editing a verified memory item."""

    def __init__(self, key: str = "", content: str = "", category: str = "fact", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Verified Long-Term Memory")
        self.setMinimumWidth(440)
        self.setStyleSheet(f"background-color: {Colors.BG_PANEL};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.key_edit = QLineEdit(key)
        self.key_edit.setPlaceholderText("e.g. Preferred Language, Programming Style")
        form.addRow("Memory Title / Key:", self.key_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["fact", "preference", "custom"])
        self.category_combo.setCurrentText(category)
        form.addRow("Category:", self.category_combo)

        self.content_edit = QTextEdit()
        self.content_edit.setText(content)
        self.content_edit.setPlaceholderText("Enter the verified fact or preference to be remembered across conversations...")
        self.content_edit.setMinimumHeight(100)
        form.addRow("Memory Details:", self.content_edit)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Memory")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._validate_and_accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _validate_and_accept(self):
        if not self.key_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Memory key/title cannot be blank.")
            return
        if not self.content_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Memory content cannot be blank.")
            return
        self.accept()

    def get_data(self):
        return (
            self.key_edit.text().strip(),
            self.content_edit.toPlainText().strip(),
            self.category_combo.currentText(),
        )


class MemoryPage(QWidget):
    """Interface for inspecting and managing persistent long-term memories."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_memories()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        header_vbox = QVBoxLayout()
        title = QLabel("LONG-TERM MEMORY BANK")
        title.setObjectName("pageTitle")
        sub = QLabel("Manage verified facts, preferences, and personal context stored locally in SQLite")
        sub.setObjectName("pageSubtitle")
        header_vbox.addWidget(title)
        header_vbox.addWidget(sub)
        header_row.addLayout(header_vbox)

        header_row.addStretch()

        self.enable_checkbox = QCheckBox("Memory Subsystem Active")
        self.enable_checkbox.setChecked(memory_service.is_enabled)
        self.enable_checkbox.toggled.connect(self._on_toggle_enabled)
        header_row.addWidget(self.enable_checkbox)

        main_layout.addLayout(header_row)

        # Action and Search Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search stored memories by keyword...")
        self.search_input.textChanged.connect(self.refresh_memories)
        action_bar.addWidget(self.search_input)

        btn_add = QPushButton("＋ Add Verified Memory")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._open_add_dialog)
        action_bar.addWidget(btn_add)

        btn_clear_all = QPushButton("🗑 Purge All Memories")
        btn_clear_all.setObjectName("dangerButton")
        btn_clear_all.clicked.connect(self._confirm_clear_all)
        action_bar.addWidget(btn_clear_all)

        main_layout.addLayout(action_bar)

        # Memory Table Card
        table_panel = GlassPanel(title="STORED FACT REPOSITORY", border_glow=False)
        t_layout = table_panel.layout

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Category", "Key / Title", "Content", "Last Updated"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        t_layout.addWidget(self.table)

        # Action Buttons under Table
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_edit = QPushButton("✏ Edit Selected")
        btn_edit.clicked.connect(self._edit_selected)
        btn_row.addWidget(btn_edit)

        btn_del = QPushButton("🗑 Delete Selected")
        btn_del.setObjectName("dangerButton")
        btn_del.clicked.connect(self._delete_selected)
        btn_row.addWidget(btn_del)

        t_layout.addLayout(btn_row)
        main_layout.addWidget(table_panel)

    def refresh_memories(self):
        query = self.search_input.text().strip()
        memories = memory_service.search_memories(query)

        self.table.setRowCount(len(memories))
        for row_idx, mem in enumerate(memories):
            id_item = QTableWidgetItem(mem.id[:8] + "…")
            id_item.setData(Qt.UserRole, mem.id)
            cat_item = QTableWidgetItem(mem.category.upper())
            key_item = QTableWidgetItem(mem.key)
            content_item = QTableWidgetItem(mem.content)
            updated_item = QTableWidgetItem(mem.updated_at[:19].replace("T", " "))

            self.table.setItem(row_idx, 0, id_item)
            self.table.setItem(row_idx, 1, cat_item)
            self.table.setItem(row_idx, 2, key_item)
            self.table.setItem(row_idx, 3, content_item)
            self.table.setItem(row_idx, 4, updated_item)

    def _open_add_dialog(self):
        dlg = MemoryDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            key, content, cat = dlg.get_data()
            memory_service.add_memory(key, content, category=cat)
            self.refresh_memories()

    def _edit_selected(self):
        cur_row = self.table.currentRow()
        if cur_row < 0:
            QMessageBox.information(self, "Selection Required", "Please select a memory row to edit.")
            return

        mem_id = self.table.item(cur_row, 0).data(Qt.UserRole)
        memories = memory_service.list_memories()
        record = next((m for m in memories if m.id == mem_id), None)
        if not record:
            return

        dlg = MemoryDialog(key=record.key, content=record.content, category=record.category, parent=self)
        if dlg.exec() == QDialog.Accepted:
            key, content, cat = dlg.get_data()
            memory_service.update_memory(record.id, key, content, cat)
            self.refresh_memories()

    def _delete_selected(self):
        cur_row = self.table.currentRow()
        if cur_row < 0:
            QMessageBox.information(self, "Selection Required", "Please select a memory row to delete.")
            return

        mem_id = self.table.item(cur_row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this memory?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            memory_service.delete_memory(mem_id)
            self.refresh_memories()

    def _confirm_clear_all(self):
        reply = QMessageBox.warning(
            self,
            "Purge All Long-Term Memories",
            "This will permanently erase ALL stored user preferences and facts from SQLite.\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            memory_service.clear_all()
            self.refresh_memories()

    def _on_toggle_enabled(self, checked: bool):
        memory_service.set_enabled(checked)
