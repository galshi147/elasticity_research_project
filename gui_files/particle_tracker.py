import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import animation
from PySide6.QtWidgets import (
    QSizePolicy, QLineEdit, QApplication, QFileDialog, QDialog
    )
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from measurements_detectors import Measure
from gui_files.gui_scripts import ParticleTrackerScripter
from gui_files.gui_resources import BaseAnalysisWindow, MEASURE_TITLE_STYLE
from gui_files.dialogs import AnimateTrajDialog
from database_manager import DatabaseManager

class ParticleTracker(BaseAnalysisWindow):
    def __init__(self, measure: Measure, source):
        super().__init__(measure, source, scripter=ParticleTrackerScripter)
        self.setWindowTitle("Particle Tracker")
        self.measure = measure
        
        # Use optimized database manager
        self.db_manager = DatabaseManager()
        
        # Register measurement for fast access
        self.db_manager.register_measurement_files(measure)
        
        # Try to load cached trajectories first
        self.all_trajectories = self.db_manager.load_trajectories(measure.get_name())
        if self.all_trajectories is None:
            print("Building trajectories (this may take a moment)...")
            self.kdt = Kdt(measure)
            self.all_trajectories = self.kdt.build_trajectories()
            # Cache for next time
            self.db_manager.cache_trajectories(measure.get_name(), self.all_trajectories)
            print("Trajectories cached for faster future loading")
        else:
            print("Loaded cached trajectories - ready to go!")
        
        self.plotter = Plotter(measure, source)
        self.calculator = Calculator(measure)
        self.init_ui()
        self._connect_zoom()


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
    
    def draw_plot(self, ax: plt.Axes, frame1_num: int, frame2_num: int):
        trajectories = self.all_trajectories[self.frame1.value()-1 : self.frame2.value()]
        selected = self.get_selected_particles()
        self.plotter.plot_particles_trajectories(ax, frame1_num, frame2_num, trajectories, selected_particles=selected)



    def update_plot(self):
        self.update_btn.setEnabled(False)
        xlim = self.ax.get_xlim()  # Save current zoom (axes limits)
        ylim = self.ax.get_ylim()
        self.ax.clear()
        self.draw_plot(self.ax, self.frame1.value(), self.frame2.value())
        if hasattr(self, "_has_updated"): # Avoid restoring zoom on the first update
            self.ax.set_xlim(xlim) # Restore zoom (axes limits)
            self.ax.set_ylim(ylim)
        else:
            self._has_updated = True
        self.canvas.draw()
        self.green_blink_button()
        self.update_btn.setEnabled(True)

    
    def save_video(self):
            self.save_video_btn.setEnabled(False)  # Disable the button to prevent multiple clicks
            original_text = self.save_video_btn.text()
            self.save_video_btn.setText("saving video...")  # Indicate saving in progress
            QApplication.processEvents()  # Force UI update

            try:
                # Create a dialog for user to select start frame, end frame, and interval
                min_frame = self.frame1.minimum()
                max_frame = self.frame2.maximum()
                dialog = AnimateTrajDialog(self, frame1_val=self.frame1.value(), frame2_val=self.frame2.value(), min_frame=min_frame, max_frame=max_frame)
                if dialog.exec() != QDialog.Accepted:
                    return

                frame1, frame2, jump, end_frame, delay_sec = dialog.get_values()
                if None in (frame1, frame2, jump, end_frame, delay_sec):
                    return
                if end_frame < frame2 or end_frame < frame1 or jump < 1:
                    return

                # Ask user for file path
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4);;GIF Files (*.gif)")
                if not file_path:
                    return

                # Prepare animation: frame2 moves, frame1 is fixed
                frames = range(frame2, end_frame + 1, jump)

                # Use a temporary figure for animation
                temp_fig, temp_ax = plt.subplots(figsize=self.figure.get_size_inches())

                def update_anim(frame2_num):
                    self.draw_plot(temp_ax, frame1, frame2_num)
                    return temp_ax

                anim = animation.FuncAnimation(
                    temp_fig,
                    update_anim,
                    frames=frames,
                    blit=False
                )

                # Save animation
                fps = int(1 / delay_sec)  # Convert delay from ms to frames per second
                if file_path.endswith('.gif'):
                    anim.save(file_path, writer='imagemagick', fps=fps, dpi=300)
                else:
                    anim.save(file_path, writer='ffmpeg', fps=fps, dpi=300)

                plt.close(temp_fig)  # Close the temp figure

                print(f"Video saved to {file_path}")

                self.green_blink_button()
            finally:
                self.save_video_btn.setText(original_text)  # Restore button text
                self.save_video_btn.setEnabled(True)  # Re-enable the button after saving
                QApplication.processEvents()  # Update UI