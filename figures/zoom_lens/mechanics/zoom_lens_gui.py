# Imports from the python standard library:
import tkinter as tk

# Our code, one .py file per module, copy files to your local directory:
import tkinter_compound_widgets as tkcw     # github.com/amsikking/tkinter
import zoom_lens # github.com/amsikking/any_immersion_remote_refocus_microscopy

class GuiZoomLens:
    def __init__(self,
                 stage1_port,
                 stage2_port,
                 stage3_port,
                 name='GuiZoomLens',
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.root = tk.Tk()
        self.root.title('Zoom lens GUI')
        if self.verbose:
            print('%s: initializing'%self.name)
        self.zoom_lens = zoom_lens.ZoomLens(stage1_port=stage1_port,
                                            stage2_port=stage2_port,
                                            stage3_port=stage3_port,
                                            verbose=very_verbose)
        frame = tk.LabelFrame(self.root, text='ZOOM LENS', bd=6)
        frame.grid(row=0, column=0, rowspan=1, padx=20, pady=20, sticky='n')
        self.sliderspinbox = tkcw.CheckboxSliderSpinbox(
            frame,
            label='focal length (mm)',
            checkbox_enabled=False,
            slider_length=600,
            tickinterval=17,
            min_value=self.zoom_lens.f_mm_min,
            max_value=self.zoom_lens.f_mm_max,
            default_value=self.zoom_lens.f_mm,
            function=self.function)
        quit_button = tk.Button(
            self.root, text="QUIT", command=self.quit, height=5, width=30)
        quit_button.grid(row=1, column=0, padx=20, pady=20, sticky='n')
        if self.verbose:
            print('%s: -> done.'%self.name)
            print('%s: current f_mm   = %s'%(self.name, self.zoom_lens.f_mm))
        self.root.mainloop()
        self.root.destroy()

    def function(self, slider_value):
        if self.verbose:
            print('%s: moving to f_mm = %s'%(self.name, slider_value))
        self.zoom_lens.set_focal_length_mm(slider_value)
        if self.verbose:
            print('%s: -> done.'%self.name)
        return None

    def quit(self):
        if self.verbose:
            print('%s: closing'%self.name)
        self.zoom_lens.close()
        self.root.quit()
        if self.verbose:
            print('%s: -> done.'%self.name)
        return None

if __name__ == '__main__':
    gui_zoom_lens = GuiZoomLens(
        'COM3',
        'COM5',
        'COM4',
        verbose=True,
        very_verbose=False)
