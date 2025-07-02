import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation


from PySide6.QtWidgets import (
    QApplication, QPushButton, QSpinBox, QFileDialog, QFormLayout, QSizePolicy, QDialog
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from measurements_detectors import Measure
from visualization import Plotter
from calculator import Calculator

from gui_files.gui_scripts import VecFieldAnalyzerScripter
from gui_files.gui_resources import BaseAnalysisWindow ,SPECIAL_SPINBOX_STYLE, MEASURE_TITLE_STYLE
from gui_files.dialogs import DisplacementVideoDialog

MAX_RINGS_NUM = 500
DEFAULT_RINGS_NUM = 100
MAX_RING_JUMP = 100
DEFAULT_RINGS_JUMP = 1

 
# === Main Window Class ===
class VectorFieldAnalyzer(BaseAnalysisWindow):
    def __init__(self, measure: Measure, source: str):
        super().__init__(measure, source, scripter=VecFieldAnalyzerScripter)
        self.setWindowTitle("Vector Field Analyzer (PySide6)")
        self.plotter = Plotter(measure, source)
        self.calculator = Calculator(measure)
        self.measure_stat = self.measure.load_measure_data(source='drive')["statistic"]
        self.vector_field = {}
        self.add_rings = True
        self.init_ui()
        self._connect_zoom()

    def init_ui(self):
        # === Rings jump selector ===
        rings_jump_layout = QFormLayout()
        self.rings_spin_jump = QSpinBox()
        self.rings_spin_jump.setRange(1, MAX_RING_JUMP)
        self.rings_spin_jump.setValue(DEFAULT_RINGS_JUMP)
        rings_jump_layout.addRow("Rings jump:", self.rings_spin_jump)
        
        # === Rings Selector ===
        rings_layout = QFormLayout()
        self.rings_spin = QSpinBox()
        self.rings_spin.setSingleStep(self.rings_spin_jump.value())
        self.rings_spin_jump.valueChanged.connect(lambda value: self.rings_spin.setSingleStep(value))
        self.rings_spin.setRange(1, MAX_RINGS_NUM)
        self.rings_spin.setValue(DEFAULT_RINGS_NUM)
        self.rings_spin.setStyleSheet(SPECIAL_SPINBOX_STYLE)    
        rings_layout.addRow("Rings:", self.rings_spin)

        add_rings_btn = QPushButton("Add/Remove Rings")
        add_rings_btn.setStyleSheet("background-color: green;" if self.add_rings else "")
        add_rings_btn.clicked.connect(self.set_rings)

        self.controls_layout.addLayout(rings_jump_layout)
        self.controls_layout.addLayout(rings_layout)
        self.controls_layout.addWidget(add_rings_btn)


        # === Matplotlib Canvas ===
        self.figure, (self.ax_vf, self.ax_av) = plt.subplots(1, 2)
        title = self.figure.suptitle(f"Measurement: {self.measure.get_name()}", fontsize=16,  x=0.5, y=0.98)
        title.set_bbox(MEASURE_TITLE_STYLE)

        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)  # Reduce plot margins

        self.colorbar = None
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Let the canvas grow
        self.canvas.updateGeometry()

        self.main_layout.addWidget(self.canvas)
    

    
    def save_video(self):
        self.save_video_btn.setEnabled(False)  # Disable the button to prevent multiple clicks
        original_text = self.save_video_btn.text()
        self.save_video_btn.setText("saving video...")  # Indicate saving in progress
        QApplication.processEvents()  # Force UI update

        try:
            # Create a dialog for user to select start frame, end frame, and interval
            min_frame = self.frame1.minimum()
            max_frame = self.frame2.maximum()
            dialog = DisplacementVideoDialog(
                self,
                self.frame1.value(),
                self.frame2.value(),
                self.interval_spin.value(),
                min_frame,
                max_frame
            )
            if dialog.exec() != QDialog.Accepted:
                return

            start_frame = dialog.start_spin.value()
            end_frame = dialog.end_spin.value()
            interval = dialog.interval_spin.value()
            if end_frame < start_frame or interval < 1:
                return

            # Ask user for file path
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4);;GIF Files (*.gif)")
            if not file_path:
                return

            # Prepare animation: frame2 moves, frame1 is fixed
            frames = range(start_frame + interval, end_frame + 1, interval)

            # Use a temporary figure for animation
            temp_fig, (temp_ax_vf, temp_ax_av) = plt.subplots(1, 2, figsize=self.figure.get_size_inches())
            colorbar_container = [None]  # Use a list to hold the colorbar reference

            def update_anim(frame2_val):
                # Remove previous colorbar if it exists
                if colorbar_container[0] is not None:
                    try:
                        colorbar_container[0].remove()
                    except Exception as e:
                        print(f"Could not remove colorbar axes: {e}")
                    colorbar_container[0] = None

                # Draw the plot and get the new colorbar
                _, _, _, new_colorbar = self.draw_plot(temp_ax_vf, temp_ax_av, temp_fig, None, start_frame, frame2_val)
                colorbar_container[0] = new_colorbar
                return temp_ax_vf, temp_ax_av

            anim = animation.FuncAnimation(
                temp_fig,
                update_anim,
                frames=frames,
                blit=False
            )

            # Save animation
            if file_path.endswith('.gif'):
                anim.save(file_path, writer='imagemagick', fps=dialog.get_fps(), dpi=300)
            else:
                anim.save(file_path, writer='ffmpeg', fps=dialog.get_fps(), dpi=300)

            plt.close(temp_fig)  # Close the temp figure

            print(f"Video saved to {file_path}")

            self.green_blink_button()
        finally:
            self.save_video_btn.setText(original_text)  # Restore button text
            self.save_video_btn.setEnabled(True)  # Re-enable the button after saving
            QApplication.processEvents()  # Update UI

    def load_vector_field_data(self, first_frame_name, second_frame_name) -> tuple:
        """_summary_

        Args:
            first_frame_name (_type_): _description_
            second_frame_name (_type_): _description_

        Returns:
            tuple[np,array]: x, y, u, v
        """
        try:
            return self.plotter.load_vector_field(first_frame_name, second_frame_name)
        except FileNotFoundError:
            print(f"==== check existance of {first_frame_name}_{second_frame_name} in vector_field folder of measure: {self.measure.get_name()} ====")

    def calculate_displacement_stats(self, x: np.array, y: np.array, u, v) -> tuple:
        """_summary_

        Args:
            x (_type_): _description_
            y (_type_): _description_
            u (_type_): _description_
            v (_type_): _description_
            rings_num (_type_): _description_

        Returns:
            tuple: radii, dr, rad_disp, tan_disp
        """
        return self.calculator.calculate_displacement_field(x, y, u, v, rings_num=self.rings_spin.value())

    def draw_plot(self, ax_vf: plt.Axes, ax_av: plt.Axes, figure, colorbar, frame1_val, frame2_val):
        frame1 = f"DSC_{frame1_val:04d}.jpg"
        frame2 = f"DSC_{frame2_val:04d}.jpg"
        vector_field = self.load_vector_field_data(frame1, frame2)
        x, y, u, v = vector_field['x'], vector_field['y'], vector_field['u'], vector_field['v']
        radii, dr, rad_disp, tan_disp = self.calculate_displacement_stats(x, y, u, v)
        
        # Clear previous plots
        ax_vf.clear()
        ax_av.clear()

        # Remove the colorbar if it exists
        if colorbar is not None:
            try:
                if colorbar.ax in figure.axes:
                    figure.delaxes(colorbar.ax)
            except Exception as e:
                print(f"Could not remove colorbar axes: {e}")
            colorbar = None
        
        # Plot the updated data
        ax_av = self.plotter.plot_displacement_by_rings(ax_av, self.measure_stat, frame1, frame2, radii, rad_disp, tan_disp)
        ax_vf, colorbar = self.plotter.plot_vector_field(ax_vf, x, y, u, v, frame1, frame2, add_rings=self.add_rings, radii=radii, dr=dr)
        return ax_vf, ax_av, figure, colorbar
    
    def update_plot(self) -> None:
        self.update_btn.setEnabled(False)  # Disable the button to prevent multiple clicks
        vf_xlim, av_xlim = self.ax_vf.get_xlim(), self.ax_av.get_xlim()  # Save current zoom (axes limits)
        vf_ylim, av_ylim = self.ax_vf.get_ylim(), self.ax_av.get_ylim()  # Save current zoom (axes limits)
        self.ax_vf, self.ax_av, self.figure, self.colorbar = self.draw_plot(self.ax_vf, self.ax_av, self.figure, self.colorbar, self.frame1.value(), self.frame2.value())
        if hasattr(self, "_has_updated"): # Avoid restoring zoom on the first update
            self.ax_vf.set_xlim(vf_xlim) # Restore zoom (axes limits)
            self.ax_vf.set_ylim(vf_ylim)
            self.ax_av.set_xlim(av_xlim)
            self.ax_av.set_ylim(av_ylim)
        else:
            self._has_updated = True
        self.canvas.draw() # Redraw the canvas
        self.green_blink_button()
        self.update_btn.setEnabled(True)

    def set_rings(self):
        """Set the add_rings attribute to True or False and update button style."""
        self.add_rings = not self.add_rings
        sender = self.sender()  # Get the button that triggered this method
        if isinstance(sender, QPushButton):
            sender.setStyleSheet("background-color: green;" if self.add_rings else "")
        self.update_plot()

    def activate_smooth_mode(self):
        """Activate or deactivate smooth mode and update button style."""
        self.smooth_mode = not self.smooth_mode

        # Update button style
        sender = self.sender()  # Get the button that triggered this method
        if isinstance(sender, QPushButton):
            sender.setStyleSheet("background-color: green;" if self.smooth_mode else "")

        # Connect or disconnect signals based on smooth mode
        if self.smooth_mode:
            self.frame1.valueChanged.connect(self.schedule_update_plot)
            self.frame2.valueChanged.connect(self.schedule_update_plot)
            self.rings_spin.valueChanged.connect(self.schedule_update_plot)
        else:
            self.frame1.valueChanged.disconnect(self.schedule_update_plot)
            self.frame2.valueChanged.disconnect(self.schedule_update_plot)
            self.rings_spin.valueChanged.disconnect(self.schedule_update_plot)

    
    