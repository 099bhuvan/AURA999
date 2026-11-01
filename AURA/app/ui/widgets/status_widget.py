from datetime import datetime
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, QTimer, Signal
import psutil

from app.config import config
from app.ui.theme import Colors


class StatusHeaderWidget(QWidget):
    """Futuristic top status and telemetry bar for AURA."""

    emergency_stop_clicked = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self._setup_ui()

        # Update clock & telemetry timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock_and_telemetry)
        self.clock_timer.start(1000)
        self._update_clock_and_telemetry()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(16)

        # Assistant Greeting / Active Mode
        self.name_badge = QLabel(f"◈ {config.assistant_name.upper()}")
        self.name_badge.setStyleSheet(f"""
            color: {Colors.CYAN_PRIMARY};
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 1.5px;
        """)
        layout.addWidget(self.name_badge)

        self.mode_chip = QLabel("MODE: AUTO")
        self.mode_chip.setStyleSheet(f"""
            background-color: rgba(0, 240, 255, 0.1);
            color: {Colors.CYAN_PRIMARY};
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
        """)
        layout.addWidget(self.mode_chip)

        self.provider_status_chip = QLabel("● OLLAMA: DETECTING")
        self.provider_status_chip.setStyleSheet(f"""
            background-color: rgba(18, 26, 47, 0.8);
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER_SUBTLE};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(self.provider_status_chip)

        self.mic_status_chip = QLabel("🎙 MIC: IDLE")
        self.mic_status_chip.setStyleSheet(f"""
            background-color: rgba(18, 26, 47, 0.8);
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER_SUBTLE};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(self.mic_status_chip)

        layout.addStretch()

        # Telemetry info: CPU & RAM
        self.telemetry_label = QLabel("CPU: 0%  |  RAM: 0%")
        self.telemetry_label.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-family: 'Consolas', monospace;
            font-size: 11px;
        """)
        layout.addWidget(self.telemetry_label)

        # Clock
        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: 600;
            background-color: rgba(14, 20, 36, 0.6);
            border: 1px solid {Colors.BORDER_SUBTLE};
            padding: 4px 10px;
            border-radius: 4px;
        """)
        layout.addWidget(self.clock_label)

        # Emergency Automation Stop Button
        self.emergency_btn = QPushButton("⛔ STOP")
        self.emergency_btn.setObjectName("dangerButton")
        self.emergency_btn.setToolTip("Emergency Stop — Halt any pending/running desktop automations")
        self.emergency_btn.clicked.connect(self.emergency_stop_clicked.emit)
        self.emergency_btn.setFixedSize(76, 30)
        layout.addWidget(self.emergency_btn)

    def set_assistant_name(self, name: str):
        self.name_badge.setText(f"◈ {name.upper()}")

    def set_mode(self, mode: str):
        self.mode_chip.setText(f"MODE: {mode.upper()}")

    def set_provider_status(self, text: str, is_active: bool = True, is_error: bool = False):
        if is_error:
            color = Colors.STATUS_ERROR
            bg = "rgba(255, 0, 85, 0.15)"
            border = "rgba(255, 0, 85, 0.4)"
        elif is_active:
            color = Colors.STATUS_ONLINE
            bg = "rgba(0, 255, 157, 0.12)"
            border = "rgba(0, 255, 157, 0.3)"
        else:
            color = Colors.TEXT_SECONDARY
            bg = "rgba(18, 26, 47, 0.8)"
            border = Colors.BORDER_SUBTLE

        self.provider_status_chip.setText(f"● {text.upper()}")
        self.provider_status_chip.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)

    def set_mic_status(self, text: str, active: bool = False):
        if active:
            color = Colors.STATUS_LISTENING
            bg = "rgba(0, 255, 204, 0.15)"
            border = Colors.CYAN_PRIMARY
        else:
            color = Colors.TEXT_SECONDARY
            bg = "rgba(18, 26, 47, 0.8)"
            border = Colors.BORDER_SUBTLE

        self.mic_status_chip.setText(f"🎙 {text.upper()}")
        self.mic_status_chip.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)

    def _update_clock_and_telemetry(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%Y-%m-%d  %H:%M:%S"))

        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.telemetry_label.setText(f"CPU: {cpu:.0f}%  |  RAM: {ram:.0f}%")
        except Exception:
            pass
