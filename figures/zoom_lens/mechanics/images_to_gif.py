# Additional details here:
# https://github.com/thevangelist/FFMPEG-gif-script-for-bash
# http://blog.pkh.me/p/21-high-quality-gif-with-ffmpeg.html

import os
from pathlib import Path
import subprocess

directory = os.path.join(Path.cwd(), 'images')
start_frame = 1 # crop frames here
end_frame = 5

if not os.path.exists(directory):
    print('\'images\' folder not found')
    raise

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
                       'zoom_lens_132.5-150mm_sheet_%d.png'), # input images
    '-vframes', str(end_frame-start_frame), # number of frames
    '-vf', filters + ",palettegen",         # generate palette with filter
     palette]                               # output palette
convert_command_2 = [
    'ffmpeg',
    '-y',
    '-f', 'image2',
    '-framerate', '1',                      # adjust framerate
    '-start_number', str(start_frame),
    '-i', os.path.join(directory,
                       'zoom_lens_132.5-150mm_sheet_%d.png'),
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
