import sys
import cv2

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer



class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Maestro")
        self.resize(1000, 700)

        self.camera_label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.camera_label)

        self.setLayout(layout)

        self.cap = cv2.VideoCapture(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, ch = frame.shape
            bytes_per_line = ch * w

            qt_image = QImage(
                frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            self.camera_label.setPixmap(
                QPixmap.fromImage(qt_image)
            )

app = QApplication(sys.argv)

app.setStyleSheet("""
QWidget {
    background-color: #111827;
    color: white;
    font-family: Segoe UI;
}

QPushButton {
    background: transparent;
    border: none;
    font-size: 24px;
    color: white;
}

#cameraFrame {
    background: #1F2937;
    border-radius: 24px;
    border: 2px solid #8B5CF6;
}

#statsPanel {
    background: rgba(31,41,55,200);
    border-radius: 20px;
    padding: 12px;
}
""")

window = CameraWindow()
window.show()

sys.exit(app.exec())