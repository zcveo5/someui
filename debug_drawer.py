import skia

from someui import GLFWWindow, Label, defaults


class Debug(Label):
    def __init__(self, parent, text = '', font_name: str | None = None, font_size: float| None = None,
                 typeface: skia.Typeface | None = None, text_color: str | None = None,
                 background_color: str | None = None, align_x: str = 'left', align_y: str = 'top', debug=False, font_style: skia.FontStyle | None = None):
        super().__init__(parent, text, font_name, font_size, typeface, text_color, background_color, align_x, align_y, debug, font_style)
        self.clip_self = False

    def draw_self(self, ctx: skia.Canvas):
        #super().draw_self(ctx)
        cur = self
        while cur is not None:
            ctx.drawRect(skia.Rect(*cur.visible_rect()), defaults.DEBUG_RED_A)
            cur = cur.parent


root = GLFWWindow()

Debug(root, "hello").place()

root.mainloop()