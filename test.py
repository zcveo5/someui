from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label
from someui.widget_extensions import Container

root = GLFWWindow()
root.window_background = 0xffffffff

container = Container(root)

for i in range(1000):
    Label(container, text=f'{i}')

root.mainloop()