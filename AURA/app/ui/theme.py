"""AURA Design System & Theme Stylesheet.

Cinematic AI command center visual style:
- Black and deep navy background.
- Cyan and electric-blue luminous accents.
- Subtle violet highlights.
- Glass-morphism panels, glowing borders, clean typography.
"""

from dataclasses import dataclass
from typing import Dict, Any


class Colors:
    # Deep Backgrounds
    BG_DARKEST = "#04060a"
    BG_MAIN = "#070b14"
    BG_PANEL = "#0d1322"
    BG_PANEL_ALT = "#121a2f"
    BG_GLASS = "rgba(13, 19, 34, 0.75)"
    BG_GLASS_LIGHT = "rgba(22, 32, 56, 0.5)"
    
    # Glow & Accent Neons
    CYAN_PRIMARY = "#00f0ff"
    CYAN_GLOW = "rgba(0, 240, 255, 0.35)"
    CYAN_DIM = "#00a3b4"
    BLUE_ELECTRIC = "#0072ff"
    BLUE_DEEP = "#102a45"
    VIOLET_ACCENT = "#8a2be2"
    VIOLET_GLOW = "rgba(138, 43, 226, 0.35)"
    
    # Status Indicators
    STATUS_ONLINE = "#00ff9d"
    STATUS_OFFLINE = "#00f0ff"
    STATUS_IDLE = "#00d2ff"
    STATUS_LISTENING = "#00ffcc"
    STATUS_THINKING = "#b829ea"
    STATUS_SPEAKING = "#00f0ff"
    STATUS_WARNING = "#ffb703"
    STATUS_ERROR = "#ff0055"
    
    # Typography
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#475569"
    TEXT_ACCENT = "#38bdf8"
    
    # Borders & Dividers
    BORDER_SUBTLE = "#1e293b"
    BORDER_GLOW = "rgba(0, 240, 255, 0.3)"
    BORDER_ACTIVE = "#00f0ff"


def get_application_stylesheet() -> str:
    """Return the global QSS stylesheet for AURA."""
    return f"""
    /* Global Application Styles */
    QMainWindow, QDialog {{
        background-color: {Colors.BG_DARKEST};
        color: {Colors.TEXT_PRIMARY};
        font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
    }}
    
    QWidget {{
        color: {Colors.TEXT_PRIMARY};
        font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
        font-size: 13px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {Colors.BG_DARKEST};
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: #1e293b;
        min-height: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Colors.CYAN_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {Colors.BG_DARKEST};
        height: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: #1e293b;
        min-width: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {Colors.CYAN_DIM};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {Colors.BG_PANEL};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_SUBTLE};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {Colors.BG_PANEL_ALT};
        border: 1px solid {Colors.CYAN_PRIMARY};
        color: #ffffff;
    }}
    QPushButton:pressed {{
        background-color: {Colors.BLUE_DEEP};
        border: 1px solid {Colors.BLUE_ELECTRIC};
    }}
    QPushButton:disabled {{
        background-color: rgba(20, 26, 40, 0.4);
        color: {Colors.TEXT_MUTED};
        border: 1px solid #141b2b;
    }}

    /* Primary Accent Buttons */
    QPushButton#primaryButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0072ff, stop:1 #00f0ff);
        color: #04060a;
        font-weight: 700;
        border: none;
        border-radius: 6px;
    }}
    QPushButton#primaryButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0088ff, stop:1 #33f3ff);
    }}
    QPushButton#primaryButton:pressed {{
        background: #005bbf;
    }}

    /* Danger / Emergency Buttons */
    QPushButton#dangerButton {{
        background-color: rgba(255, 0, 85, 0.15);
        color: #ff3377;
        border: 1px solid rgba(255, 0, 85, 0.5);
        font-weight: 600;
    }}
    QPushButton#dangerButton:hover {{
        background-color: rgba(255, 0, 85, 0.3);
        border: 1px solid #ff0055;
        color: #ffffff;
    }}

    /* Input Fields */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {Colors.BG_PANEL};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_SUBTLE};
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: {Colors.BLUE_ELECTRIC};
        selection-color: #ffffff;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {Colors.CYAN_PRIMARY};
        background-color: {Colors.BG_PANEL_ALT};
    }}

    /* Combo Boxes */
    QComboBox {{
        background-color: {Colors.BG_PANEL};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_SUBTLE};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 24px;
    }}
    QComboBox:hover, QComboBox:focus {{
        border: 1px solid {Colors.CYAN_PRIMARY};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {Colors.BG_PANEL};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_SUBTLE};
        selection-background-color: {Colors.BLUE_ELECTRIC};
        selection-color: #ffffff;
        outline: none;
    }}

    /* Lists and Tables */
    QListWidget, QTableWidget, QTreeWidget {{
        background-color: {Colors.BG_PANEL};
        border: 1px solid {Colors.BORDER_SUBTLE};
        border-radius: 6px;
        color: {Colors.TEXT_PRIMARY};
        outline: none;
    }}
    QListWidget::item, QTableWidget::item {{
        padding: 8px 12px;
        border-radius: 4px;
        margin: 2px 4px;
    }}
    QListWidget::item:hover, QTableWidget::item:hover {{
        background-color: rgba(0, 240, 255, 0.08);
    }}
    QListWidget::item:selected, QTableWidget::item:selected {{
        background-color: rgba(0, 240, 255, 0.18);
        border: 1px solid rgba(0, 240, 255, 0.35);
        color: #ffffff;
    }}

    /* Checkboxes & Radios */
    QCheckBox, QRadioButton {{
        spacing: 8px;
        color: {Colors.TEXT_PRIMARY};
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {Colors.BORDER_SUBTLE};
        border-radius: 4px;
        background-color: {Colors.BG_PANEL};
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border: 1px solid {Colors.CYAN_PRIMARY};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {Colors.CYAN_PRIMARY};
        border: 1px solid {Colors.CYAN_PRIMARY};
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {Colors.BG_PANEL_ALT};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.CYAN_PRIMARY};
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 12px;
    }}

    /* Labels */
    QLabel#pageTitle {{
        font-size: 22px;
        font-weight: 700;
        color: {Colors.TEXT_PRIMARY};
        letter-spacing: 0.5px;
    }}
    QLabel#pageSubtitle {{
        font-size: 13px;
        color: {Colors.TEXT_SECONDARY};
    }}
    QLabel#sectionHeader {{
        font-size: 14px;
        font-weight: 600;
        color: {Colors.CYAN_PRIMARY};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    """
