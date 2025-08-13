import sys
import os
import tempfile
from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox, QScrollArea,
    QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QRadioButton, QMessageBox, QSizePolicy, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QSize, Qt

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

# from calcs.wind_load import WindLoadCalculator
from calcs.glass import SGUCalculator, DGUCalculator, LGUCalculator, LDGUCalculator
from ui.dialogs.glass_dialog import NFLDialog
from ui.dialogs.report_preview import ReportPreviewWindow


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class GlassTab(QWidget):
    def __init__(self, wind_data=None):
        super().__init__()
        self.wind_data = wind_data
        self.wind_calculator = None  # Will store WindLoadCalculator instance
        self.summary = None
        self.initUI()

    def initUI(self):
        # Icons
        self.what_icon_path = resource_path("ui/assets/icons/generals/what.png")
        self.what_icon = QIcon(self.what_icon_path)
        self.explain_icon_path = resource_path("ui/assets/icons/generals/explain.png")
        self.explain_icon = QIcon(self.explain_icon_path)

        # === Left Panel ===
        # Glass Composition Group
        comp_form = QFormLayout()
        self.glass_comp_type_input = QComboBox()
        self.glass_comp_type_input.addItems([
            "Single Glaze Unit (SGU)", 
            "Double Glaze Unit (DGU)", 
            "Laminated Glaze Unit (LGU)", 
            "Laminated Double Glaze Unit (LDGU)"
        ])
        self.glass_comp_type_input.currentTextChanged.connect(self.update_glass_inputs)
        # comp_form.addRow("Glass Type:", self.glass_comp_type_input)
        comp_form.addRow(self.glass_comp_type_input)
        comp_group = QGroupBox("Glass Composition")
        comp_group.setLayout(comp_form)
        comp_group.setFixedWidth(380)

        # Glass Parameters Group
        self.params_form = QFormLayout()
        self.create_glass_inputs()
        params_group = QGroupBox("Glass Parameters")
        params_group.setLayout(self.params_form)
        params_group.setFixedWidth(380)

        # Wind Load Group
        wind_form = QFormLayout()
        
        radio_layout = QHBoxLayout()
        self.manual_radio = QRadioButton("Manual")
        self.automatic_radio = QRadioButton("Automatic")
        self.automatic_radio.setEnabled(False)
        self.manual_radio.setChecked(True)  # Manual is default
        radio_layout.addWidget(self.manual_radio)
        radio_layout.addWidget(self.automatic_radio)
        
        # Connect radio buttons
        self.automatic_radio.toggled.connect(self.on_wind_mode_changed)
        self.manual_radio.toggled.connect(self.on_wind_mode_changed)

        self.effective_area_display = QLineEdit()
        self.effective_area_display.setText(str(self.get_effective_area()))
        self.effective_area_display.setEnabled(False)
        
        self.facade_elevation_input = QLineEdit()
        self.facade_elevation_input.setText("4")
        self.facade_elevation_input.setEnabled(False)
        self.facade_elevation_input.textChanged.connect(self.update_wind_load)
        
        self.zone_input = QComboBox()
        self.zone_input.addItems(["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"])
        self.zone_input.currentTextChanged.connect(self.update_wind_load)
        
        self.wind_load_input = QDoubleSpinBox()
        self.wind_load_input.setRange(0, 100)
        self.wind_load_input.setEnabled(True)
        self.wind_load_input.setValue(2.5)

        wind_form.addRow(radio_layout)
        wind_form.addRow("Effective Area (m²):", self.effective_area_display)
        wind_form.addRow("Facade Elevation (m):", self.facade_elevation_input)
        wind_form.addRow("Wind Zone:", self.zone_input)
        wind_form.addRow("Design Wind Load (kPa):", self.wind_load_input)
        wind_group = QGroupBox("Wind Load")
        wind_group.setLayout(wind_form)
        wind_group.setFixedWidth(380)

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

        # Layout Assembly
        left_panel_container = QWidget()
        left_panel = QVBoxLayout(left_panel_container)
        left_panel.addWidget(comp_group)
        left_panel.addWidget(params_group)
        left_panel.addWidget(wind_group)
        left_panel.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel_container)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(400)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")

        output_layout = QVBoxLayout()
        output_layout.addWidget(self.result_webview)
        output_layout.addWidget(self.report_btn, alignment=Qt.AlignRight)
        output_group = QGroupBox("Glass Design Results")
        output_group.setLayout(output_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(output_group)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Initialize with default composition
        self.update_glass_inputs(self.glass_comp_type_input.currentText())

    def create_glass_inputs(self):
        """Create base glass parameter inputs"""
        self.length_input = QSpinBox()
        self.length_input.setRange(600, 5000)
        self.length_input.setValue(1500)
        self.length_input.valueChanged.connect(self.update_wind_load)
        self.length_input.valueChanged.connect(self.update_effective_area)
        
        self.width_input = QSpinBox()
        self.width_input.setRange(600, 5000)
        self.width_input.setValue(1200)
        self.width_input.valueChanged.connect(self.update_wind_load)
        self.width_input.valueChanged.connect(self.update_effective_area)
        
        self.params_form.addRow("Glass Length (mm):", self.length_input)
        self.params_form.addRow("Glass Width (mm):", self.width_input)

    def update_glass_inputs(self, composition):
        """Update input fields based on glass composition"""
        # Clear existing parameters except length and width
        while self.params_form.rowCount() > 2:
            self.params_form.removeRow(2)

        if "Single Glaze Unit (SGU)" in composition:
            self.add_sgu_inputs()
        elif "Double Glaze Unit (DGU)" in composition:
            self.add_dgu_inputs()
        elif "Laminated Glaze Unit (LGU)" in composition:
            self.add_lgu_inputs()
        elif "Laminated Double Glaze Unit (LDGU)" in composition:
            self.add_ldgu_inputs()

    def add_sgu_inputs(self):
        self.thickness_input = QComboBox()
        self.thickness_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])
        
        self.glass_type_input = QComboBox()
        self.glass_type_input.addItems(["FT", "HS", "AN"])
        
        self.support_type_input = QComboBox()
        self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
        self.support_type_input.setEnabled(False)
        
        # self.free_length_input = QComboBox()
        # self.free_length_input.addItems("Glass Length", "Glass Width")
        # self.free_length_input.setEnabled(False)
        
        nfl_layout = QHBoxLayout()
        self.nfl_input = QDoubleSpinBox()
        self.nfl_input.setValue(2.4)
        self.nfl_chart_button = QPushButton()
        self.nfl_chart_button.setIcon(self.what_icon)
        self.nfl_chart_button.setIconSize(QSize(16, 16))
        self.nfl_chart_button.clicked.connect(self.show_nfl_chart)
        nfl_layout.addWidget(self.nfl_input)
        nfl_layout.addWidget(self.nfl_chart_button)

        self.params_form.addRow("Glass Thickness (mm):", self.thickness_input)
        self.params_form.addRow("Glass Type:", self.glass_type_input)
        self.params_form.addRow("Support Type:", self.support_type_input)
        self.params_form.addRow("Non-factored Load (NFL):", nfl_layout)

    def add_dgu_inputs(self):
        self.thickness1_input = QComboBox()
        self.thickness1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])
        self.glass1_type_input = QComboBox()
        self.glass1_type_input.addItems(["FT", "HS", "AN"])
        
        self.gap_input = QComboBox()
        self.gap_input.addItems(["12", "16", "20"])
        
        self.thickness2_input = QComboBox()
        self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])
        self.glass2_type_input = QComboBox()
        self.glass2_type_input.addItems(["FT", "HS", "AN"])
        
        self.support_type_input = QComboBox()
        self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
        self.support_type_input.setEnabled(False)
        
        nfl1_layout = QHBoxLayout()
        self.nfl1_input = QDoubleSpinBox()
        self.nfl1_input.setValue(2.4)
        self.nfl1_chart_button = QPushButton()
        self.nfl1_chart_button.setIcon(self.what_icon)
        self.nfl1_chart_button.setIconSize(QSize(16, 16))
        self.nfl1_chart_button.clicked.connect(self.show_outer_nfl_chart)
        nfl1_layout.addWidget(self.nfl1_input)
        nfl1_layout.addWidget(self.nfl1_chart_button)

        nfl2_layout = QHBoxLayout()
        self.nfl2_input = QDoubleSpinBox()
        self.nfl2_input.setValue(2.4)
        self.nfl2_chart_button = QPushButton()
        self.nfl2_chart_button.setIcon(self.what_icon)
        self.nfl2_chart_button.setIconSize(QSize(16, 16))
        self.nfl2_chart_button.clicked.connect(self.show_inner_nfl_chart)
        nfl2_layout.addWidget(self.nfl2_input)
        nfl2_layout.addWidget(self.nfl2_chart_button)

        form_layout = self.params_form
        form_layout.addRow("Outer Panel Thickness (mm):", self.thickness1_input)
        form_layout.addRow("Outer Panel Glass Type:", self.glass1_type_input)
        form_layout.addRow("Air Gap (mm):", self.gap_input)
        form_layout.addRow("Inner Panel Thickness (mm):", self.thickness2_input)
        form_layout.addRow("Inner Panel Glass Type:", self.glass2_type_input)
        form_layout.addRow("Support Type:", self.support_type_input)
        form_layout.addRow("Non-factored Load for Outer Pane:", nfl1_layout)
        form_layout.addRow("Non-factored Load for Inner Pane:", nfl2_layout)

    def add_lgu_inputs(self):
        self.thickness1_input = QComboBox()
        self.thickness1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
        self.interlayer_thickness = QComboBox()
        self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
        
        self.thickness2_input = QComboBox()
        self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
        self.glass_type_input = QComboBox()
        self.glass_type_input.addItems(["FT", "HS", "AN"])
        
        self.support_type_input = QComboBox()
        self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
        self.support_type_input.setEnabled(False)
        
        nfl_layout = QHBoxLayout()
        self.nfl_input = QDoubleSpinBox()
        self.nfl_input.setValue(2.4)
        self.nfl_chart_button = QPushButton()
        self.nfl_chart_button.setIcon(self.what_icon)
        self.nfl_chart_button.setIconSize(QSize(16, 16))
        self.nfl_chart_button.clicked.connect(self.show_nfl_chart)
        nfl_layout.addWidget(self.nfl_input)
        nfl_layout.addWidget(self.nfl_chart_button)
        
        form_layout = self.params_form
        form_layout.addRow("First Glass Thickness (mm):", self.thickness1_input)
        form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
        form_layout.addRow("Second Glass Thickness (mm):", self.thickness2_input)
        form_layout.addRow("Glass Type:", self.glass_type_input)
        form_layout.addRow("Support Type:", self.support_type_input)
        form_layout.addRow("Non-factored Load for Outer Pane:", nfl_layout)

    def add_ldgu_inputs(self):
        self.thickness1_1_input = QComboBox()
        self.thickness1_1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        self.interlayer_thickness = QComboBox()
        self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
        self.thickness1_2_input = QComboBox()
        self.thickness1_2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
        self.gap_input = QComboBox()
        self.gap_input.addItems(["12", "16", "20"])
        
        self.thickness2_input = QComboBox()
        self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])

        self.glass1_type_input = QComboBox()
        self.glass1_type_input.addItems(["FT", "HS", "AN"])
        self.glass2_type_input = QComboBox()
        self.glass2_type_input.addItems(["FT", "HS", "AN"])
        
        self.support_type_input = QComboBox()
        self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
        self.support_type_input.setEnabled(False)
        
        nfl1_layout = QHBoxLayout()
        self.nfl1_input = QDoubleSpinBox()
        self.nfl1_input.setValue(2.4)
        self.nfl1_chart_button = QPushButton()
        self.nfl1_chart_button.setIcon(self.what_icon)
        self.nfl1_chart_button.setIconSize(QSize(16, 16))
        self.nfl1_chart_button.clicked.connect(self.show_outer_nfl_chart)
        nfl1_layout.addWidget(self.nfl1_input)
        nfl1_layout.addWidget(self.nfl1_chart_button)

        nfl2_layout = QHBoxLayout()
        self.nfl2_input = QDoubleSpinBox()
        self.nfl2_input.setValue(2.4)
        self.nfl2_chart_button = QPushButton()
        self.nfl2_chart_button.setIcon(self.what_icon)
        self.nfl2_chart_button.setIconSize(QSize(16, 16))
        self.nfl2_chart_button.clicked.connect(self.show_inner_nfl_chart)
        nfl2_layout.addWidget(self.nfl2_input)
        nfl2_layout.addWidget(self.nfl2_chart_button)
        
        form_layout = self.params_form
        form_layout.addRow("Laminated Glass Outer Pane Thickness (mm):", self.thickness1_1_input)
        form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
        form_layout.addRow("Laminated Glass Inner Pane Thickness (mm):", self.thickness1_2_input)
        form_layout.addRow("Laminated Glass Type:", self.glass1_type_input)
        form_layout.addRow("Air Gap (mm):", self.gap_input)
        form_layout.addRow("Inner Glass Thickness (mm):", self.thickness2_input)
        form_layout.addRow("Inner Glass Type:", self.glass2_type_input)
        form_layout.addRow("Support Type:", self.support_type_input)
        form_layout.addRow("Non-factored Load for Outer Pane:", nfl1_layout)
        form_layout.addRow("Non-factored Load for Inner Pane:", nfl2_layout)

    def get_effective_area(self):
        h = self.length_input.value() / 1000
        b = self.width_input.value() / 1000
        eff_area = round(max((h * b), (h**2 / 3)), 1)
        return eff_area
    
    def update_effective_area(self):
        effective_area = self.get_effective_area()
        self.effective_area_display.setText(str(effective_area))

    def round_thickness_lgu(self, thickness):
        available = [5, 6, 8, 10, 12, 16, 19]
        return min(available, key=lambda x: abs(x - thickness))

    def show_nfl_chart(self):
        comp_type = self.glass_comp_type_input.currentText()
        support_type = self.support_type_input.currentText()

        if "Single Glaze Unit (SGU)" in comp_type:
            thickness = float(self.thickness_input.currentText())

        elif "Laminated Glaze Unit (LGU)" in comp_type:
            t1 = float(self.thickness1_input.currentText())
            t2 = float(self.thickness2_input.currentText())
            interlayer = float(self.interlayer_thickness.currentText())
            base_thickness = t1 + interlayer + t2
            thickness = float(self.round_thickness_lgu(base_thickness))

        dialog = NFLDialog(thickness, comp_type, support_type, self)
        dialog.exec_()

    def show_outer_nfl_chart(self):
        comp_type = self.glass_comp_type_input.currentText()
        support_type = self.support_type_input.currentText()

        if "Double Glaze Unit (DGU)" in comp_type:
            thickness = float(self.thickness1_input.currentText())

        elif "Laminated Double Glaze Unit (LDGU)" in comp_type:
            t1 = float(self.thickness1_1_input.currentText())
            t2 = float(self.thickness1_2_input.currentText())
            interlayer = float(self.interlayer_thickness.currentText())
            base_thickness = t1 + interlayer + t2
            thickness = float(self.round_thickness_lgu(base_thickness))

        dialog = NFLDialog(thickness, comp_type, support_type, self)
        dialog.exec_()

    def show_inner_nfl_chart(self):
        comp_type = "Double Glaze Unit (DGU)"
        support_type = self.support_type_input.currentText()
        thickness = float(self.thickness2_input.currentText())

        dialog = NFLDialog(thickness, comp_type, support_type, self)
        dialog.exec_()


    def on_wind_mode_changed(self):
        is_manual = self.manual_radio.isChecked()
        self.wind_load_input.setEnabled(is_manual)
        if not is_manual:
            self.update_wind_load()
        else:
            self.wind_load_input.setValue(1.0)

    def update_wind_load(self):
        if self.automatic_radio.isChecked():
            try:
                if not self.wind_tab or not self.wind_tab.wind_data:
                    raise ValueError("Wind data not available. Calculate wind load first.")

                effective_area = self.get_effective_area()
                elevation = float(self.facade_elevation_input.text())
                zone = self.zone_input.currentText()

                # Use wind calculator from wind tab
                if hasattr(self.wind_tab, 'wind_pressure'):
                    pressure = self.wind_tab.wind_pressure.get_cladding_pressure(
                        effective_area, elevation, zone
                    )
                    self.wind_load_input.setValue(pressure)
                else:
                    raise ValueError("Wind pressure calculator not initialized")

            except Exception as e:
                print(f"Error calculating wind load: {e}")
                self.manual_radio.setChecked(True)
                QMessageBox.warning(self, "Warning", str(e))
        else:
            self.wind_load_input.setEnabled(True)



    def get_calculation_params(self):
        if "Single Glaze Unit (SGU)" in self.glass_comp_type_input.currentText():
            return {
                "length": self.length_input.value(),
                "width": self.width_input.value(),
                "thickness": float(self.thickness_input.currentText()),
                "glass_type": self.glass_type_input.currentText(),
                "support_type": self.support_type_input.currentText(),
                "wind_load": self.wind_load_input.value(),
                "nfl": self.nfl_input.value()
            }
        elif "Double Glaze Unit (DGU)" in self.glass_comp_type_input.currentText():
            return {
                "length": self.length_input.value(),
                "width": self.width_input.value(),
                "thickness1": float(self.thickness1_input.currentText()),
                "gap": int(self.gap_input.currentText()),
                "thickness2": float(self.thickness2_input.currentText()),
                "glass1_type": self.glass1_type_input.currentText(),
                "glass2_type": self.glass2_type_input.currentText(),
                "support_type": self.support_type_input.currentText(),
                "wind_load": self.wind_load_input.value(),
                "nfl1": self.nfl1_input.value(),
                "nfl2": self.nfl2_input.value()
            }
        # elif "Laminated" in self.glass_comp_type_input.currentText() and "Double" not in self.glass_comp_type_input.currentText():
        elif "Laminated Glaze Unit (LGU)" in self.glass_comp_type_input.currentText():
            return {
                "length": self.length_input.value(),
                "width": self.width_input.value(),
                "thickness1": float(self.thickness1_input.currentText()),
                "thickness_inner": float(self.interlayer_thickness.currentText()),
                "thickness2": float(self.thickness2_input.currentText()),
                "glass_type": self.glass_type_input.currentText(),
                "support_type": self.support_type_input.currentText(),
                "wind_load": self.wind_load_input.value(),
                "nfl": self.nfl_input.value()
            }
        # else:  # LDGU
        elif "Laminated Double Glaze Unit (LDGU)" in self.glass_comp_type_input.currentText():  # LDGU
            return {
                "length": self.length_input.value(),
                "width": self.width_input.value(),
                "thickness1_1": float(self.thickness1_1_input.currentText()),
                "thickness_inner": float(self.interlayer_thickness.currentText()),
                "thickness1_2": float(self.thickness1_2_input.currentText()),
                "gap": int(self.gap_input.currentText()),
                "thickness2": float(self.thickness2_input.currentText()),
                "glass1_type": self.glass1_type_input.currentText(),
                "glass2_type": self.glass2_type_input.currentText(),
                "support_type": self.support_type_input.currentText(),
                "wind_load": self.wind_load_input.value(),
                "nfl1": self.nfl1_input.value(),
                "nfl2": self.nfl2_input.value()
            }

    def trigger_calculate(self):
        self.calculate()

    def calculate(self):
        try:
            comp_type = self.glass_comp_type_input.currentText()
            params = self.get_calculation_params()
            
            if "Single Glaze Unit (SGU)" in comp_type:
                calculator = SGUCalculator(**params)
            elif "Double Glaze Unit (DGU)" in comp_type:
                calculator = DGUCalculator(**params)
            elif "Laminated Glaze Unit (LGU)" in comp_type:
                calculator = LGUCalculator(**params)
            elif "Laminated Double Glaze Unit (LDGU)" in comp_type:
                calculator = LDGUCalculator(**params)

            self.summary = calculator.summary()
            self.update_results()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

    def update_results(self):
        try:
            result_temp_path = resource_path("ui/renders")
            env = Environment(loader=FileSystemLoader(result_temp_path))
            template = env.get_template("glass.html")
            combined_html = template.render(
                summary=self.summary,
                composition=self.glass_comp_type_input.currentText()
            )
            base_url = QUrl.fromLocalFile(os.path.abspath(result_temp_path) + "/")
            self.result_webview.setHtml(combined_html, base_url)
            # print("Rendering with summary:", self.summary)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to render results: {str(e)}")

    def view_report(self):
        if not self.summary:
            QMessageBox.warning(self, "Warning", "Please calculate glass design first.")
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
            template = env.get_template("glass.html")

            html_content = template.render(
                project_info=project_info,
                summary=self.summary,
                composition=self.glass_comp_type_input.currentText()
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

