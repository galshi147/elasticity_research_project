from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget
from vec_field_analyzer import VectorFieldAnalyzer
from particle_tracker import ParticleTracker
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class WelcomeWindow(QMainWindow):
    def __init__(self, measure, source):
        super().__init__()
        self.setWindowTitle("Welcome")
        self.resize(500, 300)  # Set default window size
        layout = QVBoxLayout()
        # Add welcome label
        welcome_label = QLabel("Welcome! Choose App to proceed")
        welcome_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 20px;")
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Create buttons for Vector Field Analyzer and Particle Tracker apps
        vec_field_analyzer_btn = QPushButton("Vector Field Analyzer")
        particle_tracker_btn = QPushButton("Particle Tracker")
        
        # Style the buttons
        vec_field_analyzer_btn.setMinimumHeight(50)
        particle_tracker_btn.setMinimumHeight(50)
        button_style = """
            QPushButton {
            font-size: 18px;
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            }
            QPushButton:hover {
            background-color: #2980b9;
            }
        """
        vec_field_analyzer_btn.setStyleSheet(button_style)
        particle_tracker_btn.setStyleSheet(button_style)
        layout.addWidget(vec_field_analyzer_btn)
        layout.addSpacing(20)  # Add space between the buttons
        layout.addWidget(particle_tracker_btn)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        vec_field_analyzer_btn.clicked.connect(lambda: self.open_vec_field_analyzer_window(measure, source))
        particle_tracker_btn.clicked.connect(lambda: self.open_particle_tracker_window(measure, source))

    def open_vec_field_analyzer_window(self, measure, source):
        self.vfa_window = VectorFieldAnalyzer(measure, source)
        self.vfa_window.show()

    def open_particle_tracker_window(self, measure, source):
        self.pt_window = ParticleTracker(measure, source)
        self.pt_window.show()
