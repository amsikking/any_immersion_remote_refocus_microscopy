import time
import os
import numpy as np
from datetime import datetime
from tifffile import imread, imwrite

import ht_sols_microscope as htsols

if __name__ == '__main__': # required block for sols_microscope
    # Create scope:
    scope = htsols.Microscope(max_allocated_bytes=100e9, ao_rate=1e4)
    scope.apply_settings( # Mandatory call
        channels_per_slice=("LED",),# ('LED','405','488','561','640')
        power_per_channel=(10,),    # match channels 0-100% i.e. (5,0,20,30,100)
        filter_wheel_position=0,
        ## filter wheel options:        0:blocked,      1:open
        # 2:ET445/58M,  3:ET525/50M,    4:ET600/50M,    5:ET706/95M
        # 6:ZETquadM,   7:(available)   8:(available)   9:(available)
        illumination_time_us=1e3,
        height_px=248,
        width_px=1060,
        voxel_aspect_ratio=4,
        scan_range_um=100,
        volumes_per_buffer=1,
        focus_piezo_z_um=(0,'relative'),
        XY_stage_position_mm=(0,0,'relative'),
        ).join()

    # Create postprocessor for software autofocus:
    dataz = htsols.DataZ()

    # Make folder name for data":
    folder_label = 'sols_acquisition_template'
    dt = datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S_000_')
    folder_name = dt + folder_label    

    # Run acquisition: (tzcyx)
    for i in range(2):
        scope.snoutfocus()
        # Multi-color acquisition:
        filename488 = '488_%06i.tif'%i
        scope.apply_settings(illumination_time_us=10e3,
                             channels_per_slice=('488',),
                             power_per_channel=(1,),
                             filter_wheel_position=7)
        scope.acquire(display=True,
                      filename=filename488,
                      folder_name=folder_name,
                      description='488 something...',
                      delay_s=0)
        filename561 = '561_%06i.tif'%i
        scope.apply_settings(illumination_time_us=10e3,
                             channels_per_slice=('561',),
                             power_per_channel=(5,),
                             filter_wheel_position=8)
        scope.acquire(display=True,
                      filename=filename561,
                      folder_name=folder_name,
                      description='561 something...',
                      delay_s=0)
        # Software autofocus:
        scope.finish_all_tasks() # must finish before looking at preview!
        if i == 0:
            first_preview = imread(folder_name + '\preview\\' + filename561)
            first_z_um = dataz.estimate(first_preview,
                                        scope.height_px,
                                        scope.width_px,
                                        scope.preview_line_px,
                                        scope.preview_crop_px,
                                        scope.timestamp_mode)
        last_preview = imread(folder_name + '\preview\\' + filename561)
        last_z_um = dataz.estimate(last_preview,
                                   scope.height_px,
                                   scope.width_px,
                                   scope.preview_line_px,
                                   scope.preview_crop_px,
                                   scope.timestamp_mode)
        z_change_um = last_z_um - first_z_um
        print('Sample z-axis change um:', z_change_um)
        scope.apply_settings(focus_piezo_z_um=(z_change_um, 'relative'))        
        time.sleep(0) # optional time delay
    scope.close()
