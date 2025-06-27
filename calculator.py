import numpy as np
from measurements_detectors import Measure
from detection_lib import LARGE_DISK_RADIUS, PIXEL_TO_MM_RATIO

class Calculator():
    def __init__(self, measure: Measure):
        self.measure = measure
        self.measure_center_disk_rad = self.measure.get_center_disk_radius()
    
    def _calculate_ring_average_movement(self, r, radial_displacement, tangent_displacement, rings_num):
            min_rad = self.measure_center_disk_rad
            max_rad =  np.max(r)
            rings_num = rings_num
            dr = (max_rad + 1 - min_rad) / rings_num
            radii = np.linspace(min_rad, max_rad, rings_num)
            rad_disp = np.array([])
            tan_disp = np.array([])
            for ring in radii:
                mask = (ring < r) & (r < (ring + dr))
                if np.any(mask):
                    rad_disp = np.append(rad_disp, np.mean(radial_displacement[mask]))
                    tan_disp = np.append(tan_disp, np.mean(tangent_displacement[mask]))
                else: # avoid Nan values in case mask is empty
                    rad_disp = np.append(rad_disp, 0)
                    tan_disp = np.append(tan_disp, 0)
            
            return radii, dr, rad_disp, tan_disp


    def calculate_displacement_field(self, x, y, u, v, rings_num=100):
            # Filter out points with large magnitude
            magnitude = np.sqrt(u**2 + v**2) / PIXEL_TO_MM_RATIO
            mask = magnitude <= LARGE_DISK_RADIUS / 2
            x, y, u, v = x[mask], y[mask], u[mask], v[mask]
            # Center the coordinates
            x0, y0 = np.mean(x), np.mean(y)
            rx = x - x0
            ry = y - y0
            r = np.sqrt(rx**2 + ry**2)
            # Avoid division by zero
            r[r == 0] = np.nan

            # Radial unit vector components
            r_hat_x = rx / r
            r_hat_y = ry / r
            # Compute radial component
            radial_displacement = u * r_hat_x + v * r_hat_y

            # Tangent unit vector components
            theta_hat_x = -r_hat_y
            theta_hat_y = r_hat_x
            # Compute tangent component
            tangent_displacement = u * theta_hat_x + v * theta_hat_y

            radii, dr, rad_disp, tan_disp = self._calculate_ring_average_movement(r, radial_displacement,
                                                                                   tangent_displacement, rings_num)

            return radii, dr, rad_disp, tan_disp
    