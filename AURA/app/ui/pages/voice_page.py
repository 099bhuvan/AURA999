from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QSlider,
    QCheckBox,
    QProgressBar,
    QFrame,
    QLineEdit,
)
from PySide6.QtCore import Qt, Signal, Slot

from app.config import config
from app.core.voice_service import voice_service
from app.core.ai_manager import ai_manager
from app.ui.theme import Colors
from app.ui.widgets.glass_panel import GlassPanel
from app.ui.widgets.aura_core import AuraCoreWidget
from app.ui.workers.voice_worker import VoiceTranscribeWorker, TTSWorker
from app.ui.workers.ai_worker import AIWorker


class VoicePage(QWidget):
    """Cinematic Voice Assistant interaction command center."""

    state_changed = Signal(str)  # "listening", "thinking", "speaking", "idle", "error"

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.transcribe_worker: Optional[VoiceTranscribeWorker] = None
        self.ai_worker: Optional[AIWorker] = None
        self.tts_worker: Optional[TTSWorker] = None
        self.is_recording = False

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(18)

        # Header
        header = QLabel("VOICE COMMAND INTERFACE")
        header.setObjectName("pageTitle")
        sub = QLabel("Real-time bi-directional voice transmission • Speech-to-Text & Offline Speech Synthesis")
        sub.setObjectName("pageSubtitle")
        main_layout.addWidget(header)
        main_layout.addWidget(sub)

        # Center Section: Dedicated Aura Core & Audio Waveform
        center_row = QHBoxLayout()
        center_row.setSpacing(20)

        # Left Column: Visual Core & Voice Controls
        control_panel = GlassPanel(title="VOICE CONTROLS", border_glow=True)
        control_panel.setFixedWidth(380)
        c_layout = control_panel.layout
        c_layout.setAlignment(Qt.AlignCenter)

        self.voice_core = AuraCoreWidget(self, size=240)
        c_layout.addWidget(self.voice_core, alignment=Qt.AlignCenter)

        # Audio level bar
        self.audio_level_bar = QProgressBar()
        self.audio_level_bar.setRange(0, 100)
        self.audio_level_bar.setValue(0)
        self.audio_level_bar.setFixedHeight(8)
        self.audio_level_bar.setTextVisible(False)
        self.audio_level_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #070b14;
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0072ff, stop:1 #00f0ff);
                border-radius: 4px;
            }}
        """)
        c_layout.addWidget(self.audio_level_bar)

        self.status_chip = QLabel("STANDBY — READY FOR INPUT")
        self.status_chip.setStyleSheet(f"""
            color: {Colors.CYAN_PRIMARY};
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 1px;
            padding: 4px 10px;
            background-color: rgba(0, 240, 255, 0.08);
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-radius: 4px;
        """)
        c_layout.addWidget(self.status_chip, alignment=Qt.AlignCenter)

        # Main Mic Push-to-Talk / Toggle Button
        self.btn_mic_toggle = QPushButton("🎙 START RECORDING")
        self.btn_mic_toggle.setObjectName("primaryButton")
        self.btn_mic_toggle.setMinimumHeight(46)
        self.btn_mic_toggle.clicked.connect(self.toggle_recording)
        c_layout.addWidget(self.btn_mic_toggle)

        # Interrupt / Stop Speaking Button
        self.btn_interrupt = QPushButton("⏹ INTERRUPT / STOP SPEECH")
        self.btn_interrupt.setObjectName("dangerButton")
        self.btn_interrupt.setMinimumHeight(38)
        self.btn_interrupt.clicked.connect(self.stop_all)
        c_layout.addWidget(self.btn_interrupt)

        # Voice Settings inside control panel
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"background-color: rgba(7, 11, 20, 0.6); border-radius: 6px; padding: 8px;")
        sf_layout = QVBoxLayout(settings_frame)
        sf_layout.setSpacing(8)

        self.cb_voice_enabled = QCheckBox("Voice Responses Enabled (TTS)")
        self.cb_voice_enabled.setChecked(config.voice_enabled)
        self.cb_voice_enabled.toggled.connect(self._on_voice_toggle)
        sf_layout.addWidget(self.cb_voice_enabled)

        # Speech rate slider
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Speech Rate:")
        rate_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(100, 260)
        self.rate_slider.setValue(config.speech_rate)
        self.rate_slider.valueChanged.connect(self._on_rate_changed)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_slider)
        sf_layout.addLayout(rate_layout)

        c_layout.addWidget(settings_frame)
        center_row.addWidget(control_panel)

        # Right Column: Real-time Transcript & Conversation Stream
        transcript_panel = GlassPanel(title="VOICE TRANSCRIPT & RECOGNITION LOG", border_glow=False)
        t_layout = transcript_panel.layout

        self.transcript_browser = QTextBrowser()
        self.transcript_browser.setStyleSheet(f"""
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
        t_layout.addWidget(self.transcript_browser)

        # Fallback Text Input for hardware without microphone
        fallback_row = QHBoxLayout()
        self.fallback_input = QLineEdit()
        self.fallback_input.setPlaceholderText("Microphone unavailable? Type voice command text here...")
        self.fallback_input.returnPressed.connect(self._send_fallback_text)
        fallback_row.addWidget(self.fallback_input)

        btn_fallback_send = QPushButton("SUBMIT ◈")
        btn_fallback_send.clicked.connect(self._send_fallback_text)
        fallback_row.addWidget(btn_fallback_send)
        t_layout.addLayout(fallback_row)

        center_row.addWidget(transcript_panel)
        main_layout.addLayout(center_row)

        self._append_transcript("SYSTEM", f"{config.assistant_name} voice subsystem initialized. Press 'Start Recording' or type a command.")

    def _append_transcript(self, speaker: str, text: str):
        color = Colors.CYAN_PRIMARY if speaker == "SYSTEM" or speaker == config.assistant_name.upper() else "#38bdf8"
        entry = f"<div style='margin-bottom: 10px;'><span style='color: {color}; font-weight: bold;'>[{speaker}]</span> <span style='color: #e2e8f0;'>{text}</span></div>"
        self.transcript_browser.append(entry)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_and_transcribe()

    def start_recording(self):
        # Verify microphone hardware
        if not voice_service.check_microphone_available():
            self._append_transcript("SYSTEM", "⚠ Notice: No active microphone hardware detected. Use the fallback text input below.")
            self.status_chip.setText("NO MICROPHONE HARDWARE")
            self.status_chip.setStyleSheet(f"color: {Colors.STATUS_ERROR}; font-weight: bold;")
            return

        self.is_recording = True
        self.btn_mic_toggle.setText("⏹ STOP RECORDING")
        self.btn_mic_toggle.setObjectName("dangerButton")
        self.btn_mic_toggle.setStyle(self.btn_mic_toggle.style())
        self.status_chip.setText("LISTENING... SPEAK NOW")
        self.status_chip.setStyleSheet(f"color: {Colors.STATUS_LISTENING}; font-weight: bold;")
        self.voice_core.set_state(AuraCoreWidget.STATE_LISTENING)
        self.state_changed.emit("listening")

        self.transcribe_worker = VoiceTranscribeWorker(self)
        self.transcribe_worker.audio_level_changed.connect(self._on_audio_level)
        self.transcribe_worker.transcription_ready.connect(self._on_transcription_ready)
        self.transcribe_worker.error.connect(self._on_transcribe_error)
        self.transcribe_worker.start()

    def stop_and_transcribe(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.btn_mic_toggle.setText("🎙 START RECORDING")
        self.btn_mic_toggle.setObjectName("primaryButton")
        self.btn_mic_toggle.setStyle(self.btn_mic_toggle.style())
        self.status_chip.setText("PROCESSING SPEECH...")
        self.status_chip.setStyleSheet(f"color: {Colors.STATUS_THINKING}; font-weight: bold;")
        self.voice_core.set_state(AuraCoreWidget.STATE_THINKING)
        self.state_changed.emit("thinking")

        if self.transcribe_worker:
            self.transcribe_worker.stop_and_transcribe()

    @Slot(float)
    def _on_audio_level(self, level: float):
        self.voice_core.set_audio_level(level)
        self.audio_level_bar.setValue(int(level * 100))

    @Slot(str)
    def _on_transcription_ready(self, recognized_text: str):
        self.audio_level_bar.setValue(0)
        self.voice_core.set_audio_level(0.0)

        if not recognized_text.strip():
            self._append_transcript("SYSTEM", "(Audio capture silent or unintelligible. Ready for next input.)")
            self._set_idle()
            return

        self._append_transcript("USER (VOICE)", recognized_text)
        self._process_command(recognized_text)

    def _send_fallback_text(self):
        text = self.fallback_input.text().strip()
        if not text:
            return
        self.fallback_input.clear()
        self._append_transcript("USER (TEXT)", text)
        self._process_command(text)

    def _process_command(self, text: str):
        """Send recognized text to AI provider and trigger TTS playback."""
        self.status_chip.setText("SYNTHESIZING RESPONSE...")
        self.status_chip.setStyleSheet(f"color: {Colors.STATUS_THINKING}; font-weight: bold;")
        self.voice_core.set_state(AuraCoreWidget.STATE_THINKING)
        self.state_changed.emit("thinking")

        messages = [{"role": "user", "content": text}]
        self.ai_worker = AIWorker(messages=messages, parent=self)
        self.ai_worker.finished.connect(self._on_ai_voice_response)
        self.ai_worker.error.connect(self._on_ai_error)
        self.ai_worker.start()

    @Slot(str, str)
    def _on_ai_voice_response(self, response_text: str, provider_type: str):
        self._append_transcript(config.assistant_name.upper(), response_text)

        if config.voice_enabled:
            self.status_chip.setText("SPEAKING...")
            self.status_chip.setStyleSheet(f"color: {Colors.STATUS_SPEAKING}; font-weight: bold;")
            self.voice_core.set_state(AuraCoreWidget.STATE_SPEAKING)
            self.state_changed.emit("speaking")

            self.tts_worker = TTSWorker(response_text, self)
            self.tts_worker.tts_finished.connect(self._set_idle)
            self.tts_worker.start()
        else:
            self._set_idle()

    @Slot(str)
    def _on_transcribe_error(self, err: str):
        self._append_transcript("ERROR", f"Audio processing error: {err}")
        self._set_idle()

    @Slot(str)
    def _on_ai_error(self, err: str):
        self._append_transcript("ERROR", f"AI response error: {err}")
        self._set_idle()

    def _set_idle(self):
        self.status_chip.setText("STANDBY — READY FOR INPUT")
        self.status_chip.setStyleSheet(f"color: {Colors.CYAN_PRIMARY}; font-weight: bold;")
        self.voice_core.set_state(AuraCoreWidget.STATE_IDLE)
        self.audio_level_bar.setValue(0)
        self.state_changed.emit("idle")

    def stop_all(self):
        """Interrupt any current recording, inference, or TTS playback."""
        if self.is_recording:
            self.stop_and_transcribe()
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.cancel()
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.cancel()
        self._set_idle()

    def _on_voice_toggle(self, checked: bool):
        config.voice_enabled = checked

    def _on_rate_changed(self, val: int):
        voice_service.set_speech_rate(val)
