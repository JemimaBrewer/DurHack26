import sys
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
)

from PyQt6.QtCore import Qt, QTimer

from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath


class MaestroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.hand_tracker = HandTracker()

        # Make window fill screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        self.setWindowTitle("Maestro")

        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1220;
                color: white;
                font-family: Segoe UI;
            }
            QLabel#textBox {
                background-color: #172033;
                border-radius: 20px;
                padding: 18px;
                border: none;
                font-size: 18px;
                color: #E5E7EB;
            }


            QPushButton#hamburger {
                background-color: #172033;
                border-radius: 20px;
                border: none;
                color: white;
                font-size: 26px;
            }

            QLabel#cameraFrame {
                background-color: #1F2937;
                border: none;
                border-radius: 24px;
            }

            QLabel#textBox {
                background-color: #1F2937;
                border-radius: 16px;
                padding: 15px;
                border: 1px solid #374151;
                font-size: 20px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)

        # ======================
        # Top Bar
        # ======================

        top_bar = QHBoxLayout()

        self.menu_button = QPushButton("☰")
        self.menu_button.setObjectName("hamburger")
        self.menu_button.setFixedSize(60, 60)

        top_bar.addWidget(self.menu_button)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # ======================
        # Centre Content
        # ======================

        centre_layout = QVBoxLayout()
        centre_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel("Maestro")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 48px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 2px;
        """)

        centre_layout.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        centre_layout.addSpacing(20)
        # Camera Label
        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraFrame")
        self.camera_label.setFixedSize(1000, 560)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("Starting Camera...")

        # Bottom Info Label
        self.text_box = QLabel("Hello World")
        self.text_box.setObjectName("textBox")
        self.text_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_box.setFixedWidth(350)

        centre_layout.addWidget(
            self.camera_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        centre_layout.addSpacing(20)

        centre_layout.addWidget(self.text_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Stretch keeps content centred vertically
        main_layout.addStretch()
        main_layout.addLayout(centre_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # ======================
        # Camera Setup
        # ======================

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

        self.analyser=Analyser()

    def update_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            return

        # Convert OpenCV BGR -> RGB
        frame = self.hand_tracker.process_frame(frame)

        if self.hand_tracker.current_fingertip:

            x, y = self.hand_tracker.current_fingertip

            self.analyser.update(x, y)

            bpm = self.analyser.get_bars_per_minute()

            self.text_box.setText(
                f"Bars per Minute: {bpm:.1f}"
            )

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, channel = frame.shape

        qimage = QImage(
            frame.data, width, height, channel * width, QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qimage)

        scaled_pixmap = pixmap.scaled(
            self.camera_label.width(),
            self.camera_label.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        rounded = QPixmap(self.camera_label.width(), self.camera_label.height())
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.camera_label.width(), self.camera_label.height(), 24, 24
        )

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

        self.camera_label.setPixmap(rounded)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MaestroWindow()
    window.show()

    sys.exit(app.exec())