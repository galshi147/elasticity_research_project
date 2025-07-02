from openpiv import tools, pyprocess, validation, filters, scaling
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from detection_lib import PIXEL_TO_MM_RATIO
from measurements_detectors import Measure
from project_tools import create_product_name


class Piv:

    def __init__(self, measure: Measure):
        self.measure = measure
        self.measure_name = self.measure.get_name()
        self.dot_path = self.measure.get_dot_path()
        self.detector = self.measure.get_detector()
        self.vector_field_path = self.measure.get_vector_field_path()
        self.graph_path = self.measure.get_graph_path()
        self.source = Piv.__name__

    def get_source_name(self):
        return self.source

    def product_name(self, first_frame_name, second_frame_name):
        return create_product_name(self.measure_name, first_frame_name, second_frame_name, self.source)
    
    def calculate_two_frames_vector_field(self, first_frame_name, second_frame_name):
        first_frame = tools.imread(f"{self.dot_path}/{first_frame_name}")
        last_frame = tools.imread(f"{self.dot_path}/{second_frame_name}")

        winsize = 64 #32 # pixels, interrogation window size in frame A
        searchsize = 76 #38  # pixels, search area size in frame B
        overlap = 34 #17 # pixels, 50% overlap
        dt = 1 #252000 # sec, time interval between the two frames

        u0, v0, sig2noise = pyprocess.extended_search_area_piv(
            first_frame.astype(np.int32),
            last_frame.astype(np.int32),
            window_size=winsize,
            overlap=overlap,
            dt=dt,
            search_area_size=searchsize,
            sig2noise_method='peak2peak',)
        
        x, y = pyprocess.get_coordinates(
        image_size=first_frame.shape,
        search_area_size=searchsize,
        overlap=overlap,)

        invalid_mask = validation.sig2noise_val(
        sig2noise,
        threshold = 1.05,)

        u2, v2 = filters.replace_outliers(
        u0, v0,
        invalid_mask,
        method='localmean',
        max_iter=3,
        kernel_size=3,)

        # convert x,y to mm
        # convert u,v to mm/sec
        x, y, u3, v3 = scaling.uniform(
            x, y, u2, v2,
            scaling_factor = PIXEL_TO_MM_RATIO,  # pixels/millimeter
        )

        # 0,0 shall be bottom left, positive rotation rate is counterclockwise
        x, y, u3, v3 = tools.transform_coordinates(x, y, u3, v3)

        product_name = self.product_name(first_frame_name, second_frame_name)
        tools.save(f"{str(self.vector_field_path)}/{product_name}.txt" , x, y, u3, v3, invalid_mask)
        
        return x, y, u3, v3
    

    def plot_vector_field_ascii(self, first_frame_name, second_frame_name):
        product_name = self.product_name(first_frame_name, second_frame_name)
        fig, ax = plt.subplots(figsize=(8,8))
        ax.set_title(f"{self.measure_name}\n\ndisplacement field of: {first_frame_name[0:-4]} & {second_frame_name[0:-4]}", pad=15)
        tools.display_vector_field(
            (self.vector_field_path / f"{product_name}.txt").resolve(),
            ax=ax, scaling_factor = 16,
            scale=50, # scale defines here the arrow length
            width=0.0035, # width is the thickness of the arrow
            on_img=True, # overlay on the image
            image_name= f"{self.dot_path}/{first_frame_name}",
            show_invalid=False)


    def run_all_vector_fields(self, source='local'):
        if source == 'local': frame_names = self.measure.get_frame_names()
        elif source == 'drive': frame_names = sorted(file.name for file in self.measure.get_drive_path().iterdir() if file.is_file() and file.suffix.lower() == '.jpg')
        else: raise ValueError("source must be either 'local' or 'drive'")
        for i in tqdm(range(len(frame_names))):
            for j in range(i+1, len(frame_names)):
                first_frame_name, second_frame_name = frame_names[i], frame_names[j]
                self.calculate_two_frames_vector_field(first_frame_name, second_frame_name)
