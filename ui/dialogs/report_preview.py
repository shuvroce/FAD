import os
import shutil
from PyQt5 import QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QMessageBox
)


class ReportPreviewWindow(QWidget):
    def __init__(self, pdf_path=None):
        super().__init__()
        self.setWindowTitle("Report Preview")
        self.resize(900, 850)
        self._temp_pdf_path = pdf_path

        layout = QVBoxLayout(self)

        # Create the QWebEngineView
        self.viewer = QtWebEngineWidgets.QWebEngineView()
        self.viewer.settings().setAttribute(
            QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)
        self.viewer.settings().setAttribute(
            QtWebEngineWidgets.QWebEngineSettings.PdfViewerEnabled, True)

        if pdf_path:
            self.viewer.load(QtCore.QUrl.fromUserInput(pdf_path))

        # Save PDF button
        self.save_btn = QPushButton("Save PDF")
        self.save_btn.setFixedSize(100, 30)
        self.save_btn.setStyleSheet("""
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
        self.save_btn.clicked.connect(self.save_pdf)

        # Button layout (top aligned)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)

        # Compose layout
        layout.addWidget(self.viewer)
        layout.addLayout(btn_layout)

    def save_pdf(self):
        if not self._temp_pdf_path or not os.path.exists(self._temp_pdf_path):
            QMessageBox.warning(self, "Error", "Temporary PDF file not found.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "report.pdf", "PDF Files (*.pdf)"
        )
        if save_path:
            try:
                shutil.copy(self._temp_pdf_path, save_path)
                # QMessageBox.information(self, "Saved", f"Report saved to:\n{save_path}")
                
                msg = QMessageBox(self)
                msg.setWindowTitle("Saved")
                msg.setText(f"Report saved to:\n{save_path}")
                msg.setIcon(QMessageBox.NoIcon)  # No system icon → no sound
                msg.exec_()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")

    def closeEvent(self, event):
        if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
            try:
                os.remove(self._temp_pdf_path)
            except PermissionError:
                pass  # File is still locked
        event.accept()
