import time
import tifffile as tif
import napari
from ht_sols_microscope import DataPreview, DataRoi, DataNative, DataTraditional

def imread(filename): # re-define imread to keep 5D axes
    with tif.TiffFile(filename) as t:
        axes = t.series[0].axes
        hyperstack = t.series[0].asarray()
    return tif.transpose_axes(hyperstack, axes, 'TZCYX')

def imwrite(filename, data):
    return tif.imwrite(filename, data, imagej=True)

def view_in_napari(data_preview,
                   data_native=None,
                   voxel_aspect_ratio=None, # Needed for data_native
                   data_traditional=None):
    print('\nViewing in napari')
    with napari.gui_qt():
        preview = napari.Viewer()
        preview.add_image(data_preview, name='data_preview')
        if data_native is not None:
            native = napari.Viewer()
            for channel in range(data_native.shape[2]):
                native.add_image(data_native[:, :, channel, :, :],
                                 name='data_native',
                                 scale=(1, voxel_aspect_ratio, 1, 1))
        if data_traditional is not None: 
            traditional = napari.Viewer()
            for channel in range(data_traditional.shape[2]):
                traditional.add_image(data_traditional[:, :, channel, :, :],
                                      name='data_traditional')

# Get processsing tools:
datapreview     = DataPreview()
dataroi         = DataRoi()
datanative      = DataNative()
datatraditional = DataTraditional()

# Get data and metadata:
t0 = time.perf_counter()
print('\nGetting: data', end=' ')
data = imread('data.tif')
t1 = time.perf_counter()
print('(%0.2fs)'%(t1 - t0))
print('-> data.shape =', data.shape)
print('-> format = 5D "tzcyx" (volumes, slices, channels, height_px, width_px)')
scan_step_size_px = 1
preview_line_px = 10
preview_crop_px = 3
timestamp_mode = "off"
voxel_aspect_ratio =  1.19175359259421

# Get preview:
print('\nGetting: preview', end=' ')
preview = datapreview.get(
    data, scan_step_size_px, preview_line_px, preview_crop_px, timestamp_mode)
t2 = time.perf_counter()
print('(%0.2fs)'%(t2 - t1))
print('-> saving: data_preview.tif')
imwrite('data_preview.tif', preview)

# Get native data:
print('\nGetting: native view', end=' ')
native = datanative.get(data, scan_step_size_px)
t3 = time.perf_counter()
print('(%0.2fs)'%(t3 - t2))
print('-> saving: data_native.tif')
imwrite('data_native.tif', native)

# Get traditional data for roi: -> this is very slow (adds about ~30s)
print('\nGetting: traditional view', end=' ')
native_subset = native[0:1, : , 0:1, :, :] # -> picking 1 volume, but keep 5D!
traditional = datatraditional.get(native_subset, scan_step_size_px)
t4 = time.perf_counter()
print('(%0.2fs)'%(t4 - t3))
print('-> saving: data_traditional.tif')
imwrite('data_traditional.tif', traditional)

# View in napari (or checked saved data with ImageJ or similar):
view_in_napari(preview, native, voxel_aspect_ratio, traditional)
