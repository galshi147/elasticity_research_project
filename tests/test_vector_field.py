import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from visualization import Plotter
from calculator import Calculator
from measurements_detectors import Measure

# --- Load the data file ---
data_path = "C:\\university\\Elasticity_Project\\elasticity_research_project\\tests\\26.01.25_DSC_0001_DSC_0002_Kdt.txt"
df = pd.read_csv(data_path, sep="\t")

x = df["x"].to_numpy()
y = df["y"].to_numpy()
u = df["u"].to_numpy()
v = df["v"].to_numpy()

# --- Prepare dummy measure and plotter (adjust as needed) ---
measure = Measure("26.01.25", path_setting='drive')
plotter = Plotter(measure, source="Kdt")

# --- Calculate displacement field by rings ---
calculator = Calculator(measure)
radii, dr, rad_disp, tan_disp = calculator.calculate_displacement_field(x, y, u, v, rings_num=10)

# --- Plotting ---
fig, (ax_vf, ax_av) = plt.subplots(1, 2, figsize=(14, 6))

# Vector field
plotter.plot_vector_field(ax_vf, x, y, u, v, "DSC_0001.jpg", "DSC_0002.jpg", add_rings=True, radii=radii, dr=dr)

# Displacement by rings
plotter.plot_displacement_by_rings(ax_av, measure.load_measure_data(source='drive')["statistic"], "DSC_0001.jpg", "DSC_0002.jpg", radii, rad_disp, tan_disp)

plt.tight_layout()
plt.show()