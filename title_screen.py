from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)

from PyQt6.QtCore import Qt


class TitleScreen(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Maestro")

        self.setStyleSheet("""
            QWidget {
                background-color: #0B1220;
                color: white;
                font-family: Segoe UI;
            }

            QLabel#title {
                font-size: 72px;
                font-weight: 800;
                color: white;
            }

            QLabel#subtitle {
                font-size: 24px;
                color: #9CA3AF;
            }

            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 16px;
                font-size: 24px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #3B82F6;
            }

            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("MAESTRO")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.subtitle_label = QLabel(
            "Conducting Practice Assistant"
        )
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.start_button = QPushButton(
            "Start Session"
        )

        self.start_button.setFixedSize(
            260,
            75
        )

        layout.addStretch()

        layout.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        layout.addSpacing(10)

        layout.addWidget(
            self.subtitle_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        layout.addSpacing(50)

        layout.addWidget(
            self.start_button,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        layout.addStretch()

        self.setLayout(layout)