import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QMainWindow, QSpinBox, QPushButton, 
    QFormLayout, QHBoxLayout, QVBoxLayout, 
    QWidget, QComboBox
)
from PySide6.QtCore import QTimer
from abc import abstractmethod
from project_tools import create_product_name
from measurements_detectors import Measure
from gui_files.scripter import Scripter

MEASURE_TITLE_STYLE = {
     'facecolor': 'skyblue',
     'alpha': 0.5, 
     'edgecolor': 'none',
     'pad': 5,
     'boxstyle': 'round,pad=0.5'   # rounded corners
     }
SPECIAL_SPINBOX_STYLE = """QSpinBox {background-color: #5052E7; padding: 5px;}"""
MAX_INTERVAL = 1000
DEFAULT_INTERVAL = 10
SMOOTH_MODE_DELAY = 150

class BaseAnalysisWindow(QMainWindow):
    def __init__(self, measure: Measure, source: str, scripter: Scripter = None):
        super().__init__()
        self.measure = measure
        self.source = source
        self.scripter = scripter(self) if scripter else Scripter(self)
        self.total_frames = measure.get_total_frames_num()
        self.smooth_mode = False
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_plot)
        self.script_dict = self.scripter.get_script_dict()
        self.stop_script = False
        self.init_common_ui()


    def init_common_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.controls_layout = QHBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        # === Add scripts layout ===
        scripts_layout = QHBoxLayout()
        script_box_layout = QFormLayout()
        self.script_box = QComboBox()
        self.script_box.addItems(["Choose Script"] + list(self.script_dict.keys()))  # Add script options
        self.script_box.currentIndexChanged.connect(self.on_script_selected)  # Connect selection change to a method
        script_box_layout.addRow("Select Script:", self.script_box)
        scripts_layout.addLayout(script_box_layout)
        self.stop_script_btn = QPushButton("Stop Script")
        self.stop_script_btn.setStyleSheet("background-color: #FF8F8F; color: black;")
        self.stop_script_btn.clicked.connect(self.stop_running_script)
        scripts_layout.addWidget(self.stop_script_btn)
        self.save_video_btn = QPushButton("Save Video")
        self.save_video_btn.setStyleSheet("background-color: #677DFD; color: black;")
        self.save_video_btn.clicked.connect(self.save_video)
        scripts_layout.addWidget(self.save_video_btn)
        self.main_layout.addLayout(scripts_layout)

        # Control base frame (frame1) jump
        base_frame_jump_layout = QFormLayout()
        self.base_frame_jump = QSpinBox()
        self.base_frame_jump.setRange(1, self.total_frames - 1)
        self.base_frame_jump.setValue(1)
        base_frame_jump_layout.addRow("Base Frame jump:", self.base_frame_jump)

        # Frame selectors
        frame1_layout = QFormLayout()
        self.frame1 = QSpinBox()
        self.frame1.setSingleStep(self.base_frame_jump.value())
        self.base_frame_jump.valueChanged.connect(lambda value: self.frame1.setSingleStep(value))
        self.frame1.setRange(1, self.total_frames)
        self.frame1.setValue(1)
        self.frame1.setStyleSheet(SPECIAL_SPINBOX_STYLE)
        frame1_layout.addRow("Frame 1:", self.frame1)
        frame2_layout = QFormLayout()
        self.frame2 = QSpinBox()
        self.frame2.setRange(1, self.total_frames)
        self.frame2.setValue(2)
        self.frame2.setStyleSheet(SPECIAL_SPINBOX_STYLE)
        frame2_layout.addRow("Frame 2:", self.frame2)

        # Interval selector
        interval_layout = QFormLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, MAX_INTERVAL)
        self.interval_spin.setValue(DEFAULT_INTERVAL)
        self.interval_spin.valueChanged.connect(self.update_frame2_with_interval)
        self.frame1.valueChanged.connect(self.update_frame2_with_interval)
        interval_layout.addRow("Interval:", self.interval_spin)

        # Buttons
        self.update_btn = QPushButton("Update Plot")
        self.update_btn.clicked.connect(self.update_plot)
        self.save_btn = QPushButton("Save Image")
        self.save_btn.clicked.connect(self.save_image)
        self.save_video_btn = QPushButton("Save Video")
        self.save_video_btn.clicked.connect(self.save_video)
        self.smooth_mode_btn = QPushButton("Smooth Mode")
        self.smooth_mode_btn.setStyleSheet("background-color: green;" if self.smooth_mode else "")
        self.smooth_mode_btn.clicked.connect(self.activate_smooth_mode)
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)

        self.controls_layout.addLayout(base_frame_jump_layout)
        self.controls_layout.addLayout(frame1_layout)
        self.controls_layout.addLayout(frame2_layout)
        self.controls_layout.addLayout(interval_layout)
        self.controls_layout.addWidget(self.update_btn)
        self.controls_layout.addWidget(self.smooth_mode_btn)
        self.controls_layout.addWidget(self.save_btn)
        self.controls_layout.addWidget(self.reset_zoom_btn)
        
        self.central_widget.setLayout(self.main_layout)
        
        self.figure = plt.Figure()
        self.canvas = FigureCanvas()

    def on_script_selected(self, index):
        """Handle script selection from the combobox."""
        selected_script = self.script_box.itemText(index)
        if index > 0:  # Ignore "Choose Script"
            if selected_script in self.script_dict:
                # Show "<script name> - running..." in the combobox
                self.script_box.blockSignals(True)
                self.script_box.setItemText(index, f"{selected_script} - running...")
                self.script_box.setCurrentIndex(index)
                self.script_box.blockSignals(False)
                # Store the running script name for later reset
                self._running_script_index = index
                self._running_script_name = selected_script
                self.script_dict[selected_script]()
    
    def stop_running_script(self):
        self.stop_script_btn.setEnabled(False)  # Disable the button to prevent multiple clicks
        self.stop_script = True
        # Reset combobox to default and restore script name
        if hasattr(self, "_running_script_index") and hasattr(self, "_running_script_name"):
            self.script_box.blockSignals(True)
            self.script_box.setItemText(self._running_script_index, self._running_script_name)
            self.script_box.setCurrentIndex(0)
            self.script_box.blockSignals(False)
            del self._running_script_index
            del self._running_script_name
        self.stop_script_btn.setEnabled(True)  # Re-enable the button after stopping

    def activate_smooth_mode(self):
        self.smooth_mode = not self.smooth_mode
        sender = self.sender()
        if isinstance(sender, QPushButton):
            sender.setStyleSheet("background-color: green;" if self.smooth_mode else "")
        if self.smooth_mode:
            self.frame1.valueChanged.connect(self.schedule_update_plot)
            self.frame2.valueChanged.connect(self.schedule_update_plot)
        else:
            self.frame1.valueChanged.disconnect(self.schedule_update_plot)
            self.frame2.valueChanged.disconnect(self.schedule_update_plot)

    def schedule_update_plot(self):
        """Schedule the update_plot method with a debounce timer."""
        self.update_timer.start(SMOOTH_MODE_DELAY) # Adjust the delay (in milliseconds) as needed

    def update_frame2_with_interval(self):
        interval = self.interval_spin.value()
        frame1_value = self.frame1.value()
        self.frame2.setValue(frame1_value + interval)
    
    def green_blink_button(self):
        sender = self.sender()  # Get the button that triggered this method
        if isinstance(sender, QPushButton):
            original_color = sender.palette().button().color().name()
            sender.setStyleSheet("background-color: green;")
            QTimer.singleShot(500, lambda: sender.setStyleSheet(f"background-color: {original_color};"))


    def save_image(self):
        frame1 = f"DSC_{self.frame1.value():04d}.jpg"
        frame2 = f"DSC_{self.frame2.value():04d}.jpg"
        filename = f"graph_{create_product_name(self.measure.get_name(), frame1, frame2, self.source)}.png"
        filepath = self.measure.get_graph_path() / filename
        self.figure.savefig(filepath)
        self.green_blink_button()


    def _connect_zoom(self):
        """Connect zoom and pan functionality to the matplotlib canvas."""
        def zoom_factory_figure(fig, base_scale=1.1):
            def zoom(event):
                for ax in fig.axes:
                    if event.inaxes != ax:
                        continue
                    if event.xdata is None or event.ydata is None:
                        continue
                    cur_xlim = ax.get_xlim()
                    cur_ylim = ax.get_ylim()
                    xdata = event.xdata
                    ydata = event.ydata
                    if event.button == 'up':
                        scale_factor = 1 / base_scale
                    elif event.button == 'down':
                        scale_factor = base_scale
                    else:
                        scale_factor = 1
                    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
                    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
                    relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
                    rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
                    ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
                    ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
                fig.canvas.draw_idle()
            return zoom

        def pan_factory_figure(fig):
            state = {"press": None, "xlim": None, "ylim": None}

            def on_press(event):
                if event.button == 1 and event.inaxes:  # Left mouse button
                    state["press"] = (event.x, event.y)
                    state["xlim"] = event.inaxes.get_xlim()
                    state["ylim"] = event.inaxes.get_ylim()

            def on_release(event):
                state["press"] = None

            def on_motion(event):
                if state["press"] is None or event.inaxes is None:
                    return
                dx = event.x - state["press"][0]
                dy = event.y - state["press"][1]
                ax = event.inaxes
                # Calculate the movement in data coordinates
                xlim = state["xlim"]
                ylim = state["ylim"]
                width = xlim[1] - xlim[0]
                height = ylim[1] - ylim[0]
                # Sensitivity factor (adjust as needed)
                factor = 0.005
                ax.set_xlim(xlim[0] - dx * width * factor, xlim[1] - dx * width * factor)
                ax.set_ylim(ylim[0] + dy * height * factor, ylim[1] + dy * height * factor)
                fig.canvas.draw_idle()

            fig.canvas.mpl_connect('button_press_event', on_press)
            fig.canvas.mpl_connect('button_release_event', on_release)
            fig.canvas.mpl_connect('motion_notify_event', on_motion)

        self.canvas.mpl_connect('scroll_event', zoom_factory_figure(self.figure))
        pan_factory_figure(self.figure)

    def reset_zoom(self):
        """Reset all axes to autoscale (default zoom)."""
        self.reset_zoom_btn.setEnabled(False)
        for ax in self.figure.axes:
            ax.autoscale()
        self.canvas.draw_idle()
        self.green_blink_button()
        self.reset_zoom_btn.setEnabled(True)

    @abstractmethod
    def save_video(self):
        pass  # To be implemented in subclass
    
    @abstractmethod
    def update_plot(self):
        pass  # To be implemented in subclass

