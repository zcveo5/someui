from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label, Button
from someui.widget_extensions import ScrollContainerWidget

root = GLFWWindow()

container = ScrollContainerWidget(root)
container.set_size(500, 500)

for i in range(50):
    l = Label(container, text=f'Hello {i}')
    l.fast_pack()

root.mainloop()