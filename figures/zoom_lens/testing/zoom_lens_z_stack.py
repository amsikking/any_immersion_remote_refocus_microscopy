import numpy as np
import time

from scipy.ndimage import gaussian_filter
from tifffile import imread, imwrite

import asi_MS_2000_500_CP
import pco_pixelfly_usb
import zoom_lens

ms = asi_MS_2000_500_CP.Controller(
    which_port='COM6',
    axes=('Z',),
    lead_screws=('F',),
    axes_min_mm=(-2,),
    axes_max_mm=( 2,),
    verbose=False)

camera = pco_pixelfly_usb.Camera(verbose=False, very_verbose=False)
camera.apply_settings(num_images=1, exposure_us=3000, image_size='max')

zoom_lens = zoom_lens.Zoom_lens(
    stage1_port='COM3',
    stage2_port='COM5',
    stage3_port='COM4',
    verbose=False)

config_f_mm = np.linspace(132.5, 150, 8)
z_steps_um = np.linspace(0, 1000, 41) # 25um steps
images = np.zeros(
    (len(z_steps_um), camera.height_px, camera.width_px), 'uint16')

for f_mm in config_f_mm:
    zoom_lens.set_focal_length_mm(f_mm)
    for i, z in enumerate(z_steps_um):
        ms.move_um((float(z),), relative=False)
        time.sleep(0.5) # mechanical settle time
        images[i,:,:] = camera.record_to_memory()
    imwrite('images/f_mm_%0.1f.tif'%f_mm, images, imagej=True)
    smooth_images = gaussian_filter(images, sigma=1)
    focused_image_num = np.unravel_index(
        np.argmax(smooth_images), images.shape)[0]
    print('f_mm', f_mm)
    print('focused_z_um', z_steps_um[focused_image_num])

zoom_lens.close()
ms.move_um((0,), relative=False)        # home
ms.close()
