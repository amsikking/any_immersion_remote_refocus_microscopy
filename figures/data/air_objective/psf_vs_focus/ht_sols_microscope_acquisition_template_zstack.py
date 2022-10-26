import time
import os
import numpy as np
from datetime import datetime
from tifffile import imread, imwrite

import ht_sols_microscope as htsols

if __name__ == '__main__': # required block for sols_microscope
    # Create scope:
    scope = htsols.Microscope(max_allocated_bytes=100e9, ao_rate=1e4)
    scope.snoutfocus_controller.set_voltage(75/2)
    
    scope.apply_settings( # Mandatory call
        channels_per_slice=("488",),# ('LED','405','488','561','640')
        power_per_channel=(100,),   # match channels 0-100% i.e. (5,0,20,30,100)
        filter_wheel_position=3,
        ## filter wheel options:        0:blocked,      1:open
        # 2:ET445/58M,  3:ET525/50M,    4:ET600/50M,    5:ET706/95M
        # 6:ZETquadM,   7:(available)   8:(available)   9:(available)
        illumination_time_us=10e3,
        height_px=750,
        width_px=1500,
        voxel_aspect_ratio=1,
        scan_range_um=250,
        volumes_per_buffer=1,
        focus_piezo_z_um=(-20,'relative'),
        XY_stage_position_mm=(0,0,'relative'),
        ).join()

    # Make folder name for data":
    folder_label = 'sols_acquisition_zstack'
    dt = datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S_000_')
    folder_name = dt + folder_label    

    # Run acquisition: (tzcyx)
    for i in range(40):
        # Multi-color acquisition:
        scope.acquire(filename='z_%06i.tif'%i, folder_name=folder_name)
        scope.apply_settings(focus_piezo_z_um=(1, 'relative')).join()
    scope.close()
