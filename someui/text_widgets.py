import skia

from someui.widget_extensions import RelativePlaceWidget, hex_str_to_int, ScrollItemWidget


class _TypefaceManager:
    def __init__(self):
        self.cache: dict[str, skia.Typeface] = {}

    def get(self, family, style: skia.FontStyle | None = None):
        font_key = f'{family}_{style}'
        if font_key in self.cache:
            return self.cache[font_key]
        else:
            self.cache[font_key] = tf = skia.Typeface(family, style)
            return tf

typeface_manager = _TypefaceManager()


class Label(ScrollItemWidget):
    def __init__(self, parent, text = '', font: str = 'Inter', font_size: float = 14, typeface: skia.Typeface | None = None, text_color: str = 'white', background_color: str = None, debug=False):
        super().__init__(parent)

        self._text = text
        self._font = font_size
        self._font_size = font_size
        self._debug = debug

        if debug:
            self._debug_red = skia.Paint(0xffff0000)
            self._debug_green = skia.Paint(0xff00ff00)

        self._typeface = typeface or typeface_manager.get(font)

        self._font = skia.Font(self._typeface, self._font_size)

        self._font.setSubpixel(True)
        self._font.setHinting(skia.FontHinting.kNone)
        self._font.setEdging(skia.Font.Edging.kAntiAlias)
        self._font.setLinearMetrics(True)

        self._blob: skia.TextBlob | None = None
        self._blob_dirty = True
        self._text_x_offset_pending = '0'
        self._text_y_offset_pending = '0'
        self._text_x_offset = 0
        self._text_y_offset = 0
        self._text_width = 0
        self._text_height = 0
        self.text_padding = 0

        self.bg_rect = None

        self.text_paint = skia.Paint(hex_str_to_int(text_color))
        if background_color:
            self.bg_paint = skia.Paint(hex_str_to_int(background_color))
        else:
            self.bg_paint = None

        self._rebuild_blob()

    def set_text(self, text=None, x_offset='0', y_offset='0'):
        if text is not None:
            self._text = text
        self._text_x_offset_pending = x_offset
        self._text_y_offset_pending = y_offset
        self._blob_dirty = True
        self.invalidate()

    def _rebuild_blob(self):
        if not self._text.strip():
            self._blob = None
            self.bg_rect = None
            return

        self._blob = skia.TextBlob.MakeFromString(self._text, self._font)
        ink = self._blob.bounds()

        pad = self.text_padding
        w = ink.width() + pad * 2
        h = ink.height() + pad * 2

        # Сдвиг блоба, чтобы его ink-прямоугольник лёг в (pad, pad)
        base_x = pad - ink.left()
        base_y = pad - ink.top()

        self.bg_rect = skia.Rect.MakeXYWH(0, 0, w, h)
        self._text_width, self._text_height = w, h

        # Эти поля уже используются в draw_self, поэтому менять draw не нужно
        self._text_x_offset = base_x
        self._text_y_offset = base_y

        if self._is_fast_pack:
            self.fast_pack()

    def _ensure_blob(self):
        if self._blob_dirty:
            self._rebuild_blob()
            self._blob_dirty = False

    def get_size_hint(self):
        return self._text_width, self._text_height

    def draw_self(self, ctx: skia.Canvas):
        if self._debug:
            print(self.bg_rect)

        if self.bg_paint:
            ctx.drawRect(self.bg_rect, self.bg_paint)
        self._ensure_blob()
        if self._blob is not None:
            ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self.text_paint)


class Button(Label):
    def __init__(self, parent, text = '', command=None, font: str = 'Inter', font_size: float = 14, typeface: skia.Typeface | None = None, text_color: str = '#fff', background_color: str = '#888', click_color='#444', hover_color='#666', debug=False):
        super().__init__(parent, text, font, font_size, typeface, text_color, background_color, debug)

        self.bg_color = background_color
        self.click_color = click_color
        self.hover_color = hover_color

        self._last_color = background_color

        if not self.bg_paint:
            raise ValueError(self.bg_paint)

        self.bg_paint.setAntiAlias(True)
        self.on_mouse_release(self._command_wrapper)
        self.on_mouse_press(lambda *_: self._set_color())
        self.on_hover_enter(lambda *_: self._set_color())
        self.on_hover_exit(lambda *_: self._set_color())
        self.command = command

    def _set_color(self):
        if self.held:
            clr = self.click_color
        elif self.hovered:
            clr = self.hover_color
        else:
            clr = self.bg_color

        if clr != self._last_color:
            self.bg_paint.setColor(hex_str_to_int(clr))
            self._last_color = clr
            self.invalidate()

    def _command_wrapper(self, btn, x, y):
        if btn == 0 and self.command is not None:
            self.command()
        self._set_color()

    def draw_self(self, ctx: skia.Canvas):
        if self._debug:
            print(self.bg_rect, self.width, self.height)

        ctx.drawRRect(skia.RRect(self.bg_rect, 5, 5), self.bg_paint)
        self._ensure_blob()
        ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self.text_paint)