from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath

from app.ui.theme import Colors


class GlassPanel(QFrame):
    """Custom-painted glass-morphism container panel with glowing borders."""

    def __init__(
        self,
        title: str = "",
        parent: QWidget = None,
        corner_radius: int = 10,
        border_glow: bool = False,
        bg_opacity: int = 185,
    ):
        super().__init__(parent)
        self.title_text = title
        self.corner_radius = corner_radius
        self.border_glow = border_glow
        self.bg_opacity = bg_opacity
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Internal layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)
        
        if self.title_text:
            self.title_label = QLabel(self.title_text)
            self.title_label.setObjectName("sectionHeader")
            self.layout.addWidget(self.title_label)

    def set_title(self, title: str):
        self.title_text = title
        if hasattr(self, "title_label"):
            self.title_label.setText(title)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)

        # Background gradient: deep navy glass
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(14, 20, 36, self.bg_opacity))
        gradient.setColorAt(1.0, QColor(7, 11, 20, self.bg_opacity + 20))

        painter.fillPath(path, QBrush(gradient))

        # Border
        if self.border_glow:
            pen = QPen(QColor(0, 240, 255, 110), 1.5)
        else:
            pen = QPen(QColor(30, 41, 59, 140), 1.0)
        painter.setPen(pen)
        painter.drawPath(path)

        # Subtle cyber accent corner ticks
        if self.border_glow:
            painter.setPen(QPen(QColor(0, 240, 255, 200), 2))
            # Top-left accent tick
            painter.drawLine(rect.x() + 4, rect.y() + 10, rect.x() + 4, rect.y() + 4)
            painter.drawLine(rect.x() + 4, rect.y() + 4, rect.x() + 10, rect.y() + 4)
            # Bottom-right accent tick
            painter.drawLine(rect.right() - 10, rect.bottom() - 4, rect.right() - 4, rect.bottom() - 4)
            painter.drawLine(rect.right() - 4, rect.bottom() - 10, rect.right() - 4, rect.bottom() - 4)

        painter.end()
        super().paintEvent(event)
