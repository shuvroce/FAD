import sys
import os
import tempfile
from datetime import date

from PyQt5.QtWidgets import (
    QWidget, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox, QScrollArea,
    QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QRadioButton, QMessageBox, QSizePolicy, QLabel, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QSize, Qt

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

from calcs.conn import ConnCalculator
from ui.dialogs.conn_dialog import ScrewConfigDialog
from ui.dialogs.report_preview import ReportPreviewWindow


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ConnTab(QWidget):
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
        self.screw_config_input = QComboBox()
        self.screw_config_input.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
        self.screw_config_button = QPushButton()
        self.screw_config_button.setIcon(self.what_icon)
        self.screw_config_button.setIconSize(QSize(16, 16))
        self.screw_config_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.screw_config_button.setToolTip("Screw Configuration")
        self.screw_config_button.clicked.connect(self.open_screw_config_dialog)
        
        screw_layout = QHBoxLayout()
        screw_layout.addWidget(self.screw_config_input)
        screw_layout.addWidget(self.screw_config_button)
        
        comp_form = QFormLayout()
        comp_form.addRow("Screw Config:", screw_layout)
        comp_group = QGroupBox("Configuration")
        comp_group.setLayout(comp_form)
        comp_group.setFixedWidth(380)

        # Input Group
        self.t1_input = QDoubleSpinBox()
        self.t1_input.setValue(3.5)
        self.t1_grade_input = QComboBox()
        self.t1_grade_input.addItems(["6063-T5", "6063-T6", "6061-T6"])
        self.t2_input = QDoubleSpinBox()
        self.t2_input.setValue(2.5)
        self.t2_grade_input = QComboBox()
        self.t2_grade_input.addItems(["6063-T5", "6063-T6", "6061-T6"])
        
        self.dia_input = QDoubleSpinBox()
        self.dia_input.setValue(4.8)
        self.screw_length_input = QDoubleSpinBox()
        self.screw_length_input.setValue(25.0)
        self.head_dia_input = QDoubleSpinBox()
        self.head_dia_input.setValue(10.5)
        
        self.wind_load_input = QDoubleSpinBox()
        self.wind_load_input.setRange(0, 100)
        self.wind_load_input.setValue(1.6)
        self.dead_load_input = QDoubleSpinBox()
        self.dead_load_input.setRange(0, 100)
        self.dead_load_input.setValue(0.67)
        
        self.input_form = QFormLayout()
        self.input_form.addRow("Member thk. (with screw head), t<sub>1</sub> (mm):", self.t1_input)
        self.input_form.addRow("Material grade of contact member:", self.t1_grade_input)
        self.input_form.addRow("Other Member thickness, t<sub>2</sub> (mm):", self.t2_input)
        self.input_form.addRow("Material grade of not contact member:", self.t2_grade_input)
        self.input_form.addRow("Diameter of screw, d (mm):", self.dia_input)
        self.input_form.addRow("Length of screw, l (mm):", self.screw_length_input)
        self.input_form.addRow("Diameter of screw head, d<sub>h</sub> (mm):", self.head_dia_input)
        self.input_form.addRow("Reaction to wind load (kN):", self.wind_load_input)
        self.input_form.addRow("Reaction to dead load (kN):", self.dead_load_input)
        
        input_group = QGroupBox("Input Parameters")
        input_group.setLayout(self.input_form)
        input_group.setFixedWidth(380)


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
        left_panel.addWidget(input_group)
        left_panel.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel_container)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(400)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")

        output_layout = QVBoxLayout()
        output_layout.addWidget(self.result_webview)
        output_layout.addWidget(self.report_btn, alignment=Qt.AlignRight)
        output_group = QGroupBox("Connection Design Results")
        output_group.setLayout(output_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(output_group)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

    def open_screw_config_dialog(self):
        dialog = ScrewConfigDialog(self)
        dialog.exec()

    def get_calculation_params(self):
        return {
            "screw_config": self.screw_config_input.currentText(),
            "t1": self.t1_input.value(),
            "t2": self.t2_input.value(),
            "t1_grade": self.t1_grade_input.currentText(),
            "t2_grade": self.t2_grade_input.currentText(),
            "dia": self.dia_input.value(),
            "screw_length": self.screw_length_input.value(),
            "head_dia": self.head_dia_input.value(),
            "wind_load": self.wind_load_input.value(),
            "dead_load": self.dead_load_input.value(),
        }

    def trigger_calculate(self):
        self.calculate()

    def calculate(self):
        try:
            params = self.get_calculation_params()
            calculator = ConnCalculator(**params)
            self.summary = calculator.summary()
            self.update_results()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

    def update_results(self):
        try:
            result_temp_path = resource_path("ui/renders")
            env = Environment(loader=FileSystemLoader(result_temp_path))
            template = env.get_template("conn.html")
            combined_html = template.render(
                summary=self.summary,
                option=self.screw_config_input.currentText()
            )
            base_url = QUrl.fromLocalFile(os.path.abspath(result_temp_path) + "/")
            self.result_webview.setHtml(combined_html, base_url)
            # print("Rendering with summary:", self.summary)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to render results: {str(e)}")

    def view_report(self):
        if not self.summary:
            QMessageBox.warning(self, "Warning", "Please design connection first.")
            return

        try:
            project_info = {
                "rev_no": "02",
                "date_time": date.today().strftime("%d/%m/%Y")
            }

            report_temp_path = resource_path("reports/templates")
            env = Environment(loader=FileSystemLoader(report_temp_path))
            template = env.get_template("conn.html")

            html_content = template.render(
                project_info=project_info,
                summary=self.summary,
                option=self.screw_config_input.currentText()
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

