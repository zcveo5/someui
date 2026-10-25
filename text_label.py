from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label, Button


root = GLFWWindow()

btn = Button(root, 'Test', None, debug=True)
btn.set_size(*btn.text_metrics)

root.mainloop()