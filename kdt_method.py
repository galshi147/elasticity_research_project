from measurements_detectors import Measure
from detection_lib import SMALL_DISK_RADIUS, PIXEL_TO_MM_RATIO
import numpy as np
from scipy.spatial import KDTree
from project_tools import create_product_name
import pandas as pd
from tqdm import tqdm

MAX_SINGLE_DISPLACEMENT = 2 * SMALL_DISK_RADIUS * PIXEL_TO_MM_RATIO # pixels

class Kdt:
    def __init__(self, measure: Measure):
        self.measure = measure
        self.measure_name = self.measure.get_name()
        self.vector_field_path = self.measure.get_vector_field_path()
        self.measure_data = self.measure.load_measure_data(source='drive')
        self.frame_center = self.measure.get_frame_center()
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
        valid = distances < MAX_SINGLE_DISPLACEMENT
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
        """Build trajectories for each particle across frames"""
        # Efficiently pad centers arrays with 0 so all frames have the same number of particles
        centers_arrays = [np.vstack(centers) for centers in self.measure_data['centers']]
        max_particles = max(arr.shape[0] for arr in centers_arrays)
        # Preallocate output array with 0
        positions = np.full((len(centers_arrays), max_particles, 2), 0, dtype=float)
        for i, arr in enumerate(centers_arrays):
            positions[i, :arr.shape[0], :] = arr
        
        # Center the positions around the frame center
        positions[:, :, 0] -= self.frame_center[0]
        positions[:, :, 1] -= self.frame_center[1]
        
        # Initialize trajectories with the first frame's positions
        num_frames = positions.shape[0]
        trajectories = np.zeros((num_frames, max_particles, 2), dtype=float)
        trajectories[0] = positions[0]

        # For each subsequent frame, match particles using KDTree and update trajectories
        for i in range(1, num_frames):
            prev_centers = trajectories[i-1]
            curr_centers = positions[i]
            tree = KDTree(curr_centers)
            distances, indices = tree.query(prev_centers)
            
            # Filter out bad matches
            # valid = distances < MAX_SINGLE_DISPLACEMENT
            # valid_indices = indices[valid]
            # # Assign matched positions
            # trajectories[i] = trajectories[i-1].copy()  # Copy previous frame's trajectory
            # trajectories[i][valid] = curr_centers[valid_indices]
            
            trajectories[i] = curr_centers[indices]

        return trajectories
    
    def build_trajectories_robust(self):
        """
        Enhanced particle tracking with proper coordinate handling
        """
        positions = self.measure_data['centers']
        centers_arrays = [np.vstack(centers) for centers in positions]
        
        # Calculate the mean center from all particle data
        all_particles = np.vstack(centers_arrays)
        mean_center = np.mean(all_particles, axis=0)
        
        print(f"Frame center from detector (x,y): {self.frame_center}")
        print(f"Calculated mean center (x,y): {mean_center}")

        # IMPORTANT: Ensure consistent (x,y) coordinate system
        # self.frame_center is already in (x,y) format from OpenCV
        # particle centers should also be in (x,y) format

        # Start with first frame (centered using mean center)
        first_frame = centers_arrays[0] - mean_center  # Remove the coordinate swap
        trajectories = [first_frame]
        
        for frame_idx in range(1, len(centers_arrays)):
            prev_particles = trajectories[-1]
            curr_particles = centers_arrays[frame_idx] - mean_center  # Use mean center consistently
            
            if len(prev_particles) == 0 or len(curr_particles) == 0:
                trajectories.append(curr_particles)
                continue
            
            tree_curr = KDTree(curr_particles)
            dist_forward, idx_forward = tree_curr.query(prev_particles)
            
            tree_prev = KDTree(prev_particles)
            dist_backward, idx_backward = tree_prev.query(curr_particles)
            
            valid_forward = dist_forward < MAX_SINGLE_DISPLACEMENT
            mutual_matches = np.zeros(len(prev_particles), dtype=bool)
            
            for i, (valid, curr_idx) in enumerate(zip(valid_forward, idx_forward)):
                if valid:
                    if idx_backward[curr_idx] == i and dist_backward[curr_idx] < MAX_SINGLE_DISPLACEMENT:
                        mutual_matches[i] = True
            
            new_positions = prev_particles.copy()
            new_positions[mutual_matches] = curr_particles[idx_forward[mutual_matches]]
            
            matched_curr_indices = idx_forward[mutual_matches]
            unmatched_curr = np.setdiff1d(np.arange(len(curr_particles)), matched_curr_indices)
            
            if len(unmatched_curr) > 0:
                new_particles = curr_particles[unmatched_curr]
                new_positions = np.vstack([new_positions, new_particles])
            
            trajectories.append(new_positions)
        
        # Convert to standard format
        max_particles = max(len(traj) for traj in trajectories)
        result = np.zeros((len(trajectories), max_particles, 2))
        
        for i, traj in enumerate(trajectories):
            if len(traj) > 0:
                result[i, :len(traj), :] = traj
        
        return result