from measurements_detectors import Measure
from piv_method import Piv
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from gui import Gui
from programs import test_detection
from pathlib import Path

def main():
     
    
    
    m = Measure("26.01.25", path_setting='drive')
    gui = Gui(m, "Kdt")
    gui.run()
    
    # m_data = m.load_measure_data(source='drive')
    # print(m_data.keys())
    # print(m_data[m_data["frame"] == "DSC_0001.jpg"]["centers"].to_numpy())
    
    # test_detection(m, start=0, stop=9)
    
    # data = m.load_measure_data(source='drive')
    # for d in data["statistic"]:
    #     print(d["areal_fraction"])
    
    # for idx, d in enumerate(data["statistic"]):
    #     if d["areal_fraction"] < 100:
    #         print(f"Line {idx}: {d['areal_fraction']}")





    
main()