from measurements_detectors import Measure
from piv_method import Piv
from visualization import Plotter
from calculator import Calculator
from kdt_method import Kdt
from pathlib import Path

def program1():
    m1 = Measure("23.01.25")
    piv1 = Piv(m1)
    plotter1 = Plotter(m1, piv1.get_source_name())
    first = "DSC_0001.jpg"
    second = "DSC_0127.jpg"
    half = "DSC_0925.jpg"
    last = "DSC_1598.jpg"
    # p.calculate_two_frames_vector_field(first, second)
    
    save = True
    show = False
    plotter1.plot_displacement_by_rings(first, second, save=save, show=show)
    plotter1.plot_displacement_by_rings(first, half, save=save, show=show)
    plotter1.plot_displacement_by_rings(half, last, save=save, show=show)
    plotter1.plot_displacement_by_rings(first, last, save=save, show=show)
    
    # p.plot_vector_field_ascii(first, second)
    # p.plot_displacement_by_rings(first, second, show=True)
    # m.plot_area_fraction_change()

    m2 = Measure("26.01.25")
    piv2 = Piv(m2)
    plotter2 = Plotter(m2, piv2.get_source_name())
    first2 = "DSC_0001.jpg"
    second2 = "DSC_0101.jpg"
    half2 = "DSC_0401.jpg"
    last2 = "DSC_0725.jpg"

    save = True
    show = False
    plotter2.plot_displacement_by_rings(first2, second2, save=save, show=show)
    plotter2.plot_displacement_by_rings(first2, half2, save=save, show=show)
    plotter2.plot_displacement_by_rings(half2, last2, save=save, show=show)
    plotter2.plot_displacement_by_rings(first2, last2, save=save, show=show)

    # p2.plot_vector_field_ascii(first2, second2)
    # p2.plot_vector_field_ascii(first2, half2)
    # p2.plot_vector_field_ascii(half2, last2)
    # p2.plot_vector_field_ascii(first2, last2)

def program2():
    m1 = Measure("23.01.25")
    piv1 = Piv(m1)
    plotter1 = Plotter(m1, piv1.get_source_name())
    first = "DSC_0001.jpg"
    second = "DSC_0127.jpg"

    plotter1.plot_vector_field(first, second)

def program3():
    m = Measure("26.01.25")
    pt = Plotter(m, "Piv")
    c = Calculator(m)
    first = "DSC_0001.jpg"
    second = "DSC_0725.jpg"
    k = Kdt(m)
    k.save_vector_field(first, second)
    pt2= Plotter(m, "Kdt")
    data = pt2.load_vector_field(first, second)
    x, y, u, v = data['x'], data['y'], data['u'], data['v']
    radii, dr, rad_disp, tan_disp = c.calculate_displacement_field(x, y, u, v, rings_num=100)
    pt2.plot_vector_field(first, second, add_rings=True, radii=radii, dr=dr)

def program4():
    m1 = Measure("23.01.25")
    m2 = Measure("26.01.25")
    m1.save_measure_data(source='local')
    m2.save_measure_data(source='local')
    m1.save_measure_data(source='drive')
    m2.save_measure_data(source='drive')

def program5():
    m1 = Measure("23.01.25")
    k1 = Kdt(m1)
    k1.run_all_vector_fields(source='drive')
    
    m2 = Measure("26.01.25")
    k2 = Kdt(m2)
    k2.run_all_vector_fields(source='drive')

def program6():
    m = Measure("23.01.25")
    k = Kdt(m)
    p = Plotter(m, 'Kdt')
    c = Calculator(m)
    # k.run_all_vector_fields(source='local')
    frame1 = "DSC_0001.jpg"
    frame2 = "DSC_0127.jpg"
    data = p.load_vector_field(frame1, frame2)
    x, y, u, v = data['x'], data['y'], data['u'], data['v']
    radii, dr, rad_disp, tan_disp = c.calculate_displacement_field(x, y, u, v, rings_num=100)
    p.plot_displacement_by_rings(frame1, frame2, radii=radii, rad_disp=rad_disp, tan_disp=tan_disp, show=True)

def test_drive_connection():
    m = Measure("23.01.25", path_setting='drive')
    print(m.get_drive_path())
    print(m.get_frame_names())
    print(m.get_total_frames_num())

def test_detection(m: Measure, start=0, stop=2):
    frame_names = m.get_frame_names()[start:stop]
    detector = m.detector
    for frame in frame_names:
        detector.set_frame(frame)
        detector.detect_disks(test_mode=True , show_control_print=False, print_stat=True)


def count_circles_detected():
    m = Measure("26.01.25", path_setting="drive")
    data_m = m.load_measure_data(source='drive')
    num = []
    total_num = m.get_total_frames_num()
    for i in range(total_num):
        num.append(len(data_m['centers'][i]))
    print(num)





 # frame1 = f"DSC_{self.frame1.value():04d}.jpg"
        # frame2 = f"DSC_{self.frame2.value():04d}.jpg"
        # self.vector_field = self.load_vector_field_data(frame1, frame2)
        # x, y, u, v = self.vector_field['x'], self.vector_field['y'], self.vector_field['u'], self.vector_field['v']
        # radii, dr, rad_disp, tan_disp = self.calculate_displacement_stats(x, y, u, v)
        
        # # Clear previous plots
        # self.ax_vf.clear()
        # self.ax_av.clear()
        

        # # Remove the colorbar if it exists
        # if self.colorbar is not None:
        #     try:
        #         if self.colorbar.ax in self.figure.axes:
        #             self.figure.delaxes(self.colorbar.ax)
        #     except Exception as e:
        #         print(f"Could not remove colorbar axes: {e}")
        #     self.colorbar = None

        
        # # Plot the updated data
        # self.ax_av = self.plotter.plot_displacement_by_rings(self.ax_av, frame1, frame2, radii, rad_disp, tan_disp)
        # self.ax_vf, self.colorbar = self.plotter.plot_vector_field(self.ax_vf, x, y, u, v, frame1, frame2, add_rings=self.add_rings, radii=radii, dr=dr)


    p_dict = {
        "path": Path(r"C:\university\Elasticity_Project\code\measurements\26.01.25"),
    "raw_data_path": Path(r"C:\26.01.25"),
    "bw_path": Path(r"C:\university\Elasticity_Project\code\measurements\26.01.25\bw"),
    "dot_path": Path(r"C:\university\Elasticity_Project\code\measurements\26.01.25\dot"),
    "vector_field_path": Path(r"C:\university\Elasticity_Project\code\measurements\26.01.25\vector_field"),
    "graph_path": Path(r"C:\university\Elasticity_Project\code\measurements\26.01.25\graph")
    }