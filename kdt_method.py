from measurements_detectors import Measure
from detection_lib import SMALL_DISK_RADIUS, PIXEL_TO_MM_RATIO
import numpy as np
from scipy.spatial import KDTree
from project_tools import create_product_name
import pandas as pd
from tqdm import tqdm

class Kdt:
    def __init__(self, measure: Measure):
        self.measure = measure
        self.measure_name = self.measure.get_name()
        self.vector_field_path = self.measure.get_vector_field_path()
        self.measure_data = self.measure.load_measure_data(source='drive')
        self.source = Kdt.__name__

    def get_source_name(self):
        return self.source
    
    def product_name(self, first_frame_name, second_frame_name):
        return create_product_name(self.measure_name, first_frame_name, second_frame_name, self.source)
    
    def match_particles(self, first_frame_name, second_frame_name):
        frame1_centers = np.vstack(self.measure_data[self.measure_data["frame"] == first_frame_name]["centers"].to_numpy())
        frame2_centers = np.vstack(self.measure_data[self.measure_data["frame"] == second_frame_name]["centers"].to_numpy())

        # Build KDTree on frame2 (the "destination" frame)
        tree = KDTree(frame2_centers)

        # For each particle in frame1, find the closest in frame2
        distances, indices = tree.query(frame1_centers)

        # Filter out bad matches
        max_distance = 2 * SMALL_DISK_RADIUS * PIXEL_TO_MM_RATIO
        valid = distances < max_distance
        valid_indices = indices[valid]
        matched_frame1 = frame1_centers[valid]
        matched_frame2 = frame2_centers[valid_indices]
        valid_distances = distances[valid]
        
        # Create displacement vectors
        displacements = matched_frame2 - matched_frame1

        return matched_frame1, matched_frame2, valid_distances, valid_indices, displacements
    
    def save_vector_field(self, first_frame_name, second_frame_name):
        matched_frame1, matched_frame2, valid_distances, valid_indices, displacements = self.match_particles(first_frame_name, second_frame_name)
        product_name = self.product_name(first_frame_name, second_frame_name)
        
        # Create a DataFrame with original positions and displacements
        df = pd.DataFrame(np.hstack([matched_frame1, displacements]), columns=["x", "y", "u", "v"])

        # Save to a text file (tab-separated or comma-separated)
        df.to_csv(f"{self.vector_field_path}/{product_name}.txt", index=False, sep='\t')  # tab-separated

    
    def run_all_vector_fields(self, source='local'):
        print(f"source: {source}")
        if source == 'local': frame_names = self.measure.get_frame_names()
        elif source == 'drive': frame_names = sorted(file.name for file in self.measure.get_drive_path().iterdir() if file.is_file() and file.suffix.lower() == '.jpg')
        else: raise ValueError("source must be either 'local' or 'drive'")
        for i in tqdm(range(len(frame_names))):
            for j in range(i+1, len(frame_names)):
                first_frame_name, second_frame_name = frame_names[i], frame_names[j]
                self.save_vector_field(first_frame_name, second_frame_name)
    
    
    def build_trajectories(self):
        # Build trajectories for each particle across frames
        positions = self.measure_data['centers']
        # Efficiently pad centers arrays with 0 so all frames have the same number of particles
        centers_arrays = [np.vstack(centers) for centers in positions]
        max_particles = max(arr.shape[0] for arr in centers_arrays)
        # Preallocate output array with 0
        positions = np.full((len(centers_arrays), max_particles, 2), 0, dtype=float)
        for i, arr in enumerate(centers_arrays):
            positions[i, :arr.shape[0], :] = arr
        # Center the positions around the mean
        mean_x = positions[:, :, 0].mean(axis=1, keepdims=True)
        mean_y = positions[:, :, 1].mean(axis=1, keepdims=True)
        positions[:, :, 0] -= mean_x
        positions[:, :, 1] -= mean_y
        
        # Initialize trajectories with the first frame's positions
        num_frames = positions.shape[0]
        trajectories = np.zeros((num_frames, max_particles, 2), dtype=float)
        trajectories[0] = positions[0]

        # For each subsequent frame, match particles using KDTree and update trajectories
        for i in range(1, num_frames):
            prev_centers = trajectories[i-1]
            curr_centers = positions[i]
            tree = KDTree(curr_centers)
            _, indices = tree.query(prev_centers)
            # Assign matched positions
            trajectories[i] = curr_centers[indices]

        return trajectories