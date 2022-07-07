# Zoom_lens_132.5-150mm_motion.ods trendline polynomials
# Data from Zemax
def negative_lens_motion(f_mm):
    motion_mm = (- 0.012921858472509 * f_mm**2
                 + 6.467807910667240 * f_mm
                 - 630.2815284192340)
    return motion_mm

def positive_group_motion(f_mm):
    motion_mm = (+ 0.005518525287293 * f_mm**2
                 + 0.885914869404723 * f_mm
                 - 214.4010550854960)
    return motion_mm

# Input:
f_mm = 140
N_motion = negative_lens_motion(f_mm)
P_motion = positive_group_motion(f_mm)
print('requested focal length = %0.2f'%f_mm)
print('negative lens motion   = %0.2f'%N_motion)
print('positive group motion  = %0.2f'%P_motion)

# Output:
## requested focal length = 140.00
## negative lens motion   = 21.94
## positive group motion  = 17.79
