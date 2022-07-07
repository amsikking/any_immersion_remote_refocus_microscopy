import numpy as np

# Zoom_lens_132.5-150mm_motion.ods trendline polynomials
# Data from Zemax
def negative_lens_motion(f_mm):
    motion_mm = (- 0.012921858472509 * f_mm**2
                 + 6.46780791066724 * f_mm
                 - 630.281528419234)
    return motion_mm

def positive_group_motion(f_mm):
    motion_mm = (+ 0.005518525287293 * f_mm**2
                 + 0.885914869404723 * f_mm
                 - 214.401055085496)
    return motion_mm

# Zemax data:
Zemax_f_mm = (132.5, 135.0, 137.5, 140.0, 142.5, 145.0, 147.5, 150.0)
Zemax_N_mm = (0.00, 7.27, 14.58, 21.87, 29.05, 36.03, 42.71, 48.99)
Zemax_P_mm = (0.00, 5.68, 11.61, 17.72, 23.96, 30.23, 36.44, 42.51)

# Input:
f_mm = np.linspace(132.5, 150, 1000)

# Output:
N_zoom_mm = negative_lens_motion(f_mm)
P_zoom_mm = positive_group_motion(f_mm)

# Plot:
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
# labels:
ax.set_title('Zoom lens (constant track length)')
ax.set_ylabel('Motion (mm)')
ax.set_xlabel('Focal length (mm)')
# data:
ax.plot(Zemax_f_mm, Zemax_N_mm, 'b', linestyle='', marker='o',
        label='Zemax negative lens data')
ax.plot(Zemax_f_mm, Zemax_P_mm, 'r', linestyle='', marker='^',
        label='Zemax positive group data')
# curves:
ax.plot(f_mm, N_zoom_mm, 'b', linestyle='-', label='negative lens function')
ax.plot(f_mm, P_zoom_mm, 'r', linestyle='--', label='positive group function')
# configure:
ax.legend(loc="lower right", framealpha=1)
fig.savefig('zoom_lens_motion.png', dpi=150)
plt.show()
plt.close()
