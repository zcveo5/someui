import skia
from someui.text_basic import BaseTextWidget, hex_str_to_int, defaults


class Button(BaseTextWidget):
    def __init__(self, parent, text = '', command=None, font: str | None = None, font_size: float | None = None, typeface: skia.Typeface | None = None,
                 text_color: str | None = None, background_color: str | None = None, click_color: str | None = None, hover_color: str | None = None, debug=False, font_style=None):
        super().__init__(parent, text, font, font_size, typeface, text_color, background_color, 'center', 'center', debug, font_style)

        self._bg_color = background_color if background_color else self.defaults.bg
        self._click_color = click_color if click_color else self.defaults.click_color
        self._hover_color = hover_color if hover_color else self.defaults.hover_color

        self._bg_paint =    skia.Paint(hex_str_to_int(background_color)) if background_color else defaults.RootPaints.bg_paint
        self._click_paint = skia.Paint(hex_str_to_int(click_color)) if click_color else defaults.RootPaints.click_paint
        self._hover_paint = skia.Paint(hex_str_to_int(hover_color)) if hover_color else defaults.RootPaints.hover_paint

        if text_color:
            self._counter_paint = skia.Paint(hex_str_to_int(text_color))
            self._counter_paint.setAntiAlias(True)
            self._counter_paint.setStyle(skia.Paint.kStroke_Style)
            self._counter_paint.setStrokeWidth(1)
            self._counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
            self._counter_paint.setStrokeJoin(skia.Paint.kRound_Join)
        else:
            self._counter_paint = defaults.RootPaints.counter_paint

        self._active_paint = self._bg_paint

        self.on_mouse_release(self._command_wrapper)
        self.on_mouse_press(lambda *_: self._set_color())
        self.on_hover_enter(lambda *_: self._set_color())
        self.on_hover_exit(lambda *_: self._set_color())
        self.command = command

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self.set_text(value)

    def _set_color(self):
        if self.held:
            clr = self._click_paint
        elif self.hovered:
            clr = self._hover_paint
        else:
            clr = self._bg_paint

        self._active_paint = clr
        self.invalidate()

    def _command_wrapper(self, btn, x, y):
        if btn == 0 and self.command is not None:
            self.command()
        self._set_color()

    def draw_self(self, ctx: skia.Canvas):
        r = skia.RRect(skia.Rect(0, 0, self.width, self.height), 5, 5)

        ctx.drawRRect(r, self._active_paint)
        ctx.drawRRect(r, self._counter_paint)
        self._ensure_blob()
        ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self._text_paint)
