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

# Input:
focal_length_to_lens_motion(140)

# Output:
## f_mm = 140.00
## stage1_mm = 8.52
## stage2_mm = 26.85
## stage3_mm = 14.78
