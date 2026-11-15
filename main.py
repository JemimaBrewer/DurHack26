import sys
import math
import json
import time
import struct
import tempfile
import wave
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
    QScrollArea,
    QLineEdit
)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QRect,
    QUrl,
    pyqtSignal,
)

from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
from PyQt6.QtMultimedia import QSoundEffect

from audio_player import AudioPlayer
from visual_effects import VisualEffectsOverlay

from title_screen import TitleScreen

class MaestroWindow(QWidget):
    theme_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hand_tracker = HandTracker()
        self.cap = None
        self.timer = None
        self.settings_path = Path(__file__).resolve().parent / "settings.json"
        self.settings = self._load_settings()
        self.current_theme = self.settings["theme"]
        self.previous_hand_position = None
        self.movement_history = deque(maxlen=8)
        self.dynamic_volume_enabled = self.settings["dynamic_volume"]
        self.visual_effects_enabled = self.settings["visual_effects"]
        self.music_dir = Path(__file__).resolve().parent / "music"
        self.songs = self._load_songs()
        self.selected_song_index = min(self.settings["selected_song"], len(self.songs) - 1)
        self.song_buttons = []
        self.countdown_timer = None
        self.beat_timer = None
        self.countdown_beats_remaining = 0
        self.countdown_animation = None
        self.countdown_animations = []
        self.active_countdown_bars = []
        self.target_volume = None
        self.last_volume_update = None
        self.metronome_click = self._create_metronome_click()
        self._settings_ready = False

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
        metrics_header = QHBoxLayout()
        metrics_label = QLabel("SESSION METRICS")
        metrics_label.setObjectName("metricsLabel")
        metrics_header.addWidget(metrics_label)
        metrics_header.addStretch()
        self.volume_label = QLabel()
        self.volume_label.setObjectName("volumeMetric")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.volume_label.setVisible(self.dynamic_volume_enabled)
        metrics_header.addWidget(self.volume_label)
        info_layout.addLayout(metrics_header)
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
        self.settings_animation.setDuration(80)
        self.settings_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.settings_animation.valueChanged.connect(lambda _: self._update_camera_size())

        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("previewPanel")
        self._build_music_panel()
        self.preview_panel.setFixedWidth(320)
        self.preview_panel.setMinimumWidth(320)
        self.preview_panel.setMaximumWidth(320)
        for toggle, checked in (
            (self.dynamic_volume_toggle, self.dynamic_volume_enabled),
            (self.visual_effects_toggle, self.visual_effects_enabled),
            (self.visual_countdown_toggle, self.settings["visual_countdown"]),
            (self.metronome_sound_toggle, self.settings["metronome_sound"]),
            (self.preview_toggle, self.settings["song_preview"]),
        ):
            toggle.blockSignals(True)
            toggle.setChecked(checked)
            toggle.blockSignals(False)
        self.preview_panel.setVisible(self.settings["song_preview"])
        self._settings_ready = True
        self._save_settings()
        self._update_volume_display()

        center_panel = QWidget()
        center_panel.setLayout(main_layout)
        center_panel.setMinimumWidth(0)
        center_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.setStretch(1, 1)
        root_layout.addWidget(self.settings_panel)
        root_layout.addWidget(center_panel, 1)
        root_layout.addWidget(self.preview_panel)

        self.effects_overlay = VisualEffectsOverlay(self.camera_label)
        self.effects_overlay.setObjectName("effectsOverlay")
        self.effects_overlay.setGeometry(
            0,
            max(0, self.camera_label.height() - 120),
            self.camera_label.width(),
            min(120, self.camera_label.height()),
        )
        self.countdown_overlay = QFrame(self.camera_label)
        self.countdown_overlay.setObjectName("countdownOverlay")
        self.countdown_overlay.setFixedHeight(56)
        self.countdown_overlay.hide()
        self.set_theme(self.current_theme)
        QTimer.singleShot(0, self._update_song_art)

    def _load_settings(self):
        defaults = {
            "theme": "midnight",
            "dynamic_volume": False,
            "song_preview": False,
            "visual_effects": False,
            "visual_countdown": True,
            "metronome_sound": True,
            "selected_song": 0,
        }
        try:
            with self.settings_path.open(encoding="utf-8") as settings_file:
                saved = json.load(settings_file)
        except FileNotFoundError:
            return defaults
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Unable to load settings from {self.settings_path}") from error
        return {
            key: saved.get(key, value)
            for key, value in defaults.items()
        }

    def _save_settings(self):
        self.settings.update({
            "theme": self.current_theme,
            "dynamic_volume": self.dynamic_volume_enabled,
            "song_preview": (
                self.preview_toggle.isChecked()
                if hasattr(self, "preview_toggle")
                else self.settings["song_preview"]
            ),
            "visual_effects": self.visual_effects_enabled,
            "visual_countdown": (
                self.visual_countdown_toggle.isChecked()
                if hasattr(self, "visual_countdown_toggle")
                else self.settings["visual_countdown"]
            ),
            "metronome_sound": (
                self.metronome_sound_toggle.isChecked()
                if hasattr(self, "metronome_sound_toggle")
                else self.settings["metronome_sound"]
            ),
            "selected_song": self.selected_song_index,
        })
        try:
            with self.settings_path.open("w", encoding="utf-8") as settings_file:
                json.dump(self.settings, settings_file, indent=2)
                settings_file.write("\n")
        except OSError as error:
            raise RuntimeError(f"Unable to save settings to {self.settings_path}") from error

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

    @staticmethod
    def _create_metronome_click():
        click_path = Path(tempfile.gettempdir()) / "beatbuddy-metronome-click.wav"
        if not click_path.exists():
            sample_rate = 44100
            duration = 0.035
            frequency = 1450
            samples = int(sample_rate * duration)
            frames = bytearray()
            for index in range(samples):
                progress = index / samples
                envelope = (1 - progress) ** 4
                sample = int(
                    0.55
                    * envelope
                    * math.sin(2 * math.pi * frequency * index / sample_rate)
                    * 32767
                )
                frames.extend(struct.pack("<h", sample))
            with wave.open(str(click_path), "wb") as click_file:
                click_file.setnchannels(1)
                click_file.setsampwidth(2)
                click_file.setframerate(sample_rate)
                click_file.writeframes(frames)

        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str(click_path)))
        effect.setVolume(0.7)
        return effect

    def _play_metronome_click(self):
        self.metronome_click.play()

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
        self.song_art.setFixedWidth(280)
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
        self.play_button = QPushButton("▶  Play selected song")
        self.play_button.setObjectName("playButton")
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self.play_selected_song)
        layout.addWidget(self.play_button)

        layout.addSpacing(8)
        library_label = QLabel("SELECT A SONG")
        library_label.setObjectName("musicSectionLabel")
        layout.addWidget(library_label)
        self.song_search = QLineEdit()
        self.song_search.setObjectName("songSearch")
        self.song_search.setPlaceholderText("Search songs, artists, or works")
        self.song_search.setClearButtonEnabled(True)
        self.song_search.textChanged.connect(self.filter_song_list)
        layout.addWidget(self.song_search)
        song_list = QScrollArea()
        song_list.setObjectName("songList")
        song_list.setWidgetResizable(True)
        song_list.setFrameShape(QFrame.Shape.NoFrame)
        song_container = QWidget()
        song_container.setObjectName("songContainer")
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

    def filter_song_list(self, query):
        query = query.strip().casefold()
        for index, button in enumerate(self.song_buttons):
            song = self.songs[index]
            searchable_text = " ".join(
                str(song.get(field, ""))
                for field in ("title", "artist_or_composer", "album_or_symphony")
            ).casefold()
            button.setVisible(not query or query in searchable_text)

    def select_song(self, index):
        if index < 0 or index >= len(self.songs):
            return
        self._stop_visual_metronome()
        if self.countdown_timer is not None:
            self.countdown_timer.stop()
            self.countdown_timer.deleteLater()
            self.countdown_timer = None
        self.play_button.setEnabled(True)
        self.play_button.setText("▶  Play selected song")
        self.selected_song_index = index
        song = self.songs[index]
        for song_index, button in enumerate(self.song_buttons):
            button.setChecked(song_index == index)

        self._update_song_art()
        self.song_title.setText(song.get("title", "Untitled"))
        self.song_artist.setText(song.get("artist_or_composer", "Unknown artist"))
        self.song_details.setText(
            f'{song.get("album_or_symphony", "Unknown work")} · '
            f'{song.get("release_year", "—")}\n'
            f'{song.get("beats_per_minute", "—")} BPM · '
            f'{song.get("beats_per_bar", "—")} beats per bar'
        )
        self._save_settings()

    def _update_song_art(self):
        song = self.songs[self.selected_song_index]
        image_path = self.music_dir / song.get("image_url", "")
        if not image_path.is_file():
            image_path = self.music_dir / "menken.jpg"
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.song_art.clear()
        else:
            scaled = pixmap.scaled(
                self.song_art.width(),
                pixmap.height() * self.song_art.width() // pixmap.width(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.song_art.setFixedSize(scaled.size())
            size = scaled.size()
            image = QPixmap(size)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, size.width(), size.height(), 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(
                (size.width() - scaled.width()) // 2,
                (size.height() - scaled.height()) // 2,
                scaled,
            )
            painter.end()
            self.song_art.setPixmap(image)

    def _start_selected_song(self):
        self._create_selected_player()

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

        self.visual_countdown_toggle = QCheckBox("Visual countdown")
        self.visual_countdown_toggle.toggled.connect(self._settings_changed)
        layout.addWidget(self.visual_countdown_toggle)

        self.metronome_sound_toggle = QCheckBox("Metronome sound")
        self.metronome_sound_toggle.toggled.connect(self._settings_changed)
        layout.addWidget(self.metronome_sound_toggle)

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
        if self._settings_ready:
            self._save_settings()

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
            QFrame#settingsPanel {{
                background-color: {surface};
                border: 1px solid {border};
            }}
            QFrame#previewPanel {{
                background-color: {background};
                border-left: 1px solid {border};
            }}
            QLabel#musicPanelTitle {{
                color: {text};
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QLabel#songArt {{
                background-color: transparent;
                border: none;
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
            QFrame#countdownOverlay {{
                background-color: rgba(0, 0, 0, 110);
            }}
            QFrame#countdownBar {{
                background-color: #FFFFFF;
                border-radius: 3px;
            }}
            QFrame#countdownBar[atCenter="true"] {{
                background-color: {accent};
            }}
            QLabel#musicSectionLabel {{
                color: {muted};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QScrollArea#songList {{
                background: transparent;
                border: none;
            }}
            QScrollArea#songList > QWidget {{
                background-color: {background};
            }}
            QScrollArea#songList QWidget#songContainer {{
                background-color: {background};
            }}
            QLineEdit#songSearch {{
                background-color: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 10px;
                selection-background-color: {accent};
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
            QPushButton#playButton {{
                background-color: {accent};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: 700;
            }}
            QPushButton#playButton:hover {{ background-color: {text}; color: {background}; }}
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
            QLabel#volumeMetric {{
                color: {muted};
                font-size: 12px;
                font-weight: 700;
            }}
        """

    def toggle_settings(self):
        opening = self.settings_panel.maximumWidth() == 0
        self.settings_animation.setStartValue(self.settings_panel.maximumWidth())
        self.settings_animation.setEndValue(280 if opening else 0)
        self.settings_animation.start()

    def set_dynamic_volume(self, enabled):
        self.dynamic_volume_enabled = enabled
        self.volume_label.setVisible(enabled)
        self._save_settings()
        if hasattr(self, "audio_player"):
            self.audio_player.set_volume(50 if enabled else 150)
            self.target_volume = self.audio_player.get_volume()
            self.last_volume_update = time.monotonic()
        self._update_volume_display()

    def _update_volume_display(self):
        if not self.dynamic_volume_enabled:
            return
        volume = (
            self.audio_player.get_volume()
            if hasattr(self, "audio_player")
            else 150
        )
        self.volume_label.setText(f"Volume: {round(volume / 2)}%")

    def set_visual_effects(self, enabled):
        self.visual_effects_enabled = enabled
        self._save_settings()
        if not enabled:
            self.effects_overlay.set_effect(None)

    def _settings_changed(self):
        self._save_settings()
        if not self.visual_countdown_toggle.isChecked():
            self.countdown_overlay.hide()

    def preview_panel_requested(self, visible):
        self.preview_panel.setVisible(visible)
        self._update_camera_size()
        self._save_settings()

    def play_selected_song(self):
        if self.countdown_timer is not None and self.countdown_timer.isActive():
            return
        if hasattr(self, "audio_player"):
            self.audio_player.stop()
        self._create_selected_player()
        song = self.songs[self.selected_song_index]
        if not self.visual_countdown_toggle.isChecked():
            self.audio_player.play()
            self._start_visual_metronome()
            self.play_button.setText("■  Stop selected song")
            return
        self.countdown_beats_remaining = int(song["beats_per_bar"]) * 2
        self._stop_visual_metronome()
        self.play_button.setEnabled(False)
        self.play_button.setText("Preparing…")
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_tick()

    def _create_selected_player(self):
        song = self.songs[self.selected_song_index]
        self.audio_player = AudioPlayer(
            audio_file=str(self.music_dir / song["audio_url"]),
            reference_bars_per_minute=song["beats_per_minute"],
        )
        self.audio_player.set_volume(50 if self.dynamic_volume_enabled else 150)
        self.target_volume = self.audio_player.get_volume()
        self.last_volume_update = time.monotonic()
        self._update_volume_display()

    def _countdown_tick(self):
        song = self.songs[self.selected_song_index]
        total_beats = int(song["beats_per_bar"]) * 2
        if self.countdown_beats_remaining <= 0:
            self.countdown_timer.stop()
            self.countdown_timer.deleteLater()
            self.countdown_timer = None
            self.audio_player.play()
            self._start_visual_metronome()
            self.play_button.setEnabled(True)
            self.play_button.setText("▶  Play selected song")
            self.text_box.setText("GO")
            return
        beat_in_bar = (total_beats - self.countdown_beats_remaining) % int(song["beats_per_bar"])
        count = int(song["beats_per_bar"]) - beat_in_bar
        self.text_box.setText(f"Starting in {count}")
        if self.visual_countdown_toggle.isChecked():
            self._animate_countdown_bars()
        if self.metronome_sound_toggle.isChecked():
            self._play_metronome_click()
        self.countdown_beats_remaining -= 1
        interval_ms = round(60_000 / float(song["beats_per_minute"]))
        self.countdown_timer.start(interval_ms)

    def _animate_countdown_bars(self):
        width = self.camera_label.width()
        height = self.countdown_overlay.height()
        bar_width = max(4, width // 40)
        center = width // 2
        self.countdown_overlay.setGeometry(
            0,
            self.camera_label.height() - height,
            width,
            height,
        )
        self.countdown_overlay.show()
        left_bar = QFrame(self.countdown_overlay)
        right_bar = QFrame(self.countdown_overlay)
        left_bar.setObjectName("countdownBar")
        right_bar.setObjectName("countdownBar")
        left_bar.setGeometry(0, 0, bar_width, height)
        right_bar.setGeometry(width - bar_width, 0, bar_width, height)
        left_bar.show()
        right_bar.show()
        self.active_countdown_bars.extend((left_bar, right_bar))

        left_animation = QPropertyAnimation(left_bar, b"geometry", self)
        left_animation.setStartValue(left_bar.geometry())
        center_bar = QRect(center - bar_width // 2, 0, bar_width, height)
        left_animation.setEndValue(center_bar)
        right_animation = QPropertyAnimation(right_bar, b"geometry", self)
        right_animation.setStartValue(right_bar.geometry())
        right_animation.setEndValue(center_bar)
        duration = max(100, round(60_000 / self.songs[self.selected_song_index]["beats_per_minute"]))
        for animation in (left_animation, right_animation):
            animation.setDuration(duration)
            animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(left_animation)
        animation_group.addAnimation(right_animation)
        animation_group.finished.connect(
            lambda: self._finish_countdown_bars(left_bar, right_bar)
        )
        self.countdown_animations.append(animation_group)
        animation_group.start()

    def _finish_countdown_bars(self, left_bar, right_bar):
        for bar in (left_bar, right_bar):
            bar.setProperty("atCenter", True)
            bar.style().unpolish(bar)
            bar.style().polish(bar)
            bar.update()

        QTimer.singleShot(
            120,
            lambda: self._remove_countdown_bars(left_bar, right_bar),
        )

    def _remove_countdown_bars(self, left_bar, right_bar):
        for bar in (left_bar, right_bar):
            if bar in self.active_countdown_bars:
                self.active_countdown_bars.remove(bar)
            bar.deleteLater()

    def _start_visual_metronome(self):
        if self.beat_timer is None:
            self.beat_timer = QTimer(self)
            self.beat_timer.timeout.connect(self._visual_metronome_tick)
        interval_ms = round(60_000 / self.songs[self.selected_song_index]["beats_per_minute"])
        self.beat_timer.start(interval_ms)

    def _visual_metronome_tick(self):
        if self.visual_countdown_toggle.isChecked():
            self._animate_countdown_bars()
        if self.metronome_sound_toggle.isChecked():
            self._play_metronome_click()

    def _stop_visual_metronome(self):
        if self.beat_timer is not None:
            self.beat_timer.stop()

        if self.countdown_animation is not None:
            self.countdown_animation.stop()

        for animation in self.countdown_animations:
            animation.stop()

        self.countdown_animations.clear()

        for bar in self.active_countdown_bars:
            bar.deleteLater()

        self.active_countdown_bars.clear()

        if hasattr(self, "countdown_overlay"):
            self.countdown_overlay.hide()

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
        self.target_volume = 50 + min(350, movement_percent * 70)
        now = time.monotonic()
        elapsed = now - (self.last_volume_update or now)
        beat_duration = 60 / float(self.songs[self.selected_song_index]["beats_per_minute"])
        smoothing = min(1.0, elapsed / beat_duration)
        current_volume = self.audio_player.get_volume()
        next_volume = current_volume + (self.target_volume - current_volume) * smoothing
        self.audio_player.set_volume(next_volume)
        self.last_volume_update = now
        self._update_volume_display()

    def update_visual_effect(self, bpm):
        if not self.visual_effects_enabled or bpm <= 0:
            self.effects_overlay.set_effect(None)
            return
        target_bpm = self.songs[self.selected_song_index]["beats_per_minute"]
        if bpm >= target_bpm * 1.5:
            self.effects_overlay.set_effect("flames")
        elif bpm <= target_bpm * 0.75:
            self.effects_overlay.set_effect("snail")
        else:
            self.effects_overlay.set_effect(None)

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
        self._create_selected_player()



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
            (self.camera_label.width() - scaled_pixmap.width()) // 2,
            (self.camera_label.height() - scaled_pixmap.height()) // 2,
            scaled_pixmap
        )

        painter.end()

        self.camera_label.setPixmap(
            rounded
        )
        
    def _update_camera_size(self):
        side_panel_width = self.settings_panel.width()
        if self.preview_panel.isVisible():
            side_panel_width += self.preview_panel.width()
        available_width = max(1, self.width() - side_panel_width - 64)
        metrics_height = self.info_card.sizeHint().height()
        available_height = max(
            1,
            self.height() - metrics_height - 190
        )
        camera_width = min(
            available_width,
            int(available_height * 16 / 9)
        )
        camera_height = int(camera_width * 9 / 16)
        self.camera_label.setMinimumSize(1, 1)
        self.camera_label.setMaximumSize(camera_width, camera_height)
        self.camera_label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self.camera_label.setFixedSize(camera_width, camera_height)
        if hasattr(self, "countdown_overlay"):
            self.countdown_overlay.setGeometry(
                0,
                camera_height - self.countdown_overlay.height(),
                camera_width,
                self.countdown_overlay.height(),
            )
        if hasattr(self, "effects_overlay"):
            self.effects_overlay.setGeometry(
                0,
                max(0, self.camera_label.height() - 120),
                self.camera_label.width(),
                min(120, self.camera_label.height()),
            )

    def resizeEvent(self, event):
        self._update_camera_size()
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_camera_size()

    def closeEvent(self, event):
        self._stop_visual_metronome()
        if self.timer is not None:
            self.timer.stop()
        if self.cap is not None:
            self.cap.release()
        event.accept()

class AppController(QStackedWidget):

    def __init__(self):

        super().__init__()
        self.setObjectName("appController")
        self.setMinimumWidth(960)

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
        self.set_theme(self.maestro_screen.current_theme)

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