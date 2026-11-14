import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt


class MaestroWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Fit to screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)

        self.setWindowTitle("Maestro")

        self.setStyleSheet("""
            QWidget {
                background-color: #111827;
                color: white;
                font-family: Segoe UI;
            }

            #hamburger {
                border: none;
                background: transparent;
                color: white;
                font-size: 24px;
                padding: 10px;
            }

            #cameraFrame {
                background-color: #1F2937;
                border-radius: 24px;
                border: 2px solid #8B5CF6;
            }

            #textBox {
                background-color: rgba(31, 41, 55, 220);
                border-radius: 16px;
                padding: 15px;
                font-size: 20px;
                min-width: 300px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Top Bar
        top_bar = QHBoxLayout()

        hamburger = QPushButton("☰")
        hamburger.setObjectName("hamburger")
        hamburger.setFixedSize(50, 50)

        top_bar.addWidget(hamburger)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # Centre content area
        centre_layout = QVBoxLayout()
        centre_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera placeholder
        camera_frame = QLabel("Camera Feed")
        camera_frame.setObjectName("cameraFrame")
        camera_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)

        camera_frame.setFixedSize(960, 540)

        # Text panel
        text_box = QLabel("Hello World")
        text_box.setObjectName("textBox")
        text_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        centre_layout.addWidget(camera_frame)
        centre_layout.addSpacing(20)
        centre_layout.addWidget(
            text_box,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Stretch above and below keeps it centred vertically
        main_layout.addStretch()
        main_layout.addLayout(centre_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)


app = QApplication(sys.argv)

window = MaestroWindow()
window.show()

sys.exit(app.exec())