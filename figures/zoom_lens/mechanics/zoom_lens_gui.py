import tkinter as tk

import tkinter_compound_widgets as tki_cw # https://github.com/amsikking/tkinter
import zoom_lens

class GuiZoomLens:
    def __init__(self, master, name='GuiZoomLens'):
        self.master = master
        self.name = name
        print('%s: initializing'%self.name)
        self.zoom_lens = zoom_lens.ZoomLens(
            stage1_port='COM3',
            stage2_port='COM5',
            stage3_port='COM4',
            verbose=False)
        frame = tk.LabelFrame(master, text='ZOOM LENS', bd=6)
        frame.grid(row=0, column=0, rowspan=1, padx=20, pady=20, sticky='n')
        self.sliderspinbox = tki_cw.CheckboxSliderSpinbox(
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
            root, text="QUIT", command=self.quit, height=5, width=30)
        quit_button.grid(row=1, column=0, padx=20, pady=20, sticky='n')
        print('%s: -> done.'%self.name)
        print('%s: current f_mm   = %s'%(self.name, self.zoom_lens.f_mm))

    def function(self, slider_value):
        print('%s: moving to f_mm = %s'%(self.name, slider_value))
        self.zoom_lens.set_focal_length_mm(slider_value)
        print('%s: -> done.'%self.name)

    def quit(self):
        print('%s: closing'%self.name)
        self.zoom_lens.set_focal_length_mm(self.zoom_lens.f_mm_max)
        self.zoom_lens.close()
        self.master.quit()
        print('%s: -> done.'%self.name)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Zoom lens GUI')
    gui_zoom_lens = GuiZoomLens(root)
    root.mainloop()
    root.destroy()
