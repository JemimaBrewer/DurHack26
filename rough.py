import sys
import cv2

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)

from PyQt6.QtCore import (
    Qt,
    QTimer
)

from PyQt6.QtGui import (
    QPixmap,
    QImage
)


class MaestroWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Make window fill screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        self.setWindowTitle("Maestro")

        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #111827;
                color: white;
                font-family: Segoe UI;
            }

            QPushButton#hamburger {
                border: none;
                background: transparent;
                color: white;
                font-size: 28px;
                padding: 10px;
            }

            QLabel#cameraFrame {
                background-color: #1F2937;
                border: 2px solid #8B5CF6;
                border-radius: 24px;
                color: white;
                font-size: 20px;
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
        self.menu_button.setFixedSize(50, 50)

        top_bar.addWidget(self.menu_button)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # ======================
        # Centre Content
        # ======================

        centre_layout = QVBoxLayout()
        centre_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera Label
        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraFrame")
        self.camera_label.setFixedSize(960, 540)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("Starting Camera...")

        # Bottom Info Label
        self.text_box = QLabel("Hello World")
        self.text_box.setObjectName("textBox")
        self.text_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_box.setFixedWidth(350)

        centre_layout.addWidget(
            self.camera_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        centre_layout.addSpacing(20)

        centre_layout.addWidget(
            self.text_box,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Stretch keeps content centred vertically
        main_layout.addStretch()
        main_layout.addLayout(centre_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # ======================
        # Camera Setup
        # ======================

        self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Update camera roughly 30 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def update_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            return

        # Convert OpenCV BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, channel = frame.shape

        qimage = QImage(
            frame.data,
            width,
            height,
            channel * width,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qimage)

        scaled_pixmap = pixmap.scaled(
            self.camera_label.width(),
            self.camera_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.camera_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MaestroWindow()
    window.show()

    sys.exit(app.exec())