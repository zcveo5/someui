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
    def __init__(self, parent, text = '', font: str = 'Inter', font_size: float = 14, typeface: skia.Typeface | None = None, text_color: str = 'white', background_color: str = None):
        super().__init__(parent)

        self._text = text
        self._font = font_size
        self._font_size = font_size

        self._typeface = typeface or typeface_manager.get(font)

        self._font = skia.Font(self._typeface, self._font_size)
        self._font.setSubpixel(True)

        self._blob: skia.TextBlob | None = None
        self._blob_dirty = True
        self._text_x_offset_pending = '0'
        self._text_y_offset_pending = '0'
        self._text_x_offset = 0
        self._text_y_offset = 0
        self._text_width = 0
        self._text_height = 0

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

    def _rebuild_blob(self):
        if self._text.strip():
            self._blob = skia.TextBlob.MakeFromString(self._text, self._font)
            rect = self._blob.bounds()
            self._text_width, self._text_height = rect.width(), rect.height()
            self._text_x_offset = float(
                self._text_x_offset_pending.format(half=self._text_width / 2, full=self._text_width,
                                                   fourth=self._text_width / 4))
            self._text_y_offset = float(
                self._text_y_offset_pending.format(half=self._text_height / 2, full=self._text_height,
                                                   fourth=self._text_height / 4)) - self._font.getMetrics().fAscent
        else:
            self._blob = None

    def _ensure_blob(self):
        if self._blob_dirty:
            self._rebuild_blob()
            self._blob_dirty = False

    @property
    def text_metrics(self):
        return self._text_width, self._text_height

    def draw_self(self, ctx: skia.Canvas):
        if self.bg_paint:
            rect = self.skia_rect
            ctx.drawRect(rect, self.bg_paint)
        self._ensure_blob()
        if self._blob is not None:
            ctx.drawTextBlob(self._blob, self.global_x + self._text_x_offset, self.global_y + self._text_y_offset, self.text_paint)