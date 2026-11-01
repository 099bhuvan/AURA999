from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QFrame,
    QInputDialog,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from app.config import config
from app.database import get_db, DatabaseService
from app.database.models import ConversationRecord, MessageRecord
from app.core.memory_service import memory_service
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel
from app.ui.workers.ai_worker import AIWorker


class ChatPage(QWidget):
    """Futuristic AI Chat interface with conversation history, streaming, and markdown."""

    generation_state_changed = Signal(str)  # "thinking", "idle", "error"

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.db = get_db()
        self.current_conversation: Optional[ConversationRecord] = None
        self.ai_worker: Optional[AIWorker] = None
        self._streaming_content = ""
        self.active_document_context: Optional[str] = None

        self._setup_ui()
        self.load_conversations()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # Splitter between conversations list and chat window
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1e293b;
                width: 2px;
            }
        """)

        # ---------------------------------------------------------------------
        # Left Panel: Conversation History
        # ---------------------------------------------------------------------
        history_panel = GlassPanel(title="NEURAL SESSIONS", border_glow=False)
        history_panel.setFixedWidth(260)
        hist_layout = history_panel.layout

        btn_new_chat = QPushButton("＋ NEW CONVERSATION")
        btn_new_chat.setObjectName("primaryButton")
        btn_new_chat.setMinimumHeight(36)
        btn_new_chat.clicked.connect(self.new_conversation)
        hist_layout.addWidget(btn_new_chat)

        self.conv_list_widget = QListWidget()
        self.conv_list_widget.itemClicked.connect(self._on_conversation_selected)
        hist_layout.addWidget(self.conv_list_widget)

        # Conversation Management Buttons
        conv_actions = QHBoxLayout()
        conv_actions.setSpacing(6)

        btn_rename = QPushButton("✏ Rename")
        btn_rename.clicked.connect(self.rename_selected_conversation)
        conv_actions.addWidget(btn_rename)

        btn_delete = QPushButton("🗑 Delete")
        btn_delete.setObjectName("dangerButton")
        btn_delete.clicked.connect(self.delete_selected_conversation)
        conv_actions.addWidget(btn_delete)

        hist_layout.addLayout(conv_actions)
        splitter.addWidget(history_panel)

        # ---------------------------------------------------------------------
        # Right Panel: Chat Stream & Message Input
        # ---------------------------------------------------------------------
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(10)

        # Top Bar: Conversation Title & Provider Tag
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            background-color: {Colors.BG_PANEL};
            border: 1px solid {Colors.BORDER_SUBTLE};
            border-radius: 6px;
            padding: 4px 10px;
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 6, 10, 6)

        self.conv_title_label = QLabel("Neural Session Active")
        self.conv_title_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #ffffff;")
        top_layout.addWidget(self.conv_title_label)

        top_layout.addStretch()

        self.active_provider_tag = QLabel("READY")
        self.active_provider_tag.setStyleSheet(f"""
            color: {Colors.CYAN_PRIMARY};
            font-size: 11px;
            font-weight: 700;
            background-color: rgba(0, 240, 255, 0.1);
            padding: 3px 8px;
            border-radius: 4px;
        """)
        top_layout.addWidget(self.active_provider_tag)

        self.btn_copy_last = QPushButton("📋 Copy Response")
        self.btn_copy_last.setToolTip("Copy the last AI response to clipboard")
        self.btn_copy_last.clicked.connect(self._copy_last_response)
        top_layout.addWidget(self.btn_copy_last)

        chat_layout.addWidget(top_bar)

        # Message Display Browser (Supports rich HTML & Markdown)
        self.message_browser = QTextBrowser()
        self.message_browser.setOpenExternalLinks(True)
        self.message_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 16px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13.5px;
                line-height: 1.6;
            }}
        """)
        chat_layout.addWidget(self.message_browser)

        # Status / Error Banner
        self.error_banner = QLabel("")
        self.error_banner.setWordWrap(True)
        self.error_banner.setStyleSheet(f"""
            background-color: rgba(255, 0, 85, 0.15);
            color: #ff3377;
            border: 1px solid rgba(255, 0, 85, 0.5);
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 600;
        """)
        self.error_banner.hide()
        chat_layout.addWidget(self.error_banner)

        # Input Bar
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask AURA anything, or issue a command...")
        self.input_field.setMinimumHeight(44)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.btn_send = QPushButton("SEND ◈")
        self.btn_send.setObjectName("primaryButton")
        self.btn_send.setMinimumHeight(44)
        self.btn_send.setMinimumWidth(90)
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)

        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setMinimumHeight(44)
        self.btn_cancel.setMinimumWidth(80)
        self.btn_cancel.clicked.connect(self.cancel_generation)
        self.btn_cancel.hide()
        input_layout.addWidget(self.btn_cancel)

        chat_layout.addWidget(input_container)
        splitter.addWidget(chat_container)
        splitter.setSizes([260, 740])

        main_layout.addWidget(splitter)

    # -------------------------------------------------------------------------
    # Conversation Management
    # -------------------------------------------------------------------------
    def load_conversations(self):
        """Populate conversation list from database."""
        self.conv_list_widget.clear()
        convs = self.db.list_conversations()
        if not convs:
            # Create first conversation
            new_conv = self.db.create_conversation("Initial Session")
            convs = [new_conv]

        for conv in convs:
            item = QListWidgetItem(f"💬  {conv.title}")
            item.setData(Qt.UserRole, conv.id)
            self.conv_list_widget.addItem(item)

        if convs:
            self.conv_list_widget.setCurrentRow(0)
            self.switch_to_conversation(convs[0].id)

    def new_conversation(self):
        conv = self.db.create_conversation(f"Session {self.conv_list_widget.count() + 1}")
        item = QListWidgetItem(f"💬  {conv.title}")
        item.setData(Qt.UserRole, conv.id)
        self.conv_list_widget.insertItem(0, item)
        self.conv_list_widget.setCurrentRow(0)
        self.switch_to_conversation(conv.id)

    def _on_conversation_selected(self, item: QListWidgetItem):
        conv_id = item.data(Qt.UserRole)
        if conv_id:
            self.switch_to_conversation(conv_id)

    def switch_to_conversation(self, conv_id: str):
        self.current_conversation = self.db.get_conversation(conv_id)
        if not self.current_conversation:
            return
        self.conv_title_label.setText(self.current_conversation.title)
        self.render_messages()

    def rename_selected_conversation(self):
        current_item = self.conv_list_widget.currentItem()
        if not current_item or not self.current_conversation:
            return
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Conversation",
            "Enter new conversation title:",
            text=self.current_conversation.title
        )
        if ok and new_title.strip():
            self.db.update_conversation_title(self.current_conversation.id, new_title.strip())
            self.current_conversation.title = new_title.strip()
            self.conv_title_label.setText(new_title.strip())
            current_item.setText(f"💬  {new_title.strip()}")

    def delete_selected_conversation(self):
        current_item = self.conv_list_widget.currentItem()
        if not current_item or not self.current_conversation:
            return
        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            f"Permanently delete conversation '{self.current_conversation.title}' and all its messages?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_conversation(self.current_conversation.id)
            row = self.conv_list_widget.row(current_item)
            self.conv_list_widget.takeItem(row)
            if self.conv_list_widget.count() > 0:
                self.conv_list_widget.setCurrentRow(0)
                self.switch_to_conversation(self.conv_list_widget.item(0).data(Qt.UserRole))
            else:
                self.new_conversation()

    # -------------------------------------------------------------------------
    # Message Rendering & Sending
    # -------------------------------------------------------------------------
    def render_messages(self, streaming_extra: str = ""):
        if not self.current_conversation:
            return

        messages = self.db.list_messages(self.current_conversation.id)
        html_blocks = []

        for msg in messages:
            if msg.role == "user":
                bubble = f"""
                <div style='margin: 12px 0px 12px 60px; text-align: right;'>
                    <span style='color: #38bdf8; font-weight: bold; font-size: 11px;'>COMMANDER</span>
                    <div style='background-color: rgba(0, 114, 255, 0.2); border: 1px solid rgba(0, 240, 255, 0.35); border-radius: 10px; padding: 10px 14px; display: inline-block; text-align: left; color: #f8fafc;'>
                        {self._escape_and_format(msg.content)}
                    </div>
                </div>
                """
            else:
                bubble = f"""
                <div style='margin: 12px 60px 12px 0px;'>
                    <span style='color: #00f0ff; font-weight: bold; font-size: 11px;'>◈ {config.assistant_name.upper()}</span>
                    <div style='background-color: rgba(18, 26, 47, 0.85); border: 1px solid #1e293b; border-radius: 10px; padding: 12px 16px; color: #f1f5f9;'>
                        {self._escape_and_format(msg.content)}
                    </div>
                </div>
                """
            html_blocks.append(bubble)

        if streaming_extra:
            streaming_bubble = f"""
            <div style='margin: 12px 60px 12px 0px;'>
                <span style='color: #b829ea; font-weight: bold; font-size: 11px;'>◈ {config.assistant_name.upper()} (THINKING...)</span>
                <div style='background-color: rgba(18, 26, 47, 0.85); border: 1px solid rgba(184, 41, 234, 0.4); border-radius: 10px; padding: 12px 16px; color: #f1f5f9;'>
                    {self._escape_and_format(streaming_extra)}
                </div>
            </div>
            """
            html_blocks.append(streaming_bubble)

        self.message_browser.setHtml("".join(html_blocks))
        # Scroll to bottom
        sb = self.message_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _escape_and_format(self, text: str) -> str:
        """Lightweight formatting preserving paragraphs, bold, and code blocks."""
        # Simple HTML escaping
        safe = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        # Bold **text**
        import re
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        # Inline code `code`
        safe = re.sub(
            r"`([^`]+)`",
            r"<code style='background-color: #070b14; color: #00f0ff; padding: 2px 5px; border-radius: 3px; font-family: monospace;'>\1</code>",
            safe
        )
        return safe

    def send_message(self):
        text = self.input_field.text().strip()
        if not text or not self.current_conversation:
            return

        self.error_banner.hide()
        self.input_field.clear()

        # Add user message to DB
        self.db.add_message(self.current_conversation.id, role="user", content=text)
        self.render_messages()

        # Retrieve relevant memories for context injection
        relevant_memories = memory_service.get_relevant_memories(text)

        # Build message history for provider
        raw_msgs = self.db.list_messages(self.current_conversation.id)
        msg_payload = [{"role": m.role, "content": m.content} for m in raw_msgs]

        # UI State for generation
        self.btn_send.hide()
        self.btn_cancel.show()
        self.input_field.setEnabled(False)
        self.active_provider_tag.setText("PROCESSING...")
        self.active_provider_tag.setStyleSheet(f"color: {Colors.STATUS_THINKING}; font-weight: bold;")
        self.generation_state_changed.emit("thinking")

        self._streaming_content = ""

        # Launch AIWorker thread
        self.ai_worker = AIWorker(
            messages=msg_payload,
            memories=relevant_memories,
            document_context=self.active_document_context,
            parent=self
        )
        self.ai_worker.chunk_received.connect(self._on_chunk_received)
        self.ai_worker.finished.connect(self._on_generation_finished)
        self.ai_worker.error.connect(self._on_generation_error)
        self.ai_worker.cancelled.connect(self._on_generation_cancelled)
        self.ai_worker.start()

    @Slot(str)
    def _on_chunk_received(self, chunk: str):
        self._streaming_content += chunk
        self.render_messages(streaming_extra=self._streaming_content)

    @Slot(str, str)
    def _on_generation_finished(self, response: str, provider_type: str):
        self.db.add_message(self.current_conversation.id, role="assistant", content=response)
        self._streaming_content = ""
        self.render_messages()
        self._reset_input_state()
        self.active_provider_tag.setText(provider_type.upper())
        self.active_provider_tag.setStyleSheet(f"color: {Colors.CYAN_PRIMARY}; font-weight: bold;")
        self.generation_state_changed.emit("idle")

    @Slot(str)
    def _on_generation_error(self, err_msg: str):
        self._streaming_content = ""
        self.render_messages()
        self._reset_input_state()
        self.error_banner.setText(f"⚠ Generation Error: {err_msg}")
        self.error_banner.show()
        self.active_provider_tag.setText("ERROR")
        self.active_provider_tag.setStyleSheet(f"color: {Colors.STATUS_ERROR}; font-weight: bold;")
        self.generation_state_changed.emit("error")

    @Slot()
    def _on_generation_cancelled(self):
        if self._streaming_content:
            self.db.add_message(
                self.current_conversation.id,
                role="assistant",
                content=self._streaming_content + "\n\n*(Generation interrupted)*",
                status="cancelled"
            )
        self._streaming_content = ""
        self.render_messages()
        self._reset_input_state()
        self.active_provider_tag.setText("CANCELLED")
        self.generation_state_changed.emit("idle")

    def cancel_generation(self):
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.cancel()

    def _reset_input_state(self):
        self.btn_cancel.hide()
        self.btn_send.show()
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

    def _copy_last_response(self):
        if not self.current_conversation:
            return
        msgs = self.db.list_messages(self.current_conversation.id)
        assistant_msgs = [m for m in msgs if m.role == "assistant"]
        if assistant_msgs:
            last = assistant_msgs[-1].content
            QApplication.clipboard().setText(last)
            self.active_provider_tag.setText("COPIED!")
