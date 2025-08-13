import sys
import os
from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



class NFLDialog(QDialog):
    def __init__(self, thickness, composition, support_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NFL Chart")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        if "Laminated" in composition:
            base_path = resource_path("ui/assets/images/glass-load-charts/laminated")
        else:
            base_path = resource_path("ui/assets/images/glass-load-charts/monolithic")

        if support_type == "Four Edges":
            chart_path = f"{base_path}/four-edge/{thickness}mm.png"
        elif support_type == "Three Edges":
            chart_path = f"{base_path}/three-edge/{thickness}mm.png"
        elif support_type == "Two Edges":
            chart_path = f"{base_path}/two-edge/all-thk.png"
        else:
            chart_path = f"{base_path}/one-edge/all-thk.png"

        nfl_chart = QPixmap(chart_path)
        scaled_pixmap = nfl_chart.scaled(700, 520, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # print(f"Chart Path: {chart_path}")
        label = QLabel()
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(label)
        self.setLayout(layout)
        self.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())

