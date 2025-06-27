import sys
from measurements_detectors import Measure
from PySide6.QtWidgets import QApplication
from welcome_window import WelcomeWindow

# === GUI Class ===

class Gui:
    def __init__(self, measure: Measure, source: str):     
        # Initialize the GUI
        self.app = QApplication(sys.argv)
        self.window = WelcomeWindow(measure, source)
        self.window.show()

    def run(self):
        sys.exit(self.app.exec())