import sys
import os
from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout, QComboBox, QFormLayout,
                                QHBoxLayout, QGroupBox, QDialogButtonBox, QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



class ScrewConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Screw Configuration Options")
        self.setFixedSize(800, 400)

        self.image_label = QLabel()
        self.image_label.setFixedSize(750, 300)
        self.image_label.setScaledContents(True)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #b9b9b9;
                padding: 2px;
                margin-top: 6px;
                background-color: white;
            }
        """)

        self.radio_buttons = []
        self.button_group = QButtonGroup(self)

        radio_layout = QHBoxLayout()
        options = ["Option 1", "Option 2", "Option 3", "Option 4"]

        for i, option in enumerate(options):
            rb = QRadioButton(option)
            self.radio_buttons.append(rb)
            self.button_group.addButton(rb, i)
            radio_layout.addWidget(rb)
            rb.toggled.connect(lambda checked, opt=option: self.update_image_preview(opt) if checked else None)

        group_box = QGroupBox()
        group_layout = QVBoxLayout()
        group_layout.addLayout(radio_layout)
        group_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        group_box.setLayout(group_layout)

        # --- Main layout ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)

        self.radio_buttons[0].setChecked(True)
        self.update_image_preview(options[0])

    def update_image_preview(self, text):
        img_map = {
            "Option 1": resource_path("reports/images/fig_conn1.png"),
            "Option 2": resource_path("reports/images/fig_conn2.png"),
            "Option 3": resource_path("reports/images/fig_conn3.png"),
            "Option 4": resource_path("reports/images/fig_conn4.png")
        }
        img_path = img_map.get(text, "")
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("No image found.")


