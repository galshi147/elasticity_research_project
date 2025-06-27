from PySide6.QtWidgets import QInputDialog
from PySide6.QtCore import QTimer

def run_k_buffer(window):
    k, ok = QInputDialog.getInt(window, "K Buffer", "Enter k value:", 10, 1, 1000, 1)
    if not ok:
        return

    # Set up animation state on the window
    window.stop_script = False
    window.k_buffer_k = k
    window.k_buffer_frame1 = window.frame1.value()
    window.k_buffer_base_jump = window.base_frame_jump.value()
    window.k_buffer_last_frame = window.measure.get_total_frames_num()

    # Create and start the timer for animation
    if hasattr(window, 'k_buffer_timer') and window.k_buffer_timer is not None:
        window.k_buffer_timer.stop()
    window.k_buffer_timer = QTimer(window)
    window.k_buffer_timer.timeout.connect(lambda: _k_buffer_step(window))
    window.k_buffer_timer.start(100)  # ms between steps

def _k_buffer_step(window):
    if window.stop_script:
        window.k_buffer_timer.stop()
        window.stop_running_script()
        print(f"script {window.k_buffer_k}-Buffer stopped.")
        return
    frame1 = window.k_buffer_frame1
    frame2 = frame1 + window.k_buffer_k
    if frame2 > window.k_buffer_last_frame:
        window.k_buffer_timer.stop()
        window.stop_running_script()
        return
    window.frame1.setValue(frame1)
    window.frame2.setValue(frame2)
    window.update_plot()
    window.k_buffer_frame1 += window.k_buffer_base_jump


def run_decrease_rings(window):
    # Set up animation state
    window.stop_script = False
    window.decrease_rings_value = window.rings_spin.value()
    window.decrease_rings_jump = window.rings_spin_jump.value()

    # Stop any existing timer
    if hasattr(window, 'decrease_rings_timer') and window.decrease_rings_timer is not None:
        window.decrease_rings_timer.stop()
    window.decrease_rings_timer = QTimer(window)
    window.decrease_rings_timer.timeout.connect(lambda: _decrease_rings_step(window))
    window.decrease_rings_timer.start(100)  # ms between steps

def _decrease_rings_step(window):
    if window.stop_script:
        window.decrease_rings_timer.stop()
        window.reset_script_combobox()
        print(f"script decrease_rings stopped.")
        return
    rings_val = window.decrease_rings_value
    if rings_val <= 0:
        window.decrease_rings_timer.stop()
        window.reset_script_combobox()
        return
    window.rings_spin.setValue(rings_val)
    window.update_plot()
    window.decrease_rings_value -= window.decrease_rings_jump
    if window.decrease_rings_value < 0:
        window.decrease_rings_value = 0


# This dictionary maps script names to their corresponding functions
SCRIPT_DICT = {
    "run_k_buffer": run_k_buffer,
    "run_rings_jumps": run_decrease_rings,
}