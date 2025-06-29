from gui_files.scripter import Scripter
from PySide6.QtWidgets import QInputDialog
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog
from gui_files.dialogs import AnimateTrajDialog

class VecFieldAnalyzerScripter(Scripter):
    def __init__(self, window):
        super().__init__(window)
        self.script_dict = {
            "run_k_buffer": self.run_k_buffer,
            "run_rings_jumps": self.run_decrease_rings,
        }

    def run_k_buffer(self):
        k, ok = QInputDialog.getInt(self.window, "K Buffer", "Enter k value:", 10, 1, 1000, 1)
        if not ok:
            return

        # Set up animation state on the window
        self.window.stop_script = False
        self.window.k_buffer_k = k
        self.window.k_buffer_frame1 = self.window.frame1.value()
        self.window.k_buffer_base_jump = self.window.base_frame_jump.value()
        self.window.k_buffer_last_frame = self.window.measure.get_total_frames_num()

        # Create and start the timer for animation
        if hasattr(self.window, 'k_buffer_timer') and self.window.k_buffer_timer is not None:
            self.window.k_buffer_timer.stop()
        self.window.k_buffer_timer = QTimer(self.window)
        self.window.k_buffer_timer.timeout.connect(lambda: self._k_buffer_step())
        self.window.k_buffer_timer.start(100)  # ms between steps

    def _k_buffer_step(self):
        if self.window.stop_script:
            self.window.k_buffer_timer.stop()
            self.window.stop_running_script()
            print(f"script {self.window.k_buffer_k}-Buffer stopped.")
            return
        frame1 = self.window.k_buffer_frame1
        frame2 = frame1 + self.window.k_buffer_k
        if frame2 > self.window.k_buffer_last_frame:
            self.window.k_buffer_timer.stop()
            self.window.stop_running_script()
            return
        self.window.frame1.setValue(frame1)
        self.window.frame2.setValue(frame2)
        self.window.update_plot()
        self.window.k_buffer_frame1 += self.window.k_buffer_base_jump


    def run_decrease_rings(self):
        # Set up animation state
        self.window.stop_script = False
        self.window.decrease_rings_value = self.window.rings_spin.value()
        self.window.decrease_rings_jump = self.window.rings_spin_jump.value()

        # Stop any existing timer
        if hasattr(self.window, 'decrease_rings_timer') and self.window.decrease_rings_timer is not None:
            self.window.decrease_rings_timer.stop()
        self.window.decrease_rings_timer = QTimer(self.window)
        self.window.decrease_rings_timer.timeout.connect(lambda: self._decrease_rings_step())
        self.window.decrease_rings_timer.start(100)  # ms between steps

    def _decrease_rings_step(self):
        if self.window.stop_script:
            self.window.decrease_rings_timer.stop()
            self.window.reset_script_combobox()
            print(f"script decrease_rings stopped.")
            return
        rings_val = self.window.decrease_rings_value
        if rings_val <= 0:
            self.window.decrease_rings_timer.stop()
            self.window.reset_script_combobox()
            return
        self.window.rings_spin.setValue(rings_val)
        self.window.update_plot()
        self.window.decrease_rings_value -= self.window.decrease_rings_jump
        if self.window.decrease_rings_value < 0:
            self.window.decrease_rings_value = 0


        
class ParticleTrackerScripter(Scripter):
    def __init__(self, window):
        super().__init__(window)
        self.script_dict = {
            "animate_trajectoties": self.animate_trajectoties
        }


    def animate_trajectoties(self):
        # Ask user for initial frame1, frame2, jump, end_frame, and delay
        min_frame = self.window.frame1.minimum()
        max_frame = self.window.frame2.maximum()
        current_frame1 = self.window.frame1.value()
        current_frame2 = self.window.frame2.value()
        dialog = AnimateTrajDialog(self.window, frame1_val=current_frame1, frame2_val=current_frame2, min_frame=min_frame, max_frame=max_frame)
        if dialog.exec() != QDialog.Accepted:
            return
        frame1, frame2, jump, end_frame, delay_sec = dialog.get_values()
        if None in (frame1, frame2, jump, end_frame, delay_sec):
            return
        delay_ms = int(delay_sec * 1000)
        self.window.stop_script = False
        self.window.anim_frame2_jump = jump
        self.window.anim_frame2 = frame2
        self.window.anim_end_frame = end_frame
        self.window.frame1.setValue(frame1)
        self.window.frame2.setValue(frame2)
        # Stop any existing timer
        if hasattr(self.window, 'anim_timer') and self.window.anim_timer is not None:
            self.window.anim_timer.stop()
        self.window.anim_timer = QTimer(self.window)
        self.window.anim_timer.timeout.connect(lambda: self._animate_trajectoties_step())
        self.window.anim_timer.start(delay_ms)

    def _animate_trajectoties_step(self):
        if self.window.stop_script:
            self.window.anim_timer.stop()
            self.window.stop_running_script()
            print("Particle animation stopped.")
            return
        frame2 = self.window.anim_frame2
        end_frame = self.window.anim_end_frame
        if frame2 >= end_frame:
            self.window.anim_timer.stop()
            self.window.stop_running_script()
            return
        self.window.frame2.setValue(frame2)
        self.window.update_plot()
        self.window.anim_frame2 += self.window.anim_frame2_jump