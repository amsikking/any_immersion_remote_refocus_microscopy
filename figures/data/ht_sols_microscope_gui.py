import os
from datetime import datetime
import tkinter as tk

import ht_sols_microscope as htsols
import tkinter_compound_widgets as tki_cw

class GuiTransmittedLight:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='TRANSMITTED LIGHT', bd=6)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky='n')
        self.power = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='470-850nm (%)',
            checkbox_default=True,
            slider_length=200,
            default_value=25)

class GuiLaserBox:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='LASER BOX', bd=6)
        frame.grid(row=1, column=0, padx=20, pady=20, sticky='n')
        self.power405 = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='405nm (%)',
            color='magenta',
            slider_length=200,
            default_value=5)
        self.power488 = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='488nm (%)',
            color='blue',
            slider_length=200,
            default_value=5,
            row=1)
        self.power561 = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='561nm (%)',
            color='green',
            slider_length=200,
            default_value=5,
            row=2)
        self.power640 = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='640nm (%)',
            color='red',
            slider_length=200,
            default_value=5,
            row=3)

class GuiFilterWheel:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='FILTER WHEEL', bd=6)
        frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky='n')
        self.filter = tki_cw.RadioButtons(
            frame,
            label='options',
            buttons=('0: Shutter',
                     '1: Open',
                     '2: ET445/58M',
                     '3: ET525/50M',
                     '4: ET600/50M',
                     '5: ET706/95M',
                     '6: ZETquadM',
                     '7: (available)',
                     '8: (available)',
                     '9: (available)'),
            default_position=6)

class GuiGalvo:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='GALVO', bd=6)
        frame.grid(row=0, column=2, padx=20, pady=20, sticky='n')
        self.scan_range_um = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='~scan range (um)',
            checkbox_enabled=False,
            slider_length=350,
            tickinterval=10,
            min_value=1,
            max_value=250,
            default_value=100)
        self.voxel_aspect_ratio = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='~voxel aspect ratio',
            checkbox_enabled=False,
            slider_length=350,
            tickinterval=10,
            min_value=1,
            max_value=80,         
            default_value=25,
            row=1)

class GuiCamera:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='CAMERA', bd=6)
        frame.grid(row=1, column=2, padx=20, pady=20, sticky='n')
        self.illumination_time_ms = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='illumination time (ms)',
            checkbox_enabled=False,
            slider_length=350,
            tickinterval=10,
            min_value=1,
            max_value=250,
            default_value=1,
            columnspan=2)
        self.height_px = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='height pixels',
            orient='vertical',
            checkbox_enabled=False,
            slider_length=250,
            slider_flipped=True,
            min_value=12,
            max_value=1200,
            default_value=250,
            row=1)
        self.width_px = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='width pixels',
            checkbox_enabled=False,
            slider_length=250,
            min_value=60,
            max_value=1500,
            default_value=1000,
            row=2,
            column=1,
            sticky='s')
        tki_cw.CanvasRectangleSliderTrace2D(
            frame, self.width_px, self.height_px, row=1, column=1)

class GuiFocusPiezo:
    def __init__(self, master):
        frame = tk.LabelFrame(master, text='FOCUS PIEZO', bd=6)
        frame.grid(row=0, column=3, rowspan=2, padx=20, pady=20, sticky='n')
        self.position_um = tki_cw.CheckboxSliderSpinbox(
            frame,
            label='position (um)',
            orient='vertical',
            checkbox_enabled=False,
            slider_length=400,
            tickinterval=10,
            slider_flipped=True,
            min_value=0,
            max_value=800,
            default_value=gui_acquisition.focus_piezo_z_um)

class GuiAcquisition:
    def __init__(self, master):
        self.frame = tk.LabelFrame(master, text='ACQUISITION', bd=6)
        self.frame.bind('<Enter>', self.get_tkfocus)
        self.frame.grid(
            row=0, column=4, rowspan=2, padx=20, pady=20, sticky='n')
        self.spinbox_width = 20
        self.button_width = 25
        self.button_height = 2
        self.gui_delay_ms = int(1e3 * 1 / 30) # 30fps/video rate target
        # init GUI buttons:
        self.init_live_mode_button()
        self.init_scout_mode_button()
        self.init_snap_button()
        self.init_snap_and_save_button()
        self.init_volumes_spinbox()
        self.init_acquisitions_spinbox()
        self.init_delay_spinbox()
        self.init_apply_settings_and_print_button()
        self.init_label_textbox()
        self.init_description_textbox()
        self.init_run_aquisition_button()
        # init scope:
        self.scope = htsols.Microscope(max_allocated_bytes=100e9, ao_rate=1e4)
        self.scope.XY_stage.set_velocity(5, 5) # edit for taste
        # get attributes from GUI defaults:
        self.channels_per_slice, self.power_per_channel = (
            self.get_channel_settings())
        self.filter_wheel_position = gui_filter_wheel.filter.position
        self.illumination_time_us = (
            1e3 * gui_camera.illumination_time_ms.spinbox_value)
        self.height_px = gui_camera.height_px.spinbox_value
        self.width_px = gui_camera.width_px.spinbox_value
        self.voxel_aspect_ratio = gui_galvo.voxel_aspect_ratio.spinbox_value
        self.scan_range_um = gui_galvo.scan_range_um.spinbox_value
        self.volumes_per_buffer = self.volumes.spinbox_value
        # apply GUI settings:
        self.scope.apply_settings( # Mandatory call
            channels_per_slice=self.channels_per_slice,
            power_per_channel=self.power_per_channel,
            filter_wheel_position=self.filter_wheel_position,
            illumination_time_us=self.illumination_time_us,
            height_px=self.height_px,
            width_px=self.width_px,
            voxel_aspect_ratio=self.voxel_aspect_ratio,
            scan_range_um=self.scan_range_um,
            volumes_per_buffer=self.volumes_per_buffer,
            focus_piezo_z_um=(0, 'relative'),
            XY_stage_position_mm=(0, 0, 'relative')).join()
        # update attributes from hardware: (no xyz moves from init)
        self.focus_piezo_z_um = self.scope.focus_piezo_z_um
        self.XY_stage_position_mm = self.scope.XY_stage_position_mm
        # get scope ready:
##        self.loop_snoutfocus()
        self.scope.snoutfocus_controller.set_voltage(75/2)
        self.scope.acquire()
        
    def get_tkfocus(self, event):   # event is not used here (.bind)
        self.frame.focus_set()      # take from other widgets to force update
        
    def loop_snoutfocus(self):
        if not self.running_aquisition.get(): self.scope.snoutfocus()
        self.frame.after(120000, self.loop_snoutfocus)

    def init_live_mode_button(self):
        self.live_mode_enabled = tk.BooleanVar()
        live_mode_button = tk.Checkbutton(self.frame,
                                          text='Live mode (On/Off)',
                                          variable=self.live_mode_enabled,
                                          command=self.init_live_mode,
                                          indicatoron=0,
                                          width=self.button_width,
                                          height=self.button_height)
        live_mode_button.grid(row=0, column=0, padx=10, pady=10)

    def init_live_mode(self):
        self.scout_mode_enabled.set(0)
        self.run_live_mode()

    def run_live_mode(self):
        if self.live_mode_enabled.get():
            self.apply_settings(single_volume=True)
            self.scope.acquire()
            self.frame.after(self.gui_delay_ms, self.run_live_mode)

    def init_scout_mode_button(self):
        self.scout_mode_enabled = tk.BooleanVar()
        scout_mode_button = tk.Checkbutton(self.frame,
                                           text='Scout mode (On/Off)',
                                           variable=self.scout_mode_enabled,
                                           command=self.init_scout_mode,
                                           indicatoron=0,
                                           width=self.button_width,
                                           height=self.button_height)
        scout_mode_button.grid(row=1, column=0, padx=10, pady=10)

    def init_scout_mode(self):
        self.live_mode_enabled.set(0)
        self.apply_settings(single_volume=True)
        self.scope.acquire()
        self.run_scout_mode()

    def run_scout_mode(self):
        if self.scout_mode_enabled.get():
            XY_pos_mm = self.scope.XY_stage.get_position_mm()
            Z_pos_um = gui_focus_piezo.position_um.spinbox_value
            if (abs(XY_pos_mm[0] - self.XY_stage_position_mm[0]) > 0.005 or
                abs(XY_pos_mm[1] - self.XY_stage_position_mm[1]) > 0.005 or
                Z_pos_um != self.focus_piezo_z_um):
                self.XY_stage_position_mm = XY_pos_mm
                self.apply_settings(single_volume=True)
                self.scope.acquire()
            self.frame.after(self.gui_delay_ms, self.run_scout_mode)

    def init_snap_button(self):
        snap_button = tk.Button(self.frame, text="Snap volume",
                                command=self.snap_volume,
                                width=self.button_width,
                                height=self.button_height)
        snap_button.grid(row=2, column=0, padx=10, pady=10)

    def snap_volume(self):
        self.apply_settings(single_volume=True, _print=True)
        self.scope.acquire()

    def init_snap_and_save_button(self):
        snap_and_save_button = tk.Button(self.frame,
                                         text="Snap volume and save",
                                         command=self.snap_volume_and_save,
                                         width=self.button_width,
                                         height=self.button_height)
        snap_and_save_button.grid(row=3, column=0, padx=10, pady=10)

    def snap_volume_and_save(self):
        self.apply_settings(single_volume=True, _print=True)
        folder_name = self.get_folder_name() + '_snap'
        self.scope.acquire(filename='snap.tif',
                           folder_name=folder_name,
                           description=self.description.text)

    def init_volumes_spinbox(self):
        self.volumes = tki_cw.CheckboxSliderSpinbox(
            self.frame,
            label='Volumes per acquisition',
            checkbox_enabled=False,
            slider_enabled=False,
            min_value=1,
            max_value=1e3,
            default_value=1,
            row=4,
            width=self.spinbox_width)

    def init_acquisitions_spinbox(self):
        self.acquisitions = tki_cw.CheckboxSliderSpinbox(
            self.frame,
            label='Acquisition number',
            checkbox_enabled=False,
            slider_enabled=False,
            min_value=1,
            max_value=1e6,
            default_value=1,
            row=5,
            width=self.spinbox_width)

    def init_delay_spinbox(self):
        self.delay_s = tki_cw.CheckboxSliderSpinbox(
            self.frame,
            label='Inter-acquisition delay (s)',
            checkbox_enabled=False,
            slider_enabled=False,
            min_value=0,
            max_value=3600,
            default_value=0,
            row=6,
            width=self.spinbox_width)

    def init_apply_settings_and_print_button(self):
        apply_settings_and_print_button = tk.Button(
            self.frame,
            text="Print memory + time",
            command=self.apply_settings_and_print,
            width=self.button_width,
            height=self.button_height)
        apply_settings_and_print_button.bind('<Enter>', self.get_tkfocus)
        apply_settings_and_print_button.grid(row=7, column=0, padx=10, pady=10)

    def apply_settings_and_print(self):
        self.apply_settings(_print=True)

    def init_label_textbox(self):
        self.label = tki_cw.Textbox(self.frame,
                                    label='Folder label',
                                    default_text='ht_sols_gui',
                                    row=8,
                                    width=self.spinbox_width)

    def init_description_textbox(self):
        self.description = tki_cw.Textbox(self.frame,
                                          label='Description',
                                          default_text='what are you doing?',
                                          row=9,
                                          width=self.spinbox_width)

    def init_run_aquisition_button(self):
        self.running_aquisition = tk.BooleanVar()
        run_aquisition_button = tk.Button(self.frame, text="Run aquisition",
                                          command=self.run_acquisition,
                                          width=self.button_width,
                                          height=self.button_height)
        run_aquisition_button.bind('<Enter>', self.get_tkfocus)
        run_aquisition_button.grid(row=10, column=0, padx=10, pady=10)

    def run_acquisition(self):
        if self.live_mode_enabled.get(): self.live_mode_enabled.set(0)
        if self.scout_mode_enabled.get(): self.scout_mode_enabled.set(0)
        self.running_aquisition.set(1)
        self.apply_settings(_print=True)
        folder_name = self.get_folder_name()
        for i in range(self.acquisitions.spinbox_value):
            if i == 0: # avoid first delay_s
                self.scope.acquire(filename='%06i.tif'%i,
                   folder_name=folder_name,
                   description=self.description.text)
            else:
                self.scope.acquire(filename='%06i.tif'%i,
                                   folder_name=folder_name,
                                   description=self.description.text,
                                   delay_s=self.delay_s.spinbox_value)
        self.scope.finish_all_tasks()
        self.running_aquisition.set(0)

    def get_folder_name(self):
        dt = datetime.strftime(datetime.now(),'%Y-%m-%d_%H-%M-%S_')
        folder_index = 0
        folder_name = dt + '%03i_'%folder_index + self.label.text
        while os.path.exists(folder_name): # check before overwriting
            folder_index +=1
            folder_name = dt + '%03i_'%folder_index + self.label.text
        return folder_name

    def get_channel_settings(self):
        channels_per_slice, power_per_channel = [], []
        if gui_transmitted_light.power.checkbox_value:
            channels_per_slice.append('LED')
            power_per_channel.append(gui_transmitted_light.power.spinbox_value)
        if gui_laser_box.power405.checkbox_value:
            channels_per_slice.append('405')
            power_per_channel.append(gui_laser_box.power405.spinbox_value)
        if gui_laser_box.power488.checkbox_value:
            channels_per_slice.append('488')
            power_per_channel.append(gui_laser_box.power488.spinbox_value)
        if gui_laser_box.power561.checkbox_value:
            channels_per_slice.append('561')
            power_per_channel.append(gui_laser_box.power561.spinbox_value)
        if gui_laser_box.power640.checkbox_value:
            channels_per_slice.append('640')
            power_per_channel.append(gui_laser_box.power640.spinbox_value)
        if len(channels_per_slice) == 0: # default TL if nothing selected
            gui_transmitted_light.power.tk_checkbox_value.set(1)
            channels_per_slice = ('LED',)
            power_per_channel = (gui_transmitted_light.power.spinbox_value,)
        return channels_per_slice, power_per_channel

    def apply_settings(self, single_volume=False, _print=False):
        # get settings from GUI:
        channels_per_slice, power_per_channel = self.get_channel_settings()
        filter_wheel_position = gui_filter_wheel.filter.position
        illumination_time_us = (
            1e3 * gui_camera.illumination_time_ms.spinbox_value)
        height_px = gui_camera.height_px.spinbox_value
        width_px = gui_camera.width_px.spinbox_value
        voxel_aspect_ratio = gui_galvo.voxel_aspect_ratio.spinbox_value
        scan_range_um = gui_galvo.scan_range_um.spinbox_value
        volumes_per_buffer=self.volumes.spinbox_value
        focus_piezo_z_um = gui_focus_piezo.position_um.spinbox_value
        # (currently no XY stage GUI)
        if power_per_channel != self.power_per_channel:
            self.scope.apply_settings(
                channels_per_slice=channels_per_slice,
                power_per_channel=power_per_channel)
            self.power_per_channel = power_per_channel
            self.channels_per_slice = channels_per_slice
        if filter_wheel_position != self.filter_wheel_position:
            self.scope.apply_settings(
                filter_wheel_position=filter_wheel_position)
            self.filter_wheel_position = filter_wheel_position
        if illumination_time_us != self.illumination_time_us:
            self.scope.apply_settings(
                illumination_time_us=illumination_time_us)
            self.illumination_time_us = illumination_time_us
        if height_px != self.height_px:
            self.scope.apply_settings(height_px=height_px)
            self.height_px = height_px
        if width_px != self.width_px:
            self.scope.apply_settings(width_px=width_px)
            self.width_px = width_px
        if voxel_aspect_ratio != self.voxel_aspect_ratio:
            self.scope.apply_settings(voxel_aspect_ratio=voxel_aspect_ratio)
            self.voxel_aspect_ratio = voxel_aspect_ratio
        if scan_range_um != self.scan_range_um:
            self.scope.apply_settings(scan_range_um=scan_range_um)
            self.scan_range_um = scan_range_um
        if single_volume:
            self.scope.apply_settings(volumes_per_buffer=1)
        else:
            self.scope.apply_settings(volumes_per_buffer=volumes_per_buffer)
        if focus_piezo_z_um != self.focus_piezo_z_um:
            self.scope.apply_settings(
                focus_piezo_z_um=(focus_piezo_z_um, 'absolute'))
            self.focus_piezo_z_um = focus_piezo_z_um
        self.scope.finish_all_tasks()
        if _print:
            self.print_memory_and_time()
        return None

    def print_memory_and_time(self):
        # calculate memory
        total_memory_gb = 1e-9 * self.scope.total_bytes
        max_memory_gb = 1e-9 * self.scope.max_allocated_bytes
        memory_pct = 100 * total_memory_gb / max_memory_gb
        print('\nTotal memory needed   (GB) = %0.6f (%0.2f%% of max)'%(
            total_memory_gb, memory_pct))
        # calculate storage:
        data_gb = 1e-9 * self.scope.bytes_per_data_buffer
        preview_gb = 1e-9 * self.scope.bytes_per_preview_buffer
        total_storage_gb = (
            data_gb + preview_gb) * self.acquisitions.spinbox_value
        print('Total storaged needed (GB) = %0.6f'%total_storage_gb)
        # calculate time:
        acquire_time_s = self.scope.buffer_time_s + self.delay_s.spinbox_value
        total_time_s = acquire_time_s * self.acquisitions.spinbox_value
        print('Total acquisition time (s) = %0.6f (%0.2f min)'%(
            total_time_s, (total_time_s / 60)))
        print('Vps ~ %0.6f'%self.scope.volumes_per_s)
        return None

    def close(self):
        self.scope.close()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('HT SOLS Microscope GUI')

    gui_transmitted_light = GuiTransmittedLight(root)
    gui_laser_box =         GuiLaserBox(root)
    gui_filter_wheel =      GuiFilterWheel(root)
    gui_galvo =             GuiGalvo(root)
    gui_camera =            GuiCamera(root)
    gui_acquisition =       GuiAcquisition(root)
    gui_focus_piezo =       GuiFocusPiezo(root)

    quit_ = tk.Button(root, text="QUIT", command=root.quit, height=5, width=30)
    quit_.grid(row=3, column=4, padx=20, pady=20, sticky='n')

    root.mainloop()
    gui_acquisition.close()
    root.destroy()
