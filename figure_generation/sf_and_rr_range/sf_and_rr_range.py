import numpy as np

# Standard focus range:
def sf_range(na, n_i, wd_mm, n_s, lambda_um):
    theta_i = np.arcsin(na / n_i)
    a = lambda_um / (2 * np.sin(theta_i/2)**4)
    b = abs(n_s**3 / (n_i**2 * (n_s**2 - n_i**2)))
    z_um = a * b
    wd_um = 1000 * wd_mm
    z_sf_max_um = np.where(z_um <= wd_um, z_um, wd_um) # working distance limit
    return z_sf_max_um

# Remote refocus range:
def rr_range(m, na, n_s, lambda_um):
    f_um = 1000 * 200 / m # objective focal length (200mm tube lens)
    na = np.where(na <= n_s, na, n_s) # limit na <= b_bio
    theta_s = np.arcsin(na / n_s)
    a = 1 / (2 * np.sin(theta_s/2)**2)
    b = 15*lambda_um**2 * f_um**2 * (3 + 8*np.cos(theta_s) + np.cos(2*theta_s))
    c = np.pi**2 * n_s**2 * (3 + 16*np.cos(theta_s) + np.cos(2*theta_s))
    z_rr_max_um = a * (b / c)**0.25
    return z_rr_max_um

# Combined range:
def combined_range(m, na, n_i, wd_mm, n_s, lambda_um):
    z_sf_max_um = sf_range(na, n_i, wd_mm, n_s, lambda_um)
    z_rr_max_um = rr_range(m, na, n_s, lambda_um)
    z_max_um = z_sf_max_um + z_rr_max_um
    return z_sf_max_um, z_max_um

# Input:
lambda_um = 0.532
n_s = np.linspace(1.325, 1.515, 1000)

# Highest NA:
N040x_air = combined_range( 40, 0.95, 1.00, 0.210, n_s, lambda_um)
N060x_wat = combined_range( 60, 1.27, 1.33, 0.180, n_s, lambda_um)
N100x_sil = combined_range(100, 1.35, 1.41, 0.310, n_s, lambda_um)
N100x_oil = combined_range(100, 1.45, 1.51, 0.130, n_s, lambda_um)

# Most pixels:
N020x_air = combined_range( 20, 0.80, 1.00, 0.800, n_s, lambda_um)
N020x_wat = combined_range( 20, 0.95, 1.33, 0.990, n_s, lambda_um)
N025x_sil = combined_range( 25, 1.05, 1.41, 0.550, n_s, lambda_um)
N040x_oil = combined_range( 40, 1.30, 1.51, 0.240, n_s, lambda_um)

# Plot:
import matplotlib.pyplot as plt

def plot(title, obj_name, obj_data, y_limits, filename, log=False, show=False):
    fig, ax = plt.subplots()
    # labels:
    ax.set_title(title)
    ax.set_ylabel('Diffraction limited depth (µm)')
    ax.set_xlabel('Sample refractive index')
    # curves:
    ax.plot(n_s, obj_data[0], 'c', linestyle='-',
            label='%s (≥%iµm)'%(obj_name[0], min(obj_data[0])))
    ax.plot(n_s, obj_data[1], 'b', linestyle=':',
            label='%s (≥%iµm)'%(obj_name[1], min(obj_data[1])))
    ax.plot(n_s, obj_data[2], 'y', linestyle='--',
            label='%s (≥%iµm)'%(obj_name[2], min(obj_data[2])))
    ax.plot(n_s, obj_data[3], 'r', linestyle='-.',
            label='%s (≥%iµm)'%(obj_name[3], min(obj_data[3])))
    # lines:
    ax.axvline(x=1.33, color='b', linestyle=':')
    ax.axvline(x=1.41, color='y', linestyle='--')
    ax.axvline(x=1.51, color='r', linestyle='-.')
    ax.axhline(y=min(obj_data[3]), color='k', linestyle=(0,(1,1)),
               label='lower bound (%iµm)'%min(obj_data[3]))
    # configure:
    ax.set_xlim(xmin=n_s[0], xmax=n_s[-1])
    ax.set_xticks(np.linspace(1.33, 1.51, 10))
    ax.legend(loc="upper right", framealpha=1)
    if log:
        ax.set_yscale('log')
    else:
        ax.set_ylim(ymin=y_limits[0], ymax=y_limits[1])
    fig.savefig(filename, dpi=150)
    if show:
        plt.show()
    plt.close()

lambda_nm = 1000*lambda_um

# Highest NA:
obj_name = (' 40x0.95 air', ' 60x1.27 wat', '100x1.35 sil', '100x1.45 oil')
y_limits = (0, 400)
# standard:
title = ('Standard focus range (%inm)\n'%lambda_nm)
obj_data = (N040x_air[0], N060x_wat[0], N100x_sil[0], N100x_oil[0])
filename = 'sf_range_highest_na.png'
plot(title, obj_name, obj_data, y_limits, filename)
title = ('Standard focus range (%inm, log scale)\n'%lambda_nm)
filename = 'sf_range_highest_na_log.png'
plot(title, obj_name, obj_data, y_limits, filename, log=True)
# combined:
title = ('Standard focus and remote refocus range (%inm)\n'%lambda_nm)
obj_data = (N040x_air[1], N060x_wat[1], N100x_sil[1], N100x_oil[1])
filename = 'sf_and_rr_range_highest_na.png'
plot(title, obj_name, obj_data, y_limits, filename)
title = ('Standard focus and remote refocus range (%inm, log scale)\n'%
         lambda_nm)
filename = 'sf_and_rr_range_highest_na_log.png'
plot(title, obj_name, obj_data, y_limits, filename, log=True)

# Most pixels:
obj_name = ('20x0.80 air', '20x0.95 wat', '25x1.05 sil', '40x1.30 oil')
y_limits = (0, 1250)
# standard:
title = ('Standard focus range (%inm)\n'%lambda_nm)
obj_data = (N020x_air[0], N020x_wat[0], N025x_sil[0], N040x_oil[0])
filename = 'sf_range_most_pixels.png'
plot(title, obj_name, obj_data, y_limits, filename)
title = ('Standard focus range (%inm, log scale)\n'%lambda_nm)
filename = 'sf_range_most_pixels_log.png'
plot(title, obj_name, obj_data, y_limits, filename, log=True)
# combined:
title = ('Standard focus and remote refocus range (%inm)\n'%lambda_nm)
obj_data = (N020x_air[1], N020x_wat[1], N025x_sil[1], N040x_oil[1])
filename = 'sf_and_rr_range_most_pixels.png'
plot(title, obj_name, obj_data, y_limits, filename)
title = ('Standard focus and remote refocus range:(%inm, log scale)\n'%
         lambda_nm)
filename = 'sf_and_rr_range_most_pixels_log.png'
plot(title, obj_name, obj_data, y_limits, filename, log=True)
