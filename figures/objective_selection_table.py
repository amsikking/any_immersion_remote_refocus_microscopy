import numpy as np

def objective_properties(part, m, na, imm, wd_um, lambda_um):
    r_min_um = 0.61 * lambda_um / na
    fov_um = 1000 * 20 / m # assume 20mm field number
    n_px = 2 * fov_um / r_min_um
    print('%s:%3ix%0.2f_%s, '%(part, m, na, imm) +
          'WD(um):%3i, '%wd_um +
          'FOV(um):%4i, '%fov_um +          
          'r_min(um):%0.3f, '%r_min_um +
          'px:%i'%n_px)

##124 objectives considered
##Filtered for NA > 0.76 (SOLS condition 1.33sin(35))
##In each immersion category:
##-> lower NA objectives with the same mag discarded
##-> higher mag objectives with the same NA as lower mag discarded
##-> TIRF and MP objectives avoided

# Input:
lambda_um = 0.532

# Highest NA:
objective_properties('MRD70470', 40, 0.95, 'air', 210, lambda_um)
objective_properties('MRY10060', 60, 1.27, 'wat', 180, lambda_um)
objective_properties('MRD73950',100, 1.35, 'sil', 310, lambda_um)
objective_properties('MRD71970',100, 1.45, 'oil', 130, lambda_um)

# Most pixels:
objective_properties('MRD70270', 20, 0.80, 'air', 800, lambda_um)
objective_properties('MRD77200', 20, 0.95, 'wat', 990, lambda_um)
objective_properties('MRD73250', 25, 1.05, 'sil', 550, lambda_um)
objective_properties('MRH01401', 40, 1.30, 'oil', 240, lambda_um)
