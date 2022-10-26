# Additional details here:
# https://github.com/thevangelist/FFMPEG-gif-script-for-bash
# http://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html

import os
from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
from tifffile import imread

data = imread('preview.tif')
print('-> data.shape =', data.shape)

z_steps, y_px, x_px = data.shape

directory = os.path.join(Path.cwd(), 'images')
if not os.path.exists(directory):
    os.makedirs(directory)

xmargin, ymargin, space = 0.15, 0.1, 0.03
x_inch = 6
y_inch = x_inch * y_px / x_px
vmax = 700

fig = plt.figure()
plt.figure(figsize=(x_inch, y_inch), dpi=120)

for i in range(z_steps):
    image = data[i, :, :]
    image[50:277, 1450:1460] = vmax # add white scale bar
    z_um = int(i - 20)
    print('-> z_um =', z_um)
    plt.clf()
    plt.imshow(image, cmap='gray', vmin=0, vmax=vmax)
    plt.axis('off')
    plt.figtext(xmargin, ymargin + 25*space,
                'XZ', color='white', family='monospace')
    plt.figtext(xmargin, ymargin + 18.5*space,
                'XY', color='white', family='monospace')
    plt.figtext(xmargin + 18.5*space, ymargin + 18.5*space,
                'YZ', color='white', family='monospace')
    if i in (18, 20, 22):
        plt.figtext(xmargin, ymargin + 10*space,
                    'Good volumetric PSF!',
                    color='yellow', family='monospace')
    plt.figtext(xmargin, ymargin + 3*space,
                'Objective = 40x0.95 air', color='white', family='monospace')
    plt.figtext(xmargin, ymargin + 2*space,
                'scale bar = 50$\mu$m', color='white', family='monospace')
    plt.figtext(xmargin, ymargin + space,
                'z =%6s$\mu$m'%('%0.1f'%z_um),
                color='yellow', family='monospace')
    plt.savefig('images/img%02i.png'%i, bbox_inches='tight', pad_inches = 0)
    plt.close(fig)

start_frame = 0 # crop frames here
end_frame = z_steps

# Adjust fps and scale for file size:
palette = Path.cwd() / "palette.png"
filters = "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos"

# Scan images for color subset and make 'palette.png'
print("Converting images to gif...", end=' ')
convert_command_1 = [
    'ffmpeg',                               # callable ffmpeg on path
    '-y',                                   # auto overwrite files
    '-f', 'image2',                         # force file format to 'image2'
    '-start_number', str(start_frame),      # start frame
    '-i', os.path.join(directory,
                       'img%02d.png'),      # input images
    '-vframes', str(end_frame-start_frame), # number of frames
    '-vf', filters + ",palettegen",         # generate palette with filter
     palette]                               # output palette
convert_command_2 = [
    'ffmpeg',
    '-y',
    '-f', 'image2',
    '-framerate', '5',                      # adjust framerate
    '-start_number', str(start_frame),
    '-i', os.path.join(directory,
                       'img%02d.png'),
    '-i', palette,
    '-vframes', str(end_frame-start_frame),      
    '-lavfi', filters + " [x]; [x][1:v] paletteuse",
    Path.cwd() / 'output.gif']

for convert_command in convert_command_1, convert_command_2:
    try:
        with open(Path.cwd() / 'conversion_messages.txt', 'wt') as f:
            f.write("So far, everthing's fine...\n")
            f.flush()
            subprocess.check_call(convert_command, stderr=f, stdout=f)
            f.flush()
        (Path.cwd() / 'conversion_messages.txt').unlink()
    except: # This is unlikely to be platform independent :D
        print("GIF conversion failed. Is ffmpeg installed?")
        raise
print('done.')
