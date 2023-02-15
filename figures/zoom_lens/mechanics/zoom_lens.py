import thorlabs_DDS050
import thorlabs_DDS100

class ZoomLens:
    def __init__(self,
                 stage1_port,
                 stage2_port,
                 stage3_port,
                 name='Zoom_lens',
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        self.stage1_set_point_mm = 48
        self.stage2_set_point_mm = 73
        self.stage3_set_point_mm = 48
        self.stage1 = thorlabs_DDS050.Controller(
            which_port=stage1_port, verbose=verbose, very_verbose=very_verbose)
        self.stage1.move_mm(self.stage1_set_point_mm, relative=False)
        self.stage2 = thorlabs_DDS100.Controller(
            which_port=stage2_port, verbose=verbose, very_verbose=very_verbose)
        self.stage2.move_mm(self.stage2_set_point_mm, relative=False)
        self.stage3 = thorlabs_DDS050.Controller(
            which_port=stage3_port, verbose=verbose, very_verbose=very_verbose)
        self.stage3.move_mm(self.stage3_set_point_mm, relative=False)
        self.f_mm = 132.5
        self.f_mm_min = 132.5
        self.f_mm_max = 150.0

    def focal_length_to_lens_motion(self, f_mm): # Zemax data
        stage1_mm = (-     0.000103278288*f_mm**4
                     +     0.059929457484*f_mm**3
                     -    13.033982374525*f_mm**2
                     +  1260.150733009070*f_mm
                     - 45717.573446038700)
        stage2_mm = (-     0.000083979119*f_mm**4
                     +     0.049656589716*f_mm**3
                     -    10.961078884881*f_mm**2
                     +  1074.586675413890*f_mm
                     - 39574.398463977100)
        stage3_mm = (+    0.000018343468*f_mm**4
                     -    0.009692931167*f_mm**3
                     +    1.950506313955*f_mm**2
                     -  175.313955214639*f_mm
                     + 5879.390039195720)
        return stage1_mm, stage2_mm, stage3_mm

    def set_focal_length_mm(self, f_mm):
        assert self.f_mm_min <= f_mm <= self.f_mm_max
        stage1_mm, stage2_mm, stage3_mm = self.focal_length_to_lens_motion(f_mm)
        if self.verbose:
            print('requested focal length = %0.2f'%f_mm)
            print('stage1_mm  = %0.2f'%stage1_mm)
            print('stage2_mm  = %0.2f'%stage2_mm)
            print('stage3_mm  = %0.2f'%stage3_mm)
        stage1_move_mm = self.stage1_set_point_mm - stage1_mm
        stage2_move_mm = self.stage2_set_point_mm - stage2_mm
        stage3_move_mm = self.stage3_set_point_mm - stage3_mm
        if f_mm > self.f_mm:
            self.stage3.move_mm(stage3_move_mm, relative=False, block=False)
            self.stage2.move_mm(stage2_move_mm, relative=False, block=False)
            self.stage1.move_mm(stage1_move_mm, relative=False, block=False)
            self.stage3._finish_move()
            self.stage2._finish_move()
            self.stage1._finish_move()
        if f_mm < self.f_mm:
            self.stage1.move_mm(stage1_move_mm, relative=False, block=False)
            self.stage2.move_mm(stage2_move_mm, relative=False, block=False)
            self.stage3.move_mm(stage3_move_mm, relative=False, block=False)
            self.stage1._finish_move()
            self.stage2._finish_move()
            self.stage3._finish_move()
        self.f_mm = f_mm
        if self.verbose:
            print('-> set focal length = %0.2f'%self.f_mm)

    def close(self):
        if self.verbose: print("%s: closing..."%self.name, end=' ')
        self.stage3.move_mm(0, relative=False, block=False)
        self.stage2.move_mm(0, relative=False, block=False)
        self.stage1.move_mm(0, relative=False, block=False)        
        self.stage3._finish_move()
        self.stage2._finish_move()
        self.stage1._finish_move()        
        self.stage3.close()
        self.stage2.close()
        self.stage1.close()
        if self.verbose: print("done.")
        return None

if __name__ == '__main__':
    import numpy as np
    import time
    
    zoom_lens = ZoomLens(
        stage1_port='COM3', stage2_port='COM5', stage3_port='COM4')

    print('\n# Configuration focal lengths:')
    config_f_mm = np.linspace(132.5, 150, 8)
    for f_mm in config_f_mm:
        zoom_lens.set_focal_length_mm(f_mm)
        time.sleep(0.2)

    print('\n# Focal lengths in steps of 0.1 RI:')
    step_f_mm = np.linspace(132.5, 150, 19)
    for f_mm in step_f_mm:
        zoom_lens.set_focal_length_mm(f_mm)

    print('\n# Some random focal lengths:')
    from random import uniform
    for i in range(10):
        random_f_mm = uniform(132.5, 150)
        zoom_lens.set_focal_length_mm(random_f_mm)
        time.sleep(0.2)

    zoom_lens.close()
