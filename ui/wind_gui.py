import sys
import os
import tempfile
from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox, QScrollArea,
    QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QRadioButton, QMessageBox, QSizePolicy, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QSize

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

import math
# from config.project_info import ProjectInfo
from calcs.wind_load import WindLoadCalculator
from calcs.package.wind_parameters import location_wind_speeds, importance_factor, directionality_factor, gust_factor
from ui.dialogs.wind_dialog import FloorHeightsDialog, TopographyDialog, WindMapDialog, ExposureExplainDialog, OccupancyExplainDialog, TopographyExplainDialog
from ui.dialogs.report_preview import ReportPreviewWindow


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class WindLoadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.mwfrs_pressure = None
        self.wall_cladding_pressure = None
        self.roof_cladding_pressure = None
        self.summary = None
        self.initUI()

    def initUI(self):
        # icons
        self.what_icon_path = resource_path("ui/assets/icons/generals/what.png")
        self.what_icon = QIcon(self.what_icon_path)
        self.explain_icon_path = resource_path("ui/assets/icons/generals/explain.png")
        self.explain_icon = QIcon(self.explain_icon_path)
        self.location_icon_path = resource_path("ui/assets/icons/generals/map.png")
        self.location_icon = QIcon(self.location_icon_path)

        # === Left Panel ===
        self.structure_type_input = QComboBox()
        self.structure_type_input.addItems([
            "Buildings", "Solid Sign", "Open Sign", "Lattice framework",
            "Trussed Tower (Rectangular)", "Trussed Tower (Square)", "Trussed Tower (Triangular)", "Trussed Tower (Others)",
            "Chimney, Tanks (Hexagonal)", "Chimney, Tanks (Round)", "Chimney, Tanks (Square)"
        ])
        self.structure_type_input.setEnabled(False)
        
        # Geometry Inputs
        self.b_type_input = QComboBox()
        self.b_type_input.addItems(["Regular", "Irregular"])
        self.b_type_input.setEnabled(False)
        self.enclosure_type_input = QComboBox()
        self.enclosure_type_input.addItems(["Enclosed", "Partially Enclosed", "Open"])
        
        self.roof_type_input = QComboBox()
        self.roof_type_input.addItems(["Flat", "Monoslope", "Gable", "Hip", "Dome"])
        self.roof_type_input.setEnabled(False)
        
        self.b_height_input = QDoubleSpinBox()      # consider it as ridge height
        self.b_height_input.setValue(52.6)
        self.b_height_input.setMaximum(9999.99)
        self.b_eave_height_input = QDoubleSpinBox()
        self.b_eave_height_input.setValue(45.3)
        self.b_eave_height_input.setMaximum(9999.99)
        self.b_mean_roof_height_input = QDoubleSpinBox()
        self.b_mean_roof_height_input.setValue(47.4)
        self.b_mean_roof_height_input.setMaximum(9999.99)
        
        self.b_width_input = QDoubleSpinBox()
        self.b_width_input.setValue(42.3)
        self.b_width_input.setMaximum(9999.99)
        self.b_length_input = QDoubleSpinBox()
        self.b_length_input.setValue(28.6)
        self.b_length_input.setMaximum(9999.99)

        self.parapet_enable = QCheckBox()
        self.parapet_input = QDoubleSpinBox()
        self.parapet_input.setValue(0)
        self.parapet_input.setEnabled(False)
        self.parapet_enable.stateChanged.connect(lambda: self.parapet_input.setEnabled(self.parapet_enable.isChecked()))
        
        self.num_floors_input = QSpinBox()
        self.num_floors_input.setRange(1, 200)
        self.num_floors_input.setValue(18)
        self.num_floors_input.valueChanged.connect(self.adjust_floor_heights_length)
        self.floor_data_button = QPushButton("Floor Data")
        self.floor_data_button.clicked.connect(self.open_floor_data_dialog)
        self.floor_height_inputs = [3.2] * self.num_floors_input.value()
        self.selected_levels_inputs = [math.ceil(self.num_floors_input.value() / 2), self.num_floors_input.value()]

        # Basic Parameters Inputs
        self.location_input = QComboBox()
        self.location_input.addItems(sorted(location_wind_speeds.keys()))
        
        self.wind_enable = QCheckBox()
        self.wind_speed_input = QDoubleSpinBox()
        self.wind_speed_input.setEnabled(False)
        self.wind_enable.stateChanged.connect(lambda: self.wind_speed_input.setEnabled(self.wind_enable.isChecked()))
        self.wind_map_button = QPushButton()
        self.wind_map_button.setIcon(self.location_icon)
        self.wind_map_button.setIconSize(QSize(16, 16))
        self.wind_map_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.wind_map_button.setToolTip("Wind Speed Map")
        self.wind_map_button.clicked.connect(self.open_wind_map_dialog)
        
        self.exposure_cat_input = QComboBox()
        self.exposure_cat_input.addItems(["A", "B", "C"])
        self.exposure_note = ""
        self.exposure_explain_button = QPushButton()
        self.exposure_explain_button.setIcon(self.explain_icon)
        self.exposure_explain_button.setIconSize(QSize(16, 16))
        self.exposure_explain_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.exposure_explain_button.setToolTip("Exposure Category Explanation")
        self.exposure_explain_button.clicked.connect(self.open_exposure_explain_dialog)
        
        self.occupancy_cat_input = QComboBox()
        self.occupancy_cat_input.addItems(["I", "II", "III", "IV"])
        self.occupancy_note = ""
        self.occupancy_explain_button = QPushButton()
        self.occupancy_explain_button.setIcon(self.explain_icon)
        self.occupancy_explain_button.setIconSize(QSize(16, 18))
        self.occupancy_explain_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.occupancy_explain_button.setToolTip("Occupancy Category Explanation")
        self.occupancy_explain_button.clicked.connect(self.open_occupancy_explain_dialog)
        
        self.importance_display = QLineEdit()
        self.importance_display.setEnabled(False)
        self.directionality_factor_display = QLineEdit()
        self.directionality_factor_display.setEnabled(False)

        self.topo_check = QCheckBox("Consider Topography")
        self.topography_type = "Homogeneous"
        self.topo_height = 15.3     # default values
        self.topo_length = 12.8
        self.topo_distance = 18.2
        self.topo_crest_side = "Upwind"
        self.K_zt_value = 1.0
        self.topo_button = QPushButton("Topography Data")
        self.topo_button.setEnabled(False)
        self.topo_check.stateChanged.connect(lambda: self.topo_button.setEnabled(self.topo_check.isChecked()))
        self.topo_button.clicked.connect(self.open_topography_dialog)
        self.topography_note = ""
        self.topo_explain_button = QPushButton()
        self.topo_explain_button.setIcon(self.explain_icon)
        self.topo_explain_button.setIconSize(QSize(16, 16))
        self.topo_explain_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.topo_explain_button.setToolTip("Topograpy Explanation")
        self.topo_explain_button.clicked.connect(self.open_topography_explain_dialog)
        
        # Gust Effect Inputs
        self.rigid_radio = QRadioButton("Rigid")
        self.flexible_radio = QRadioButton("Flexible")
        self.rigid_radio.setChecked(True)

        self.damping_input = QDoubleSpinBox()
        self.damping_input.setValue(0.02)
        self.damping_input.setEnabled(False)
        
        self.b_freq_input = QDoubleSpinBox()
        self.b_freq_input.setValue(0.45)
        self.b_freq_input.setEnabled(False)
        
        self.gust_display = QLineEdit("0.85")
        self.gust_display.setEnabled(False)

        self.wind_speed_input.valueChanged.connect(self.update_gust_factor)
        self.exposure_cat_input.currentTextChanged.connect(self.update_gust_factor)
        self.damping_input.valueChanged.connect(self.update_gust_factor)
        self.b_freq_input.valueChanged.connect(self.update_gust_factor)
        self.flexible_radio.toggled.connect(self.update_gust_factor)
        self.rigid_radio.toggled.connect(self.update_gust_mode)

        # === Right Panel ===
        self.result_webview = QWebEngineView()
        self.report_btn = QPushButton("View Report")
        self.report_btn.setFixedSize(110, 30)
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.report_btn.clicked.connect(self.view_report)



        # ==============================
        # LAYOUTS
        # ==============================
        parapet_layout = QHBoxLayout()
        parapet_layout.addWidget(self.parapet_enable)
        parapet_layout.addWidget(self.parapet_input)
        
        floor_layout = QHBoxLayout()
        floor_layout.addWidget(self.num_floors_input)
        floor_layout.addWidget(self.floor_data_button)
        
        wind_layout = QHBoxLayout()
        wind_layout.addWidget(self.wind_enable)
        wind_layout.addWidget(self.wind_speed_input)
        wind_layout.addWidget(self.wind_map_button)
        
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(self.exposure_cat_input)
        exposure_layout.addWidget(self.exposure_explain_button)
        
        occupancy_layout = QHBoxLayout()
        occupancy_layout.addWidget(self.occupancy_cat_input)
        occupancy_layout.addWidget(self.occupancy_explain_button)
        
        topo_layout = QHBoxLayout()
        topo_layout.addWidget(self.topo_check)
        topo_layout.addWidget(self.topo_button)
        topo_layout.addWidget(self.topo_explain_button)
        
        gust_buttons = QHBoxLayout()
        gust_buttons.addWidget(self.rigid_radio)
        gust_buttons.addWidget(self.flexible_radio)
        
        
        struc_form = QFormLayout()
        struc_form.addRow(self.structure_type_input)
        struc_group = QGroupBox("Structure Type")
        struc_group.setLayout(struc_form)
        struc_group.setFixedWidth(380)
        
        geo_form = QFormLayout()
        # geo_form.setLabelAlignment(Qt.AlignRight)
        geo_form.addRow("Building Type:", self.b_type_input)
        geo_form.addRow("Enclosure Type:", self.enclosure_type_input)
        geo_form.addRow("Roof Type:", self.roof_type_input)
        geo_form.addRow("Height (m):", self.b_height_input)
        geo_form.addRow("Eaves Height (m):", self.b_eave_height_input)
        geo_form.addRow("Mean Roof Height (m):", self.b_mean_roof_height_input)
        geo_form.addRow("Width (m):", self.b_width_input)
        geo_form.addRow("Length (m):", self.b_length_input)
        geo_form.addRow("Parapet (m):", parapet_layout)
        geo_form.addRow("No. of Floors:", floor_layout)
        geo_group = QGroupBox("Geometry")
        geo_group.setLayout(geo_form)
        geo_group.setFixedWidth(380)
        
        basic_form = QFormLayout()
        # basic_form.setLabelAlignment(Qt.AlignRight)
        basic_form.addRow("Location:", self.location_input)
        basic_form.addRow("Wind Speed (m/s):", wind_layout)
        basic_form.addRow("Exposure Category:", exposure_layout)
        basic_form.addRow("Occupancy Category:", occupancy_layout)
        basic_form.addRow("Importance Factor:", self.importance_display)
        basic_form.addRow("Directionality Factor:", self.directionality_factor_display)
        basic_form.addRow(topo_layout)
        basic_group = QGroupBox("Basic Parameters")
        basic_group.setLayout(basic_form)
        basic_group.setFixedWidth(380)
        
        gust_form = QFormLayout()
        # gust_form.setLabelAlignment(Qt.AlignRight)
        gust_form.addRow(gust_buttons)
        gust_form.addRow("Damping Ratio:", self.damping_input)
        gust_form.addRow("Natural Freq. (Hz):", self.b_freq_input)
        gust_form.addRow("Gust Factor:", self.gust_display)
        gust_group = QGroupBox("Gust Effect Factor")
        gust_group.setLayout(gust_form)
        gust_group.setFixedWidth(380)
        
        
        btn_layout = QHBoxLayout()  # report button
        btn_layout.addStretch()
        btn_layout.addWidget(self.report_btn)
        
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(0, 2, 0, 0)
        output_layout.addWidget(self.result_webview)
        output_layout.addLayout(btn_layout)

        output_group = QGroupBox("Wind Load Results")
        output_group.setLayout(output_layout)
        
        
        left_panel_container = QWidget()
        
        left_panel = QVBoxLayout(left_panel_container)
        left_panel.addWidget(struc_group)
        left_panel.addWidget(geo_group)
        left_panel.addWidget(basic_group)
        left_panel.addWidget(gust_group)
        
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel_container)
        left_scroll.setFixedWidth(400)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        right_panel_container = QWidget()
        right_panel = QVBoxLayout(right_panel_container)
        right_panel.addWidget(output_group)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(right_panel_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)


        # Signals
        self.structure_type_input.currentTextChanged.connect(self.update_directionality_factor)     # the whole form to be changed, add later
        self.roof_type_input.currentTextChanged.connect(self.update_geometry_input)
        self.location_input.currentTextChanged.connect(self.update_wind_speed)
        self.occupancy_cat_input.currentTextChanged.connect(self.update_importance_factor)

        # Initialize
        self.update_directionality_factor()
        self.update_geometry_input()
        self.update_wind_speed()
        self.update_importance_factor()


    def adjust_floor_heights_length(self, new_floor_count):
        current_count = len(self.floor_height_inputs)
        if new_floor_count > current_count:
            # Add default heights for new floors
            self.floor_height_inputs.extend([3.2] * (new_floor_count - current_count))
        elif new_floor_count < current_count:
            # Trim the list
            self.floor_height_inputs = self.floor_height_inputs[:new_floor_count]

    def open_floor_data_dialog(self):
        num_floors = self.num_floors_input.value()

        # Pad or trim the existing list
        while len(self.floor_height_inputs) < num_floors:
            self.floor_height_inputs.append(3.2)
        self.floor_height_inputs = self.floor_height_inputs[:num_floors]

        selected_str = ", ".join(str(lvl) for lvl in self.selected_levels_inputs)

        dialog = FloorHeightsDialog(
            num_floors=num_floors,
            initial_heights=self.floor_height_inputs,
            initial_selected_levels=selected_str,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.floor_height_inputs = dialog.get_floor_heights()
            self.selected_levels_inputs = dialog.get_selected_levels()

    def update_directionality_factor(self):
        str_type = self.structure_type_input.currentText()
        self.directionality_factor_display.setText(str(directionality_factor(str_type)))

    def update_geometry_input(self):
        roof_type = self.roof_type_input.currentText()
        is_roof = roof_type == "Flat"
        self.b_eave_height_input.setDisabled(is_roof)
        self.b_mean_roof_height_input.setDisabled(is_roof)

    def update_wind_speed(self):
        loc = self.location_input.currentText()
        self.wind_speed_input.setValue(location_wind_speeds.get(loc, 0))

    def update_importance_factor(self):
        occ = self.occupancy_cat_input.currentText()
        self.importance_display.setText(str(importance_factor(occ)))

    def update_gust_mode(self):
        is_flexible = self.flexible_radio.isChecked()
        self.damping_input.setEnabled(is_flexible)
        self.b_freq_input.setEnabled(is_flexible)
        self.damping_input.valueChanged.connect(self.update_gust_factor)
        self.b_freq_input.valueChanged.connect(self.update_gust_factor)

    def update_gust_factor(self):
        if not self.flexible_radio.isChecked():
            self.gust_display.setText("0.85")
            return

        try:
            H = self.b_height_input.value()
            B = self.b_width_input.value()
            L = self.b_length_input.value()
            V = self.wind_speed_input.value()
            n1 = self.b_freq_input.value()
            beta = self.damping_input.value()
            exposure_cat = self.exposure_cat_input.currentText()

            # Call the actual gust factor function
            G_f = gust_factor(H, L, B, V, n1, beta, exposure_cat)
            self.gust_display.setText(f"{G_f:.3f}")
        except Exception as e:
            self.gust_display.setText("Err")
            print("Gust factor calculation failed:", e)

    def open_topography_dialog(self):
        dialog = TopographyDialog(
            topography_type=self.topography_type,
            topo_height=self.topo_height,
            topo_length=self.topo_length,
            topo_distance=self.topo_distance,
            topo_crest_side=self.topo_crest_side,
            parent=self
        )
        if dialog.exec():
            self.topography_type = dialog.topo_type_input.currentText()
            self.topo_height = dialog.topo_height_input.value()
            self.topo_length = dialog.topo_length_input.value()
            self.topo_distance = dialog.topo_distance_input.value()
            self.topo_crest_side = dialog.topo_crest_side_input.currentText()
    
    def open_wind_map_dialog(self):
        dialog = WindMapDialog(self)
        dialog.exec()
    
    def open_exposure_explain_dialog(self):
        dialog = ExposureExplainDialog(exposure_note=self.exposure_note, parent=self)
        if dialog.exec():
            self.exposure_note = dialog.exposure_note
    
    def open_occupancy_explain_dialog(self):
        dialog = OccupancyExplainDialog(occupancy_note=self.occupancy_note, parent=self)
        if dialog.exec():
            self.occupancy_note = dialog.occupancy_note
    
    def open_topography_explain_dialog(self):
        dialog = TopographyExplainDialog(topography_note=self.topography_note, parent=self)
        if dialog.exec():
            self.topography_note = dialog.topography_note


    def get_calculation_params(self):
        return {
            "structure_type": self.structure_type_input.currentText(),
            "b_type": self.b_type_input.currentText(),
            "enclosure_type": self.enclosure_type_input.currentText(),
            "roof_type": self.roof_type_input.currentText(),
            "location": self.location_input.currentText(),
            "wind_speed": self.wind_speed_input.value() if self.wind_enable.isChecked() else location_wind_speeds.get(self.location_input.currentText(), 0),
            "b_rigidity": "Flexible" if self.flexible_radio.isChecked() else "Rigid",
            "b_freq": self.b_freq_input.value(),
            "damping": self.damping_input.value(),
            "b_height": self.b_height_input.value(),
            "b_width": self.b_width_input.value(),
            "b_length": self.b_length_input.value(),
            "parapet_height": self.parapet_input.value() if self.parapet_enable.isChecked() else 0.0,
            "exposure_cat": self.exposure_cat_input.currentText(),
            "exposure_note": self.exposure_note,
            "occupancy_cat": self.occupancy_cat_input.currentText(),
            "occupancy_note": self.occupancy_note,
            "topography_type": self.topography_type if self.topo_check.isChecked() else "Homogeneous",
            "topo_height": self.topo_height,
            "topo_length": self.topo_length,
            "topo_distance": self.topo_distance,
            "topo_crest_side": self.topo_crest_side,
            "topography_note": self.topography_note,
            "floor_heights": self.floor_height_inputs,
            "eff_area": [5, 10, 20, 30, 40, 46.5],
            "selected_levels": self.selected_levels_inputs,
        }
    
    def trigger_calculate(self):
        self.calculate()

    def calculate(self):
        try:
            params = self.get_calculation_params()
            wind_pressure = WindLoadCalculator(**params)
            self.summary = wind_pressure.summary()
            self.update_results()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

    def update_results(self):
        try:
            result_temp_path = resource_path("ui/renders")
            env = Environment(loader=FileSystemLoader(result_temp_path))
            template = env.get_template("wind.html")
            combined_html = template.render(
                summary=self.summary
            )
            base_url = QUrl.fromLocalFile(os.path.abspath(result_temp_path) + "/")
            self.result_webview.setHtml(combined_html, base_url)
            # print("Rendering with summary:", self.summary)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to render results: {str(e)}")

    def view_report(self):
        if not self.summary:
            QMessageBox.warning(self, "Warning", "Please calculate wind loads first.")
            return

        try:
            project_info = {
                # "project_name": "Taj & Vivanta Hotel",
                # "ref_no": "REF# RFA-001/REV-02/AEL/CW/2025",
                "rev_no": "02",
                "date_time": date.today().strftime("%d/%m/%Y")
            }

            report_temp_path = resource_path("reports/templates")
            env = Environment(loader=FileSystemLoader(report_temp_path))
            template = env.get_template("wind.html")

            html_content = template.render(
                project_info=project_info,
                summary=self.summary
            )
            
            # Generate Temporary PDF File
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf_path = temp_pdf.name
            temp_pdf.close()
            
            HTML(string=html_content, base_url=report_temp_path).write_pdf(
                pdf_path,
                stylesheets=[CSS(filename=os.path.join(report_temp_path, "css/report.css"))]
            )

            self.preview_window = ReportPreviewWindow(pdf_path)
            self.preview_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to preview report: {str(e)}")
