import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QDoubleSpinBox, QLineEdit,
    QDialogButtonBox, QLabel, QHBoxLayout, QVBoxLayout,
    QTextEdit, QComboBox, QGroupBox, QScrollArea, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import math


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



class FloorHeightsDialog(QDialog):
    def __init__(self, num_floors, initial_heights=None, initial_selected_levels=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Floor Heights")
        self.setFixedSize(400, 500)

        self.num_floors = num_floors
        self.initial_heights = [float(h) for h in (initial_heights or [3.2] * num_floors)]

        self.floor_height_inputs = []

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        container = QWidget()
        self.floor_heights_layout = QVBoxLayout(container)
        self.floor_heights_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(container)
        
        self.update_floor_inputs()

        # selected level for c&c
        if initial_selected_levels is None:
            mid = math.ceil(num_floors / 2)
            top = num_floors
            initial_selected_levels = f"{mid}, {top}"
        
        self.selected_levels_input = QLineEdit(initial_selected_levels)
        self.selected_levels_input.setPlaceholderText("e.g., 1, 3, 5")
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        
        # add to layout
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        layout.addWidget(QLabel("Levels for C&C Pressure:"))
        layout.addWidget(self.selected_levels_input)
        layout.addWidget(self.buttons)

    def update_floor_inputs(self):
        for i in reversed(range(self.floor_heights_layout.count())):
            item = self.floor_heights_layout.itemAt(i)
            if item.layout():
                layout = item.layout()
                for j in reversed(range(layout.count())):
                    child = layout.itemAt(j).widget()
                    if child:
                        child.setParent(None)
                self.floor_heights_layout.removeItem(item)

        self.floor_height_inputs.clear()
        for i in range(self.num_floors):
            row = QHBoxLayout()
            label = QLabel(f"Level {i + 1}:")
            inp = QLineEdit(str(self.initial_heights[i]) if i < len(self.initial_heights) else "3.2")
            row.addWidget(label)
            row.addWidget(inp)
            self.floor_heights_layout.addLayout(row)
            self.floor_height_inputs.append(inp)

    def get_floor_heights(self):
        try:
            return [float(inp.text()) for inp in self.floor_height_inputs]
        except ValueError as e:
            raise ValueError("Invalid floor height input. Please ensure all values are numeric.") from e

    def get_selected_levels(self):
        raw = self.selected_levels_input.text()
        try:
            # Convert to list of unique sorted integers
            levels = sorted(set(int(s.strip()) for s in raw.split(",") if s.strip()))
            # Validate range
            for lvl in levels:
                if not (1 <= lvl <= self.num_floors):
                    raise ValueError(f"Level {lvl} is out of range (1 to {self.num_floors})")
            return levels
        except Exception:
            raise ValueError("Invalid inputs. Value must be comma-separated and not more than total no. of floor.")

    def validate_and_accept(self):
        try:
            self.get_floor_heights()
            self.get_selected_levels()
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))



class TopographyDialog(QDialog):
    def __init__(self, topography_type, topo_height, topo_length, topo_distance, topo_crest_side, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Topography Data")
        self.setFixedSize(600, 350)

        self.K_zt = 1.0
        self.topography_type = topography_type
        self.topo_height = topo_height
        self.topo_length = topo_length
        self.topo_distance = topo_distance
        self.topo_crest_side = topo_crest_side

        self.topo_type_input = QComboBox()
        self.topo_type_input.addItems(["2-Dimensional Ridge", "2-Dimensional Escarpment", "3-Dimensional Hill"])
        self.topo_type_input.setCurrentText(topography_type)
        self.topo_type_input.currentTextChanged.connect(self.on_type_changed)
        
        self.topo_crest_side_input = QComboBox()
        self.topo_crest_side_input.addItems(["Upwind", "Downwind"])
        self.topo_crest_side_input.setCurrentText(topo_crest_side)

        self.topo_height_input = QDoubleSpinBox()
        self.topo_height_input.setRange(0, 9999)
        self.topo_height_input.setValue(topo_height)

        self.topo_length_input = QDoubleSpinBox()
        self.topo_length_input.setRange(0, 9999)
        self.topo_length_input.setValue(topo_length)

        self.topo_distance_input = QDoubleSpinBox()
        self.topo_distance_input.setRange(0, 9999)
        self.topo_distance_input.setValue(topo_distance)

        input_layout = QFormLayout()
        input_layout.setLabelAlignment(Qt.AlignRight)
        input_layout.addRow("Feature Type:", self.topo_type_input)
        input_layout.addRow("Site Direction:", self.topo_crest_side_input)
        input_layout.addRow("Feature Height, H (m):", self.topo_height_input)
        input_layout.addRow("Distance, L<sub>h</sub> (m):", self.topo_length_input)
        input_layout.addRow("Distance, X (m):", self.topo_distance_input)

        self.image_label = QLabel()
        self.image_label.setFixedSize(280, 200)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #b9b9b9;
                padding: 2px;
                margin-right: 4px;
                background-color: white;
            }
        """)
        self.update_image_preview(self.topo_type_input.currentText())

        top_layout = QHBoxLayout()
        top_layout.addLayout(input_layout)
        top_layout.addWidget(self.image_label)

        note_label = QLabel("* Topography factor is calculated based on Fig. 6.2.4, BNBC 2020.")
        note_label.setStyleSheet("font-size: 8pt; color: gray;")

        group_box = QGroupBox()
        group_layout = QVBoxLayout()
        group_layout.addLayout(top_layout)
        group_layout.addWidget(note_label)
        group_box.setLayout(group_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(buttons)

        main_layout = QVBoxLayout()
        main_layout.addWidget(group_box)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def on_type_changed(self, text):
        self.update_image_preview(text)

    def update_image_preview(self, topo_type):
        img_map = {
            "3-Dimensional Hill": resource_path("ui/assets/images/hill.png"),
            "2-Dimensional Ridge": resource_path("ui/assets/images/ridge.png"),
            "2-Dimensional Escarpment": resource_path("ui/assets/images/escarpment.png")
        }
        img_path = img_map.get(topo_type, "")
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("No image found.")



class WindMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wind Load Map")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        wind_map_path = resource_path("ui/assets/images/wind-map.jpg")
        wind_map = QPixmap(wind_map_path)

        scaled_map = wind_map.scaled(
            600, 800, Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        label = QLabel()
        label.setPixmap(scaled_map)

        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        self.setLayout(layout)
        self.setFixedSize(scaled_map.width(), scaled_map.height())


class ExposureExplainDialog(QDialog):
    def __init__(self, exposure_note: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exposure Category Explanation")
        self.exposure_note = exposure_note

        layout = QFormLayout()
        self.exposure_note_input = QTextEdit()
        self.exposure_note_input.setPlainText(self.exposure_note)
        layout.addRow(self.exposure_note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)
        self.setFixedSize(500, 400)
        self.exposure_note_input.textChanged.connect(self.update_exposure_note)

    def update_exposure_note(self):
        self.exposure_note = self.exposure_note_input.toPlainText()


class OccupancyExplainDialog(QDialog):
    def __init__(self, occupancy_note: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Occupancy Category Explanation")
        self.occupancy_note = occupancy_note

        layout = QFormLayout()
        self.occupancy_note_input = QTextEdit()
        self.occupancy_note_input.setPlainText(self.occupancy_note)
        layout.addRow(self.occupancy_note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)
        self.setFixedSize(500, 400)
        self.occupancy_note_input.textChanged.connect(self.update_occupancy_note)

    def update_occupancy_note(self):
        self.occupancy_note = self.occupancy_note_input.toPlainText()


class TopographyExplainDialog(QDialog):
    def __init__(self, topography_note: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Topography Explanation")
        self.topography_note = topography_note

        layout = QFormLayout()
        self.topography_note_input = QTextEdit()
        self.topography_note_input.setPlainText(self.topography_note)
        layout.addRow(self.topography_note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)
        self.setFixedSize(500, 400)
        self.topography_note_input.textChanged.connect(self.update_topography_note)

    def update_topography_note(self):
        self.topography_note = self.topography_note_input.toPlainText()
