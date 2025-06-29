from PySide6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QDialogButtonBox,
    QVBoxLayout, QDoubleSpinBox
)

class KBufferDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("K Buffer Parameters")
        layout = QFormLayout(self)
        self.k_spin = QSpinBox()
        self.k_spin.setRange(1, 1000)  # Set a reasonable range for k
        self.k_spin.setValue(10)
        layout.addRow("K Value:", self.k_spin)
        self.delay_edit = QDoubleSpinBox()
        self.delay_edit.setDecimals(2)
        self.delay_edit.setSingleStep(0.1)
        self.delay_edit.setRange(0.0, 10.0)
        self.delay_edit.setValue(0.1)
        layout.addRow("Delay between steps (seconds):", self.delay_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        try:
            k_value = self.k_spin.value()
            delay_sec = self.delay_edit.value()
            return k_value, delay_sec
        except Exception:
            print("Error getting values from KBufferDialog dialog")
            return None, None


class DisplacementVideoDialog(QDialog):
            def __init__(self, parent, start_val, end_val, interval_val, min_frame, max_frame):
                super().__init__(parent)
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
                self.fps_spin.setValue(2)
                layout.addRow("Frames per Second (FPS):", self.fps_spin)
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(self.accept)
                buttons.rejected.connect(self.reject)
                layout.addWidget(buttons)
            
            def get_fps(self):
                return self.fps_spin.value()
    
class AnimateTrajDialog(QDialog):
    def __init__(self, parent, frame1_val, frame2_val, min_frame, max_frame):
        super().__init__(parent)
        self.setWindowTitle("Animation Parameters")
        self.frame1_spin = QSpinBox()
        self.frame1_spin.setRange(min_frame, max_frame)
        self.frame1_spin.setValue(frame1_val)
        self.frame2_spin = QSpinBox()
        self.frame2_spin.setRange(min_frame, max_frame)
        self.frame2_spin.setValue(frame2_val)
        self.jump_edit = QSpinBox()
        self.jump_edit.setRange(1, max(1, max_frame - min_frame))
        self.jump_edit.setValue(1)
        self.delay_edit = QDoubleSpinBox()
        self.delay_edit.setDecimals(2)
        self.delay_edit.setSingleStep(0.1)
        self.delay_edit.setRange(0.0, 10.0)
        self.delay_edit.setValue(0.1)
        self.end_frame_spin = QSpinBox()
        self.end_frame_spin.setRange(2, max_frame)
        self.end_frame_spin.setValue(max_frame)
        layout = QFormLayout()
        layout.addRow("Initial Frame1:", self.frame1_spin)
        layout.addRow("Initial Frame2:", self.frame2_spin)
        layout.addRow("End Frame (optional):", self.end_frame_spin)
        layout.addRow("Frame2 Jump:", self.jump_edit)
        layout.addRow("Delay between steps (seconds):", self.delay_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addWidget(buttons)
    
    def get_values(self):
        try:
            frame1 = self.frame1_spin.value()
            frame2 = self.frame2_spin.value()
            end_frame = self.end_frame_spin.value()
            jump = self.jump_edit.value()
            delay_sec = self.delay_edit.value()
            return frame1, frame2, jump, end_frame, delay_sec
        except Exception:
            print("Error getting values from AnimateTrajDialog dialog")
            return None, None, None, None, None
        
        