from typing import List, Dict, Optional
from PySide6.QtCore import QThread, Signal

from app.core.ai_manager import ai_manager


class AIWorker(QThread):
    """Worker thread for running AI inference asynchronously without blocking UI."""

    chunk_received = Signal(str)
    finished = Signal(str, str)  # response_text, provider_type
    error = Signal(str)
    cancelled = Signal()

    def __init__(
        self,
        messages: List[Dict[str, str]],
        memories: Optional[List[str]] = None,
        document_context: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.messages = messages
        self.memories = memories
        self.document_context = document_context
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            def on_chunk(delta: str):
                if not self._is_cancelled:
                    self.chunk_received.emit(delta)

            def check_cancel() -> bool:
                return self._is_cancelled

            response_text, provider_type = ai_manager.generate(
                messages=self.messages,
                stream_callback=on_chunk,
                cancel_check=check_cancel,
                memories=self.memories,
                document_context=self.document_context,
            )

            if self._is_cancelled:
                self.cancelled.emit()
            else:
                self.finished.emit(response_text, provider_type)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
