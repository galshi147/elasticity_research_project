import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from measurements_detectors import Measure
from project_tools import create_product_name
from detection_lib import PIXEL_TO_MM_RATIO, LARGE_DISK_RADIUS, TOTAL_SYSTEM_RADIUS

class Plotter:
    def __init__(self, measure: Measure, source: str):
        self.measure = measure
        self.measure_name = self.measure.get_name()
        self.vector_field_path = self.measure.get_vector_field_path()
        self.graph_path = self.measure.get_graph_path()
        self.source = source

    def product_name(self, first_frame_name, second_frame_name):
        return create_product_name(self.measure_name, first_frame_name, second_frame_name, self.source)
    
    def load_vector_field(self, first_frame_name, second_frame_name):
        product_name = self.product_name(first_frame_name, second_frame_name)
        data = pd.read_csv((self.vector_field_path / f"{product_name}.txt").resolve(), sep="\t")
        if self.source == "Piv": 
            data.rename(columns={"# x": "x"}, inplace=True)
            mask = data['flags'] == 0
            data = data[mask]            
        return {col: data[col].to_numpy() for col in data.columns}

    def _plot_displacement_by_rings_helper(self, ax: plt.Axes, measure_statistics, first_frame_num, second_frame_num):
        ax.set_xlabel("radius [mm]")
        ax.set_ylabel("components displacement (normalized)")
        # extra_data = self.measure.get_measure_statistics()
        stat_f1, stat_f2 = measure_statistics[int(first_frame_num)], measure_statistics[int(second_frame_num)]
        area_fraction_str = f"area fraction: {round(0.5*(stat_f1['areal_fraction'] + stat_f2['areal_fraction']), 2)} %"
        ax.plot([], [], alpha=0, label=area_fraction_str)
        ax.legend()
        return ax
    

    def plot_displacement_by_rings(self, ax: plt.Axes, measure_statistics, first_frame_name, second_frame_name, radii, rad_disp, tan_disp, save=False, show=True):
        # product_name = self.product_name(first_frame_name, second_frame_name)
        # fig, ax = plt.subplots()
        first_frame_num, second_frame_num = first_frame_name[4:-4], second_frame_name[4:-4]
        ax.scatter(radii, rad_disp, linewidths=0.5, marker=".", alpha=0.5, color="orange", label=r"$\hat{r}$")
        ax.plot(radii, rad_disp, color="orange", label=r"$\hat{r}$")
        ax.scatter(radii, tan_disp, linewidths=0.5, marker=".", alpha=0.5, color="green", label=r"$\hat{\theta}$")
        ax.plot(radii, tan_disp, color="green", label=r"$\hat{\theta}$")
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
        ax.set_title(f"displacement field of: {first_frame_num} & {second_frame_num}", pad=15)
        ax = self._plot_displacement_by_rings_helper(ax, measure_statistics, first_frame_num, second_frame_num)
        # if save: plt.savefig(f"{str(self.graph_path)}/disp_{product_name}.png")
        # if show: plt.show()
        return ax
    
    def plot_vector_field(self, ax: plt.Axes, x, y, u, v, first_frame_name, second_frame_name, **kwargs):
        """
        Plots the vector field for the given pair of frames.
        Args:
            first_frame_name (str): The name of the first frame.
            second_frame_name (str): The name of the second frame.

        Keyword Args:
            add_rings (bool): If True, adds concentric rings to the plot.
            radii (np.array): Radii of the rings to be plotted (required if add_rings is True).
            dr (float): Radial increment in pixels (required if add_rings is True).

        Raises:
            KeyError: If required keyword arguments for rings are missing when add_rings is True.
        """
        x = (x - np.mean(x)) / PIXEL_TO_MM_RATIO # Centerlize and Convert to mm
        y = (y - np.mean(y)) / PIXEL_TO_MM_RATIO  
        magnitude = np.sqrt(u**2 + v**2) / PIXEL_TO_MM_RATIO  # Convert to mm
        magnitude[magnitude == 0] = np.nan
        # fig, ax = plt.subplots()
        quiv = ax.quiver(x, y, u / magnitude, v / magnitude, magnitude, cmap='cool')
        ax.scatter(x,y, marker='.', linewidths=0.1)
        # Highlight NaN points (magnitude=0)
        nan_mask = np.isnan(magnitude)
        if np.any(nan_mask):
            ax.scatter(x[nan_mask], y[nan_mask], color='midnightblue', marker='x', label='magnitude=0')
        # Highlight exceed points (magnitude > LARGE_DISK_RADIUS / 2)
        exceed_mask = magnitude > LARGE_DISK_RADIUS / 2
        if np.any(exceed_mask):
            ax.scatter(x[exceed_mask], y[exceed_mask], color='darkmagenta', marker='x', label='magnitude > LARGE_DISK_RADIUS / 2')

        # colorbar = plt.colorbar(quiv, label='Magnitude (normalized)')
        
        # Attach a colorbar safely with axes divider
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        colorbar = ax.figure.colorbar(quiv, cax=cax)
        colorbar.set_label("Magnitude (normalized) mm")

        ax.set_title(f"Vector Field of {first_frame_name[0:-4]} & {second_frame_name[0:-4]} ({self.source})")
        ax.set_xlabel('x [mm]')
        ax.set_ylabel('y [mm]')
        ax.axis('equal')

        if kwargs["add_rings"] == True:
            # Check if required keyword arguments are provided
            if "radii" not in kwargs or "dr" not in kwargs:
                raise KeyError("If add_rings is True, 'radii' and 'dr' must be provided in kwargs.")
            # Plotting rings
            radii = kwargs["radii"]
            dr_str = str(round(kwargs["dr"] / PIXEL_TO_MM_RATIO, 2))
            for radius in (radii / PIXEL_TO_MM_RATIO):
                circle = plt.Circle((0, 0), radius, color='gray', fill=False, alpha=0.5)
                ax.add_patch(circle)
            ax.plot([], [], label=f"$dr={dr_str} mm $", color="white")
        ax.legend()
        # plt.show()
        return ax, colorbar

    def plot_particles_trajectories(self, ax: plt.Axes, frame1_num, frame2_num, trajectories: np.ndarray, selected_particles: np.ndarray = None):
        x = trajectories[:, :, 0] / PIXEL_TO_MM_RATIO  # shape: (num_frames, num_particles)
        y = trajectories[:, :, 1] / PIXEL_TO_MM_RATIO  # shape: (num_frames, num_particles)
        if selected_particles is not None:
            x = x[:, selected_particles]
            y = y[:, selected_particles]
        
        # ax.plot(x, y, alpha=0.7)
        num_frames, num_particles = x.shape
        # Assign each particle a unique color from a continuous colormap
        base_cmap = cm.get_cmap('nipy_spectral')  # 'hsv', 'nipy_spectral', or 'turbo', 'gist_ncar'
        base_colors = base_cmap(np.arange(num_particles) / max(1, num_particles - 1))  # shape: (num_particles, 4)
        # Create alpha gradient for frames
        alphas = np.linspace(0.3, 1.0, num_frames)  # shape: (num_frames,)

        # Broadcast base colors and alphas to all points
        rgb = np.repeat(base_colors[np.newaxis, :, :3], num_frames, axis=0)  # (num_frames, num_particles, 3)
        alpha = np.repeat(alphas[:, np.newaxis], num_particles, axis=1)[..., np.newaxis]  # (num_frames, num_particles, 1)
        colors_all = np.concatenate([rgb, alpha], axis=2).reshape(-1, 4)  # (num_frames*num_particles, 4)
        # Flatten x and y for scatter
        ax.scatter(x.flatten(), y.flatten(), c=colors_all, s=20, marker='o', edgecolor='black', linewidth=0.3, alpha=0.7)

        circle = plt.Circle((0, 0), TOTAL_SYSTEM_RADIUS, color='gray', fill=False, alpha=0.5)
        ax.add_patch(circle)
        ax.grid(True, alpha=0.5)
        ax.set_title(fr"Particle Trajectories: DSC_{frame1_num:04d} $\rightarrow$ DSC_{frame2_num:04d} ({self.source})")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.axis('equal')