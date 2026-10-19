import time

from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label, Button
from someui.widget_extensions import Container

root = GLFWWindow()
root.scale_mod = 2.0

inf_fmt = 'cursor at: {}, {}'

lbl_cursor = Label(root, '')
lbl_cursor.set_size(*lbl_cursor.text_metrics)
lbl_click = Label(root, '')
lbl_click.set_position(0, lbl_cursor.global_y1)
lbl_click.set_size(*lbl_click.text_metrics)

lbl = Button(root, 'This should be at x:100 y:100', font_size=16, command=lambda: print('123'))
lbl.set_position(100, 100)
lbl.set_size(*lbl.text_metrics)

hover = Container(root, '#ff0000ff')
hover.set_size(5, 5)

last_frame_at = time.time()

last_mouse_x, last_mouse_y = 0, 0
last_event_time = time.time()
smoothed_velocity = 0.0

@root.on_mouse_press
def press(button, x, y):
    lbl

@root.on_mouse_exit
def exit_mouse(*args):
    lbl_cursor.text_paint.setColor(0xffff0000)

@root.on_mouse_enter
def enter_mouse(*args):
    lbl_cursor.text_paint.setColor(0xffffffff)

@root.on_hover
def w(x, y):
    global last_mouse_x, last_mouse_y, last_event_time, smoothed_velocity
    global last_frame_at
    lbl_cursor.set_text(inf_fmt.format(
        str(round(x)).zfill(4), str(round(y)).zfill(4),
    ))
    hover.set_position(x, y)

root.mainloop()