import skia
from someui.util import hex_str_to_int
from someui.widget_extensions import ScrollItemWidget
from someui import defaults


class _TypefaceManager:
    def __init__(self):
        self.cache: dict[str, dict] = {}

    def get(self, family, style: skia.FontStyle | None = None):
        if style is None:
            style = skia.FontStyle.Normal()
        font_key = f'{family}{style.slant()}{style.weight()}{style.weight()}'
        if font_key in self.cache:
            self.cache[font_key]['refcount'] += 1
            return self.cache[font_key]['font']
        else:
            tf = skia.Typeface(family, style)
            self.cache[font_key] = {'font': tf, 'refcount': 1}
            return tf

    def sub_ref(self, tf: skia.Typeface):
        family = tf.getFamilyName()
        style = tf.fontStyle()
        font_key = f'{family}{style.slant()}{style.weight()}{style.weight()}'
        self.cache[font_key]['refcount'] -= 1
        if self.cache[font_key]['refcount'] <= 0:
            del self.cache[font_key]

typeface_manager = _TypefaceManager()


class BaseTextWidget(ScrollItemWidget):
    def __init__(self, parent, text = '', font_name: str | None = None, font_size: float| None = None,
                 typeface: skia.Typeface | None = None, text_color: str | None = None,
                 background_color: str | None = None, align_x: str = 'left', align_y: str = 'top', debug=False, font_style: skia.FontStyle | None = None):
        super().__init__(parent)

        if not font_name:
            font_name = self.defaults.font

        if not font_size:
            font_size = self.defaults.font_size

        self._text = text
        self._font_size = font_size

        self._typeface = typeface or typeface_manager.get(font_name, font_style)

        self._font = skia.Font(self._typeface, self._font_size)

        self._font.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
        self._font.setHinting(skia.FontHinting.kNormal)
        self._font.setSubpixel(True)
        self._font.setLinearMetrics(True)

        self._blob: skia.TextBlob | None = None
        self._blob_dirty = True
        self._text_x_offset = 0
        self._text_y_offset = 0
        self._text_width = 0
        self._text_height = 0
        self.text_pad_x = 12
        self.text_pad_y = 6
        self._align_x = align_x
        self._align_y = align_y

        self._text_paint = skia.Paint(hex_str_to_int(text_color)) if text_color else defaults.RootPaints.fg_paint
        self._bg_paint = skia.Paint(hex_str_to_int(background_color)) if background_color else defaults.RootPaints.bg_paint

        self._rebuild_blob()
        self.on_resize(lambda *_: self._rebuild_blob())

    def set_colors(self, *, text_color=None, bg_color=None):
        if text_color:
            self._text_paint.setColor(hex_str_to_int(text_color))
        if bg_color:
            self._bg_paint.setColor(bg_color)

    def set_align(self, align_x: str | None = None, align_y: str | None = None):
        if align_x is not None:
            self._align_x = align_x
        if align_y is not None:
            self._align_y = align_y
        self._blob_dirty = True
        self.invalidate()

    def set_text(self, text):
        self._text = text
        self._blob_dirty = True
        self.invalidate()

    def _rebuild_blob(self):
        if not self._text.strip():
            self._blob = None
            self._text_width, self._text_height = 0, 0
            return

        if self._blob_dirty:
            self._blob = skia.TextBlob.MakeFromString(self._text, self._font)

        ink = self._blob.bounds()

        content_w = self._font.measureText(self._text)
        content_h = ink.height()

        widget_w = max(self.width, content_w + self.text_pad_x)
        widget_h = max(self.height, content_h + self.text_pad_y)

        if self._align_x == 'center':
            base_x = (widget_w - content_w) / 2
        elif self._align_x == 'right':
            base_x = widget_w - self.text_pad_x - content_w
        else:
            base_x = self.text_pad_x

        if self._align_y == 'center':
            base_y = (widget_h - content_h) / 2 - ink.top()
        elif self._align_y == 'bottom':
            base_y = widget_h - self.text_pad_y - content_h - ink.top()
        else:
            base_y = self.text_pad_y - ink.top()

        self._text_width = widget_w
        self._text_height = widget_h

        self._text_x_offset = base_x
        self._text_y_offset = base_y

        self.invalidate_place()

    def _ensure_blob(self):
        if self._blob_dirty:
            self._rebuild_blob()
            self._blob_dirty = False

    def get_size_hint(self):
        return self._text_width, self._text_height

    def draw_self(self, ctx: skia.Canvas):
        if self._bg_paint:
            ctx.drawRect(skia.Rect(0, 0, self.width, self.height), self._bg_paint)
        self._ensure_blob()
        if self._blob is not None:
            ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self._text_paint)

    def destroy_render_resources(self):
        typeface_manager.sub_ref(self._typeface)


Label = BaseTextWidget