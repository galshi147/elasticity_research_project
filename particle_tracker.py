import numpy as np
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from measurements_detectors import Measure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QSizePolicy, QLineEdit,
                               QWidget, QPushButton, QSpinBox, QLabel, QFormLayout, QHBoxLayout
                               )
from gui_resources import BaseAnalysisWindow, SPECIAL_SPINBOX_STYLE, MEASURE_TITLE_STYLE

class ParticleTracker(BaseAnalysisWindow):
    def __init__(self, measure: Measure, source):
        super().__init__(measure.get_total_frames_num())
        self.setWindowTitle("Particle Tracker")
        self.measure = measure
        self.measure_data = self.measure.load_measure_data(source='drive')
        self.kdt = Kdt(measure)
        self.plotter = Plotter(measure, source)
        self.calculator = Calculator(measure)
        self.all_trajectories = self.kdt.build_trajectories()
        self.init_ui()
    
    def init_ui(self):
        self.particle_selector = QLineEdit()
        self.particle_selector.setPlaceholderText("Particles to show (e.g. 0,1,2 or 0-5)")
        self.particle_selector.editingFinished.connect(self.update_plot)
        self.main_layout.addWidget(self.particle_selector)
        self.figure, self.ax = plt.subplots()
        title = self.figure.suptitle(f"Measurement: {self.measure.get_name()}", fontsize=16,  x=0.5, y=0.98)
        title.set_bbox(MEASURE_TITLE_STYLE)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Let the canvas grow
        self.canvas.updateGeometry()
        self.main_layout.addWidget(self.canvas)
    
    def get_selected_particles(self):
        text = self.particle_selector.text().replace(' ', '')
        indices = []
        for part in text.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                indices.extend(range(start, end+1))
            elif part.isdigit():
                indices.append(int(part))
        return np.array(indices) if indices else None
    
    def update_plot(self):
        self.update_btn.setEnabled(False)
        self.ax.clear()
        trajectories = self.all_trajectories[self.frame1.value()-1 : self.frame2.value()]
        selected = self.get_selected_particles()
        self.plotter.plot_particles_trajectories(self.ax, trajectories, selected_particles=selected)
        self.canvas.draw()
        self.green_blink_button()
        self.update_btn.setEnabled(True)
