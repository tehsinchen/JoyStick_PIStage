import tkinter as tk
from pipython import GCSDevice, pitools


class JoyStick(tk.Frame):

    def __init__(self, root, stage):
        self.stage = GCSDevice()
        self.stage.ConnectUSB(serialnum=stage)
        print('connected: {}'.format(self.stage.qIDN().strip()))
        pitools.startup(self.stage, stages=None, refmodes=None)
        self.x = self.stage.axes[1]
        self.y = self.stage.axes[0]
        self.x_range = [self.stage.qTMN(self.x)[self.x], self.stage.qTMX(self.x)[self.x]]
        self.y_range = [self.stage.qTMN(self.y)[self.y], self.stage.qTMX(self.y)[self.y]]
        self.nb_axis = len(self.stage.axes)
        if self.nb_axis == 3:
            self.z = self.stage.axes[2]
        if self.stage.HasHIN():
            self.stage.HIN(self.x, False)
            self.stage.HIN(self.y, False)

        self.popup_win = tk.Toplevel(root)
        dev = self.stage.devname.split('.')[0]
        self.popup_win.wm_title(f"{dev}  Controller")
        self.popup_win.geometry('320x320')
        self.popup_win.configure(bg='white')
        self.popup_win.resizable(0, 0)
        self.popup_win.update()
        self.wn_size = self.popup_win.winfo_width()
        self.wn_pos = [self.popup_win.winfo_rootx(), self.popup_win.winfo_rooty()]
        self.radius = 110
        pad = 200
        self.canvas_range = tk.Canvas(self.popup_win,
                                      bg='white',
                                      borderwidth=0,
                                      highlightthickness=0)
        range_pos = (self.wn_size-(self.radius+pad))*0.5
        range_size = (self.radius+pad)
        relsize = range_size / self.wn_size
        self.canvas_range.place(x=range_pos, y=range_pos, relwidth=relsize, relheight=relsize)
        self.create_circle(range_size // 2, range_size // 2, self.radius, self.canvas_range, None)

        if self.nb_axis == 3:
            self.canvas_range.bind('<Enter>', self.bound_to_mousewheel)
            self.canvas_range.bind('<Leave>', self.unbound_to_mousewheel)

        self.dot = tk.Canvas(self.canvas_range,
                             bg='white',
                             borderwidth=0,
                             highlightthickness=0)
        size_ratio = 3
        dot_size = range_size / size_ratio
        self.dot_pos = (range_size-dot_size)*0.5
        self.dot.place(x=self.dot_pos, y=self.dot_pos, relwidth=1/size_ratio, relheight=1/size_ratio)
        self.create_circle(dot_size // 2, dot_size // 2, dot_size*0.8//2, self.dot, 'black')
        self.dot.bind("<Motion>", self.mouse_appearance)
        self.dot.bind("<B1-Motion>", self.drag)
        self.dot.bind("<ButtonRelease-1>", self.centralize)
        self.offset = dot_size - range_pos - dot_size*0.2*2

        self.generator = 0
        self.pressed = False
        self.increment_x = 0
        self.increment_y = 0

    @staticmethod
    def create_circle(x, y, r, canvas, fill):  # center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        return canvas.create_oval(x0, y0, x1, y1, outline='black', width=2, fill=fill)

    def bound_to_mousewheel(self, event):
        self.canvas_range.bind("<MouseWheel>", self.set_piezo_axis)

    def unbound_to_mousewheel(self, event):
        self.canvas_range.unbind("<MouseWheel>")
        pitools.waitontarget(self.stage, axes=[self.z])

    def drag(self, event):
        self.pressed = True
        if self.generator == 0:
            self.set_stage()
        cur_wn_pos = [self.popup_win.winfo_rootx(), self.popup_win.winfo_rooty()]
        if cur_wn_pos != self.wn_pos:
            self.wn_pos = cur_wn_pos
        x = event.widget.winfo_pointerx()-self.wn_pos[0]-self.offset
        y = event.widget.winfo_pointery()-self.wn_pos[1]-self.offset
        x, y = self.get_coord(x, y)
        event.widget.place(x=x, y=y)
    
    def mouse_appearance(self, event):
        self.dot.config(cursor="hand2")

    def centralize(self, event):
        self.pressed = False
        self.dot.place(x=self.dot_pos, y=self.dot_pos)
        pitools.waitontarget(self.stage, axes=[self.x, self.y])

    def get_coord(self, x, y):
        delta_x = self.dot_pos-x
        delta_y = self.dot_pos-y
        radius = (delta_x**2 + delta_y**2)**0.5
        ratio = radius/self.radius
        if ratio <= 1:
            self.increment_x = (x-self.dot_pos) / self.radius
            self.increment_y = (self.dot_pos-y) / self.radius
            return x, y
        else:
            if delta_x < 0:
                edge_x = abs(delta_x/ratio) + self.dot_pos
            else:
                edge_x = self.dot_pos - (delta_x/ratio)
            if delta_y < 0:
                edge_y = abs(delta_y/ratio) + self.dot_pos
            else:
                edge_y = self.dot_pos - (delta_y/ratio)
            self.increment_x = (edge_x-self.dot_pos) / self.radius
            self.increment_y = (self.dot_pos- edge_y) / self.radius
            return edge_x, edge_y

    def set_stage(self):
        cur_pos = [self.stage.qPOS(self.x)[self.x],
                   self.stage.qPOS(self.y)[self.y]]
        self.generator = 0
        if self.pressed:
            if self.nb_axis == 3:
                increment_x = -self.increment_x
                increment_y = -self.increment_y
                unit_x = unit_y = self.stage.qVEL(self.x)[self.x] * 4
            else:
                increment_x = self.increment_x
                increment_y = self.increment_y
                unit_x = 0.02 * (1 + abs(increment_x))
                unit_y = 0.02 * (1 + abs(increment_y))
                self.stage.VEL(self.x, unit_x * abs(increment_x))
                self.stage.VEL(self.y, unit_y * abs(increment_y))
            target_x = cur_pos[0] + unit_x * increment_x
            target_y = cur_pos[1] + unit_y * increment_y
            if self.x_range[0] < target_x < self.x_range[1]:
                self.stage.MOV(self.x, target_x)
            if self.y_range[0] < target_y < self.y_range[1]:
                self.stage.MOV(self.y, target_y)
            self.generator = root.after(time_unit, self.set_stage)
        else:
            if self.generator != 0:
                root.after_cancel(self.generator)

    def set_piezo_axis(self, event):
        cur_z = self.stage.qPOS(self.z)[self.z]
        target_z = cur_z + event.delta / 1200
        self.stage.MOV(self.z, target_z)


class Main(tk.Frame):

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        popup_win = tk.Toplevel(root)
        popup_win.wm_title("JoyStick Control")
        popup_win.geometry('350x200')
        popup_win.configure(bg='white')
        popup_win.resizable(0, 0)

        sn_label_1 = tk.Label(popup_win, text='Serial Number 1:',
                              bg='white', font='Arial 12',)
        sn_label_1.place(relx=0.05, rely=0.2)
        self.sn_entry_1 = tk.Entry(popup_win, width=20)
        self.sn_entry_1.place(relx=0.45, rely=0.22)

        sn_label_2 = tk.Label(popup_win, text='Serial Number 2:',
                              bg='white', font='Arial 12', )
        sn_label_2.place(relx=0.05, rely=0.5)
        self.sn_entry_2 = tk.Entry(popup_win, width=20)
        self.sn_entry_2.place(relx=0.45, rely=0.52)

        enter_btn = tk.Button(popup_win, text='Enter',
                              font='Arial 12', width=12,
                              command=lambda: [self.get_joystick(),
                                               popup_win.destroy()])
        enter_btn.place(relx=0.52, rely=0.78)

    def get_joystick(self):
        stage1 = self.sn_entry_1.get()
        stage2 = self.sn_entry_2.get()
        if stage1 != '':
            JoyStick(root, stage1)
        if stage2 != '' and stage2 != stage1:
            JoyStick(root, stage2)


if __name__ == '__main__':
    root = tk.Tk()
    root.iconify()
    Main(root)
    root.mainloop()
