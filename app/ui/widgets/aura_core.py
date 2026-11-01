import math
import random
import time
from typing import List, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QLinearGradient,
    QPainterPath,
    QFont,
)

from app.config import config
from app.ui.theme import Colors


class Particle:
    """Floating energy particle in the AURA core field."""

    def __init__(self, cx: float, cy: float, max_radius: float):
        self.cx = cx
        self.cy = cy
        self.max_radius = max_radius
        self.reset()

    def reset(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.dist = random.uniform(15, self.max_radius)
        self.speed = random.uniform(0.01, 0.035) * (1 if random.random() > 0.5 else -1)
        self.radial_speed = random.uniform(-0.3, 0.3)
        self.size = random.uniform(1.2, 3.2)
        self.alpha = random.randint(70, 220)
        self.life = random.uniform(0.4, 1.0)
        self.fade_speed = random.uniform(0.005, 0.02)

    def update(self, speed_factor: float = 1.0):
        self.angle += self.speed * speed_factor
        self.dist += self.radial_speed * speed_factor
        self.life -= self.fade_speed * speed_factor
        if self.dist < 10 or self.dist > self.max_radius or self.life <= 0:
            self.reset()

    def pos(self, cx: float, cy: float) -> Tuple[float, float]:
        x = cx + self.dist * math.cos(self.angle)
        y = cy + self.dist * math.sin(self.angle)
        return x, y


class AuraCoreWidget(QWidget):
    """Futuristic interactive animated AURA core widget."""

    STATE_IDLE = "idle"
    STATE_LISTENING = "listening"
    STATE_THINKING = "thinking"
    STATE_SPEAKING = "speaking"
    STATE_ERROR = "error"

    def __init__(self, parent: QWidget = None, size: int = 340):
        super().__init__(parent)
        self.setMinimumSize(size, size)
        self.core_size = size
        self.state = self.STATE_IDLE
        self.reduced_motion = config.reduced_motion

        # Core angles and dynamics
        self.rotation_ring1 = 0.0
        self.rotation_ring2 = 0.0
        self.rotation_ring3 = 0.0
        self.pulse_phase = 0.0
        self.audio_level = 0.0  # 0.0 to 1.0
        self.target_audio_level = 0.0
        
        # Interactive mouse dragging
        self.user_rotation_offset = 0.0
        self.is_dragging = False
        self.last_mouse_x = 0
        self.user_spin_velocity = 0.0

        # Particle system
        self.particles: List[Particle] = []
        self.init_particles(40 if not self.reduced_motion else 10)

        # Animation Timer (60 FPS standard, 30 FPS reduced motion)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        interval = 33 if self.reduced_motion else 16
        self.timer.start(interval)

        self.setToolTip("AURA Core — Click and drag horizontally to spin")

    def init_particles(self, count: int):
        cx = self.width() / 2 or 170
        cy = self.height() / 2 or 170
        self.particles = [Particle(cx, cy, 140) for _ in range(count)]

    def set_state(self, state: str):
        """Set state: idle, listening, thinking, speaking, error."""
        if state in (self.STATE_IDLE, self.STATE_LISTENING, self.STATE_THINKING, self.STATE_SPEAKING, self.STATE_ERROR):
            self.state = state
            self.update()

    def set_audio_level(self, level: float):
        """Set normalized audio level (0.0 to 1.0) for reactive waveforms."""
        self.target_audio_level = max(0.0, min(1.0, level))

    def set_reduced_motion(self, enabled: bool):
        self.reduced_motion = enabled
        self.timer.setInterval(33 if enabled else 16)
        self.init_particles(10 if enabled else 40)

    def _animate_step(self):
        # Smooth audio level transition
        self.audio_level += (self.target_audio_level - self.audio_level) * 0.25

        # Speed multipliers depending on core state
        if self.state == self.STATE_THINKING:
            speed1 = 2.4
            speed2 = -3.2
            speed3 = 1.8
            pulse_inc = 0.09
        elif self.state == self.STATE_LISTENING:
            speed1 = 0.8 + self.audio_level * 1.5
            speed2 = -0.6 - self.audio_level * 1.8
            speed3 = 0.4 + self.audio_level * 1.0
            pulse_inc = 0.06 + self.audio_level * 0.12
        elif self.state == self.STATE_SPEAKING:
            speed1 = 1.2 + self.audio_level * 2.0
            speed2 = -1.4 - self.audio_level * 2.5
            speed3 = 0.9 + self.audio_level * 1.5
            pulse_inc = 0.08 + self.audio_level * 0.15
        elif self.state == self.STATE_ERROR:
            speed1 = 0.3
            speed2 = -0.2
            speed3 = 0.1
            pulse_inc = 0.15  # Rapid warning pulse
        else:  # IDLE
            speed1 = 0.6
            speed2 = -0.4
            speed3 = 0.3
            pulse_inc = 0.03

        if self.reduced_motion:
            speed1 *= 0.3
            speed2 *= 0.3
            speed3 *= 0.3
            pulse_inc *= 0.4

        self.rotation_ring1 = (self.rotation_ring1 + speed1) % 360
        self.rotation_ring2 = (self.rotation_ring2 + speed2) % 360
        self.rotation_ring3 = (self.rotation_ring3 + speed3) % 360
        self.pulse_phase = (self.pulse_phase + pulse_inc) % (2 * math.pi)

        # Apply inertial spin velocity from user mouse drag
        if not self.is_dragging:
            self.user_rotation_offset += self.user_spin_velocity
            self.user_spin_velocity *= 0.94  # Friction decay

        # Update particles
        cx = self.width() / 2
        cy = self.height() / 2
        p_factor = 2.5 if self.state == self.STATE_THINKING else (1.5 if self.state == self.STATE_SPEAKING else 0.8)
        for p in self.particles:
            p.update(p_factor)

        self.update()

    # -------------------------------------------------------------------------
    # Mouse Interaction
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_x = event.position().x()
            self.user_spin_velocity = 0.0

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            cur_x = event.position().x()
            delta = cur_x - self.last_mouse_x
            self.user_rotation_offset += delta * 0.8
            self.user_spin_velocity = delta * 0.4
            self.last_mouse_x = cur_x
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        max_r = min(w, h) / 2.0 - 15

        # Colors based on state
        if self.state == self.STATE_ERROR:
            primary_color = QColor(255, 0, 85)
            glow_color = QColor(255, 0, 85, 90)
            center_color = QColor(255, 40, 100)
            accent_ring_color = QColor(255, 120, 160)
        elif self.state == self.STATE_THINKING:
            primary_color = QColor(184, 41, 234)
            glow_color = QColor(184, 41, 234, 100)
            center_color = QColor(210, 80, 255)
            accent_ring_color = QColor(0, 240, 255)
        elif self.state == self.STATE_LISTENING:
            primary_color = QColor(0, 255, 204)
            glow_color = QColor(0, 255, 204, 100)
            center_color = QColor(40, 255, 220)
            accent_ring_color = QColor(0, 150, 255)
        elif self.state == self.STATE_SPEAKING:
            primary_color = QColor(0, 240, 255)
            glow_color = QColor(0, 240, 255, 120)
            center_color = QColor(100, 255, 255)
            accent_ring_color = QColor(138, 43, 226)
        else:  # IDLE
            primary_color = QColor(0, 240, 255)
            glow_color = QColor(0, 240, 255, 80)
            center_color = QColor(0, 210, 255)
            accent_ring_color = QColor(0, 114, 255)

        pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0  # 0.0 to 1.0
        effective_audio = self.audio_level if self.state in (self.STATE_LISTENING, self.STATE_SPEAKING) else 0.0

        # 1. Background Aura Glow Field
        bg_glow_radius = max_r * (0.85 + 0.15 * pulse + 0.1 * effective_audio)
        bg_gradient = QRadialGradient(cx, cy, bg_glow_radius)
        bg_gradient.setColorAt(0.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), int(45 + 30 * pulse)))
        bg_gradient.setColorAt(0.5, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), int(15 + 15 * pulse)))
        bg_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_gradient))
        painter.drawEllipse(QPointF(cx, cy), bg_glow_radius, bg_glow_radius)

        # 2. Draw Floating Energy Particles
        for p in self.particles:
            px, py = p.pos(cx, cy)
            p_alpha = int(p.alpha * p.life * (0.6 + 0.4 * pulse))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), max(0, min(255, p_alpha)))))
            painter.drawEllipse(QPointF(px, py), p.size, p.size)

        # 3. Outer Reticle Ring (dashed & segmented)
        r_outer = max_r * 0.95
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_ring1 + self.user_rotation_offset)

        pen_outer = QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 100), 1.2)
        pen_outer.setDashPattern([12, 10, 4, 10])
        painter.setPen(pen_outer)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), r_outer, r_outer)

        # Reticle Tick Marks
        num_ticks = 16
        tick_pen = QPen(primary_color, 1.5)
        painter.setPen(tick_pen)
        for i in range(num_ticks):
            angle = (360 / num_ticks) * i
            rad = math.radians(angle)
            x1 = (r_outer - 5) * math.cos(rad)
            y1 = (r_outer - 5) * math.sin(rad)
            x2 = (r_outer + 5) * math.cos(rad)
            y2 = (r_outer + 5) * math.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        painter.restore()

        # 4. Middle Concentric Ring & Segmented Arcs
        r_mid = max_r * 0.72
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_ring2 + self.user_rotation_offset * 1.3)

        pen_mid = QPen(accent_ring_color, 1.8)
        pen_mid.setDashPattern([30, 20, 60, 20])
        painter.setPen(pen_mid)
        painter.drawEllipse(QPointF(0, 0), r_mid, r_mid)

        # Orbiting node dots
        for ang in [0, 90, 180, 270]:
            rad = math.radians(ang)
            nx = r_mid * math.cos(rad)
            ny = r_mid * math.sin(rad)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(primary_color))
            painter.drawEllipse(QPointF(nx, ny), 3.5, 3.5)
        painter.restore()

        # 5. Inner Orbital Ring & Acoustic Waveform
        r_inner = max_r * 0.50
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation_ring3 + self.user_rotation_offset * 0.7)

        pen_inner = QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 180), 2.0)
        painter.setPen(pen_inner)
        painter.drawEllipse(QPointF(0, 0), r_inner, r_inner)

        # Reactive Acoustic Waveform around inner orbital when active
        if self.state in (self.STATE_LISTENING, self.STATE_SPEAKING):
            wave_path = QPainterPath()
            points_count = 60
            for i in range(points_count + 1):
                ang = (360 / points_count) * i
                rad = math.radians(ang)
                # Harmonic ripple wave
                harm = math.sin(ang * 4 + self.pulse_phase * 3) * (6 + 18 * effective_audio)
                rw = r_inner + harm
                wx = rw * math.cos(rad)
                wy = rw * math.sin(rad)
                if i == 0:
                    wave_path.moveTo(wx, wy)
                else:
                    wave_path.lineTo(wx, wy)
            painter.setPen(QPen(QColor(center_color.red(), center_color.green(), center_color.blue(), 190), 1.6))
            painter.drawPath(wave_path)

        painter.restore()

        # 6. Glowing Central Sphere
        core_r = max_r * (0.28 + 0.05 * pulse + 0.06 * effective_audio)
        core_gradient = QRadialGradient(cx, cy, core_r)
        core_gradient.setColorAt(0.0, QColor(255, 255, 255, 250))
        core_gradient.setColorAt(0.35, QColor(center_color.red(), center_color.green(), center_color.blue(), 230))
        core_gradient.setColorAt(0.75, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 140))
        core_gradient.setColorAt(1.0, QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # Center highlight bead
        bead_r = core_r * 0.35
        painter.setBrush(QBrush(QColor(255, 255, 255, int(200 + 55 * pulse))))
        painter.drawEllipse(QPointF(cx, cy), bead_r, bead_r)

        # 7. State text watermark under core
        state_label = self.state.upper()
        painter.setPen(QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 160)))
        font = QFont("Segoe UI", 8, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 3.0)
        painter.setFont(font)
        painter.drawText(
            self.rect().adjusted(0, 0, 0, -6),
            Qt.AlignBottom | Qt.AlignHCenter,
            f"●  {state_label}  ●"
        )

        painter.end()
