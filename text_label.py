from someui.crossplatform.headerless_styles import HeaderlessWindow
from someui.text_basic import Label


def _test(_=None):
    lbl.set_text(root.headerless.debug())

    root.call_after(_test, 0.2)


root = HeaderlessWindow()

lbl = Label(root, 'hello')
_test()

root.mainloop()