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
from calcs.fixing import BoxClumpCalculator, UClumpCalculator
# from ui.dialogs.fixing_dialog import NFLDialog
from ui.dialogs.report_preview import ReportPreviewWindow


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class FixingTab(QWidget):
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
        # Fixing Type Group
        self.fixing_type_input = QComboBox()
        self.fixing_type_input.addItems([
            "Box Clump", 
            "U Clump", 
            "L Clump (Top)", 
            "L Clump (Bottom)", 
            "Pin Base Plate", 
            "Moment Base Plate" 
        ])
        self.fixing_type_input.currentTextChanged.connect(self.update_input_fields)
        self.fixing_type_input.currentTextChanged.connect(self.update_input_buttons)
        
        self.fixing_type_button = QPushButton()
        self.fixing_type_button.setIcon(self.what_icon)
        self.fixing_type_button.setIconSize(QSize(16, 16))
        self.fixing_type_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.fixing_type_button.setToolTip("Fixing Type Layout")
        # self.fixing_type_button.clicked.connect(self.open_fixing_type_dialog)
        
        fixing_layout = QHBoxLayout()
        fixing_layout.addWidget(self.fixing_type_input)
        fixing_layout.addWidget(self.fixing_type_button)
        
        type_form = QFormLayout()
        type_form.addRow(fixing_layout)
        type_group = QGroupBox("Fixing Type")
        type_group.setLayout(type_form)
        type_group.setFixedWidth(380)
        
        
        # input dialog buttons
        self.anchor_button = QPushButton()
        self.anchor_button.setText("Anchor Bolt Data")
        # self.anchor_button.clicked.connect(self.open_anchor_input_dialog)
        
        self.bp_button = QPushButton()
        self.bp_button.setText("Base Plate Data")
        # self.bp_button.clicked.connect(self.open_bp_input_dialog)
        
        self.conc_button = QPushButton()
        self.conc_button.setText("Concrete Data")
        # self.conc_button.clicked.connect(self.open_conc_input_dialog)
        
        self.fin_button = QPushButton()
        self.fin_button.setText("Fin & Bolt Data")
        self.fin_button.setEnabled(False)
        # self.fin_button.clicked.connect(self.open_fin_input_dialog)
        
        button1_layout = QHBoxLayout()
        button1_layout.addWidget(self.anchor_button)
        button1_layout.addWidget(self.bp_button)
        
        button2_layout = QHBoxLayout()
        button2_layout.addWidget(self.conc_button)
        button2_layout.addWidget(self.fin_button)
        
        button_form = QFormLayout()
        button_form.addRow(button1_layout)
        button_form.addRow(button2_layout)
        button_group = QGroupBox("Fixing Inputs")
        button_group.setLayout(button_form)
        button_group.setFixedWidth(380)
        


        # inputs form
        input_form = QWidget()
        input_form.setFixedWidth(380)
        self.input_layout = QVBoxLayout(input_form)
        self.input_layout.setContentsMargins(0, 0, 0, 0)


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
        # self.report_btn.clicked.connect(self.view_report)


        # Layout Assembly
        left_panel_container = QWidget()
        left_panel = QVBoxLayout(left_panel_container)
        left_panel.addWidget(type_group)
        left_panel.addWidget(button_group)
        left_panel.addWidget(input_form)
        left_panel.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel_container)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(400)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")

        output_layout = QVBoxLayout()
        output_layout.addWidget(self.result_webview)
        output_layout.addWidget(self.report_btn, alignment=Qt.AlignRight)
        output_group = QGroupBox("Fixing Design Results")
        output_group.setLayout(output_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(output_group)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Initialize with default fixing type
        self.update_input_fields(self.fixing_type_input.currentText())


    def clear_input_form(self):
        while self.input_layout.count():
            child = self.input_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_input_fields(self, fixing_type):
        self.clear_input_form()
        
        # Update input fields based on fixing type
        if "Box Clump" in fixing_type:
            self.box_clump_inputs()
        elif "U Clump" in fixing_type:
            self.u_clump_inputs()
        elif "L Clump (Top)" in fixing_type:
            self.l_clump_top_inputs()
        elif "L Clump (Bottom)" in fixing_type:
            self.l_clump_bottom_inputs()
        elif "Pin Base Plate" in fixing_type:
            self.pin_base_inputs()
        elif "Moment Base Plate" in fixing_type:
            self.moment_base_inputs()

    def box_clump_inputs(self):
        # load group
        self.wind_load_input = QDoubleSpinBox()
        self.dead_load_input = QDoubleSpinBox()
        self.wind_ecc_input = QDoubleSpinBox()
        self.dead_ecc_input = QDoubleSpinBox()
        
        load_form = QFormLayout()
        load_form.addRow("Wind Load Reaction, R<sub>y</sub> (kN):", self.wind_load_input)
        load_form.addRow("Dead Load Reaction, R<sub>z</sub> (kN):", self.dead_load_input)
        load_form.addRow("Wind Eccentricity, e<sub>y</sub> (mm):", self.wind_ecc_input)
        load_form.addRow("Dead Eccentricity, e<sub>z</sub> (mm):", self.dead_ecc_input)
        
        load_group = QGroupBox("Reaction Forces")
        load_group.setLayout(load_form)
        load_group.setFixedWidth(380)
        self.input_layout.addWidget(load_group)
        
        # anchor group
        self.n_anchor_input = QComboBox()
        self.n_anchor_input.addItems(["2", "4"])
        self.anchor_dia_input = QComboBox()
        self.anchor_dia_input.addItems(["10", "12", "14", "16", "18", "20", "22", "24", "27", "30", "33", "36", "39", "42", "48"])
        self.embed_depth_input = QDoubleSpinBox()
        self.anchor_grade_input = QComboBox()
        self.anchor_grade_input.addItems(["Grade 4.6", "Grade 5.8", "Grade 6.8", "Grade 8.8", "ASTM A307", "ASTM A325"])
        self.install_type_input = QComboBox()
        self.install_type_input.addItems(["Cast-in", "Post-installed"])
        self.install_type_input.currentTextChanged.connect(self.update_basic_conc_breakout)
        
        anchor_form = QFormLayout()
        anchor_form.addRow("No. of Anchors, n<sub>a</sub>:", self.n_anchor_input)
        anchor_form.addRow("Anchor Diameter, d<sub>a</sub> (mm):", self.anchor_dia_input)
        anchor_form.addRow("Embed Depth, h<sub>ef</sub> (mm):", self.embed_depth_input)
        anchor_form.addRow("Anchor Grade:", self.anchor_grade_input)
        anchor_form.addRow("Installation Type:", self.install_type_input)
        
        anchor_group = QGroupBox("Anchor Info")
        anchor_group.setLayout(anchor_form)
        anchor_group.setFixedWidth(380)
        self.input_layout.addWidget(anchor_group)
        
        # base plate group
        self.bp_length_input = QDoubleSpinBox()
        self.bp_width_input = QDoubleSpinBox()
        self.steel_grade_input = QComboBox()
        self.steel_grade_input.addItems(["A36", "A500 Gr. B", "A572 Gr. 50", "SS 304"])
        self.profile_depth_input = QDoubleSpinBox() 
        self.profile_width_input = QDoubleSpinBox()
        self.ed1_input = QDoubleSpinBox()
        self.ed2_input = QDoubleSpinBox()
        
        bp_form = QFormLayout()
        bp_form.addRow("Length of Base Plate, N (mm):", self.bp_length_input)
        bp_form.addRow("Width of Base Plate, B (mm):", self.bp_width_input)
        bp_form.addRow("Material Grade:", self.steel_grade_input)
        bp_form.addRow("Profile Depth, d (mm):", self.profile_depth_input)
        bp_form.addRow("Profile Width, b (mm):", self.profile_width_input)
        bp_form.addRow("Edge Distance along Length, ed<sub>N</sub> (mm):", self.ed1_input)
        bp_form.addRow("Edge Distance along Width, ed<sub>B</sub> (mm):", self.ed2_input)
        
        bp_group = QGroupBox("Base Plate Geometry")
        bp_group.setLayout(bp_form)
        bp_group.setFixedWidth(380)
        self.input_layout.addWidget(bp_group)
        
        # concrete
        self.conc_grade_input = QComboBox()
        self.conc_grade_input.addItems(["M20", "M25", "M30", "M35", "M40", "M45", "M50", "M55", "3500 psi", "4000 psi", "4500 psi"])
        self.conc_condition_input = QComboBox()
        self.conc_condition_input.addItems(["Cracked", "Uncracked"])
        self.conc_weight_type_input = QComboBox()
        self.conc_weight_type_input.addItems(["Normal", "Lightweight"])
        self.conc_depth_input = QDoubleSpinBox()
        self.conc_Np5_input = QDoubleSpinBox()
        self.conc_Np5_input.setEnabled(False)
        
        self.C_a1_input = QDoubleSpinBox()
        self.C_b1_input = QDoubleSpinBox()
        self.C_a2_input = QDoubleSpinBox()
        self.C_b2_input = QDoubleSpinBox()

        ed_layout = QLabel()
        ed_layout.setText("Concrete Edge Distances (mm):")
        
        ed1_layout = QHBoxLayout()
        ca1_label = QLabel("C<sub>a1</sub>: ")
        ca1_label.setFixedWidth(22)
        ed1_layout.addWidget(ca1_label)
        ed1_layout.addWidget(self.C_a1_input)
        
        cb1_label = QLabel("C<sub>b1</sub>: ")
        cb1_label.setFixedWidth(22)
        ed1_layout.addWidget(cb1_label)
        ed1_layout.addWidget(self.C_b1_input)
        
        ed2_layout = QHBoxLayout()
        ca2_label = QLabel("C<sub>a2</sub>: ")
        ca2_label.setFixedWidth(22)
        ed2_layout.addWidget(ca2_label)
        ed2_layout.addWidget(self.C_a2_input)
        
        cb2_label = QLabel("C<sub>a2</sub>: ")
        cb2_label.setFixedWidth(22)
        ed2_layout.addWidget(cb2_label)
        ed2_layout.addWidget(self.C_b2_input)
        
        conc_form = QFormLayout()
        conc_form.addRow("Concrete Grade:", self.conc_grade_input)
        conc_form.addRow("Concrete Condition:", self.conc_condition_input)
        conc_form.addRow("Concrete Weight Type:", self.conc_weight_type_input)
        conc_form.addRow("Concrete Member Depth, h<sub>a</sub> (mm):", self.conc_depth_input)
        conc_form.addRow("Basic Conc. Breakout Strength, N<sub>b</sub> (mm):", self.conc_Np5_input)
        conc_form.addRow(ed_layout)
        conc_form.addRow(ed1_layout)
        conc_form.addRow(ed2_layout)
        
        conc_group = QGroupBox("Concrete Member Geometry")
        conc_group.setLayout(conc_form)
        conc_group.setFixedWidth(380)
        self.input_layout.addWidget(conc_group)
        
        # bolt group
        # for u/l clump
        
        # fin plate group
        # for u/l clump


    # def u_clump_inputs(self):
    #     self.thickness1_input = QComboBox()
    #     self.thickness1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])
    #     self.glass1_type_input = QComboBox()
    #     self.glass1_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.gap_input = QComboBox()
    #     self.gap_input.addItems(["12", "16", "20"])
        
    #     self.thickness2_input = QComboBox()
    #     self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])
    #     self.glass2_type_input = QComboBox()
    #     self.glass2_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.support_type_input = QComboBox()
    #     self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
    #     self.support_type_input.setEnabled(False)
        
    #     nfl1_layout = QHBoxLayout()
    #     self.nfl1_input = QDoubleSpinBox()
    #     self.nfl1_input.setValue(2.4)
    #     self.nfl1_chart_button = QPushButton()
    #     self.nfl1_chart_button.setIcon(self.what_icon)
    #     self.nfl1_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl1_chart_button.clicked.connect(self.show_outer_nfl_chart)
    #     nfl1_layout.addWidget(self.nfl1_input)
    #     nfl1_layout.addWidget(self.nfl1_chart_button)

    #     nfl2_layout = QHBoxLayout()
    #     self.nfl2_input = QDoubleSpinBox()
    #     self.nfl2_input.setValue(2.4)
    #     self.nfl2_chart_button = QPushButton()
    #     self.nfl2_chart_button.setIcon(self.what_icon)
    #     self.nfl2_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl2_chart_button.clicked.connect(self.show_inner_nfl_chart)
    #     nfl2_layout.addWidget(self.nfl2_input)
    #     nfl2_layout.addWidget(self.nfl2_chart_button)

    #     form_layout = self.input_form
    #     form_layout.addRow("Outer Panel Thickness (mm):", self.thickness1_input)
    #     form_layout.addRow("Outer Panel Glass Type:", self.glass1_type_input)
    #     form_layout.addRow("Air Gap (mm):", self.gap_input)
    #     form_layout.addRow("Inner Panel Thickness (mm):", self.thickness2_input)
    #     form_layout.addRow("Inner Panel Glass Type:", self.glass2_type_input)
    #     form_layout.addRow("Support Type:", self.support_type_input)
    #     form_layout.addRow("Non-factored Load for Outer Pane:", nfl1_layout)
    #     form_layout.addRow("Non-factored Load for Inner Pane:", nfl2_layout)

    # def l_clump_top_inputs(self):
    #     self.thickness1_input = QComboBox()
    #     self.thickness1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.interlayer_thickness = QComboBox()
    #     self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
        
    #     self.thickness2_input = QComboBox()
    #     self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.fixing_type_input = QComboBox()
    #     self.fixing_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.support_type_input = QComboBox()
    #     self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
    #     self.support_type_input.setEnabled(False)
        
    #     nfl_layout = QHBoxLayout()
    #     self.nfl_input = QDoubleSpinBox()
    #     self.nfl_input.setValue(2.4)
    #     self.nfl_chart_button = QPushButton()
    #     self.nfl_chart_button.setIcon(self.what_icon)
    #     self.nfl_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl_chart_button.clicked.connect(self.show_nfl_chart)
    #     nfl_layout.addWidget(self.nfl_input)
    #     nfl_layout.addWidget(self.nfl_chart_button)
        
    #     form_layout = self.input_form
    #     form_layout.addRow("First Glass Thickness (mm):", self.thickness1_input)
    #     form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
    #     form_layout.addRow("Second Glass Thickness (mm):", self.thickness2_input)
    #     form_layout.addRow("Glass Type:", self.fixing_type_input)
    #     form_layout.addRow("Support Type:", self.support_type_input)
    #     form_layout.addRow("Non-factored Load for Outer Pane:", nfl_layout)

    # def l_clump_bottom_inputs(self):
    #     self.thickness1_input = QComboBox()
    #     self.thickness1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.interlayer_thickness = QComboBox()
    #     self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
        
    #     self.thickness2_input = QComboBox()
    #     self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.fixing_type_input = QComboBox()
    #     self.fixing_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.support_type_input = QComboBox()
    #     self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
    #     self.support_type_input.setEnabled(False)
        
    #     nfl_layout = QHBoxLayout()
    #     self.nfl_input = QDoubleSpinBox()
    #     self.nfl_input.setValue(2.4)
    #     self.nfl_chart_button = QPushButton()
    #     self.nfl_chart_button.setIcon(self.what_icon)
    #     self.nfl_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl_chart_button.clicked.connect(self.show_nfl_chart)
    #     nfl_layout.addWidget(self.nfl_input)
    #     nfl_layout.addWidget(self.nfl_chart_button)
        
    #     form_layout = self.input_form
    #     form_layout.addRow("First Glass Thickness (mm):", self.thickness1_input)
    #     form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
    #     form_layout.addRow("Second Glass Thickness (mm):", self.thickness2_input)
    #     form_layout.addRow("Glass Type:", self.fixing_type_input)
    #     form_layout.addRow("Support Type:", self.support_type_input)
    #     form_layout.addRow("Non-factored Load for Outer Pane:", nfl_layout)

    # def pin_base_inputs(self):
    #     self.thickness1_1_input = QComboBox()
    #     self.thickness1_1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
    #     self.interlayer_thickness = QComboBox()
    #     self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
    #     self.thickness1_2_input = QComboBox()
    #     self.thickness1_2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.gap_input = QComboBox()
    #     self.gap_input.addItems(["12", "16", "20"])
        
    #     self.thickness2_input = QComboBox()
    #     self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])

    #     self.glass1_type_input = QComboBox()
    #     self.glass1_type_input.addItems(["FT", "HS", "AN"])
    #     self.glass2_type_input = QComboBox()
    #     self.glass2_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.support_type_input = QComboBox()
    #     self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
    #     self.support_type_input.setEnabled(False)
        
    #     nfl1_layout = QHBoxLayout()
    #     self.nfl1_input = QDoubleSpinBox()
    #     self.nfl1_input.setValue(2.4)
    #     self.nfl1_chart_button = QPushButton()
    #     self.nfl1_chart_button.setIcon(self.what_icon)
    #     self.nfl1_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl1_chart_button.clicked.connect(self.show_outer_nfl_chart)
    #     nfl1_layout.addWidget(self.nfl1_input)
    #     nfl1_layout.addWidget(self.nfl1_chart_button)

    #     nfl2_layout = QHBoxLayout()
    #     self.nfl2_input = QDoubleSpinBox()
    #     self.nfl2_input.setValue(2.4)
    #     self.nfl2_chart_button = QPushButton()
    #     self.nfl2_chart_button.setIcon(self.what_icon)
    #     self.nfl2_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl2_chart_button.clicked.connect(self.show_inner_nfl_chart)
    #     nfl2_layout.addWidget(self.nfl2_input)
    #     nfl2_layout.addWidget(self.nfl2_chart_button)
        
    #     form_layout = self.input_form
    #     form_layout.addRow("Laminated Glass Outer Pane Thickness (mm):", self.thickness1_1_input)
    #     form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
    #     form_layout.addRow("Laminated Glass Inner Pane Thickness (mm):", self.thickness1_2_input)
    #     form_layout.addRow("Laminated Glass Type:", self.glass1_type_input)
    #     form_layout.addRow("Air Gap (mm):", self.gap_input)
    #     form_layout.addRow("Inner Glass Thickness (mm):", self.thickness2_input)
    #     form_layout.addRow("Inner Glass Type:", self.glass2_type_input)
    #     form_layout.addRow("Support Type:", self.support_type_input)
    #     form_layout.addRow("Non-factored Load for Outer Pane:", nfl1_layout)
    #     form_layout.addRow("Non-factored Load for Inner Pane:", nfl2_layout)

    # def moment_base_inputs(self):
    #     self.thickness1_1_input = QComboBox()
    #     self.thickness1_1_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
    #     self.interlayer_thickness = QComboBox()
    #     self.interlayer_thickness.addItems(["0.76", "1.52", "2.28"])
    #     self.thickness1_2_input = QComboBox()
    #     self.thickness1_2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19"])
        
    #     self.gap_input = QComboBox()
    #     self.gap_input.addItems(["12", "16", "20"])
        
    #     self.thickness2_input = QComboBox()
    #     self.thickness2_input.addItems(["2.5", "2.7", "3", "4", "5", "6", "8", "10", "12", "16", "19", "22"])

    #     self.glass1_type_input = QComboBox()
    #     self.glass1_type_input.addItems(["FT", "HS", "AN"])
    #     self.glass2_type_input = QComboBox()
    #     self.glass2_type_input.addItems(["FT", "HS", "AN"])
        
    #     self.support_type_input = QComboBox()
    #     self.support_type_input.addItems(["Four Edges", "Three Edges", "Two Edges", "One Edge"])
    #     self.support_type_input.setEnabled(False)
        
    #     nfl1_layout = QHBoxLayout()
    #     self.nfl1_input = QDoubleSpinBox()
    #     self.nfl1_input.setValue(2.4)
    #     self.nfl1_chart_button = QPushButton()
    #     self.nfl1_chart_button.setIcon(self.what_icon)
    #     self.nfl1_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl1_chart_button.clicked.connect(self.show_outer_nfl_chart)
    #     nfl1_layout.addWidget(self.nfl1_input)
    #     nfl1_layout.addWidget(self.nfl1_chart_button)

    #     nfl2_layout = QHBoxLayout()
    #     self.nfl2_input = QDoubleSpinBox()
    #     self.nfl2_input.setValue(2.4)
    #     self.nfl2_chart_button = QPushButton()
    #     self.nfl2_chart_button.setIcon(self.what_icon)
    #     self.nfl2_chart_button.setIconSize(QSize(16, 16))
    #     self.nfl2_chart_button.clicked.connect(self.show_inner_nfl_chart)
    #     nfl2_layout.addWidget(self.nfl2_input)
    #     nfl2_layout.addWidget(self.nfl2_chart_button)
        
    #     form_layout = self.input_form
    #     form_layout.addRow("Laminated Glass Outer Pane Thickness (mm):", self.thickness1_1_input)
    #     form_layout.addRow("Interlayer Thickness (mm):", self.interlayer_thickness)
    #     form_layout.addRow("Laminated Glass Inner Pane Thickness (mm):", self.thickness1_2_input)
    #     form_layout.addRow("Laminated Glass Type:", self.glass1_type_input)
    #     form_layout.addRow("Air Gap (mm):", self.gap_input)
    #     form_layout.addRow("Inner Glass Thickness (mm):", self.thickness2_input)
    #     form_layout.addRow("Inner Glass Type:", self.glass2_type_input)
    #     form_layout.addRow("Support Type:", self.support_type_input)
    #     form_layout.addRow("Non-factored Load for Outer Pane:", nfl1_layout)
    #     form_layout.addRow("Non-factored Load for Inner Pane:", nfl2_layout)

    def update_basic_conc_breakout(self):
        if self.install_type_input.currentText() == "Post-installed":
            self.conc_Np5_input.setEnabled(True)
        else:
            self.conc_Np5_input.setEnabled(False)
    
    def update_input_buttons(self):
        if self.fixing_type_input.currentText() == "U Clump" or self.fixing_type_input.currentText() == "L Clump (Top)" or self.fixing_type_input.currentText() == "L Clump (Bottom)":
            self.fin_button.setEnabled(True)
        else:
            self.fin_button.setEnabled(False)


    # def get_effective_area(self):
    #     h = self.length_input.value() / 1000
    #     b = self.width_input.value() / 1000
    #     eff_area = round(max((h * b), (h**2 / 3)), 1)
    #     return eff_area
    
    # def update_effective_area(self):
    #     effective_area = self.get_effective_area()
    #     self.effective_area_display.setText(str(effective_area))

    # def round_thickness_lgu(self, thickness):
    #     available = [5, 6, 8, 10, 12, 16, 19]
    #     return min(available, key=lambda x: abs(x - thickness))

    # def show_nfl_chart(self):
    #     comp_type = self.fixing_comp_type_input.currentText()
    #     support_type = self.support_type_input.currentText()

    #     if "Single Glaze Unit (SGU)" in comp_type:
    #         thickness = float(self.thickness_input.currentText())

    #     elif "Laminated Glaze Unit (LGU)" in comp_type:
    #         t1 = float(self.thickness1_input.currentText())
    #         t2 = float(self.thickness2_input.currentText())
    #         interlayer = float(self.interlayer_thickness.currentText())
    #         base_thickness = t1 + interlayer + t2
    #         thickness = float(self.round_thickness_lgu(base_thickness))

    #     dialog = NFLDialog(thickness, comp_type, support_type, self)
    #     dialog.exec_()

    # def show_outer_nfl_chart(self):
    #     comp_type = self.fixing_comp_type_input.currentText()
    #     support_type = self.support_type_input.currentText()

    #     if "Double Glaze Unit (DGU)" in comp_type:
    #         thickness = float(self.thickness1_input.currentText())

    #     elif "Laminated Double Glaze Unit (LDGU)" in comp_type:
    #         t1 = float(self.thickness1_1_input.currentText())
    #         t2 = float(self.thickness1_2_input.currentText())
    #         interlayer = float(self.interlayer_thickness.currentText())
    #         base_thickness = t1 + interlayer + t2
    #         thickness = float(self.round_thickness_lgu(base_thickness))

    #     dialog = NFLDialog(thickness, comp_type, support_type, self)
    #     dialog.exec_()

    # def show_inner_nfl_chart(self):
    #     comp_type = "Double Glaze Unit (DGU)"
    #     support_type = self.support_type_input.currentText()
    #     thickness = float(self.thickness2_input.currentText())

    #     dialog = NFLDialog(thickness, comp_type, support_type, self)
    #     dialog.exec_()


    # def on_wind_mode_changed(self):
    #     is_manual = self.manual_radio.isChecked()
    #     self.wind_load_input.setEnabled(is_manual)
    #     if not is_manual:
    #         self.update_wind_load()
    #     else:
    #         self.wind_load_input.setValue(1.0)

    # def update_wind_load(self):
    #     if self.automatic_radio.isChecked():
    #         try:
    #             if not self.wind_tab or not self.wind_tab.wind_data:
    #                 raise ValueError("Wind data not available. Calculate wind load first.")

    #             effective_area = self.get_effective_area()
    #             elevation = float(self.facade_elevation_input.text())
    #             zone = self.zone_input.currentText()

    #             # Use wind calculator from wind tab
    #             if hasattr(self.wind_tab, 'wind_pressure'):
    #                 pressure = self.wind_tab.wind_pressure.get_cladding_pressure(
    #                     effective_area, elevation, zone
    #                 )
    #                 self.wind_load_input.setValue(pressure)
    #             else:
    #                 raise ValueError("Wind pressure calculator not initialized")

    #         except Exception as e:
    #             print(f"Error calculating wind load: {e}")
    #             self.manual_radio.setChecked(True)
    #             QMessageBox.warning(self, "Warning", str(e))
    #     else:
    #         self.wind_load_input.setEnabled(True)



    # def get_calculation_params(self):
    #     if "Single Glaze Unit (SGU)" in self.fixing_comp_type_input.currentText():
    #         return {
    #             "length": self.length_input.value(),
    #             "width": self.width_input.value(),
    #             "thickness": float(self.thickness_input.currentText()),
    #             "fixing_type": self.fixing_type_input.currentText(),
    #             "support_type": self.support_type_input.currentText(),
    #             "wind_load": self.wind_load_input.value(),
    #             "nfl": self.nfl_input.value()
    #         }
    #     elif "Double Glaze Unit (DGU)" in self.fixing_comp_type_input.currentText():
    #         return {
    #             "length": self.length_input.value(),
    #             "width": self.width_input.value(),
    #             "thickness1": float(self.thickness1_input.currentText()),
    #             "gap": int(self.gap_input.currentText()),
    #             "thickness2": float(self.thickness2_input.currentText()),
    #             "glass1_type": self.glass1_type_input.currentText(),
    #             "glass2_type": self.glass2_type_input.currentText(),
    #             "support_type": self.support_type_input.currentText(),
    #             "wind_load": self.wind_load_input.value(),
    #             "nfl1": self.nfl1_input.value(),
    #             "nfl2": self.nfl2_input.value()
    #         }
    #     # elif "Laminated" in self.fixing_comp_type_input.currentText() and "Double" not in self.fixing_comp_type_input.currentText():
    #     elif "Laminated Glaze Unit (LGU)" in self.fixing_comp_type_input.currentText():
    #         return {
    #             "length": self.length_input.value(),
    #             "width": self.width_input.value(),
    #             "thickness1": float(self.thickness1_input.currentText()),
    #             "thickness_inner": float(self.interlayer_thickness.currentText()),
    #             "thickness2": float(self.thickness2_input.currentText()),
    #             "fixing_type": self.fixing_type_input.currentText(),
    #             "support_type": self.support_type_input.currentText(),
    #             "wind_load": self.wind_load_input.value(),
    #             "nfl": self.nfl_input.value()
    #         }
    #     # else:  # LDGU
    #     elif "Laminated Double Glaze Unit (LDGU)" in self.fixing_comp_type_input.currentText():  # LDGU
    #         return {
    #             "length": self.length_input.value(),
    #             "width": self.width_input.value(),
    #             "thickness1_1": float(self.thickness1_1_input.currentText()),
    #             "thickness_inner": float(self.interlayer_thickness.currentText()),
    #             "thickness1_2": float(self.thickness1_2_input.currentText()),
    #             "gap": int(self.gap_input.currentText()),
    #             "thickness2": float(self.thickness2_input.currentText()),
    #             "glass1_type": self.glass1_type_input.currentText(),
    #             "glass2_type": self.glass2_type_input.currentText(),
    #             "support_type": self.support_type_input.currentText(),
    #             "wind_load": self.wind_load_input.value(),
    #             "nfl1": self.nfl1_input.value(),
    #             "nfl2": self.nfl2_input.value()
    #         }

    # def trigger_calculate(self):
    #     self.calculate()

    # def calculate(self):
    #     try:
    #         comp_type = self.fixing_comp_type_input.currentText()
    #         params = self.get_calculation_params()
            
    #         if "Single Glaze Unit (SGU)" in comp_type:
    #             calculator = SGUCalculator(**params)
    #         elif "Double Glaze Unit (DGU)" in comp_type:
    #             calculator = DGUCalculator(**params)
    #         elif "Laminated Glaze Unit (LGU)" in comp_type:
    #             calculator = LGUCalculator(**params)
    #         elif "Laminated Double Glaze Unit (LDGU)" in comp_type:
    #             calculator = LDGUCalculator(**params)

    #         self.summary = calculator.summary()
    #         self.update_results()
            
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Calculation failed: {str(e)}")

    # def update_results(self):
    #     try:
    #         result_temp_path = resource_path("ui/renders")
    #         env = Environment(loader=FileSystemLoader(result_temp_path))
    #         template = env.get_template("glass.html")
    #         combined_html = template.render(
    #             summary=self.summary,
    #             composition=self.fixing_comp_type_input.currentText()
    #         )
    #         base_url = QUrl.fromLocalFile(os.path.abspath(result_temp_path) + "/")
    #         self.result_webview.setHtml(combined_html, base_url)
    #         # print("Rendering with summary:", self.summary)
        
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Failed to render results: {str(e)}")

    # def view_report(self):
    #     if not self.summary:
    #         QMessageBox.warning(self, "Warning", "Please calculate glass design first.")
    #         return

    #     try:
    #         project_info = {
    #             # "project_name": "Taj & Vivanta Hotel",
    #             # "ref_no": "REF# RFA-001/REV-02/AEL/CW/2025",
    #             "rev_no": "02",
    #             "date_time": date.today().strftime("%d/%m/%Y")
    #         }

    #         report_temp_path = resource_path("reports/templates")
    #         env = Environment(loader=FileSystemLoader(report_temp_path))
    #         template = env.get_template("glass.html")

    #         html_content = template.render(
    #             project_info=project_info,
    #             summary=self.summary,
    #             composition=self.fixing_comp_type_input.currentText()
    #         )
            
    #         # Generate Temporary PDF File
    #         temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    #         pdf_path = temp_pdf.name
    #         temp_pdf.close()
            
    #         HTML(string=html_content, base_url=report_temp_path).write_pdf(
    #             pdf_path,
    #             stylesheets=[CSS(filename=os.path.join(report_temp_path, "css/report.css"))]
    #         )

    #         self.preview_window = ReportPreviewWindow(pdf_path)
    #         self.preview_window.show()

    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Failed to preview report: {str(e)}")

