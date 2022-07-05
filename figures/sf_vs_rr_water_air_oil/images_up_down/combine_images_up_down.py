import os
import numpy as np
import imageio

cwd = os.getcwd()
d = os.path.dirname(cwd)

for i in range(45):
    print('reading:' + d + '\\images\\' + 'img%i'%i)
    sf_image = imageio.imread(d + '\\images\\' + 'img%i.png'%i)
    print('reading:' + d + '\\images\\' + 'img%i'%(i + 45))
    rr_image = imageio.imread(d + '\\images\\' + 'img%i.png'%(i + 45))
    img = np.concatenate((sf_image, rr_image), axis=0)
    imageio.imwrite(cwd + '\\img%i.png'%i, img)
