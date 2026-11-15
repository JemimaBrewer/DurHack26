from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame
)

from PyQt6.QtCore import Qt


class TitleScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEATBUDDY")
        self.setObjectName("titleScreen")

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(QLabel("BEATBUDDY"))
        header.addStretch()

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setMaximumWidth(560)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(42, 38, 42, 42)
        card_layout.setSpacing(0)

        self.title_label = QLabel("Get started")
        self.title_label.setObjectName("title")
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel("Test your timing and get to know some pieces.")
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setWordWrap(True)
        self.start_button = QPushButton("Start a practice session")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(48)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)

        #card_layout.addWidget(QLabel("CONDUCTOR PRACTICE"))
        #card_layout.addSpacing(18)
        card_layout.addWidget(self.title_label)
        card_layout.addSpacing(14)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addSpacing(30)
        card_layout.addWidget(self.start_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)
        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
