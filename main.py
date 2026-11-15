import sys
import math
from collections import deque
import cv2
from hand_tracker import HandTracker
from analyser import Analyser

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QCheckBox
)

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal

from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath

from audio_player import AudioPlayer

from title_screen import TitleScreen

class MaestroWindow(QWidget):
    theme_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hand_tracker = HandTracker()
        self.cap = None
        self.timer = None
        self.current_theme = "midnight"
        self.previous_hand_position = None
        self.movement_history = deque(maxlen=8)
        self.dynamic_volume_enabled = False
        self.visual_effects_enabled = False

        self.setWindowTitle("BeatBuddy")
        self.setObjectName("mainScreen")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 24, 32, 28)

        top_bar = QHBoxLayout()
        self.menu_button = QPushButton("☰")
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.clicked.connect(self.toggle_settings)
        top_bar.addWidget(self.menu_button)
        brand = QLabel("BeatBuddy  /  PRACTICE ROOM")
        brand.setObjectName("eyebrow")
        top_bar.addWidget(brand)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        heading = QHBoxLayout()
        heading.setSpacing(16)
        title = QLabel("Live rehearsal")
        title.setObjectName("pageTitle")
        heading.addWidget(title)
        self.session_status = QLabel("●  READY")
        self.session_status.setObjectName("status")
        heading.addWidget(self.session_status, alignment=Qt.AlignmentFlag.AlignVCenter)
        heading.addStretch()
        main_layout.addLayout(heading)
        main_layout.addSpacing(18)

        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraFrame")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("Starting camera...")
        self.camera_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        info_card = QFrame()
        info_card.setObjectName("infoCard")
        self.info_card = info_card
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(4)
        metrics_label = QLabel("SESSION METRICS")
        metrics_label.setObjectName("metricsLabel")
        info_layout.addWidget(metrics_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.text_box = QLabel("Move your index finger to begin a downbeat.")
        self.text_box.setObjectName("textBox")
        self.text_box.setWordWrap(True)
        info_layout.addWidget(self.text_box)

        # Keep the metrics above the flexible video area so it cannot be pushed
        # out of view when the window height is limited.
        main_layout.addWidget(info_card)
        main_layout.addSpacing(14)
        main_layout.addWidget(self.camera_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.settings_panel = self._build_settings_panel()
        self.settings_panel.setMaximumWidth(0)
        self.settings_animation = QPropertyAnimation(self.settings_panel, b"maximumWidth", self)
        self.settings_animation.setDuration(220)
        self.settings_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("previewPanel")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.addWidget(QLabel("SONG PREVIEW"))
        preview_layout.addStretch()
        self.preview_panel.setFixedWidth(240)
        self.preview_panel.setVisible(False)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.settings_panel)
        root_layout.addLayout(main_layout, 1)
        root_layout.addWidget(self.preview_panel)

        self.effects_label = QLabel("", self.camera_label)
        self.effects_label.setObjectName("effectsBadge")
        self.effects_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.effects_label.hide()
        self.set_theme("midnight")

    def _build_settings_panel(self):
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 24, 22, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("SETTINGS"))
        close_button = QPushButton("×")
        close_button.setObjectName("drawerClose")
        close_button.clicked.connect(self.toggle_settings)
        title_row.addWidget(close_button)
        layout.addLayout(title_row)

        self.dynamic_volume_toggle = QCheckBox("Dynamic volume")
        self.dynamic_volume_toggle.setToolTip("Raise volume as your hand movement covers more of the camera.")
        self.dynamic_volume_toggle.toggled.connect(self.set_dynamic_volume)
        layout.addWidget(self.dynamic_volume_toggle)

        self.preview_toggle = QCheckBox("Song preview")
        self.preview_toggle.toggled.connect(self.preview_panel_requested)
        layout.addWidget(self.preview_toggle)

        self.visual_effects_toggle = QCheckBox("Visual effects")
        self.visual_effects_toggle.toggled.connect(self.set_visual_effects)
        layout.addWidget(self.visual_effects_toggle)

        layout.addSpacing(10)
        layout.addWidget(QLabel("THEME"))
        self.theme_name_label = QLabel("Midnight")
        self.theme_name_label.setObjectName("themeName")
        self.theme_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.theme_name_label)

        theme_row = QHBoxLayout()
        for theme_name, color in (
            ("midnight", "#26354D"),
            ("paper", "#E9DDC7"),
            ("forest", "#294A43"),
        ):
            button = QPushButton()
            button.setObjectName(f"theme_{theme_name}")
            button.setFixedSize(42, 42)
            button.setToolTip(theme_name.title())
            button.clicked.connect(lambda checked=False, name=theme_name: self.theme_selected.emit(name))
            button.enterEvent = lambda event, name=theme_name: self.theme_name_label.setText(name.title())
            button.leaveEvent = lambda event: self.theme_name_label.setText(self.current_theme.title())
            theme_row.addWidget(button)
        layout.addLayout(theme_row)
        layout.addStretch()
        return panel

    def set_theme(self, theme):
        if isinstance(theme, bool):
            theme = "midnight" if theme else "paper"
        self.current_theme = theme
        self.theme_name_label.setText(theme.title())
        self.setStyleSheet(self._stylesheet(theme))

    @staticmethod
    def _stylesheet(theme):
        if theme == "midnight":
            background, surface, raised, text, muted, border, accent = (
                "#111827", "#182235", "#202d42", "#F8FAFC", "#9AA8BC", "#314158", "#3F89EB"
            )
        elif theme == "paper":
            background, surface, raised, text, muted, border, accent = (
                "#F5F2EC", "#FFFCF7", "#F0EBE1", "#17202D", "#667085", "#D8D1C4", "#DAC2ED"
            )
        else:
            background, surface, raised, text, muted, border, accent = (
                "#102521", "#18362F", "#21463D", "#F4FBF7", "#A9C3B9", "#376257", "#256E31"
            )
        return f"""
            QWidget#mainScreen, QWidget#titleScreen {{
                background-color: {background};
                color: {text};
                font-family: Segoe UI;
            }}
            QFrame#settingsPanel, QFrame#previewPanel {{
                background-color: {surface};
                border: 1px solid {border};
            }}
            QPushButton#menuButton, QPushButton#drawerClose {{
                background-color: transparent;
                color: {text};
                border: none;
                font-size: 22px;
            }}
            QCheckBox {{
                color: {text};
                spacing: 10px;
                font-size: 14px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {border};
                border-radius: 9px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border-color: {accent};
            }}
            QLabel#themeName {{
                color: {muted};
                font-size: 13px;
            }}
            QPushButton#theme_midnight, QPushButton#theme_paper, QPushButton#theme_forest {{
                border-radius: 21px;
                border: 2px solid {border};
            }}
            QPushButton#theme_midnight {{ background: #26354D; }}
            QPushButton#theme_paper {{ background: #E9DDC7; }}
            QPushButton#theme_forest {{ background: #294A43; }}
            QPushButton#theme_midnight:hover, QPushButton#theme_paper:hover,
            QPushButton#theme_forest:hover {{ border-color: {accent}; }}
            QLabel#effectsBadge {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#title {{
                color: {text};
                font-size: 34px;
                font-weight: 700;
            }}
            QLabel#subtitle {{
                color: {muted};
                font-size: 16px;
                line-height: 1.4;
            }}
            QPushButton#primaryButton {{
                background-color: {accent};
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 12px 16px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton#primaryButton:hover {{ background-color: {text}; color: {background}; }}
            QLabel#eyebrow, QLabel#status {{
                color: {muted};
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QLabel#pageTitle {{
                color: {text};
                font-size: 30px;
                font-weight: 700;
            }}
            QLabel#cameraFrame {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 14px;
            }}
            QFrame#infoCard, QFrame#welcomeCard {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 14px;
            }}
            QLabel#textBox {{
                color: {text};
                font-size: 16px;
            }}
            QLabel#metricsLabel {{
                color: {muted};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
        """

    def toggle_settings(self):
        opening = self.settings_panel.maximumWidth() == 0
        self.settings_animation.setStartValue(self.settings_panel.maximumWidth())
        self.settings_animation.setEndValue(280 if opening else 0)
        self.settings_animation.start()

    def set_dynamic_volume(self, enabled):
        self.dynamic_volume_enabled = enabled
        if not enabled and hasattr(self, "audio_player"):
            self.audio_player.set_volume(50)

    def set_visual_effects(self, enabled):
        self.visual_effects_enabled = enabled
        if not enabled:
            self.effects_label.hide()

    def preview_panel_requested(self, visible):
        self.preview_panel.setVisible(visible)

    def update_movement(self, x, y, frame_width, frame_height):
        if self.previous_hand_position is not None:
            distance = math.hypot(
                x - self.previous_hand_position[0],
                y - self.previous_hand_position[1],
            )
            frame_diagonal = math.hypot(frame_width, frame_height)
            self.movement_history.append(distance / frame_diagonal * 100)
        self.previous_hand_position = (x, y)

        if not self.dynamic_volume_enabled or not hasattr(self, "audio_player"):
            return
        movement_percent = sum(self.movement_history) / max(len(self.movement_history), 1)
        self.audio_player.set_volume(50 + movement_percent * 20)

    def update_visual_effect(self, bpm):
        if not self.visual_effects_enabled or bpm <= 0:
            self.effects_label.hide()
            return
        if bpm >= 60:
            self.effects_label.setText("🔥")
        elif bpm <= 30:
            self.effects_label.setText("🐌")
        else:
            self.effects_label.hide()
            return
        self.effects_label.adjustSize()
        self.effects_label.move(
            self.camera_label.width() - self.effects_label.width() - 16,
            16,
        )
        self.effects_label.show()

    def start_session(self):
        self.cap = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )
        self.cap.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG")
        )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        print(
            self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        # Update camera roughly 30 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)
        self.session_status.setText("●  LISTENING")

        self.analyser=Analyser()

        self.audio_player = AudioPlayer(
            audio_file="demo.mp3",
            reference_bars_per_minute=37.5
        )

        self.audio_player.set_volume(50)
        self.audio_player.play()


    def update_frame(self):

        ret, frame = self.cap.read()

        if not ret:
            return

        frame = self.hand_tracker.process_frame(
            frame
        )

        if self.hand_tracker.current_fingertip:

            x, y = (
                self.hand_tracker.current_fingertip
            )

            new_downbeat = (
                self.analyser.update(
                    x,
                    y
                )
            )

            if new_downbeat:

                bpm = (
                    self.analyser
                    .get_bars_per_minute()
                )

                if bpm > 0:

                    self.audio_player.update_tempo(
                        bpm
                    )

            bpm = (
                self.analyser
                .get_bars_per_minute()
            )

            self.text_box.setText(
                f"Bars per Minute: {bpm:.1f}\n"
                f"Playback Rate: "
                f"{self.audio_player.get_rate():.2f}x"
            )
            self.update_movement(x, y, frame.shape[1], frame.shape[0])
            self.update_visual_effect(bpm)

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channel = (
            frame.shape
        )

        qimage = QImage(
            frame.data,
            width,
            height,
            channel * width,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            qimage
        )

        scaled_pixmap = pixmap.scaled(
            self.camera_label.width(),
            self.camera_label.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        rounded = QPixmap(
            self.camera_label.width(),
            self.camera_label.height()
        )

        rounded.fill(
            Qt.GlobalColor.transparent
        )

        painter = QPainter(
            rounded
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        path = QPainterPath()

        path.addRoundedRect(
            0,
            0,
            self.camera_label.width(),
            self.camera_label.height(),
            24,
            24
        )

        painter.setClipPath(
            path
        )

        painter.drawPixmap(
            0,
            0,
            scaled_pixmap
        )

        painter.end()

        self.camera_label.setPixmap(
            rounded
        )
        
    def resizeEvent(self, event):
        side_panel_width = self.settings_panel.width()
        if self.preview_panel.isVisible():
            side_panel_width += self.preview_panel.width()
        available_width = max(240, self.width() - side_panel_width - 64)
        metrics_height = self.info_card.sizeHint().height()
        available_height = max(
            120,
            self.height() - metrics_height - 190
        )
        camera_width = min(
            available_width,
            int(available_height * 16 / 9)
        )
        camera_height = int(camera_width * 9 / 16)
        self.camera_label.setFixedSize(
            camera_width,
            camera_height
        )
        if hasattr(self, "effects_label"):
            self.effects_label.move(
                self.camera_label.width() - self.effects_label.width() - 16,
                16,
            )

        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.timer is not None:
            self.timer.stop()
        if self.cap is not None:
            self.cap.release()
        event.accept()

class AppController(QStackedWidget):

    def __init__(self):

        super().__init__()

        self.title_screen = TitleScreen()

        self.maestro_screen = MaestroWindow()

        self.addWidget(
            self.title_screen
        )

        self.addWidget(
            self.maestro_screen
        )

        self.setCurrentWidget(
            self.title_screen
        )

        self.title_screen.start_button.clicked.connect(
            self.show_maestro
        )
        self.maestro_screen.theme_selected.connect(self.set_theme)
        self.set_theme("midnight")

    def show_maestro(self):

        self.maestro_screen.start_session()

        self.setCurrentWidget(
            self.maestro_screen
        )

    def set_theme(self, theme):
        self.maestro_screen.set_theme(theme)
        self.title_screen.setStyleSheet(
            self.maestro_screen._stylesheet(self.maestro_screen.current_theme)
        )

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = AppController()

    window.showMaximized()

    sys.exit(app.exec())