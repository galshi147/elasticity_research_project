import time
import cv2
import os
from pathlib import Path
from tqdm import tqdm
from detection_lib import Detector
from measurements_detectors import CONFIGURES

    
def _find_diffs_helper(source_path, target_path, base_image, image_name):
    path = source_path + image_name
    other_image = cv2.imread(path)

    # Ensure the images are the same size
    if base_image.shape != other_image.shape:
        other_image = cv2.resize(other_image, (base_image.shape[1], base_image.shape[0]))

    # Compute the absolute difference
    difference = cv2.absdiff(base_image, other_image)

    # Save or display the result
    cv2.imwrite(target_path + image_name + "_diff.jpg", difference)

def find_diffs(self):
    # Get from user the folder with the source files
    aquisition_name = input("insert source folder name: ")
    base_image_name = input("insert base image name: ")
    source_path = self.base_path + aquisition_name + "\\"
    target_path = self.base_path + aquisition_name + "_diffs\\"
    
    # Load the base image
    base_image = cv2.imread(source_path + base_image_name)
    
    # in order to show image in resizeable window:
    # cv2.namedWindow("base", cv2.WINDOW_NORMAL)
    # cv2.imshow("base", base_image)
    # cv2.waitKey(0)

    image_names = [name for name in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, name))][1::]
    for image_name in tqdm(image_names):
        _find_diffs_helper(source_path, target_path, base_image, image_name)

def count_disks_using_disk_num_sample():
    name = "disk_num"
    path = (Path(__file__).parent / "measurements").resolve()
    detector = Detector(path, name, CONFIGURES[name])
    detector.detect_disks(test_mode=True)

def create_clip(frames_source_path, output_path, video_name_without_extension, fps): 
    start_time = time.time()
    frames = [name for name in os.listdir(frames_source_path) if os.path.isfile(os.path.join(frames_source_path, name))]
    frame_height, frame_width, _ =  cv2.imread(frames_source_path + frames[0], cv2.IMREAD_COLOR).shape
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video = cv2.VideoWriter(f'{output_path}/{video_name_without_extension}.mp4', fourcc, fps, (frame_width, frame_height))
    for frame_name in tqdm(frames):
        frame = cv2.imread(frames_source_path + frame_name, cv2.IMREAD_COLOR)
        video.write(frame)
    video.release()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Script \"{video_name_without_extension}\" runtime: {elapsed_time:.2f} seconds")


def create_product_name(measure_name: str, first_frame_name: str, second_frame_name: str, source_name: str) -> str:
    """create a product name for the data to be saved
    The name is in the format: measure_name_first_frame_name_second_frame_name_source_name

    Args:
        measure_name (str): name of the measure in formart 'dd.mm.yy'
        first_frame_name (str): frame name in format 'DSC_####.jpg'
        second_frame_name (str): frame name in format 'DSC_####.jpg'
        source_name (str): which module generated the data (such as 'Kdt', 'Piv', etc.)

    Returns:
        str: name to save the data with
    """
    return f"{measure_name}_{first_frame_name[0:-4]}_{second_frame_name[0:-4]}_{source_name}"
