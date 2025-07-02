import cv2
import numpy as np
from pathlib import Path


PIXEL_TO_MM_RATIO = 16
SMALL_DISK_RADIUS = 2.5 # mm
LARGE_DISK_RADIUS = 3.5 # mm
TOTAL_SYSTEM_RADIUS = 84 # mm
TOTAL_SYSTEM_AREA = np.pi * TOTAL_SYSTEM_RADIUS**2 # mm^2


def get_frame_size(frame):
    if len(frame.shape) == 2:
        frame_height, frame_width = frame.shape
    elif len(frame.shape) == 3:
        frame_height, frame_width, channels = frame.shape
    return frame_height, frame_width


def show_preview(image, window_name="preview", wait=True):
    height, width  = get_frame_size(image)
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, width, height)
    cv2.imshow(window_name, image)
    if wait: cv2.waitKey(0)


class CenterDisk:
    """
    Represents a circular disk with a specified diameter and center shift.
    This class is used to model a disk by its diameter (in millimeters) and its center shift
    along the x and y axes (in pixels). It provides methods to retrieve the radius (converted
    to millimeters using a pixel-to-mm ratio) and the center shifts.
    Attributes:
        radius (float): The radius of the disk in millimeters.
        center_x_shift (int): The horizontal shift of the disk's center in pixels.
        center_y_shift (int): The vertical shift of the disk's center in pixels.
    Methods:
        get_radius():
            Returns the radius of the disk in millimeters, accounting for the pixel-to-mm ratio.
        get_center_x_shift():
            Returns the horizontal shift of the disk's center in pixels.
        get_center_y_shift():
            Returns the vertical shift of the disk's center in pixels.
    """
    
    def __init__(self, diameter=0, center_x_shift=0, center_y_shift=0):
        """
        @param diameter: in mm units
        @param center_x_shift: in pixels
        @param center_y_shift: in pixels
        """
        self.radius = diameter / 2
        self.center_x_shift = center_x_shift
        self.center_y_shift = center_y_shift

    def get_radius(self):
        return self.radius * PIXEL_TO_MM_RATIO
    
    def get_center_x_shift(self):
        return self.center_x_shift
    
    def get_center_y_shift(self):
        return self.center_y_shift


class Configuration:
    def __init__(self, outer_crop_w_shitf, outer_crop_h_shift, scale_factor, mask_thresh, center_disk: CenterDisk):
        """_summary_
        Args:
            outer_crop_w_shitf (_type_): in pixels
            outer_crop_h_shift (_type_): in pixels
            scale_factor (int or float): detremines the radius of the outer crop
            mask_thresh (int): _description_
            center_disk (CenterDisk): threshold for black and white level
        """
        self.width_shift = outer_crop_w_shitf
        self.height_shift = outer_crop_h_shift
        self.image_scale_factor = scale_factor
        self.mask_thresh = mask_thresh
        self.center_disk = center_disk

    def get_width_shift(self):
        return self.width_shift
    
    def get_height_shift(self):
        return self.height_shift
    
    def get_outer_crop_scale_factor(self):
        return self.image_scale_factor
    
    def get_mask_thresh(self):
        return self.mask_thresh
    
    def get_center_disk_radius(self):
        return self.center_disk.get_radius()
    
    def get_center_disk_shifts(self):
        return self.center_disk.get_center_x_shift(), self.center_disk.get_center_y_shift()
    

class Detector:
    def __init__(self, measure_raw_data_path: Path, frame_name: str, configure: Configuration):
        self.configure = configure
        self.measure_raw_data_path = measure_raw_data_path
        self.frame_name = frame_name
        self.frame_path = (self.measure_raw_data_path / self.frame_name).resolve()
        self.small_disk_radius = SMALL_DISK_RADIUS * PIXEL_TO_MM_RATIO
        self.large_disk_radius = LARGE_DISK_RADIUS * PIXEL_TO_MM_RATIO
        self.reset()
        
    def reset(self):
        self.circles = np.empty(1)
        self.image = cv2.imread(str(self.frame_path), cv2.IMREAD_COLOR)
        if self.image is None:
            raise FileNotFoundError(f"Detector.reset() Could not read the image at {self.frame_path}.")
        self.frame_height, self.frame_width = get_frame_size(self.image)
        self.frame_center = (self.frame_width // 2 + self.configure.get_width_shift(),  self.frame_height // 2 + self.configure.get_height_shift())
    
    def get_configure(self):
        return self.configure

    def get_frame_name(self):
        return self.frame_name()
    
    def get_frame_sizes(self):
        return self.frame_height, self.frame_width
    
    def get_center_disk_radius(self):
        return self.configure.get_center_disk_radius()

    def get_circles(self):
        return self.circles
    
    def get_circles_positions(self):
        return self.circles[0][:, :2]
    
    def get_circles_radii(self):
        return self.circles[0][:, 2]
    
    def get_frame_center(self):
        return self.frame_center
    
    def set_frame(self, new_frame_name: str):
        self.frame_name = new_frame_name
        self.frame_path = (self.measure_raw_data_path / new_frame_name).resolve()
        self.reset()

    def _detect_circles(self, frame):
        sensitivity = 8
        circles = cv2.HoughCircles(frame, cv2.HOUGH_GRADIENT, dp=1.2, 
            minDist=self.small_disk_radius * 2, 
            param1=50, 
            param2=sensitivity, 
            minRadius=int(self.small_disk_radius), 
            maxRadius= int(self.large_disk_radius))
        if circles is None:
            raise ValueError(f"Detector._detect_circles() No circles were detected in the frame {self.frame_name}.")
        self.circles = circles.astype(np.int32)

    def _create_outer_crop_mask(self):
        outer_crop_center = self.frame_center
        outer_crop_radius = int(self.frame_height // self.configure.get_outer_crop_scale_factor())
        outer_mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
        return outer_mask, outer_crop_center, outer_crop_radius

    def _create_inner_mask(self):
        x, y = self.frame_center
        x_shift, y_shift = self.configure.get_center_disk_shifts()
        center_disk_center = (x + x_shift, y + y_shift)
        center_disk_radius = self.configure.get_center_disk_radius()
        center_disk_mask = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
        return center_disk_mask, center_disk_center, center_disk_radius
    
    def _draw_rects(self, frame):
         if self.circles is not None:
            bboxes = self.circles_to_bboxes(self.circles)
            centers = self.circles[0][:, :2]  # First two columns: x, y
            radii = self.circles[0][:, 2] # Circle radius
            
            for center, radius, bbox in zip(centers, radii, bboxes):
                # Draw the circle's outline
                frame_with_circles = cv2.circle(frame, center, radius, (0, 0, 255), 2)
                p1 = tuple((bbox[0], bbox[1]))
                p2 = tuple((bbox[0] + bbox[2], bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255, 0, 0), 2)
    
    def _draw_circles(self, frame):
        if self.circles is not None:
            centers = self.circles[0][:, :2]  # First two columns: x, y
            radii = self.circles[0][:, 2] # Circle radius

            for center, radius in zip(centers, radii):
                # Draw the circle's outline
                frame_with_circles = cv2.circle(frame, center, radius, (0, 0, 255), 2)
                
                # Draw the circle's center point
                frame_with_circles = cv2.circle(frame, center, 3, (0, 0, 255), -1)

        return frame_with_circles

    def calculate_radii_statistics(self, print_stat=False):
        radii = self.circles[0, :, 2] / PIXEL_TO_MM_RATIO # mm
        max_detected_radius, min_detected_radius  = round(np.max(radii), 2), round(np.min(radii), 2)
        medium_radius = round((0.5 * (max_detected_radius + min_detected_radius)), 2)

        # Count radii in the range min to medium (inclusive)
        count_small_disks = np.count_nonzero((radii >= min_detected_radius) & (radii <= medium_radius))
        
        # Count radii in the range medium+1 to max (inclusive)
        count_large_disks = np.count_nonzero((radii > medium_radius) & (radii <= max_detected_radius))
        

        covered_detected_area = round(np.sum(np.pi * np.power(radii, 2)), 2)
        covered_area = round(np.pi * SMALL_DISK_RADIUS**2 * count_small_disks + np.pi * LARGE_DISK_RADIUS**2 * count_large_disks + np.pi * self.configure.get_center_disk_radius()**2, 2)
        total_area = round(TOTAL_SYSTEM_AREA, 2)
        areal_fraction = round(covered_detected_area / total_area, 2) * 100
        num_detected = self.circles.shape[1]


        if print_stat:
            print(f"\n{'='*20}frame: {self.frame_name}{'='*20}")
            print(f"detected {num_detected} circles\n{'-'*50}")
            print(f"min detected radius: {min_detected_radius} mm")
            print(f"max detected radius: {max_detected_radius} mm")
            print(f"medium radius: {medium_radius} mm")
            print(f"Number of small circles with radius {min_detected_radius} to {medium_radius}: {count_small_disks}")
            print(f"Number of large circles with radius {medium_radius} to {max_detected_radius}: {count_large_disks}")
            print(f"covered detected area: {covered_detected_area} mm^2")
            print(f"covered area: {covered_area} mm^2")
            print(f"total area: {total_area} mm^2")
            print(f"areal fraction: {areal_fraction} %")
            print(f"{'='*50}\n")

        
        statistics = {
            "num_detected" : num_detected,
            "min_detected_radius" : min_detected_radius,
            "max_detected_radius": max_detected_radius,
            "medium_radius": medium_radius,
            "small_disks_num": count_small_disks,
            "large_disks_num": count_large_disks,
            "covered_detected_area": covered_detected_area,
            "covered_area": covered_area,
            "areal_fraction": areal_fraction
        }
        return statistics

    def detect_disks(self, test_mode=False, show_control_print=False, print_stat=False):
        # Load the image
        image = np.copy(self.image)
        if show_control_print: print(f"\nimage loaded: {self.frame_name}\n")

        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if show_control_print: print("converted to grayscale\n")
        if test_mode: show_preview(gray)

        # crop the outer frame
        outer_mask, outer_crop_center, outer_crop_radius = self._create_outer_crop_mask()
        cv2.circle(outer_mask, outer_crop_center, outer_crop_radius, 255, -1)
        
        # crop center disk
        center_disk_mask, center_disk_center, center_disk_radius = self._create_inner_mask()
        cv2.circle(center_disk_mask, center_disk_center, int(center_disk_radius), 255, -1)
        
        # Apply the mask to isolate the region inside the ring
        masked_gray_image = cv2.bitwise_and(gray, gray, mask=outer_mask)
        masked_gray_image = cv2.bitwise_not(masked_gray_image, masked_gray_image, mask=center_disk_mask)
        if show_control_print: print("cropped outer frame and center disk\n")
        if test_mode: show_preview(masked_gray_image)
        
        # Convert to Black & White
        mask_thresh = self.configure.get_mask_thresh()
        black_white_image = cv2.threshold(masked_gray_image, mask_thresh, 255, cv2.THRESH_BINARY)[1]
        if show_control_print: print("converted to black and white\n")
        if test_mode: show_preview(black_white_image)

        # Detect the disks using Hough Circle Transform
        self._detect_circles(black_white_image)
        if show_control_print: print(f"detected {self.circles.shape[1]} circles\n")
    
        # Draw detected circles
        frame_with_circles = self._draw_circles(image)
        
        # Print calculations
        self.calculate_radii_statistics(print_stat=print_stat)
        
        if test_mode: show_preview(frame_with_circles)

        return frame_with_circles
    
    def circles_to_bboxes(self):
        """
        Convert circles detected by cv2.HoughCircles to bounding boxes using NumPy.

        Parameters:
            circles (numpy.ndarray): Array of circles with shape (1, N, 3), where each circle is (x, y, radius).

        Returns:
            numpy.ndarray: Array of bounding boxes with shape (N, 4), where each bbox is (x, y, width, height).
        """
        bboxes = np.empty((0, 4))  # Return empty array if no circles
        if self.circles is not None:
            # Circles Shape (N, 3): [x_center, y_center, radius]
            radii = self.circles[0][:, 2]
            top_left_x = self.circles[0][:, 0] - radii
            top_left_y = self.circles[0][:, 1] - radii
            width_height = 2 * radii

            # Stack results into (N, 4): [x, y, width, height]
            bboxes = np.column_stack((top_left_x, top_left_y, width_height, width_height))
        return bboxes

