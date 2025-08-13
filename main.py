import sys
import os
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QStackedWidget, QSizePolicy, QMessageBox
)

from ui.splash import SplashScreen


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class RibbonTab(QPushButton):
    def __init__(self, icon_path, label_text):
        super().__init__()

        self.setIcon(QIcon(icon_path))
        self.setText(label_text)
        self.setIconSize(QtCore.QSize(28, 28))
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px 20px;
                font-size: 16px;
                color: #000;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:checked {
                background-color: #CFCFCF;
                color: #000;
                font-weight: normal;
            }
            QToolTip {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #b8b8b8;
                padding: 4px;
                border-radius: 4px;
            }
        """)
        self.setFixedHeight(56)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        QApplication.setStyle("Fusion")
        self.setWindowTitle("FAD – Façade Analysis & Design")
        window_icon_path = resource_path("ui/assets/icons/icon.png")
        self.setWindowIcon(QIcon(window_icon_path))
        
        font_path = resource_path("ui/assets/fonts/custom-font.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Failed to load font!")
        else:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font = QFont(family, 10)

        # Center main window
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_width, window_height = 1250, 750
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.ribbon = self.create_ribbon()
        self.stack = QStackedWidget()

        self.main_layout.addWidget(self.ribbon)
        self.main_layout.addWidget(self.stack)

        self.init_pages()
        self.set_active_tab(1)

    def create_ribbon(self):
        ribbon = QWidget()
        ribbon.setFixedHeight(56)
        ribbon.setStyleSheet("""
            background-color: #E1E1E1;
            border-bottom: 1px solid #CFCFCF;
        """)

        layout = QHBoxLayout(ribbon)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: Logo
        logo = QLabel()
        logo_path = resource_path("ui/assets/logo.png")
        logo_pixmap = QPixmap(logo_path)
        logo.setPixmap(logo_pixmap.scaled(135, 75, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft)
        logo.setStyleSheet("padding: 1px 10px;")

        layout.addStretch(1)

        # ==== Center Tabs ========
        # tab icons
        rib_home_icon =  resource_path("ui/assets/icons/home.png")
        rib_wind_icon =  resource_path("ui/assets/icons/wind.png")
        rib_glass_icon =  resource_path("ui/assets/icons/glass.png")
        rib_frame_icon =  resource_path("ui/assets/icons/frame.png")
        rib_conn_icon =  resource_path("ui/assets/icons/conn.png")
        rib_fixing_icon =  resource_path("ui/assets/icons/fixing.png")
        rib_project_icon =  resource_path("ui/assets/icons/project.png")
        
        self.tabs = {}
        tab_info = [
            (rib_home_icon, "HOME"),
            (rib_wind_icon, "WIND"),
            (rib_glass_icon, "GLASS"),
            (rib_frame_icon, "FRAME"),
            (rib_conn_icon, "CONN"),
            (rib_fixing_icon, "FIXING"),
            (rib_project_icon, "PROJECT"),
        ]

        for idx, (icon_path, name) in enumerate(tab_info):
            tab = RibbonTab(icon_path, name)
            tab.setFont(self.custom_font)
            tab.clicked.connect(lambda checked, i=idx: self.set_active_tab(i))
            self.tabs[name] = tab
            layout.addWidget(tab)

        project_tab = self.tabs["PROJECT"]
        project_tab.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px 20px;
                font-size: 16px;
                color: black;
                background-color: #fff2c7;
                margin: 1px 0;
            }
            QPushButton:hover {
                background-color: #ffecad;
            }
            QPushButton:checked {
                background-color: #ffecad;
                color: black;
                font-weight: normal;
            }
        """)
        
        layout.addStretch(1)

        # Right: Calculate Button
        self.calc_btn = QPushButton("CALCULATE")
        self.calc_btn.setFont(self.custom_font)
        self.calc_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                border: none;
                font-size: 16px;
                font-weight: normal;
                padding: 5px 16px 5px 20px;
                margin-bottom: 1px;
            }
            QPushButton:hover {
                background-color: #FFB300;
            }
        """)
        self.calc_btn.clicked.connect(self.handle_calculate)
        layout.addWidget(self.calc_btn)

        return ribbon

    def set_active_tab(self, index):
        for i, tab in enumerate(self.tabs.values()):
            tab.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def init_pages(self):
        from ui.wind_gui import WindLoadTab
        from ui.glass_gui import GlassTab
        from ui.conn_gui import ConnTab
        # from ui.project_tab import ProjectTab
        from PyQt5.QtWidgets import QLabel

        self.home_tab = QLabel("Home Page")
        self.wind_tab = WindLoadTab()
        self.glass_tab = GlassTab()
        self.frame_tab = QLabel("Frame Page Coming soon")
        self.conn_tab = ConnTab()
        self.fixing_tab = QLabel("Fixing Page Coming soon")
        self.project_tab = QLabel("Project Page Coming soon")
        
        pages = [
            self.home_tab,
            self.wind_tab,
            self.glass_tab,
            self.frame_tab,
            self.conn_tab,
            self.fixing_tab,
            self.project_tab
        ]

        for page in pages:
            self.stack.addWidget(page)

        for i in range(self.stack.count()):
            self.stack.setCurrentIndex(i)
            QApplication.processEvents()

        self.stack.setCurrentIndex(1)
        
        
    def handle_calculate(self):
        current_index = self.stack.currentIndex()
        current_widget = self.stack.currentWidget()

        if hasattr(current_widget, 'trigger_calculate'):
            current_widget.trigger_calculate()
        else:
            print(f"No calculate function in tab index {current_index}")
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "FAD",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


# === Application Entry ===
if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.start_loading(duration_ms=1000)  # Start visual loading
    app.processEvents()

    # Flags to sync splash and main window readiness
    splash_done = False
    window_ready = False
    window = None

    app.setStyleSheet("""
        QToolTip {
            background-color: #fcfcfc;   /* light yellow */
            color: #000000;
            border: 1px solid #b8b8b8;
            padding: 2px;
            border-radius: 4px;
        }
    """)
    
    def show_main_window():
        global window_ready, window
        window_ready = True
        maybe_start()

    def splash_minimum_shown():
        global splash_done
        splash_done = True
        maybe_start()

    def maybe_start():
        if splash_done and window_ready:
            splash.close()
            window.show()
            window.showMaximized()

    window = MainWindow()
    show_main_window()

    QTimer.singleShot(1000, splash_minimum_shown)  # At least 1s splash

    sys.exit(app.exec_())
