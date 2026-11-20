import skia
from someui.util import Defaults, hex_str_to_int


class Registry:
    def __init__(self, defaults: Defaults):
        self.defaults = defaults

        self.bg_paint =      skia.Paint(hex_str_to_int(defaults.bg))
        self.fg_paint =      skia.Paint(hex_str_to_int(defaults.fg))
        self.hover_paint =   skia.Paint(hex_str_to_int(defaults.hover_color or '#f0f'))
        self.click_paint =   skia.Paint(hex_str_to_int(defaults.click_color or '#f0f'))
        self.counter_paint = skia.Paint(hex_str_to_int(defaults.fg))

        self.counter_paint.setAntiAlias(True)
        self.counter_paint.setStyle(skia.Paint.kStroke_Style)
        self.counter_paint.setStrokeWidth(1)
        self.counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
        self.counter_paint.setStrokeJoin(skia.Paint.kRound_Join)

        defaults.on_change(self._rebuild_colors)

    def _rebuild_colors(self):
        self.bg_paint.setColor(      hex_str_to_int(self.defaults.bg))
        self.fg_paint.setColor(      hex_str_to_int(self.defaults.fg))
        self.hover_paint.setColor(   hex_str_to_int(self.defaults.hover_color or '#f0f'))
        self.click_paint.setColor(   hex_str_to_int(self.defaults.click_color or '#f0f'))
        self.counter_paint.setColor( hex_str_to_int(self.defaults.fg))