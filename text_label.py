from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label, Button


root = GLFWWindow()

def ext():
    btn.set_text(f'[{btn.text}]')

btn = Button(root, 'Test', ext, debug=True)
btn.place(y='auto')

root.mainloop()