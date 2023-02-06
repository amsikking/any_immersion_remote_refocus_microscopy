import numpy as np

# Zoom_lens_132.5-150mm_motion.ods trendline polynomials
# Data from Zemax

def focal_length_to_lens_motion(f_mm, verbose=True):
    stage1_mm = (-     0.000103278288*f_mm**4
                 +     0.059929457484*f_mm**3
                 -    13.033982374525*f_mm**2
                 +  1260.150733009060*f_mm
                 - 45717.573446038600)
    stage2_mm = (-     0.000083979119*f_mm**4
                 +     0.049656589716*f_mm**3
                 -    10.961078884880*f_mm**2
                 +  1074.586675413890*f_mm
                 - 39574.398463973600)
    stage3_mm = (+    0.000018343468*f_mm**4
                 -    0.009692931167*f_mm**3
                 +    1.950506313956*f_mm**2
                 -  175.313955214666*f_mm
                 + 5879.390039196680)
    if verbose:
        print('\nf_mm = %0.2f'%f_mm)
        print('stage1_mm = %0.2f'%stage1_mm)
        print('stage2_mm = %0.2f'%stage2_mm)
        print('stage3_mm = %0.2f'%stage3_mm)
    return stage1_mm, stage2_mm, stage3_mm

# Zemax data:
Zemax_f_mm = (132.5, 135.0, 137.5, 140.0, 142.5, 145.0, 147.5, 150.0)
Zemax_stage1_mm = (0.00, 3.46, 6.14, 8.53, 10.73, 13.06, 15.32, 17.73)
Zemax_stage2_mm = (0.00, 9.27, 18.07, 26.88, 35.80, 45.36, 55.23, 65.90)
Zemax_stage3_mm = (0.00, 4.53, 9.45, 14.79, 20.55, 26.92, 33.80, 41.43)

# Input:
f_mm = np.linspace(132.5, 150, 1000)

# Output:
stage1_mm, stage2_mm, stage3_mm = focal_length_to_lens_motion(
    f_mm, verbose=False)

# Plot:
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
# labels:
ax.set_title('Zoom lens (constant track length)')
ax.set_ylabel('Motion (mm)')
ax.set_xlabel('Focal length (mm)')
# data:
ax.plot(Zemax_f_mm, Zemax_stage1_mm, 'b', linestyle='', marker='o',
        label='stage1: zemax data')
ax.plot(Zemax_f_mm, Zemax_stage2_mm, 'r', linestyle='', marker='^',
        label='stage2: zemax data')
ax.plot(Zemax_f_mm, Zemax_stage3_mm, 'y', linestyle='', marker='^',
        label='stage3: zemax data')

# curves:
ax.plot(f_mm, stage1_mm, 'b', linestyle='-',  label='stage1: polynomial')
ax.plot(f_mm, stage2_mm, 'r', linestyle='--', label='stage2: polynomial')
ax.plot(f_mm, stage3_mm, 'y', linestyle='-.', label='stage3: polynomial')
# configure:
ax.legend(loc="upper left", framealpha=1)
fig.savefig('zoom_lens_motion.png', dpi=150)
plt.show()
plt.close()
