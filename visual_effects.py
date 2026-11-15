import math
import random

import noise
import numpy
import pygame
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QWidget


class PygameFire:
    PARTICLE_COUNT = 2400
    MAX_FPS = 60

    def __init__(self):
        pygame.init()
        self.random = random.Random()
        self.clock = pygame.time.Clock()
        self.elapsed = 0.0
        self.surface = None
        self.particles = []
        self.width = 0
        self.height = 0

    def resize(self, width, height):
        width = max(1, width)
        height = max(1, height)
        if (width, height) == (self.width, self.height):
            return
        self.width, self.height = width, height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.particles = [self._new_particle(initial=True) for _ in range(self.PARTICLE_COUNT)]

    def _new_particle(self, initial=False):
        life = self.random.uniform(0.55, 1.8)
        return {
            "x": self.random.uniform(0, self.width),
            "y": self.random.uniform(self.height * 0.72, self.height) if initial else self.height + 4,
            "vx": self.random.uniform(-18, 18),
            "vy": self.random.uniform(-250, -90),
            "life": self.random.uniform(0, life) if initial else 0,
            "max_life": life,
            "size": self.random.uniform(0.8, 3.2),
            "noise": self.random.uniform(-1000, 1000),
        }

    def update(self):
        if self.surface is None:
            return
        dt = min(0.05, self.clock.tick(self.MAX_FPS) / 1000)
        self.elapsed += dt
        for particle in self.particles:
            particle["life"] += dt
            if particle["life"] >= particle["max_life"]:
                particle.update(self._new_particle())
                continue
            progress = particle["life"] / particle["max_life"]
            turbulence = noise.pnoise3(
                particle["x"] * 0.012,
                particle["y"] * 0.012,
                self.elapsed * 0.7 + particle["noise"],
                octaves=3,
            )
            particle["vx"] += turbulence * 180 * dt
            particle["vy"] -= (90 + (1 - progress) * 90) * dt
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            if particle["x"] < -20 or particle["x"] > self.width + 20 or particle["y"] < -20:
                particle.update(self._new_particle())

        self._render()

    def _render(self):
        self.surface.fill((0, 0, 0, 0))
        particles = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        glow = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        alpha_mask = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        for particle in self.particles:
            progress = particle["life"] / particle["max_life"]
            color = self._cooling_color(progress)
            center = (int(particle["x"]), int(particle["y"]))
            radius = max(1, int(particle["size"] * (1 - progress * 0.6)))
            lifetime_fade = math.sin(math.pi * progress) ** 0.7
            edge_fade = min(1.0, max(0.0, particle["y"] / (self.height * 0.3)))
            alpha = max(0, int(color[3] * lifetime_fade * edge_fade))
            color = (*color[:3], alpha)
            pygame.draw.circle(particles, color, center, radius)
            pygame.draw.circle(
                glow,
                (*color[:3], max(0, color[3] // 4)),
                center,
                radius * 4,
            )
            pygame.draw.circle(
                alpha_mask,
                (255, 255, 255, color[3]),
                center,
                radius * 4,
            )
        self.surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
        self.surface.blit(pygame.transform.gaussian_blur(glow, 6), (0, 0), special_flags=pygame.BLEND_ADD)
        self.surface.blit(particles, (0, 0), special_flags=pygame.BLEND_ADD)
        alpha = numpy.maximum(
            pygame.surfarray.array_alpha(alpha_mask),
            pygame.surfarray.array_alpha(particles),
        )
        pygame.surfarray.pixels_alpha(self.surface)[:] = alpha

    @staticmethod
    def _cooling_color(progress):
        stops = (
            (0.0, (255, 225, 125)),
            (0.22, (255, 132, 18)),
            (0.5, (245, 58, 8)),
            (0.8, (180, 22, 5)),
            (1.0, (75, 7, 4)),
        )
        for index in range(len(stops) - 1):
            start, start_color = stops[index]
            end, end_color = stops[index + 1]
            if progress <= end:
                ratio = (progress - start) / (end - start)
                rgb = tuple(
                    int(start_color[channel] + (end_color[channel] - start_color[channel]) * ratio)
                    for channel in range(3)
                )
                return (*rgb, max(0, int(255 * (1 - progress * 0.55))))
        return (*stops[-1][1], 0)

    def image(self):
        if self.surface is None:
            return QImage()
        return QImage(
            pygame.image.tostring(self.surface, "RGBA"),
            self.width,
            self.height,
            QImage.Format.Format_RGBA8888,
        ).copy()


class VisualEffectsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.effect = None
        self.elapsed = 0.0
        self.snail_x = -100.0
        self.fire = PygameFire()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)
        self.timer.start(16)
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
        self.elapsed += 0.016
        if self.effect == "flames":
            self.fire.resize(self.width(), self.height())
            self.fire.update()
        elif self.effect == "snail":
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
            painter.drawImage(0, 0, self.fire.image())
        else:
            self._draw_snail(painter)
        painter.end()

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
