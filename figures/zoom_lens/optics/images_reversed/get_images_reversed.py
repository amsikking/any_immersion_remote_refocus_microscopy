import os
import imageio

d = os.path.dirname(os.getcwd()) + '\\animation_images_reversed\\'
filenames = ('0_reversed.png',
             '1_reversed.png',
             '2_reversed.png',
             '3_reversed.png',
             '4_reversed.png',
             '5_reversed.png',
             '6_reversed.png',
             '7_reversed.png')

ud_crop_px = 300
lr_crop_px = 550
images = []
for i, file in enumerate(filenames):
    image = imageio.imread(d + file)
    print(image.shape, type(image))
    images.append(image[ud_crop_px:-ud_crop_px,
                        lr_crop_px:-lr_crop_px])

image_sequence = []
image_sequence.append(images[0])
for i in range(8):
    image_sequence.append(images[i])
image_sequence.append(images[7])
for i in reversed(range(8)):
    image_sequence.append(images[i])

for i, image in enumerate(image_sequence):
    imageio.imwrite('%d_reversed.png'%i, image)

