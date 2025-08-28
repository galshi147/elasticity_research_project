import matplotlib.pyplot as plt
import numpy as np
from detection_lib import TOTAL_SYSTEM_RADIUS, PIXEL_TO_MM_RATIO
from kdt_method import Kdt
from measurements_detectors import Measure

def test_build_trajectories(measure: Measure, image_folder: str):
    radii = measure.load_measure_data(source='drive')['radii'].to_numpy()
    frame_names = measure.get_frame_names()
    kdt = Kdt(measure)
    # Build trajectories
    trajectories = kdt.build_trajectories()
    num_frames, num_particles, _ = trajectories.shape

    # Optionally select a subset of frames to plot
    if frame_names is None:
        frame_names = range(num_frames)

    for i, frame_name in enumerate(frame_names):
        # Load the corresponding image
        img_path = f"{image_folder}/{frame_name}"
        img = plt.imread(img_path)

        fig, ax = plt.subplots(figsize=(8, 8))
        # Show the image, stretching it to fill the axes
        x0, y0 = measure.get_frame_center()
        print(img.shape, x0, y0)
        ax.imshow(
            img,
            cmap='gray',
            extent=[
            -x0, img.shape[1] - x0,
            -y0, img.shape[0] - y0
            ],
            alpha=0.75,
            origin='upper'
        )
        ax.set_xlim(-x0, img.shape[1] - x0)
        ax.set_ylim(-y0, img.shape[0] - y0)
        centers = np.column_stack([trajectories[i][:, 0], img.shape[0] - trajectories[i][:, 1]])

        # Plot circles and labels
        for idx, (x, y) in enumerate(centers):
            if np.isnan(x) or np.isnan(y):
                continue
            y = img.shape[0] - y  # Adjust y coordinate for image origin
            if i < len(radii):
                color = 'r'
                radius = radii[i-1][idx]  
            else:
                radius = 5  # Default radius if not available
                color = 'white'
            circle = plt.Circle((x, y), radius, color=color, fill=False, lw=0.6)
            ax.add_patch(circle)
            ax.text(x, y, str(idx), color='yellow', fontsize=6, ha='center', va='center')

            # Draw line to next frame's corresponding particle (if not last frame)
            # if i < num_frames - 1:
            #     next_x, next_y = trajectories[i+1, idx]
            #     if not (np.isnan(next_x) or np.isnan(next_y)):
            #         ax.plot([x, next_x], [y, next_y], 'g-', lw=1)
        # system_border = plt.Circle((img.shape[1] // 2, img.shape[0] // 2), TOTAL_SYSTEM_RADIUS * PIXEL_TO_MM_RATIO, color='blue', fill=False, alpha=1)
        system_border = plt.Circle((0, 0), TOTAL_SYSTEM_RADIUS * PIXEL_TO_MM_RATIO, color='blue', fill=False, alpha=1)
        ax.add_patch(system_border)
        system_border_2 = plt.Circle((x0, y0), TOTAL_SYSTEM_RADIUS * PIXEL_TO_MM_RATIO, color='k', fill=False, alpha=1)
        ax.add_patch(system_border_2)
        # Plot a blue point at (0, 0)
        ax.plot(0, 0, 'bo', markersize=6, label='Origin')
        ax.plot(x0, y0, color='k',marker='o', markersize=6)

        # Plot a purple point
        # ax.plot(img.shape[1], img.shape[0], 'o', color='purple', markersize=6, label='Corner')
        # ax.plot(x0, y0, 'o', color='purple', markersize=6, label='Corner')
        # ax.plot(2 * x0 - img.shape[1], 2 * y0 - img.shape[0], 'o', color='purple', markersize=6)
        ax.set_title(f"Frame {i+1}")
        # ax.axis('off')
        plt.show()

# Usage example:
measure = Measure("26.01.25", path_setting='local')
test_build_trajectories(measure, image_folder="measurements/26.01.25/raw_data")  # Adjust frame_indices as needed