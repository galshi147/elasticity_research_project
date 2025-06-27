from detection_lib import CenterDisk, Configuration, Detector, cv2, np, Path, PIXEL_TO_MM_RATIO
from matplotlib import pyplot as plt
import pandas as pd
from tqdm import tqdm

BASE_PATH = (Path(__file__).parent / "measurements").resolve()
RAW_DATA = "raw_data"
BW = "bw"
DOT = "dot"
VECTOR_FIELD = "vector_field"
GRAPH = "graph"

# DRIVE_PATH = Path(r"G:\My Drive\מעבדג\פוטואלסטיות(שוב)\מדידות")
DRIVE_PATH = Path(r"G:\My Drive\mabadag\photoelasticity(again)\measurements")

#################################### disk_num ####################################
center_disk_disk_num = CenterDisk()
configure_disk_num = Configuration(
                        outer_crop_w_shitf=-190,
                        outer_crop_h_shift=-150,
                        scale_factor=2.2, 
                        mask_thresh=150,
                        center_disk=center_disk_disk_num)
##################################################################################

#################################### 04.01.25 ####################################
center_disk_040125 = CenterDisk(diameter=26, center_x_shift=-10, center_y_shift=0)
configure_040125 = Configuration(
                        outer_crop_w_shitf=-10,
                        outer_crop_h_shift=0,
                        scale_factor=1.85, 
                        mask_thresh=80,
                        center_disk=center_disk_040125)
##################################################################################

#################################### 21.01.25 ####################################
center_disk_210125 = CenterDisk(diameter=30, center_x_shift=0, center_y_shift=0)
configure_210125 = Configuration(
                        outer_crop_w_shitf=-250,
                        outer_crop_h_shift=-150,
                        scale_factor=2, 
                        mask_thresh=80,
                        center_disk=center_disk_210125)
##################################################################################

#################################### 23.01.25 ####################################
center_disk_230125 = CenterDisk(diameter=34, center_x_shift=0, center_y_shift=-40)
configure_230125 = Configuration(
                        outer_crop_w_shitf=25,
                        outer_crop_h_shift=-100,
                        scale_factor=2.35, 
                        mask_thresh=80,
                        center_disk=center_disk_230125)
##################################################################################

#################################### 26.01.25 ####################################
center_disk_260125 = CenterDisk(diameter=30, center_x_shift=-60, center_y_shift=-20)
configure_260125 = Configuration(
                        outer_crop_w_shitf=-120,
                        outer_crop_h_shift=0,
                        scale_factor=2.28, 
                        mask_thresh=80,
                        center_disk=center_disk_260125)
# center_disk_260125 = CenterDisk(diameter=30, center_x_shift=0, center_y_shift=-40)
# configure_260125 = Configuration(
#                         outer_crop_w_shitf=25,
#                         outer_crop_h_shift=-100,
#                         scale_factor=2.35, 
#                         mask_thresh=80,
#                         center_disk=center_disk_260125)
##################################################################################


CONFIGURES = {
    "disk_num": configure_disk_num,
    "04.01.25": configure_040125,
    "21.01.25": configure_210125,
    "23.01.25": configure_230125,
    "26.01.25": configure_260125
}

class Measure:
    """This class represents a Measurement object, which include the data taken from the lab.
    """
    def __init__(self, measurement_name: str, path_setting: str = 'local', **kwargs) -> None:
        """_summary_

        Args:
            measurement_name (str): The name of the measurement. It should be one of the keys in CONFIGURES, in the format 'dd.mm.yy'.
            path_setting (str, optional): The path setting for the measurement. It can be 'local', 'drive' or 'manual'. Defaults to 'local'.
            **kwargs: Additional keyword arguments. If path_setting is 'manual', a dictionary with the paths must be provided under the key 'manual_path_dict'.
            Raises:
                ValueError: If the measurement name is not in CONFIGURES or if the path_setting is not one of 'local', 'drive', or 'manual'.
        """
        self.name = measurement_name
        self.path_setting = path_setting
        self.drive_path = (DRIVE_PATH / f"{self.name}").resolve()
        self.set_path_config(kwargs.get('manual_path_dict', None))
        self.frame_names = sorted(file.name for file in self.raw_data_path.iterdir() if file.is_file() and file.suffix.lower() == '.jpg')
        self.total_frames_num = sum(1 for _ in self.drive_path.glob("*.jpg"))
        self.detector = Detector(self.raw_data_path, self.frame_names[0], CONFIGURES[measurement_name])
    
    def set_path_config(self, manual_path_dict: dict = None) -> None:

        # Set the path of the measurement to the local disk.
        if self.path_setting == 'local':
            self._set_local_paths()
        elif self.path_setting == 'drive':
            self._set_local_paths()
            self.raw_data_path = self.drive_path
        elif self.path_setting == 'manual':
            self.path = manual_path_dict['path']
            self.raw_data_path = manual_path_dict['raw_data_path']
            self.bw_path = manual_path_dict['bw_path']
            self.dot_path = manual_path_dict['dot_path']
            self.vector_field_path = manual_path_dict['vector_field_path']
            self.graph_path = manual_path_dict['graph_path']
        else:
            raise ValueError("path_setting must be either 'local', 'drive', or 'manual'")
        
    def _set_local_paths(self) -> None:
        self.path = (BASE_PATH / self.name).resolve()
        self.raw_data_path = (self.path / RAW_DATA).resolve()
        self.bw_path = (self.path / BW).resolve()
        self.dot_path = (self.path / DOT).resolve()
        self.vector_field_path = (self.path / VECTOR_FIELD).resolve()
        self.graph_path = (self.path / GRAPH).resolve()
        
    def get_name(self) -> str:
        """Get the name of the measurement.

        Returns:
            str: measurement name
        """
        return self.name

    def get_detector(self) -> Detector:
        """Get the measurement detector object.

        Returns:
            Detector: measurement detector
        """
        return self.detector
    
    def get_path(self) -> Path:
        """Get the path of the measurement.

        Returns:
            Path: path to the folder of the measurement in local disk
        """
        return self.path
    
    def get_drive_path(self) -> Path:
        """Get the path of the measurement raw data in Google Drive.

        Returns:
            Path: path to the folder of the lab images in Google Drive
        """
        return self.drive_path
    
    def get_dot_path(self) -> Path:
        """Get the path of the measurement dot version folder.

        Returns:
            Path: path to the folder of the measurement images in dot version in local disk
        """
        return self.dot_path
    
    def get_vector_field_path(self) -> Path:
        """Get the path of the measurement vector field folder.

        Returns:
            Path: path to the folder of the measurement vector field files in local disk
        """
        return self.vector_field_path
    
    def get_graph_path(self) -> Path:
        """Get the path of the measurement graph folder.

        Returns:
            Path: path to the folder of the measurement graphs in local disk
        """
        return self.graph_path

    def get_frame_names(self) -> list:
        """Get the names of the frames in the measurement.

        Returns:
            list: list of frame names in format 'DSC_####.jpg'
        """
        return self.frame_names
    
    def get_total_frames_num(self) -> int:
        """Get the total number of frames in the measurement (using Google drive folder).

        Returns:
            int: total number of frames captured in lab for this measurement
        """
        return self.total_frames_num
    
    def get_center_disk_radius(self) -> float:
        """Get the radius of the center disk.

        Returns:
            float: center disk radius in pixels for this measurement
        """
        return self.detector.get_center_disk_radius()
    
    def save_bw_version(self, frame_name: str) -> np.ndarray:
        """_summary_

        Args:
            frame_name (str): _description_

        Returns:
            np.ndarray: _description_
        """
        # prev_capture = self.detector.get_capture()
        # self.detector.change_capture(frame_name)
        config = self.detector.get_configure()
        
        # Load frame
        frame_path = (self.raw_data_path / frame_name).resolve()
        frame = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)

        # Convert the image to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # crop the outer frame
        outer_mask, outer_crop_center, outer_crop_radius = self.detector._create_outer_crop_mask(gray)
        cv2.circle(outer_mask, outer_crop_center, outer_crop_radius, 255, -1)
        
        #crop center disk
        center_disk_mask, center_disk_center, center_disk_radius = self.detector._create_inner_mask(outer_crop_center, gray)
        cv2.circle(center_disk_mask, center_disk_center, int(center_disk_radius), 255, -1)
        
        # Apply the mask to isolate the region inside the ring
        masked_gray_image = cv2.bitwise_and(gray, gray, mask=outer_mask)
        masked_gray_image = cv2.bitwise_not(masked_gray_image, masked_gray_image, mask=center_disk_mask)
        
        # Convert to Black & White
        mask_thresh = config.get_mask_thresh()
        black_white_image = cv2.threshold(masked_gray_image, mask_thresh, 255, cv2.THRESH_BINARY)[1]

        # Save black and white version
        # self.detector.set_capture(prev_capture)
        output_path = (self.bw_path / frame_name).resolve()
        cv2.imwrite(str(output_path), black_white_image)
        return black_white_image

    def save_dot_version(self, frame_name: str):
        # prev_capture = self.detector.get_capture()
        # self.detector.change_capture(frame_name)
        self.detector.detect_disks()
        disk_pos = self.detector.get_circles_positions()
        height, width = self.detector.get_frame_sizes()
        # Create a black image
        dotted_image = np.zeros((height, width))
        for center in disk_pos:
            dotted_image = cv2.circle(dotted_image, center, 3, 255, -1)
        # save dotted version
        # self.detector.set_capture(prev_capture)
        output_path = (self.dot_path / frame_name).resolve()
        cv2.imwrite(str(output_path), dotted_image)
        return dotted_image
           
    def create_bw_versions(self):
        # create dotted versions
        for frame in tqdm(self.frame_names):
            self.save_bw_version(frame)
    
    def create_dot_versions(self):
        # create dotted versions
        for frame in tqdm(self.frame_names):
            self.save_dot_version(frame)

    def test_detector(self, save_fig=False, control_print=False, print_stat=False):
        """Test the detector on the first frame of the measurement."""
        frame_with_circles = self.detector.detect_disks(test_mode=True, show_control_print=control_print, print_stat=print_stat)
        if save_fig: cv2.imwrite(str((self.path / "tests").resolve()) + f"/{self.detector.get_frame_name()[0:-4]}.png", frame_with_circles)
    
    def get_measure_statistics(self):
        self.detector.set_frame(self.frame_names[0])
        self.detector.detect_disks(test_mode=False)
        return self.detector.calculate_radii_statistics()

    def calculate_area_fraction_change(self):
        area_fracs = []
        for frame_name in self.frame_names:
            self.detector.change_capture(frame_name)
            self.detector.detect_disks(test_mode=False)
            data = self.detector.calculate_radii_statistics()
            area_fracs.append(data["areal_fraction"])
        return np.arange(len(self.frame_names)), np.array(area_fracs)

    def plot_area_fraction_change(self):
        frames, area_fracs = self.calculate_area_fraction_change()
        fig, ax = plt.subplots()
        ax.plot(frames, area_fracs)
        ax.set_xlabel("frames")
        ax.set_ylabel("area fraction [%]")
        ax.set_title(f"Area fraction changes in frames of {self.name}")
        plt.show()

    def save_measure_data(self, source='local'):
        if not (self.path_setting == 'manual' or source == self.path_setting):
            raise ValueError("source must be either 'local' or 'drive' and must match the path_setting of the Measure object")
        df_data = []
        if source == 'local': frames_list = self.frame_names
        elif source == 'drive': frames_list = sorted(file.name for file in self.drive_path.iterdir() if file.is_file() and file.suffix.lower() == '.jpg')
        elif source == 'manual': frames_list = sorted(file.name for file in self.raw_data_path.iterdir() if file.is_file() and file.suffix.lower() == '.jpg')
        else: raise ValueError("source must be either 'local' or 'drive'")
        for frame_name in tqdm(frames_list):
            self.detector.set_frame(frame_name)
            self.detector.detect_disks()
            centers = self.detector.get_circles_positions() # in pixels
            radii = self.detector.get_circles_radii() # in pixels
            statistics = self.detector.calculate_radii_statistics()
            df_data.append({"frame": frame_name,
                            "centers": centers,
                            "radii": radii,
                            "statistic": statistics
                            })
        df = pd.DataFrame(df_data)
        save_path = (self.path / f"data_{source}_{self.name}.pkl").resolve()
        df.to_pickle(save_path)


    def load_measure_data(self, source='local'):
        if source not in ["local", "drive", "manual"]:
            raise ValueError("source must be either 'local', 'drive' or 'manual")
        load_path = (self.path / f"data_{source}_{self.name}.pkl").resolve()
        return pd.read_pickle(load_path)


