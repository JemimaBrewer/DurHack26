import sys
import math
import json
from collections import deque
from pathlib import Path
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
    QCheckBox,
    QScrollArea
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
        self.music_dir = Path(__file__).resolve().parent / "music"
        self.songs = self._load_songs()
        self.selected_song_index = 0
        self.song_buttons = []

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
        self._build_music_panel()
        self.preview_panel.setFixedWidth(320)
        self.preview_toggle.setChecked(True)

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

    def _load_songs(self):
        metadata_path = self.music_dir / "musicinfo.json"
        try:
            with metadata_path.open(encoding="utf-8") as metadata_file:
                songs = json.load(metadata_file).get("songs", [])
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Unable to load music metadata from {metadata_path}") from error
        if not songs:
            raise RuntimeError(f"No songs found in {metadata_path}")
        return songs

    def _build_music_panel(self):
        layout = QVBoxLayout(self.preview_panel)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("MUSIC LIBRARY")
        title.setObjectName("musicPanelTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        self.song_art = QLabel()
        self.song_art.setObjectName("songArt")
        self.song_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_art.setFixedHeight(150)
        layout.addWidget(self.song_art)

        self.song_title = QLabel()
        self.song_title.setObjectName("songTitle")
        self.song_title.setWordWrap(True)
        layout.addWidget(self.song_title)
        self.song_artist = QLabel()
        self.song_artist.setObjectName("songArtist")
        self.song_artist.setWordWrap(True)
        layout.addWidget(self.song_artist)
        self.song_details = QLabel()
        self.song_details.setObjectName("songDetails")
        self.song_details.setWordWrap(True)
        layout.addWidget(self.song_details)

        layout.addSpacing(8)
        library_label = QLabel("SELECT A SONG")
        library_label.setObjectName("musicSectionLabel")
        layout.addWidget(library_label)
        song_list = QScrollArea()
        song_list.setObjectName("songList")
        song_list.setWidgetResizable(True)
        song_list.setFrameShape(QFrame.Shape.NoFrame)
        song_container = QWidget()
        song_layout = QVBoxLayout(song_container)
        song_layout.setContentsMargins(0, 0, 4, 0)
        song_layout.setSpacing(8)
        for index, song in enumerate(self.songs):
            button = QPushButton(song.get("title", "Untitled"))
            button.setObjectName("songButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip(
                f'{song.get("artist_or_composer", "Unknown artist")} · '
                f'{song.get("album_or_symphony", "Unknown work")}'
            )
            button.clicked.connect(lambda checked=False, song_index=index: self.select_song(song_index))
            self.song_buttons.append(button)
            song_layout.addWidget(button)
        song_layout.addStretch()
        song_list.setWidget(song_container)
        layout.addWidget(song_list, 1)
        self.select_song(self.selected_song_index)

    def select_song(self, index):
        if index < 0 or index >= len(self.songs):
            return
        self.selected_song_index = index
        song = self.songs[index]
        for song_index, button in enumerate(self.song_buttons):
            button.setChecked(song_index == index)

        image_path = self.music_dir / song.get("image_url", "")
        if not image_path.is_file():
            image_path = self.music_dir / "menken.jpg"
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.song_art.clear()
        else:
            self.song_art.setPixmap(
                pixmap.scaled(
                    self.song_art.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.song_title.setText(song.get("title", "Untitled"))
        self.song_artist.setText(song.get("artist_or_composer", "Unknown artist"))
        self.song_details.setText(
            f'{song.get("album_or_symphony", "Unknown work")} · '
            f'{song.get("release_year", "—")}\n'
            f'{song.get("beats_per_minute", "—")} BPM · '
            f'{song.get("beats_per_bar", "—")} beats per bar'
        )
        if hasattr(self, "audio_player"):
            self._start_selected_song()

    def _start_selected_song(self):
        song = self.songs[self.selected_song_index]
        if hasattr(self, "audio_player"):
            self.audio_player.stop()
        self.audio_player = AudioPlayer(
            audio_file=str(self.music_dir / song["audio_url"]),
            reference_bars_per_minute=song["beats_per_minute"],
        )
        self.audio_player.set_volume(100)
        self.audio_player.play()

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
            QStackedWidget#appController, QWidget#mainScreen, QWidget#titleScreen {{
                background-color: {background};
                color: {text};
                font-family: Segoe UI;
            }}
            QFrame#settingsPanel, QFrame#previewPanel {{
                background-color: {surface};
                border: 1px solid {border};
            }}
            QLabel#musicPanelTitle {{
                color: {text};
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QLabel#songArt {{
                background-color: {raised};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QLabel#songTitle {{
                color: {text};
                font-size: 18px;
                font-weight: 700;
            }}
            QLabel#songArtist, QLabel#songDetails {{
                color: {muted};
                font-size: 13px;
            }}
            QLabel#musicSectionLabel {{
                color: {muted};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QScrollArea#songList {{
                background: transparent;
            }}
            QPushButton#songButton {{
                background-color: {raised};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 10px;
                text-align: left;
            }}
            QPushButton#songButton:hover, QPushButton#songButton:checked {{
                background-color: {accent};
                border-color: {accent};
                color: #FFFFFF;
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

        self._start_selected_song()


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
        self.setObjectName("appController")

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
        stylesheet = self.maestro_screen._stylesheet(self.maestro_screen.current_theme)
        self.setStyleSheet(stylesheet)
        self.title_screen.setStyleSheet(stylesheet)

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = AppController()

    window.showMaximized()

    sys.exit(app.exec())