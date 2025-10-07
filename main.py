from pathlib import Path
from measurements_detectors import Measure
from piv_method import Piv
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from gui_files.gui import Gui
from programs import test_detection
from database_manager import DatabaseManager
from db.performance_benchmark import run_benchmark


def main():
    db_manager = DatabaseManager()

    m = Measure("26.01.25", path_setting='drive', use_database=True)
    gui = Gui(m, "Kdt")
    gui.run()

    # Migrate existing measurements
    # db = DatabaseManager()
    # for measurement_name in ["26.01.25"]:
    #     measure = Measure(measurement_name, path_setting='drive', use_database=True)
    #     db.migration_from_files(measure)
    # results = run_benchmark()
    stats = db_manager.get_performance_stats()
    print("\nPerformance Stats:", stats)
    
main()