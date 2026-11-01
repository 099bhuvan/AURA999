from PySide6.QtCore import QThread, Signal
from app.core.voice_service import voice_service


class VoiceTranscribeWorker(QThread):
    """Worker thread for recording audio and transcribing speech."""

    transcription_ready = Signal(str)
    audio_level_changed = Signal(float)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stopped = False

    def stop_and_transcribe(self):
        self._stopped = True

    def run(self):
        try:
            voice_service.start_recording(level_callback=self.audio_level_changed.emit)
            while not self._stopped:
                self.msleep(50)
            
            text = voice_service.stop_recording()
            self.transcription_ready.emit(text)
        except Exception as e:
            voice_service.is_recording = False
            self.error.emit(str(e))


class TTSWorker(QThread):
    """Worker thread for playing text-to-speech without freezing GUI."""

    tts_started = Signal()
    tts_finished = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        self.tts_started.emit()
        try:
            voice_service.speak_text(self.text, interrupt_check=lambda: self._cancel)
        finally:
            self.tts_finished.emit()
