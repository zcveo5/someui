import skia

import someui
from someui import Widget


class Cursor(someui.Label):
    def __init__(self, parent: Widget):
        super().__init__(parent)
        self.z = 9999

        self.window.on_hover(self._on_hover)

    def _on_hover(self, x, y):
        self.set_text(f'x:{x}, y:{y}')

        x1 = x + self._text_width
        y1 = y + self._text_height

        if x1 > self.parent.width:
            x = x - self._text_width

        if y1 > self.parent.height:
            y = y - self._text_height

        self.set_position(x, y)

        self.set_size(self._text_width, self._text_height)

    def draw_self(self, ctx: skia.Canvas):
        super().draw_self(ctx)
