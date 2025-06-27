from project_tools import create_product_name

from PySide6.QtWidgets import (
    QMainWindow, QSpinBox, QPushButton, 
    QFormLayout, QHBoxLayout, QVBoxLayout, 
    QWidget, QDialog, QDialogButtonBox
)
from PySide6.QtCore import QTimer

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
    def __init__(self, total_frames):
        super().__init__()
        self.smooth_mode = False
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_plot)
        self.init_common_ui(total_frames)

    def init_common_ui(self, total_frames):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.controls_layout = QHBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        # Control base frame (frame1) jump
        base_frame_jump_layout = QFormLayout()
        self.base_frame_jump = QSpinBox()
        self.base_frame_jump.setRange(1, total_frames - 1)
        self.base_frame_jump.setValue(1)
        base_frame_jump_layout.addRow("Base Frame jump:", self.base_frame_jump)

        # Frame selectors
        frame1_layout = QFormLayout()
        self.frame1 = QSpinBox()
        self.frame1.setSingleStep(self.base_frame_jump.value())
        self.base_frame_jump.valueChanged.connect(lambda value: self.frame1.setSingleStep(value))
        self.frame1.setRange(1, total_frames)
        self.frame1.setValue(1)
        self.frame1.setStyleSheet(SPECIAL_SPINBOX_STYLE)
        frame1_layout.addRow("Frame 1:", self.frame1)
        frame2_layout = QFormLayout()
        self.frame2 = QSpinBox()
        self.frame2.setRange(1, total_frames)
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

        self.controls_layout.addLayout(base_frame_jump_layout)
        self.controls_layout.addLayout(frame1_layout)
        self.controls_layout.addLayout(frame2_layout)
        self.controls_layout.addLayout(interval_layout)
        self.controls_layout.addWidget(self.update_btn)
        self.controls_layout.addWidget(self.smooth_mode_btn)
        self.controls_layout.addWidget(self.save_btn)
        
        self.central_widget.setLayout(self.main_layout)


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

    def save_video(self):
        pass  # To be implemented in subclass

    def update_plot(self):
        pass  # To be implemented in subclass

class VideoParamsDialog(QDialog):
            def __init__(self, parent, start_val, end_val, interval_val, min_frame, max_frame):
                super().__init__(parent)
                self.fps = 2  # Default frames per second for the video
                self.setWindowTitle("Select Video Parameters")
                layout = QFormLayout(self)
                self.start_spin = QSpinBox()
                self.start_spin.setRange(min_frame, max_frame)
                self.start_spin.setValue(start_val)
                layout.addRow("Start Frame:", self.start_spin)
                self.end_spin = QSpinBox()
                self.end_spin.setRange(min_frame, max_frame)
                self.end_spin.setValue(end_val)
                layout.addRow("End Frame:", self.end_spin)
                self.interval_spin = QSpinBox()
                self.interval_spin.setRange(1, max(1, max_frame - min_frame))
                self.interval_spin.setValue(interval_val)
                layout.addRow("Interval:", self.interval_spin)
                self.fps_spin = QSpinBox()
                self.fps_spin.setRange(1, 60)  # Set a reasonable range for FPS
                self.fps_spin.setValue(self.fps)
                layout.addRow("Frames per Second (FPS):", self.fps_spin)
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(self.accept)
                buttons.rejected.connect(self.reject)
                layout.addWidget(buttons)
            
            def get_fps(self):
                return self.fps_spin.value()