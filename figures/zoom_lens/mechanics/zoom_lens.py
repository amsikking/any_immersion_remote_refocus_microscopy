# Imports from the python standard library:
from threading import Thread

# Our code, one .py file per module, copy files to your local directory:
import thorlabs_DDS050  # github.com/amsikking/thorlabs_DDS100
import thorlabs_DDS100  # github.com/amsikking/thorlabs_DDS050

class ZoomLens:
    def __init__(self,
                 stage1_port,
                 stage2_port,
                 stage3_port,
                 name='Zoom_lens',
                 verbose=True,
                 very_verbose=False,
                 fast_init=True): # set False and push stages to 0mm to reset
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        if self.verbose: print("%s: opening..."%self.name)
        # setup init threads and set points:
        self.stage1_set_point_mm = 48
        self.stage2_set_point_mm = 73
        self.stage3_set_point_mm = 48
        init_stage1 = Thread(target=self._init_stage1, args=(stage1_port,))
        init_stage2 = Thread(target=self._init_stage2, args=(stage2_port,))
        init_stage3 = Thread(target=self._init_stage3, args=(stage3_port,))
        # initialize and home:
        if fast_init: # home simultanously -> requires correct start positions
            init_stage1.start()
            init_stage2.start()
            init_stage3.start()
            init_stage3.join()
            init_stage1.join()
            init_stage2.join()
            self.stage1.move_mm(
                self.stage1_set_point_mm, relative=False, block=False)
            self.stage2.move_mm(
                self.stage2_set_point_mm, relative=False, block=False)
            self.stage3.move_mm(
                self.stage3_set_point_mm, relative=False, block=False)
            self.stage1._finish_move()
            self.stage2._finish_move()
            self.stage3._finish_move()
        if not fast_init: # home stages one at a time -> slower but more robust
            init_stage1.start()
            init_stage1.join()
            self.stage1.move_mm(self.stage1_set_point_mm, relative=False)
            init_stage2.start()
            init_stage2.join()
            self.stage2.move_mm(self.stage2_set_point_mm, relative=False)            
            init_stage3.start()
            init_stage3.join()
            self.stage3.move_mm(self.stage3_set_point_mm, relative=False)
        self.f_mm = 132.5
        self.f_mm_min = 132.5
        self.f_mm_max = 150.0
        self.set_focal_length_mm(132.5)
        if self.verbose: print("%s: done opening"%self.name)

    def _init_stage1(self, stage1_port):
        self.stage1 = thorlabs_DDS050.Controller(
            which_port=stage1_port,
            verbose=self.verbose,
            very_verbose=self.very_verbose)
        return None

    def _init_stage2(self, stage2_port):
        self.stage2 = thorlabs_DDS100.Controller(
            which_port=stage2_port,
            verbose=self.verbose,
            very_verbose=self.very_verbose)
        return None

    def _init_stage3(self, stage3_port):
        self.stage3 = thorlabs_DDS050.Controller(
            which_port=stage3_port,
            verbose=self.verbose,
            very_verbose=self.very_verbose)
        return None

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
            print('%s: requested focal length = %0.2f'%(self.name, f_mm))
            print('%s: stage1_mm  = %0.2f'%(self.name, stage1_mm))
            print('%s: stage2_mm  = %0.2f'%(self.name, stage2_mm))
            print('%s: stage3_mm  = %0.2f'%(self.name, stage3_mm))
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
            print('%s: -> set focal length = %0.2f'%(self.name, self.f_mm))
        return None

    def close(self):
        if self.verbose: print("%s: closing..."%self.name)
        # park stages in carefully chosen locations so they don't collide
        # during the init!
        self.stage3.move_mm(0, relative=False, block=False)        
        self.stage2.move_mm(0, relative=False, block=False)
        self.stage1.move_mm(20, relative=False, block=False) # 20 for fast_init!
        self.stage3._finish_move()
        self.stage2._finish_move()
        self.stage1._finish_move()        
        self.stage3.close()
        self.stage2.close()
        self.stage1.close()
        if self.verbose: print("%s: done closing."%self.name)
        return None

if __name__ == '__main__':
    import numpy as np
    import time

    zoom_lens = ZoomLens(stage1_port='COM3',
                         stage2_port='COM5',
                         stage3_port='COM4',
                         verbose=True,
                         very_verbose=False,
                         fast_init=True)

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
