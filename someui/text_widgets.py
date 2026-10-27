import traceback

import skia

from someui.widget_extensions import RelativePlaceWidget, hex_str_to_int, ScrollItemWidget
from someui._logging import Logger


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
    def __init__(self, parent, text = '', font: str = 'Inter', font_size: float = 14,
                 typeface: skia.Typeface | None = None, text_color: str = 'white',
                 background_color: str = None, align_x: str = 'left', align_y: str = 'top', debug=False):
        super().__init__(parent)

        self._text = text
        self._font = font_size
        self._font_size = font_size
        self._debug = debug

        if debug:
            self._debug_red = skia.Paint(0xffff0000)
            self._debug_green = skia.Paint(0xff00ff00)
            self._logger = Logger.make_from_file(f'LabelDebug{self.id}')
            self._logger.info(f'{self} Start')

        self._typeface = typeface or typeface_manager.get(font)

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
        self.text_padding = 0
        self._align_x = align_x
        self._align_y = align_y

        self.text_paint = skia.Paint(hex_str_to_int(text_color))
        if background_color:
            self.bg_paint = skia.Paint(hex_str_to_int(background_color))
        else:
            self.bg_paint = None

        self._rebuild_blob()
        self.on_resize(lambda *_: self._rebuild_blob())

    def set_align(self, align_x: str = None, align_y: str = None):
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

        pad = self.text_padding

        # Базовый размер текста по bounding box с учетом паддингов
        content_w = ink.width()
        content_h = ink.height()

        # Размеры виджета (если он уже прошел лейаут, иначе fallback на размер контента)
        widget_w = max(self.width, content_w + pad * 2)
        widget_h = max(self.height, content_h + pad * 2)

        # --- Горизонтальное выравнивание (X) ---
        if self._align_x == 'center':
            # Центрируем относительно ширины виджета
            base_x = (widget_w - content_w) / 2 - ink.left()
        elif self._align_x == 'right':
            # Прижимаем к правому краю
            base_x = widget_w - pad - content_w - ink.left()
        else:  # 'left' по умолчанию
            base_x = pad - ink.left()

        # --- Вертикальное выравнивание (Y) ---
        if self._align_y == 'center':
            # Центрируем относительно высоты виджета
            base_y = (widget_h - content_h) / 2 - ink.top()
        elif self._align_y == 'bottom':
            # Прижимаем к нижнему краю
            base_y = widget_h - pad - content_h - ink.top()
        else:  # 'top' по умолчанию
            base_y = pad - ink.top()

        self._text_width = content_w + pad * 2
        self._text_height = content_h + pad * 2

        self._text_x_offset = base_x
        self._text_y_offset = base_y

        self.on_resize.process(self._text_width, self._text_height)

    def _ensure_blob(self):
        if self._blob_dirty:
            self._rebuild_blob()
            self._blob_dirty = False

    def get_size_hint(self):
        return self._text_width, self._text_height

    def draw_self(self, ctx: skia.Canvas):
        if self.bg_paint:
            ctx.drawRect(skia.Rect(0, 0, self.width, self.height), self.bg_paint)
        self._ensure_blob()
        if self._blob is not None:
            ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self.text_paint)


class Button(Label):
    def __init__(self, parent, text = '', command=None, font: str = 'Inter', font_size: float = 14, typeface: skia.Typeface | None = None,
                 text_color: str = '#fff', background_color: str = '#888', click_color='#444', hover_color='#666', debug=False):
        super().__init__(parent, text, font, font_size, typeface, text_color, background_color, 'center', 'center', debug)

        self.bg_color = background_color
        self.click_color = click_color
        self.hover_color = hover_color

        self.counter_paint = skia.Paint(hex_str_to_int(text_color))
        self.counter_paint.setAntiAlias(True)
        self.counter_paint.setStyle(skia.Paint.kStroke_Style)
        self.counter_paint.setStrokeWidth(1)
        self.counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
        self.counter_paint.setStrokeJoin(skia.Paint.kRound_Join)

        self._last_color = background_color

        if not self.bg_paint:
            raise ValueError(self.bg_paint)

        self.bg_paint.setAntiAlias(True)
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

    def set_size(self, w=None, h=None, x1=None, y1=None):
        if self._debug:
            self._logger.info(f'Set size {w, h, x1, y1} from\n{''.join(traceback.format_stack())}')

        super().set_size(w, h, x1, y1)

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
        r = skia.RRect(skia.Rect(0, 0, self.width, self.height), 5, 5)

        ctx.drawRRect(r, self.bg_paint)
        ctx.drawRRect(r, self.counter_paint)
        self._ensure_blob()
        ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self.text_paint)