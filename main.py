from measurements_detectors import Measure
from piv_method import Piv
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from gui_files.gui import Gui
from programs import test_detection
from pathlib import Path

def main():
    m = Measure("26.01.25", path_setting='drive')
    gui = Gui(m, "Kdt")
    gui.run()
    
    
main()