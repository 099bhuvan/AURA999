from typing import Callable, List, Tuple
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QButtonGroup,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen

from app.ui.theme import Colors


class SidebarButton(QPushButton):
    """Custom sidebar navigation button with cyan glow accent."""

    def __init__(self, icon_str: str, text: str, page_index: int, parent: QWidget = None):
        super().__init__(parent)
        self.page_index = page_index
        self.setText(f"  {icon_str}   {text}")
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                text-align: left;
                padding-left: 18px;
                border: none;
                border-left: 3px solid transparent;
                font-size: 13px;
                font-weight: 500;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 240, 255, 0.07);
                color: {Colors.TEXT_PRIMARY};
                border-left: 3px solid rgba(0, 240, 255, 0.5);
            }}
            QPushButton:checked {{
                background-color: rgba(0, 240, 255, 0.12);
                color: #ffffff;
                font-weight: 600;
                border-left: 3px solid {Colors.CYAN_PRIMARY};
            }}
        """)


class Sidebar(QWidget):
    """Futuristic navigation sidebar for AURA."""

    page_changed = Signal(int)

    NAV_ITEMS: List[Tuple[str, str, int]] = [
        ("⬡", "Home Dashboard", 0),
        ("💬", "AI Neural Chat", 1),
        ("🎙", "Voice Assistant", 2),
        ("🧠", "Long-Term Memory", 3),
        ("📄", "Document Intelligence", 4),
        ("⏰", "Smart Reminders", 5),
        ("⚡", "Desktop Automation", 6),
        ("⚙", "System & AI Settings", 7),
    ]

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.buttons: List[SidebarButton] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)

        # Brand Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(18, 8, 18, 16)

        brand_logo = QLabel("◈")
        brand_logo.setStyleSheet(f"color: {Colors.CYAN_PRIMARY}; font-size: 24px; font-weight: bold;")
        
        brand_title = QLabel("AURA")
        brand_title.setStyleSheet(f"""
            color: #ffffff;
            font-size: 19px;
            font-weight: 800;
            letter-spacing: 2px;
        """)

        brand_sub = QLabel("AI v1.0")
        brand_sub.setStyleSheet(f"""
            color: {Colors.CYAN_DIM};
            font-size: 10px;
            font-weight: 600;
            background-color: rgba(0, 240, 255, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(0, 240, 255, 0.25);
        """)

        header_layout.addWidget(brand_logo)
        header_layout.addWidget(brand_title)
        header_layout.addWidget(brand_sub)
        header_layout.addStretch()

        layout.addWidget(header_widget)

        # Subtle divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {Colors.BORDER_SUBTLE}; max-height: 1px; margin-bottom: 8px;")
        layout.addWidget(divider)

        # Nav Buttons
        for icon, title, page_idx in self.NAV_ITEMS:
            btn = SidebarButton(icon, title, page_idx, self)
            btn.clicked.connect(lambda checked, idx=page_idx: self._on_btn_clicked(idx))
            self.button_group.addButton(btn, page_idx)
            self.buttons.append(btn)
            layout.addWidget(btn)

        # Set default active page (Home)
        if self.buttons:
            self.buttons[0].setChecked(True)

        layout.addStretch()

        # System Status Chip at bottom
        self.status_container = QWidget()
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setContentsMargins(16, 8, 16, 8)
        
        status_card = QFrame()
        status_card.setStyleSheet(f"""
            background-color: rgba(13, 19, 34, 0.8);
            border: 1px solid {Colors.BORDER_SUBTLE};
            border-radius: 6px;
            padding: 8px;
        """)
        card_layout = QHBoxLayout(status_card)
        card_layout.setContentsMargins(8, 6, 8, 6)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {Colors.STATUS_ONLINE}; font-size: 12px;")

        self.status_text = QLabel("SYSTEM READY")
        self.status_text.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")

        card_layout.addWidget(self.status_dot)
        card_layout.addWidget(self.status_text)
        card_layout.addStretch()

        status_layout.addWidget(status_card)
        layout.addWidget(self.status_container)

    def _on_btn_clicked(self, page_index: int):
        self.page_changed.emit(page_index)

    def select_page(self, page_index: int):
        """Programmatically switch active sidebar button."""
        btn = self.button_group.button(page_index)
        if btn:
            btn.setChecked(True)

    def update_system_status(self, text: str, color_hex: str = Colors.STATUS_ONLINE):
        self.status_text.setText(text.upper())
        self.status_dot.setStyleSheet(f"color: {color_hex}; font-size: 12px;")

    def paintEvent(self, event):
        # Draw background and right border
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Colors.BG_MAIN))
        painter.setPen(QPen(QColor(Colors.BORDER_SUBTLE), 1))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        painter.end()
        super().paintEvent(event)
