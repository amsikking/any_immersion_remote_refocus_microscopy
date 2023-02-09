# Imports from the python standard library:
import time
import os
from datetime import datetime
import atexit
import queue

# Third party imports, installable via pip:
import numpy as np
from scipy.ndimage import zoom, rotate, gaussian_filter1d
from tifffile import imread, imwrite

# Our code, one .py file per module, copy files to your local directory:
try:
    import pco_edge42_cl        # github.com/amsikking/pco_edge42_cl
    import ni_PCIe_6738         # github.com/amsikking/ni_PCIe_6738
    import sutter_Lambda_10_3   # github.com/amsikking/sutter_Lambda_10_3
    import pi_C_867_2U2         # github.com/amsikking/pi_C_867_2U2
    import pi_E_709_1C1L        # github.com/amsikking/pi_E_709_1C1L
    import thorlabs_MDT694B     # github.com/amsikking/thorlabs_MDT694B
    import concurrency_tools as ct              # github.com/AndrewGYork/tools
    from napari_in_subprocess import display    # github.com/AndrewGYork/tools
except Exception as e:
    print('sols_microscope.py -> One or more imports failed')
    print('sols_microscope.py -> error =',e)

# SOLS optical configuration (edit as needed):
M1 = 200 / 5; Mscan = 100 / 100; M2 = 10 / 300; M3 = 200 / 9
MRR = M1 * Mscan * M2; Mtot = MRR * M3;
camera_px_um = 6.5; sample_px_um = camera_px_um / Mtot
tilt = np.deg2rad(50)

class Microscope:
    def __init__(self,
                 max_allocated_bytes,   # Limit of available RAM for machine
                 ao_rate,               # slow ~1e3, medium ~1e4, fast ~1e5
                 name='SOLS v1.1',
                 verbose=True):
        self.name = name
        self.verbose = verbose
        if self.verbose: print("%s: opening..."%self.name)
        self.unfinished_tasks = queue.Queue()
        slow_fw_init = ct.ResultThread(
            target=self._init_filter_wheel).start() #~5.3s
        slow_camera_init = ct.ResultThread(
            target=self._init_camera).start()       #~3.6s
        slow_snoutfocus_init = ct.ResultThread(
            target=self._init_snoutfocus).start()   #1s
        slow_focus_init = ct.ResultThread(
            target=self._init_focus_piezo).start()  #~0.6s
        slow_stage_init = ct.ResultThread(
            target=self._init_XY_stage).start()     #~0.4s
        self._init_display()                        #~1.3s
        self._init_datapreview()                    #~0.8s
        self._init_ao(ao_rate)                      #~0.2s
        slow_stage_init.get_result()
        slow_focus_init.get_result()
        slow_snoutfocus_init.get_result()
        slow_camera_init.get_result()
        slow_fw_init.get_result()
        self.max_allocated_bytes = max_allocated_bytes
        self.illumination_sources = ( # configure as needed
            'LED', '405', '488', '561', '640', '405_on_during_rolling')        
        self.max_bytes_per_buffer = (2**31) # legal tiff
        self.max_data_buffers = 4 # camera, preview, display, filesave
        self.max_preview_buffers = self.max_data_buffers
        self.preview_line_px = 10 # line thickness for previews
        # The pco_edge42_cl has unreliable pixel rows at the top and bottom,
        # so for clean previews it's best to remove them:
        self.preview_crop_px = 3 # crop top and bottom pixel rows for previews
        self.num_active_data_buffers = 0
        self.num_active_preview_buffers = 0
        self.timestamp_mode = "binary+ASCII"
        self.camera._set_timestamp_mode(self.timestamp_mode) # default on
        self._settings_applied = False
        if self.verbose: print("\n%s: -> open and ready."%self.name)

    def _init_ao(self, ao_rate):
        self.names_to_voltage_channels = {
            '405_TTL': 0,
            '405_power': 1,
            '445_TTL': 2,
            '445_power': 3,            
            '488_TTL': 4,
            '488_power': 5,
            '561_TTL': 6,
            '561_power': 7,
            '640_TTL': 8,
            '640_power': 9,
            'LED_power': 10,
            'camera': 11,
            'galvo': 12,
            'snoutfocus_piezo': 13,
            'snoutfocus_shutter': 14,
            'LSx_BFP': 16,
            'LSy_BFP': 17,
            'LSx_IMG': 18,
            'LSy_IMG': 19,}
        if self.verbose: print("\n%s: opening ao card..."%self.name)
        self.ao = ni_PCIe_6738.DAQ(
            num_channels=20, rate=ao_rate, verbose=False)
        if self.verbose: print("\n%s: -> ao card open."%self.name)
        atexit.register(self.ao.close)

    def _init_filter_wheel(self):
        if self.verbose: print("\n%s: opening filter wheel..."%self.name)
        self.filter_wheel = sutter_Lambda_10_3.Controller(
            which_port='COM7', verbose=False)
        if self.verbose: print("\n%s: -> filter wheel open."%self.name)        
        self.filter_wheel_position = 0
        atexit.register(self.filter_wheel.close)

    def _init_camera(self):
        if self.verbose: print("\n%s: opening camera..."%self.name)
        self.camera = ct.ObjectInSubprocess(
            pco_edge42_cl.Camera, verbose=False, close_method_name='close')
        if self.verbose: print("\n%s: -> camera open."%self.name)

    def _init_snoutfocus(self):
        if self.verbose: print("\n%s: opening snoutfocus piezo..."%self.name)
        self.snoutfocus_controller = thorlabs_MDT694B.Controller(
            which_port='COM4', verbose=False)
        if self.verbose: print("\n%s: -> snoutfocus piezo open."%self.name)        
        atexit.register(self.snoutfocus_controller.close)

    def _init_focus_piezo(self):
        if self.verbose: print("\n%s: opening focus piezo..."%self.name)
        self.focus_piezo = pi_E_709_1C1L.Controller(
            which_port='COM3', z_min_um=0, z_max_um=800, verbose=False)
        if self.verbose: print("\n%s: -> focus piezo open."%self.name)
        atexit.register(self.focus_piezo.close)

    def _init_XY_stage(self):
        if self.verbose: print("\n%s: opening XY stage..."%self.name)        
        self.XY_stage = pi_C_867_2U2.Controller(
            which_port='COM6', verbose=False)
        if self.verbose: print("\n%s: -> XY stage open."%self.name)
        atexit.register(self.XY_stage.close)

    def _init_datapreview(self):
        if self.verbose: print("\n%s: opening datapreview..."%self.name) 
        self.datapreview = ct.ObjectInSubprocess(DataPreview)
        if self.verbose: print("\n%s: -> datapreview open."%self.name)        

    def _init_display(self):
        if self.verbose: print("\n%s: opening display..."%self.name)  
        self.display = display()
        if self.verbose: print("\n%s: -> display open."%self.name) 

    def _check_memory(self):        
        memory_exceeded = False
        # Data:
        self.images = (self.volumes_per_buffer *
                       len(self.channels_per_slice) *
                       self.slices_per_volume)
        self.bytes_per_data_buffer = (
            2 * self.images * self.height_px * self.width_px)
        if self.bytes_per_data_buffer > self.max_bytes_per_buffer:
            print("\n%s: ***WARNING*** -> settings rejected"%self.name +
                  " (bytes_per_data_buffer > max)")
            print("%s: -> reduce settings"%self.name +
                  " or increase 'max_bytes_per_buffer'")
            memory_exceeded = True
        # Preview:
        preview_shape = DataPreview.shape(self.volumes_per_buffer,
                                          self.slices_per_volume,
                                          len(self.channels_per_slice),
                                          self.height_px,
                                          self.width_px,
                                          self.scan_step_size_px,
                                          self.preview_line_px,
                                          self.preview_crop_px,
                                          self.timestamp_mode)
        self.bytes_per_preview_buffer = 2 * int(np.prod(preview_shape))
        if self.bytes_per_preview_buffer > self.max_bytes_per_buffer:
            print("\n%s: ***WARNING*** -> settings rejected"%self.name +
                  " (bytes_per_preview_buffer > max)")
            print("%s: -> reduce settings"%self.name +
                  " or increase 'max_bytes_per_buffer'")
            memory_exceeded = True
        # Total:
        self.total_bytes = (
            self.bytes_per_data_buffer * self.max_data_buffers +
            self.bytes_per_preview_buffer * self.max_preview_buffers)
        if self.total_bytes > self.max_allocated_bytes:
            print("\n%s: ***WARNING*** -> settings rejected"%self.name +
                  " (total_bytes > max)")
            print("%s: -> reduce settings"%self.name +
                  " or increase 'max_allocated_bytes'")
            memory_exceeded = True
        return memory_exceeded

    def _calculate_voltages(self):
        n2c = self.names_to_voltage_channels # nickname
        # Timing information:
        exposure_px = self.ao.s2p(1e-6 * self.camera.exposure_us)
        rolling_px =  self.ao.s2p(1e-6 * self.camera.rolling_time_us)
        jitter_px = max(self.ao.s2p(30e-6), 1)
        period_px = max(exposure_px, rolling_px) + jitter_px
        # Galvo voltages:
        galvo_volts_per_um = -1.146 / 100 # calibrated using graticule
        galvo_scan_volts = galvo_volts_per_um * self.scan_range_um
        galvo_voltages = np.linspace(
            - galvo_scan_volts/2, galvo_scan_volts/2, self.slices_per_volume)
        # Calculate voltages:
        voltages = []
        for volumes in range(self.volumes_per_buffer):
            # TODO: either bidirectional volumes, or smoother galvo flyback
            for _slice in range(self.slices_per_volume):
                for channel, power in zip(self.channels_per_slice,
                                          self.power_per_channel):
                    v = np.zeros((period_px, self.ao.num_channels), 'float64')
                    v[:rolling_px, n2c['camera']] = 5 # falling edge-> light on!
                    v[:, n2c['galvo']] = galvo_voltages[_slice]
                    light_on_px = rolling_px
                    if channel in ('405_on_during_rolling',): light_on_px = 0
                    if channel != 'LED': # i.e. laser channels
                        v[light_on_px:period_px - jitter_px,
                          n2c[channel + '_TTL']] = 3
                    v[light_on_px:period_px - jitter_px,
                      n2c[channel + '_power']] = 4.5 * power / 100
                    voltages.append(v)
        voltages = np.concatenate(voltages, axis=0)
        # Timing attributes:
        self.buffer_time_s = self.ao.p2s(voltages.shape[0])
        self.volumes_per_s = self.volumes_per_buffer / self.buffer_time_s
        return voltages

    def _plot_voltages(self):
        import matplotlib.pyplot as plt
        # Reverse lookup table; channel numbers to names:
        c2n = {v:k for k, v in self.names_to_voltage_channels.items()}
        for c in range(self.voltages.shape[1]):
            plt.plot(self.voltages[:, c], label=c2n.get(c, f'ao-{c}'))
        plt.legend(loc='upper right')
        xlocs, xlabels = plt.xticks()
        plt.xticks(xlocs, [self.ao.p2s(l) for l in xlocs])
        plt.ylabel('Volts')
        plt.xlabel('Seconds')
        plt.show()

    def _prepare_to_save(self, filename, folder_name, description, delay_s):
        def make_folders(folder_name):
            os.makedirs(folder_name)
            os.makedirs(folder_name + '\data')
            os.makedirs(folder_name + '\metadata')
            os.makedirs(folder_name + '\preview')                    
        assert type(filename) is str
        if folder_name is None:
            folder_index = 0
            dt = datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S')
            folder_name = dt + '_%03i_sols'%folder_index
            while os.path.exists(folder_name): # check overwriting
                folder_index +=1
                folder_name = dt + '_%03i_sols'%folder_index
            make_folders(folder_name)
        else:
            if not os.path.exists(folder_name): make_folders(folder_name)
        data_path =     folder_name + '\data\\'     + filename
        metadata_path = folder_name + '\metadata\\' + filename
        preview_path =  folder_name + '\preview\\'  + filename
        self._save_metadata(filename, description, delay_s, metadata_path)
        return data_path, preview_path

    def _save_metadata(self, filename, description, delay_s, path):
        to_save = {
            'Date':datetime.strftime(datetime.now(),'%Y-%m-%d'),
            'Time':datetime.strftime(datetime.now(),'%H:%M:%S'),
            'filename':filename,
            'description':description,
            'delay_s':delay_s,
            'channels_per_slice':self.channels_per_slice,
            'power_per_channel':self.power_per_channel,
            'filter_wheel_position':self.filter_wheel_position,
            'illumination_time_us':self.illumination_time_us,
            'volumes_per_s':self.volumes_per_s,
            'buffer_time_s':self.buffer_time_s,
            'height_px':self.height_px,
            'width_px':self.width_px,
            'timestamp_mode':self.timestamp_mode,
            'scan_step_size_px':self.scan_step_size_px,
            'scan_step_size_um':calculate_scan_step_size_um(
                self.scan_step_size_px),
            'slices_per_volume':self.slices_per_volume,
            'scan_range_um': self.scan_range_um,
            'volumes_per_buffer':self.volumes_per_buffer,
            'focus_piezo_z_um':self.focus_piezo_z_um,
            'XY_stage_position_mm':self.XY_stage_position_mm,
            'preview_line_px':self.preview_line_px,
            'preview_crop_px':self.preview_crop_px,
            'MRR':MRR,
            'Mtot':Mtot,
            'tilt':tilt,
            'sample_px_um':sample_px_um,
            'voxel_aspect_ratio':calculate_voxel_aspect_ratio(
                self.scan_step_size_px),
            }
        with open(os.path.splitext(path)[0] + '.txt', 'w') as file:
            for k, v in to_save.items():
                file.write(k + ': ' + str(v) + '\n')

    def _get_data_buffer(self, shape, dtype):
        while self.num_active_data_buffers >= self.max_data_buffers:
            time.sleep(1e-3) # 1.7ms min
        # Note: this does not actually allocate the memory. Allocation happens
        # during the first 'write' process inside camera.record_to_memory
        data_buffer = ct.SharedNDArray(shape, dtype)
        self.num_active_data_buffers += 1
        return data_buffer

    def _release_data_buffer(self, shared_numpy_array):
        assert isinstance(shared_numpy_array, ct.SharedNDArray)
        self.num_active_data_buffers -= 1

    def _get_preview_buffer(self, shape, dtype):
        while self.num_active_preview_buffers >= self.max_preview_buffers:
            time.sleep(1e-3) # 1.7ms min
        # Note: this does not actually allocate the memory. Allocation happens
        # during the first 'write' process inside camera.record_to_memory
        preview_buffer = ct.SharedNDArray(shape, dtype)
        self.num_active_preview_buffers += 1
        return preview_buffer

    def _release_preview_buffer(self, shared_numpy_array):
        assert isinstance(shared_numpy_array, ct.SharedNDArray)
        self.num_active_preview_buffers -= 1

    def apply_settings( # Must call before .acquire()
        self,
        channels_per_slice=None,    # Tuple of strings
        power_per_channel=None,     # Tuple of floats
        filter_wheel_position=None, # Int
        illumination_time_us=None,  # Float
        height_px=None,             # Int
        width_px=None,              # Int
        timestamp_mode=None,        # "off" or "binary" or "binary+ASCII"
        voxel_aspect_ratio=None,    # Int
        scan_range_um=None,         # Int or float
        volumes_per_buffer=None,    # Int
        focus_piezo_z_um=None,      # (Float, "relative" or "absolute")
        XY_stage_position_mm=None,  # (Float, Float, "relative" or "absolute")
        max_bytes_per_buffer=None,  # Int
        max_data_buffers=None,      # Int
        max_preview_buffers=None,   # Int
        preview_line_px=None,       # Int
        preview_crop_px=None,       # Int
        ):
        args = locals()
        args.pop('self')
        def settings_task(custody):
            custody.switch_from(None, to=self.camera) # Safe to change settings
            self._settings_applied = False # In case the thread crashes
            # Attributes must be set previously or currently:
            for k, v in args.items(): 
                if v is not None:
                    setattr(self, k, v) # A lot like self.x = x
                assert hasattr(self, k), (
                    "%s: attribute %s must be set at least once"%(self.name, k))
            if height_px is not None or width_px is not None: # legalize first
                h_px, w_px = height_px, width_px
                if height_px is None: h_px = self.height_px
                if width_px is None:  w_px = self.width_px
                self.height_px, self.width_px, self.roi_px = ( 
                    pco_edge42_cl.legalize_image_size(
                        h_px, w_px, verbose=False))
            if voxel_aspect_ratio is not None or scan_range_um is not None:
                self.scan_step_size_px, self.slices_per_volume = (
                    calculate_cuboid_voxel_scan(self.voxel_aspect_ratio,
                                                self.scan_range_um))
                self.scan_range_um = calculate_scan_range_um(
                    self.scan_step_size_px, self.slices_per_volume)
                assert 0 <= self.scan_range_um <= 500 # optical limit
            memory_exceeded = self._check_memory()
            if memory_exceeded:
                custody.switch_from(self.camera, to=None)
                return
            # Send hardware commands, slowest to fastest:
            if XY_stage_position_mm is not None:
                assert XY_stage_position_mm[2] in ('relative', 'absolute')
                x, y = XY_stage_position_mm[0], XY_stage_position_mm[1]
                if XY_stage_position_mm[2] == 'relative':
                    self.XY_stage.move_mm(x, y, block=False)
                if XY_stage_position_mm[2] == 'absolute':
                    self.XY_stage.move_mm(x, y, relative=False, block=False)
            if filter_wheel_position is not None:
                self.filter_wheel.move(filter_wheel_position,
                                       speed=6,
                                       block=False)
            if focus_piezo_z_um is not None:
                assert focus_piezo_z_um[1] in ('relative', 'absolute')
                z = focus_piezo_z_um[0]
                if focus_piezo_z_um[1] == 'relative':
                    self.focus_piezo.move_um(z, block=False)
                if focus_piezo_z_um[1] == 'absolute':
                    self.focus_piezo.move_um(z, relative=False, block=False)
            if (height_px is not None or
                width_px is not None or
                illumination_time_us is not None):
                self.camera._disarm()
                self.camera._set_roi(self.roi_px) # height_px updated first
                self.camera._set_exposure_time_us(int( 
                    self.illumination_time_us + self.camera.rolling_time_us))
                self.camera._arm(self.camera._num_buffers)
            if timestamp_mode is not None:
                self.camera._set_timestamp_mode(timestamp_mode)
            check_write_voltages_thread = False
            if (channels_per_slice is not None or
                power_per_channel is not None or
                illumination_time_us is not None or
                voxel_aspect_ratio is not None or
                scan_range_um is not None or
                volumes_per_buffer is not None):
                for channel in self.channels_per_slice:
                    assert channel in self.illumination_sources
                assert len(self.power_per_channel) == (
                    len(self.channels_per_slice))
                for power in self.power_per_channel: assert 0 <= power <= 100
                assert type(self.volumes_per_buffer) is int
                assert self.volumes_per_buffer > 0
                self.camera.num_images = self.images # update attribute
                self.voltages = self._calculate_voltages()
                write_voltages_thread = ct.ResultThread(
                    target=self.ao._write_voltages,
                    args=(self.voltages,)).start()
                check_write_voltages_thread = True
            # Finalize hardware commands, fastest to slowest:
            if focus_piezo_z_um is not None:
                self.focus_piezo._finish_moving()
                self.focus_piezo_z_um = self.focus_piezo.z
            if filter_wheel_position is not None:
                self.filter_wheel._finish_moving()
            if XY_stage_position_mm is not None:
                self.XY_stage._finish_moving()
                self.XY_stage_position_mm = self.XY_stage.x, self.XY_stage.y
            if check_write_voltages_thread:
                write_voltages_thread.get_result()
            self._settings_applied = True
            custody.switch_from(self.camera, to=None) # Release camera
        settings_thread = ct.CustodyThread(
            target=settings_task, first_resource=self.camera).start()
        self.unfinished_tasks.put(settings_thread)
        return settings_thread

    def snoutfocus(self, filename=None, delay_s=None):
        def snoutfocus_task(custody):
            custody.switch_from(None, to=self.camera) # Safe to change settings
            if delay_s is not None:
                start_time = time.perf_counter()
                if delay_s > 3: # 3 seconds is def. enough time to focus
                    time.sleep(delay_s - 3)
            if not self._settings_applied:
                print("\n%s: ***WARNING*** -> settings not applied"%self.name)
                print("%s: -> please apply legal settings"%self.name)
                print("%s: (all arguments must be specified at least once)")
                custody.switch_from(self.camera, to=None)
                return
            self._settings_applied = False # In case the thread crashes
            # Record the settings we'll have to reset:
            old_fw_pos = self.filter_wheel_position
            old_images = self.camera.num_images
            old_exp_us = self.camera.exposure_us
            old_roi_px = self.camera.roi_px
            old_timestamp = self.camera.timestamp_mode
            old_voltages = self.voltages
            # Get microscope settings ready to take our measurement:
            self.filter_wheel.move(1, speed=6, block=False) # Empty slot
            self.snoutfocus_controller.set_voltage(0, block=False) # fw slower
            piezo_limit_v = 75 # 20 um for current piezo
            piezo_step_v = 1 # 267 nm steps
            piezo_voltages = np.arange(
                0, piezo_limit_v + piezo_step_v, piezo_step_v)
            images = len(piezo_voltages)
            self.camera.num_images = images # update attribute
            roi_px = {'left': 901, 'right': 1160, 'top': 901, 'bottom': 1148}
            self.camera._disarm()
            self.camera._set_roi(roi_px)
            self.camera._set_exposure_time_us(100)
            self.camera._set_timestamp_mode('off')
            self.camera._arm(self.camera._num_buffers)
            # Calculate voltages for the analog-out card:
            exp_px = self.ao.s2p(1e-6*self.camera.exposure_us)
            roll_px = self.ao.s2p(1e-6*self.camera.rolling_time_us)
            jitter_px = max(self.ao.s2p(30e-6), 1)
            piezo_settling_px = self.ao.s2p(0.000) # Not yet measured
            period_px = (max(exp_px, roll_px, piezo_settling_px) + jitter_px)
            n2c = self.names_to_voltage_channels # A temporary nickname
            v_open_shutter = np.zeros((self.ao.s2p(5*1e-3), # Shutter open time
                                       self.ao.num_channels), 'float64')
            v_open_shutter[:, n2c['snoutfocus_shutter']] = 5
            voltages = [v_open_shutter] # insert the shutter open array first
            for piezo_voltage in piezo_voltages:
                v = np.zeros((period_px, self.ao.num_channels), 'float64')
                v[:, n2c['snoutfocus_shutter']] = 5
                v[:roll_px, n2c['camera']] = 5
                v[:, n2c['snoutfocus_piezo']] = (
                    10 * (piezo_voltage / piezo_limit_v)) # 10 V
                voltages.append(v)
            voltages = np.concatenate(voltages, axis=0)
            # Allocate memory and finalize microscope settings:
            data_buffer = self._get_data_buffer(
                (images, self.camera.height_px, self.camera.width_px), 'uint16')
            self.snoutfocus_controller._finish_set_voltage(polling_wait_s=0)
            self.filter_wheel._finish_moving()
            # Take pictures while moving the snoutfocus piezo:
            camera_thread = ct.ResultThread(
                target=self.camera.record_to_memory,
                kwargs={'allocated_memory': data_buffer,
                        'software_trigger': False},).start()
            self.ao.play_voltages(voltages, block=False) # Ends at 0 V
            camera_thread.get_result()
            # Start cleaning up after ourselves:
            write_voltages_thread = ct.ResultThread(
                target=self.ao._write_voltages,
                args=(old_voltages,)).start()
            self.filter_wheel.move(old_fw_pos, speed=6, block=False)
            # Inspect the images to find/set best snoutfocus piezo position:
            if np.max(data_buffer) < 5 * np.min(data_buffer):
                print('\n%s: WARNING snoutfocus laser intensity low:'%self.name)
                print('%s: -> is the laser/shutter powered up?'%self.name)
            v = piezo_step_v * np.unravel_index(
                np.argmax(data_buffer), data_buffer.shape)[0]
            if (v == 0 or v == piezo_limit_v):
                print('\n%s: WARNING snoutfocus piezo out of range!'%self.name)
            self.snoutfocus_controller.set_voltage(v, block=False)
            if self.verbose:
                print('\n%s: snoutfocus piezo voltage = %0.2f'%(self.name, v))
            # Finish cleaning up after ourselves:
            self.camera.num_images = old_images
            self.camera._disarm()
            self.camera._set_roi(old_roi_px)
            self.camera._set_exposure_time_us(old_exp_us)
            self.camera._set_timestamp_mode(old_timestamp)
            self.camera._arm(self.camera._num_buffers)
            self.snoutfocus_controller._finish_set_voltage(polling_wait_s=0)
            self.filter_wheel._finish_moving()
            write_voltages_thread.get_result()
            self._settings_applied = True
            # We might want to hold camera custody for a fixed amount of time:
            if delay_s is not None:
                while time.perf_counter() - start_time < delay_s:
                    time.sleep(0.001)
            custody.switch_from(self.camera, to=None)
            if filename is not None:
                if not os.path.exists('sols_snoutfocus'):
                    os.makedirs('sols_snoutfocus')
                path = 'sols_snoutfocus\\' + filename
                if self.verbose:
                    print("%s: saving '%s'"%(self.name, path))
                imwrite(path, data_buffer[:, np.newaxis, :, :], imagej=True)
                if self.verbose: print("%s: done saving."%self.name)
            self._release_data_buffer(data_buffer)
        snoutfocus_thread = ct.CustodyThread(
            target=snoutfocus_task, first_resource=self.camera).start()
        self.unfinished_tasks.put(snoutfocus_thread)
        return snoutfocus_thread

    def acquire(self,               # 'tzcyx' format
                filename=None,      # None = no save, same string = overwrite
                folder_name=None,   # None = new folder, same string = re-use
                description=None,   # Optional metadata description
                delay_s=None,       # Optional time delay baked in + Snoutfocus
                display=True):      # Optional turn off
        delay_during_acquire = True # default apply delay_s during acquire task
        if delay_s is not None and delay_s > 3:
            self.snoutfocus(delay_s=delay_s) # Run snoutfocus for longer delays
            delay_during_acquire = False # snoutfocus will apply the delay_s
        def acquire_task(custody):
            custody.switch_from(None, to=self.camera) # get camera
            if not self._settings_applied:
                print("\n%s: ***WARNING*** -> settings not applied"%self.name)
                print("%s: -> please apply legal settings"%self.name)
                print("%s: (all arguments must be specified at least once)")
                custody.switch_from(self.camera, to=None)
                return
            if delay_during_acquire and delay_s is not None:
                time.sleep(delay_s) # simple but not 'us' precise
            if filename is not None:
                prepare_to_save_thread = ct.ResultThread(
                    target=self._prepare_to_save,
                    args=(filename, folder_name, description, delay_s)).start()
            # We have custody of the camera so attribute access is safe:
            vo   = self.volumes_per_buffer
            sl   = self.slices_per_volume
            ch   = len(self.channels_per_slice)
            h_px = self.height_px
            w_px = self.width_px
            s_px = self.scan_step_size_px
            l_px = self.preview_line_px
            c_px = self.preview_crop_px
            ts   = self.timestamp_mode
            im   = self.images
            data_buffer = self._get_data_buffer((im, h_px, w_px), 'uint16')
            # camera.record_to_memory() blocks, so we use a thread:
            camera_thread = ct.ResultThread(
                target=self.camera.record_to_memory,
                kwargs={'allocated_memory': data_buffer,
                        'software_trigger': False},).start()
            # Race condition: the camera starts with (typically 16) single
            # frame buffers, which are filled by triggers from
            # ao.play_voltages(). The camera_thread empties them, hopefully
            # fast enough that we never run out. So far, the camera_thread
            # seems to both start on time, and keep up reliably once it starts,
            # but this could be fragile. The camera thread (effectively)
            # acquires shared memory as it writes to the allocated buffer.
            # On this machine the memory acquisition is faster than the camera
            # (~4GB/s vs ~1GB/s) but this could also be fragile if another
            # process interferes.
            self.ao.play_voltages(block=False)
            camera_thread.get_result()
            custody.switch_from(self.camera, to=self.datapreview)
            # Acquisition is 3D, but display and filesaving are 5D:
            data_buffer = data_buffer.reshape(vo, sl, ch, h_px, w_px)
            preview_shape = DataPreview.shape(
                vo, sl, ch, h_px, w_px, s_px, l_px, c_px, ts)
            preview_buffer = self._get_preview_buffer(preview_shape, 'uint16')
            self.datapreview.get(data_buffer, s_px, l_px, c_px, ts,
                                 allocated_memory=preview_buffer)
            if display:
                custody.switch_from(self.datapreview, to=self.display)
                self.display.show_image(preview_buffer)
                custody.switch_from(self.display, to=None)
            else:
                custody.switch_from(self.datapreview, to=None)
            if filename is not None:
                data_path, preview_path = prepare_to_save_thread.get_result()
                if self.verbose:
                    print("%s: saving '%s'"%(self.name, data_path))
                    print("%s: saving '%s'"%(self.name, preview_path))
                # TODO: consider puting FileSaving in a SubProcess
                imwrite(data_path, data_buffer, imagej=True)
                imwrite(preview_path, preview_buffer, imagej=True)
                if self.verbose:
                    print("%s: done saving."%self.name)
            self._release_data_buffer(data_buffer)
            self._release_preview_buffer(preview_buffer)
            del preview_buffer
        acquire_thread = ct.CustodyThread(
            target=acquire_task, first_resource=self.camera).start()
        self.unfinished_tasks.put(acquire_thread)
        return acquire_thread

    def finish_all_tasks(self):
        collected_tasks = []
        while True:
            try:
                th = self.unfinished_tasks.get_nowait()
            except queue.Empty:
                break
            th.get_result()
            collected_tasks.append(th)
        return collected_tasks

    def close(self):
        if self.verbose: print("%s: closing..."%self.name)
        self.finish_all_tasks()
        self.ao.close()
        self.filter_wheel.close()
        self.camera.close()
        self.snoutfocus_controller.close()
        self.focus_piezo.close()
        self.XY_stage.close()
        self.display.close()
        if self.verbose: print("%s: done closing."%self.name)

# SOLS definitions and API:

# The chosen API (exposed via '.apply_settings()') forces the user to
# select scan settings (via 'voxel_aspect_ratio' and 'scan_range_um') that are
# then legalized to give integer pixel shears when converting the raw data to
# the 'native' view data. This speeds up data processing and gives a natural or
# 'native' view of the data ***without interpolation***. If necessary an expert
# user can bypass these legalizers by directly setting the 'scan_step_size_px'
# and 'scan_range_um' attributes after the last call to '.apply_settings()'.

def calculate_scan_step_size_um(scan_step_size_px):
    return scan_step_size_px * sample_px_um / np.cos(tilt)

def calculate_scan_range_um(scan_step_size_px, slices_per_volume):
    scan_step_size_um = calculate_scan_step_size_um(scan_step_size_px)
    return scan_step_size_um * (slices_per_volume - 1)

def calculate_voxel_aspect_ratio(scan_step_size_px):
    return scan_step_size_px * np.tan(tilt)

def calculate_cuboid_voxel_scan(voxel_aspect_ratio, scan_range_um):
    scan_step_size_px = max(int(round(voxel_aspect_ratio / np.tan(tilt))), 1)
    scan_step_size_um = calculate_scan_step_size_um(scan_step_size_px)
    slices_per_volume = 1 + int(round(scan_range_um / scan_step_size_um))
    return scan_step_size_px, slices_per_volume # watch out for fencepost!

class DataPreview:
    # Returns 3 max intensity projections along the traditional XYZ axes. For
    # speed (and simplicity) these are calculated to the nearest pixel (without
    # interpolation) and should propably not be used for rigorous analysis.
    @staticmethod
    def shape(volumes_per_buffer,
              slices_per_volume,
              num_channels_per_slice, # = len(channels_per_slice)
              height_px,
              width_px,
              scan_step_size_px,
              preview_line_px,
              preview_crop_px,
              timestamp_mode):
        # Calculate max pixel shear:
        scan_step_size_um = calculate_scan_step_size_um(scan_step_size_px)
        prop_px_per_scan_step = scan_step_size_um / ( # for an O1 axis view
            sample_px_um * np.cos(tilt))
        prop_px_shear_max = int(np.rint(
            prop_px_per_scan_step * (slices_per_volume - 1)))
        # Get image size with projections:
        t_px, b_px = 2 * (preview_crop_px,) # crop top and bottom pixel rows
        if timestamp_mode == "binary+ASCII": t_px = 8 # ignore timestamps
        h_px = height_px - t_px - b_px
        x_px = width_px
        y_px = int(round((h_px + prop_px_shear_max) * np.cos(tilt)))
        z_px = int(round(h_px * np.sin(tilt)))
        shape = (volumes_per_buffer,
                 num_channels_per_slice,
                 y_px + z_px + 2 * preview_line_px,
                 x_px + z_px + 2 * preview_line_px)
        return shape

    def get(self,
            data, # raw 5D data, 'tzcyx' input -> 'tcyx' output
            scan_step_size_px,
            preview_line_px,
            preview_crop_px,
            timestamp_mode,
            allocated_memory=None):
        vo, slices, ch, h_px, w_px = data.shape
        s_px, l_px, c_px = scan_step_size_px, preview_line_px, preview_crop_px
        # Get preview shape and check allocated memory (or make new array):
        preview_shape = self.shape(
            vo, slices, ch, h_px, w_px, s_px, l_px, c_px, timestamp_mode)
        if allocated_memory is not None:
            assert allocated_memory.shape == preview_shape
            return_value = None # use given memory and avoid return
        else: # make new array and return
            allocated_memory = np.zeros(preview_shape, 'uint16')
            return_value = allocated_memory
        t_px, b_px = 2 * (preview_crop_px,) # crop top and bottom pixel rows
        if timestamp_mode == "binary+ASCII": t_px = 8 # ignore timestamps
        prop_px = h_px - t_px - b_px # i.e. prop_px = h_px (with cropping)
        data = data[:, :, :, t_px:h_px - b_px, :]
        scan_step_size_um = calculate_scan_step_size_um(scan_step_size_px)
        # Calculate max px shear on the propagation axis for an 'O1' projection:
        # -> more shear than for a 'native' projection
        prop_px_per_scan_step = scan_step_size_um / ( # O1 axis view
            sample_px_um * np.cos(tilt))
        prop_px_shear_max = int(np.rint(prop_px_per_scan_step * (slices - 1)))
        # Calculate max px shear on the scan axis for a 'width' projection:
        scan_steps_per_prop_px = 1 / prop_px_per_scan_step  # width axis view
        scan_px_shear_max = int(np.rint(scan_steps_per_prop_px * (prop_px - 1)))
        # Make projections:
        for v in range(vo):
            for c in range(ch):
                O1_proj = np.zeros(
                    (prop_px + prop_px_shear_max, w_px), 'uint16')
                width_proj = np.zeros(
                    (slices + scan_px_shear_max, prop_px), 'uint16')
                max_width = np.amax(data[v, :, c, :, :], axis=2)
                scan_proj = np.amax(data[v, :, c, :, :], axis=0)
                for i in range(slices):
                    prop_px_shear = int(np.rint(i * prop_px_per_scan_step))
                    target = O1_proj[prop_px_shear:prop_px + prop_px_shear, :]
                    np.maximum(target, data[v, i, c, :, :], out=target)
                for i in range(prop_px):
                    scan_px_shear = int(np.rint(i * scan_steps_per_prop_px))
                    width_proj[scan_px_shear:slices + scan_px_shear, i] = (
                        max_width[:, i])
                # Scale images according to pixel size (divide by X_px_um):
                X_px_um = sample_px_um # width axis
                Y_px_um = sample_px_um * np.cos(tilt) # prop. axis to scan axis
                Z_px_um = sample_px_um * np.sin(tilt) # prop. axis to O1 axis
                O1_img = zoom(O1_proj, (Y_px_um / X_px_um, 1))
                scan_img = zoom(scan_proj, (Z_px_um / X_px_um, 1))
                scan_scale = O1_img.shape[0] / width_proj.shape[0]
                # = scan_step_size_um / X_px_um rounded to match O1_img.shape[0]
                width_img = zoom(width_proj, (scan_scale, Z_px_um / X_px_um))
                # Make image with all projections and flip for traditional view:
                y_px, x_px = O1_img.shape
                line_min, line_max = O1_img.min(), O1_img.max()
                # Pass projections into allocated memory:
                m = allocated_memory # keep code short!
                m[v, c, l_px:y_px + l_px, l_px:x_px + l_px] = O1_img
##                m[v, c, y_px + 2*l_px:, l_px:x_px + l_px] = np.flipud(scan_img)
                m[v, c, y_px + 2*l_px:, l_px:x_px + l_px] = scan_img
##                m[v, c, l_px:y_px + l_px, x_px + 2*l_px:] = np.fliplr(width_img)
                m[v, c, l_px:y_px + l_px, x_px + 2*l_px:] = width_img
                m[v, c, y_px + 2*l_px:, x_px + 2*l_px:] = np.full(
                    (scan_img.shape[0], width_img.shape[1]), 0)
                # Add line separations between projections:
                m[v, c, :l_px,    :] = line_max
                m[v, c, :l_px, ::10] = line_min
                m[v, c, y_px + l_px:y_px + 2*l_px,    :] = line_max
                m[v, c, y_px + l_px:y_px + 2*l_px, ::10] = line_min
                m[v, c, :,    :l_px] = line_max
                m[v, c, ::10, :l_px] = line_min
                m[v, c, :,    x_px + l_px:x_px + 2*l_px] = line_max
                m[v, c, ::10, x_px + l_px:x_px + 2*l_px] = line_min
                m[v, c, :] = np.flipud(m[v, c, :])
        return return_value

class DataZ:
    # Can be used to estimate the z location of the sample in um relative to
    # the lowest pixel (useful for software autofocus for example). Choose:
    # - 'max_intensity' to track the brightest z pixel
    # - 'max_gradient' as a proxy for the coverslip boundary
    def estimate(
        self,
        preview_image, # 2D preview image: single volume, single channel
        height_px,
        width_px,       
        preview_line_px,
        preview_crop_px,
        timestamp_mode,
        method='max_gradient',
        gaussian_filter_std=3,
        ):
        assert method in ('max_intensity', 'max_gradient')
        t_px, b_px = 2 * (preview_crop_px,) # crop top and bottom pixel rows
        if timestamp_mode == "binary+ASCII": t_px = 8 # ignore timestamps
        h_px = height_px - t_px - b_px
        z_px = int(round(h_px * np.sin(tilt))) # DataPreview definition
        inspect_me = preview_image[:z_px, preview_line_px:width_px]
        intensity_line = np.average(inspect_me, axis=1)[::-1] # O1 -> coverslip
        intensity_line_smooth = gaussian_filter1d(
            intensity_line, gaussian_filter_std) # reject hot pixels 
        if method == 'max_intensity':
            max_z_intensity_um = np.argmax(intensity_line_smooth) * sample_px_um
            return max_z_intensity_um
        intensity_gradient = np.zeros((len(intensity_line_smooth) - 1))
        for px in range(len(intensity_line_smooth) - 1):
            intensity_gradient[px] = (
                intensity_line_smooth[px + 1] - intensity_line_smooth[px])
        max_z_gradient_um = np.argmax(intensity_gradient) * sample_px_um
        return max_z_gradient_um

class DataRoi:
    # Can be used for cropping empty pixels from raw data. The SOLS microscope
    # produces vast amounts of data very quickly, often with many empty
    # pixels (so discarding them can help). This simple routine assumes a
    # central sample/roi and then attemps to reject the surrounding empty pixels
    # accroding to the 'signal_to_bg_ratio' (threshold method).
    def get(
        self,
        data, # raw 5D data, 'tzcyx' input -> 'tzcyx' output
        preview_crop_px,
        timestamp_mode,
        signal_to_bg_ratio=1.2, # adjust for threshold
        gaussian_filter_std=3, # adjust for smoothing/hot pixel rejection
        ):
        vo, slices, ch, h_px, w_px = data.shape
        t_px, b_px = 2 * (preview_crop_px,) # crop top and bottom pixel rows
        if timestamp_mode == "binary+ASCII": t_px = 8 # ignore timestamps
        min_index_vo, max_index_vo = [], []
        for v in range(vo):
            min_index_ch, max_index_ch = [], []
            for c in range(ch):
                # Max project volume to images:
                width_projection = np.amax(
                    data[v, :, c, t_px:h_px - b_px, :], axis=2)
                scan_projection  = np.amax(
                    data[v, :, c, t_px:h_px - b_px, :], axis=0)
                # Max project images to lines and smooth to reject hot pixels:
                scan_line  = gaussian_filter1d(
                    np.max(width_projection, axis=1), gaussian_filter_std)
                prop_line  = gaussian_filter1d(
                    np.max(scan_projection, axis=1), gaussian_filter_std)
                width_line = gaussian_filter1d(
                    np.max(scan_projection, axis=0), gaussian_filter_std)
                # Find background level and set threshold:
                scan_threshold  = int(min(scan_line)  * signal_to_bg_ratio)
                prop_threshold  = int(min(prop_line)  * signal_to_bg_ratio)
                width_threshold = int(min(width_line) * signal_to_bg_ratio)
                # Estimate roi:.
                min_index_zyx = [0, 0, 0]
                max_index_zyx = [slices - 1, h_px - 1, w_px - 1]
                for i in range(slices):
                    if scan_line[i]  > scan_threshold:
                        min_index_zyx[0] = i
                        break
                for i in range(h_px - t_px - b_px):
                    if prop_line[i]  > prop_threshold:
                        min_index_zyx[1] = i + t_px # put cropped pixels back
                        break
                for i in range(w_px):
                    if width_line[i] > width_threshold:
                        min_index_zyx[2] = i
                        break        
                for i in range(slices):
                    if scan_line[-i] > scan_threshold:
                        max_index_zyx[0] = max_index_zyx[0] - i
                        break
                for i in range(h_px - t_px - b_px):
                    if prop_line[-i] > prop_threshold:
                        max_index_zyx[1] = max_index_zyx[1] - i - b_px
                        break
                for i in range(w_px):
                    if width_line[-i] > width_threshold:
                        max_index_zyx[2] = max_index_zyx[2] - i
                        break
                min_index_ch.append(min_index_zyx)
                max_index_ch.append(max_index_zyx)
            min_index_vo.append(np.amin(min_index_ch, axis=0))
            max_index_vo.append(np.amax(max_index_ch, axis=0))
        min_i = np.amin(min_index_vo, axis=0)
        max_i = np.amax(max_index_vo, axis=0)
        data_roi = data[
            :, min_i[0]:max_i[0], :, min_i[1]:max_i[1], min_i[2]:max_i[2]]
        return data_roi # hopefully smaller!

class DataNative:
    # The 'native view' is the most principled view of the data for analysis.
    # If 'type(scan_step_size_px) is int' (default) then no interpolation is
    # needed to view the volume. The native view looks at the sample with
    # the 'tilt' of the Snouty objective (microsope 3 in the emmission path).
    def get(
        self,
        data, # raw 5D data, 'tzcyx' input -> 'tzcyx' output
        scan_step_size_px):
        vo, slices, ch, h_px, w_px = data.shape
        prop_px = h_px # light-sheet propagation axis
        scan_step_px_max = int(np.rint(scan_step_size_px * (slices - 1)))
        data_native = np.zeros(
            (vo, slices, ch, prop_px + scan_step_px_max, w_px), 'uint16')
        for v in range(vo):
            for c in range(ch):
                for i in range(slices):
                    prop_px_shear = int(np.rint(i * scan_step_size_px))
                    data_native[
                        v, i, c, prop_px_shear:prop_px + prop_px_shear, :] = (
                            data[v, i, c, :, :])
        return data_native # larger!

class DataTraditional:
    # Very slow but pleasing - rotates the native view to the traditional view!
    def get(
        self,
        data_native, # raw 5D data, 'tzcyx' input -> 'tzcyx' output
        scan_step_size_px):
        vo, slices, ch, h_px, w_px = data_native.shape
        voxel_aspect_ratio = calculate_voxel_aspect_ratio(scan_step_size_px)
        tzcyx = []
        for v in range(vo):
            zcyx = []
            for c in range(ch):
                zyx_native_cubic_voxels = zoom(
                    data_native[v, :, c, :, :], (voxel_aspect_ratio, 1, 1))
                zyx_traditional = rotate(
                    zyx_native_cubic_voxels, np.rad2deg(tilt))
                zcyx.append(zyx_traditional[:, np.newaxis, : ,:])
            zcyx = np.concatenate(zcyx, axis=1)
            tzcyx.append(zcyx[np.newaxis, :, :, : ,:])
        data_traditional = np.concatenate(tzcyx, axis=0)
        return data_traditional # even larger!

if __name__ == '__main__':
    t0 = time.perf_counter()

    # Create scope object:
    scope = Microscope(max_allocated_bytes=100e9, ao_rate=1e4)
    scope.apply_settings(       # Mandatory call
        channels_per_slice=("LED", "488"),
        power_per_channel=(50, 10),
        filter_wheel_position=3,
        illumination_time_us=100,
        height_px=248,
        width_px=1060,
        voxel_aspect_ratio=2,
        scan_range_um=50,
        volumes_per_buffer=1,
        focus_piezo_z_um=(0,'relative'),
        XY_stage_position_mm=(0,0,'relative'),
        ).join()

    # Run snoutfocus and acquire:
    folder_label = 'sols_test_data'
    dt = datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S_000_')
    folder_name = dt + folder_label
    scope.snoutfocus(filename='snoutfocus.tif')
    for i in range(3):
        scope.acquire(
            filename='%06i.tif'%i,
            folder_name=folder_name,
            description='something...',
            delay_s=0,
            display=True,
            )
    scope.close()

    t1 = time.perf_counter()
    print('time_s', t1 - t0) # ~ 9.5s
