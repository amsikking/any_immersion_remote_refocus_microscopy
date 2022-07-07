import imageio

filenames = ('Huygens_PSF_config_1.png',
             'Huygens_PSF_config_8.png',
             'layout_config_1.png',
             'layout_config_8.png',
             'RMS_vs_field_config_1.png',
             'RMS_vs_field_config_8.png',
             'spot_diagram_all_configs.png',
             'spot_diagram_config_1.png',
             'spot_diagram_config_8.png')

for file in filenames:
    image = imageio.imread(file)
    print(image.shape, type(image))
    imageio.imwrite(file, image[:,0:1810,:])
