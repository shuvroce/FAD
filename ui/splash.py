import sys
import os
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()

        self.setFixedSize(600, 400)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        )

        # Set splash image
        splash_path = resource_path("ui/assets/splash.png")
        pixmap = QPixmap(splash_path).scaled(
            self.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.setPixmap(pixmap)

        # Progress Bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(40, self.height() - 50, self.width() - 80, 20)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Loading... 0%")
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 50);
                color: white;
                border-style: none;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #354453;
                border-radius: 5px;
            }
        """)

        # Center splash screen
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.move(
            (geo.width() - self.width()) // 2,
            (geo.height() - self.height()) // 2
        )

        self._callback = None

    def start_loading(self, duration_ms=1000, on_complete=None):
        self.show()
        self._step = 0
        self._callback = on_complete
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_progress)
        self._timer.start(duration_ms // 100)

    def update_progress(self):
        if self._step < 100:
            self._step += 1
            self.progress.setValue(self._step)
            self.progress.setFormat(f"Loading... {self._step}%")
        else:
            self._timer.stop()
            if self._callback:
                self._callback()
