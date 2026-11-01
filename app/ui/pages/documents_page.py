from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QTextBrowser,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, Slot

from app.core.document_service import document_service
from app.database.models import DocumentRecord
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel
from app.ui.workers.ai_worker import AIWorker


class DocumentsPage(QWidget):
    """Document Intelligence interface for PDFs, DOCX, and text analysis."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.active_doc: Optional[DocumentRecord] = None
        self.ai_worker: Optional[AIWorker] = None

        self._setup_ui()
        self.refresh_document_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Header
        header = QLabel("DOCUMENT INTELLIGENCE")
        header.setObjectName("pageTitle")
        sub = QLabel("Analyze local PDF, DOCX, and TXT files • Executive Summaries • Grounded Q&A")
        sub.setObjectName("pageSubtitle")
        main_layout.addWidget(header)
        main_layout.addWidget(sub)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Ingested Documents List
        list_panel = GlassPanel(title="INGESTED DOCUMENTS", border_glow=False)
        list_panel.setFixedWidth(280)
        lp_layout = list_panel.layout

        btn_browse = QPushButton("📁 Ingest New Document")
        btn_browse.setObjectName("primaryButton")
        btn_browse.setMinimumHeight(38)
        btn_browse.clicked.connect(self._browse_and_ingest)
        lp_layout.addWidget(btn_browse)

        self.doc_list = QListWidget()
        self.doc_list.itemClicked.connect(self._on_doc_selected)
        lp_layout.addWidget(self.doc_list)

        btn_remove = QPushButton("🗑 Remove Record")
        btn_remove.setObjectName("dangerButton")
        btn_remove.clicked.connect(self._remove_selected_doc)
        lp_layout.addWidget(btn_remove)

        splitter.addWidget(list_panel)

        # Right Column: Document Insights & Q&A
        doc_details_panel = GlassPanel(title="DOCUMENT ANALYSIS & GROUNDED Q&A", border_glow=True)
        d_layout = doc_details_panel.layout

        # Metadata Bar
        self.meta_label = QLabel("No document selected. Choose a document on the left or click 'Ingest New Document'.")
        self.meta_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; margin-bottom: 4px;")
        d_layout.addWidget(self.meta_label)

        # Action Buttons: Summarize / Key Takeaways
        btn_action_bar = QHBoxLayout()
        self.btn_summarize = QPushButton("⚡ Generate AI Summary")
        self.btn_summarize.setObjectName("primaryButton")
        self.btn_summarize.clicked.connect(self._summarize_current)
        self.btn_summarize.setEnabled(False)
        btn_action_bar.addWidget(self.btn_summarize)

        self.btn_key_points = QPushButton("📌 Extract Key Takeaways")
        self.btn_key_points.clicked.connect(self._extract_key_points)
        self.btn_key_points.setEnabled(False)
        btn_action_bar.addWidget(self.btn_key_points)

        btn_action_bar.addStretch()
        d_layout.addLayout(btn_action_bar)

        # Insights Display Area
        self.insights_browser = QTextBrowser()
        self.insights_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {Colors.BG_MAIN};
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 8px;
                padding: 14px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        d_layout.addWidget(self.insights_browser)

        # Grounded Q&A Input Bar
        qa_bar = QHBoxLayout()
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText("Ask a question specifically about this document...")
        self.qa_input.returnPressed.connect(self._ask_doc_question)
        self.qa_input.setEnabled(False)
        qa_bar.addWidget(self.qa_input)

        self.btn_ask = QPushButton("Ask AI ◈")
        self.btn_ask.clicked.connect(self._ask_doc_question)
        self.btn_ask.setEnabled(False)
        qa_bar.addWidget(self.btn_ask)

        d_layout.addLayout(qa_bar)
        splitter.addWidget(doc_details_panel)
        splitter.setSizes([280, 720])

        main_layout.addWidget(splitter)

    def refresh_document_list(self):
        self.doc_list.clear()
        docs = document_service.list_documents()
        for doc in docs:
            item = QListWidgetItem(f"📄  {doc.filename}")
            item.setData(Qt.UserRole, doc.id)
            self.doc_list.addItem(item)

        if docs and not self.active_doc:
            self.doc_list.setCurrentRow(0)
            self._select_doc(docs[0].id)

    def _browse_and_ingest(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document to Ingest",
            "",
            "Documents (*.pdf *.docx *.txt *.md);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt *.md)"
        )
        if not file_path:
            return

        try:
            record = document_service.ingest_document(file_path)
            self.refresh_document_list()
            self._select_doc(record.id)
            QMessageBox.information(self, "Document Ingested", f"Successfully ingested: {record.filename}")
        except Exception as e:
            QMessageBox.critical(self, "Ingestion Error", str(e))

    def _on_doc_selected(self, item: QListWidgetItem):
        doc_id = item.data(Qt.UserRole)
        if doc_id:
            self._select_doc(doc_id)

    def _select_doc(self, doc_id: str):
        self.active_doc = document_service.get_document(doc_id)
        if not self.active_doc:
            return

        size_kb = self.active_doc.file_size / 1024
        self.meta_label.setText(
            f"FILE: {self.active_doc.filename} | TYPE: {self.active_doc.file_type.upper()} | "
            f"SIZE: {size_kb:.1f} KB | WORDS: ~{len(self.active_doc.extracted_text.split())}"
        )

        self.btn_summarize.setEnabled(True)
        self.btn_key_points.setEnabled(True)
        self.qa_input.setEnabled(True)
        self.btn_ask.setEnabled(True)

        if self.active_doc.summary:
            self.insights_browser.setMarkdown(self.active_doc.summary)
        else:
            preview = self.active_doc.extracted_text[:1200]
            self.insights_browser.setPlainText(
                f"--- DOCUMENT PREVIEW (First 1,200 characters) ---\n\n{preview}...\n\n"
                "(Click 'Generate AI Summary' above for full synthesis and key points)"
            )

    def _remove_selected_doc(self):
        if not self.active_doc:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove '{self.active_doc.filename}' from AURA history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            document_service.delete_document(self.active_doc.id)
            self.active_doc = None
            self.btn_summarize.setEnabled(False)
            self.btn_key_points.setEnabled(False)
            self.qa_input.setEnabled(False)
            self.btn_ask.setEnabled(False)
            self.insights_browser.clear()
            self.meta_label.setText("No document selected.")
            self.refresh_document_list()

    def _summarize_current(self):
        if not self.active_doc:
            return

        self.insights_browser.setPlainText("AI is analyzing document and generating executive summary...")
        self.btn_summarize.setEnabled(False)

        prompt = (
            f"Please provide an executive summary and analysis of the document titled '{self.active_doc.filename}'.\n"
            "Format your response with clear Markdown headers, bullet points, and key takeaways."
        )
        self._run_doc_ai(prompt)

    def _extract_key_points(self):
        if not self.active_doc:
            return

        self.insights_browser.setPlainText("Extracting actionable takeaways and critical facts...")
        prompt = (
            f"Analyze the document '{self.active_doc.filename}' and extract the top 7 most critical actionable takeaways, "
            "metrics, or decisions in bullet format."
        )
        self._run_doc_ai(prompt)

    def _ask_doc_question(self):
        question = self.qa_input.text().strip()
        if not question or not self.active_doc:
            return

        self.qa_input.clear()
        self.insights_browser.append(f"\n\n**QUESTION:** {question}\n\n*Analyzing document...*")
        self._run_doc_ai(question)

    def _run_doc_ai(self, query: str):
        if not self.active_doc:
            return

        messages = [{"role": "user", "content": query}]
        self.ai_worker = AIWorker(
            messages=messages,
            document_context=self.active_doc.extracted_text,
            parent=self
        )
        self.ai_worker.finished.connect(self._on_doc_ai_finished)
        self.ai_worker.error.connect(self._on_doc_ai_error)
        self.ai_worker.start()

    @Slot(str, str)
    def _on_doc_ai_finished(self, response: str, provider_type: str):
        self.btn_summarize.setEnabled(True)
        self.insights_browser.setMarkdown(response)

    @Slot(str)
    def _on_doc_ai_error(self, err: str):
        self.btn_summarize.setEnabled(True)
        self.insights_browser.setPlainText(f"⚠ Analysis error: {err}")
