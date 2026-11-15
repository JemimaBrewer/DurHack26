import math

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget


class VisualEffectsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.effect = None
        self.elapsed = 0.0
        self.snail_x = -100.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)
        self.timer.start(33)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def set_effect(self, effect):
        if effect != self.effect:
            self.effect = effect
            if effect == "snail" and self.snail_x >= self.width():
                self.snail_x = -100.0
            self.update()
        if effect:
            self.show()
        else:
            self.hide()

    def _advance(self):
        self.elapsed += 0.033
        if self.effect == "snail":
            self.snail_x += max(1.0, self.width() / 900)
            if self.snail_x > self.width() + 100:
                self.snail_x = -100.0
        if self.effect:
            self.update()

    def paintEvent(self, event):
        if not self.effect:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.effect == "flames":
            self._draw_flames(painter)
        else:
            self._draw_snail(painter)
        painter.end()

    def _draw_flames(self, painter):
        width = self.width()
        height = self.height()
        baseline = height
        columns = max(8, width // 28)
        column_width = width / columns

        for index in range(columns + 1):
            phase = self.elapsed * 7 + index * 1.7
            sway = math.sin(phase) * column_width * 0.22
            flame_height = height * (0.55 + 0.28 * (math.sin(phase * 1.31) + 1) / 2)
            x = index * column_width
            path = QPainterPath()
            path.moveTo(x - column_width * 0.62, baseline)
            path.cubicTo(
                x - column_width * 0.7,
                baseline - flame_height * 0.38,
                x + sway - column_width * 0.25,
                baseline - flame_height * 0.7,
                x + sway,
                baseline - flame_height,
            )
            path.cubicTo(
                x + column_width * 0.12,
                baseline - flame_height * 0.68,
                x + column_width * 0.72,
                baseline - flame_height * 0.42,
                x + column_width * 0.62,
                baseline,
            )
            path.closeSubpath()
            gradient = QLinearGradient(0, baseline - flame_height, 0, baseline)
            gradient.setColorAt(0, QColor("#fff4a3"))
            gradient.setColorAt(0.38, QColor("#ffbf3f"))
            gradient.setColorAt(1, QColor("#ed3b24"))
            painter.fillPath(path, gradient)

            inner = QPainterPath()
            inner.moveTo(x - column_width * 0.3, baseline)
            inner.cubicTo(
                x - column_width * 0.2,
                baseline - flame_height * 0.28,
                x + sway * 0.5,
                baseline - flame_height * 0.48,
                x + sway * 0.15,
                baseline - flame_height * 0.68,
            )
            inner.cubicTo(
                x + column_width * 0.35,
                baseline - flame_height * 0.4,
                x + column_width * 0.35,
                baseline - flame_height * 0.2,
                x + column_width * 0.3,
                baseline,
            )
            inner.closeSubpath()
            painter.fillPath(inner, QColor("#fff6c2"))

    def _draw_snail(self, painter):
        ground = self.height() - 13
        x = self.snail_x
        y = ground - 28

        body_gradient = QLinearGradient(0, y + 20, 0, ground)
        body_gradient.setColorAt(0, QColor("#a8d58d"))
        body_gradient.setColorAt(1, QColor("#4f8d52"))
        painter.setBrush(body_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(x), int(y + 29), 92, 22)
        painter.drawEllipse(int(x + 70), int(y + 7), 27, 38)

        shell_gradient = QRadialGradient(x + 39, y + 25, 32)
        shell_gradient.setColorAt(0, QColor("#f6c56f"))
        shell_gradient.setColorAt(0.72, QColor("#b56437"))
        shell_gradient.setColorAt(1, QColor("#713627"))
        painter.setBrush(shell_gradient)
        painter.drawEllipse(int(x + 10), int(y), 65, 65)
        painter.setPen(QColor("#713627"))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(x + 25), int(y + 15), 35, 35)
        painter.drawArc(int(x + 32), int(y + 22), 24, 24, 0, 270 * 16)

        painter.setPen(QColor("#4f8d52"))
        painter.drawLine(int(x + 88), int(y + 9), int(x + 98), int(y - 10))
        painter.drawLine(int(x + 91), int(y + 10), int(x + 111), int(y - 3))
        painter.setBrush(QColor("#243d2a"))
        painter.drawEllipse(int(x + 96), int(y - 13), 5, 5)
        painter.drawEllipse(int(x + 109), int(y - 6), 5, 5)
