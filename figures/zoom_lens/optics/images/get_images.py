import os
import imageio

d = os.path.dirname(os.getcwd()) + '\\animation_images\\'
filenames = ('0.png',
             '1.png',
             '2.png',
             '3.png',
             '4.png',
             '5.png',
             '6.png',
             '7.png')

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
    imageio.imwrite('%d.png'%i, image)

