import math
import time

from . import widget
import skia


CSS4_COLORS = {
    'aliceblue':            '#F0F8FF',
    'antiquewhite':         '#FAEBD7',
    'aqua':                 '#00FFFF',
    'aquamarine':           '#7FFFD4',
    'azure':                '#F0FFFF',
    'beige':                '#F5F5DC',
    'bisque':               '#FFE4C4',
    'black':                '#000000',
    'blanchedalmond':       '#FFEBCD',
    'blue':                 '#0000FF',
    'blueviolet':           '#8A2BE2',
    'brown':                '#A52A2A',
    'burlywood':            '#DEB887',
    'cadetblue':            '#5F9EA0',
    'chartreuse':           '#7FFF00',
    'chocolate':            '#D2691E',
    'coral':                '#FF7F50',
    'cornflowerblue':       '#6495ED',
    'cornsilk':             '#FFF8DC',
    'crimson':              '#DC143C',
    'cyan':                 '#00FFFF',
    'darkblue':             '#00008B',
    'darkcyan':             '#008B8B',
    'darkgoldenrod':        '#B8860B',
    'darkgray':             '#A9A9A9',
    'darkgreen':            '#006400',
    'darkgrey':             '#A9A9A9',
    'darkkhaki':            '#BDB76B',
    'darkmagenta':          '#8B008B',
    'darkolivegreen':       '#556B2F',
    'darkorange':           '#FF8C00',
    'darkorchid':           '#9932CC',
    'darkred':              '#8B0000',
    'darksalmon':           '#E9967A',
    'darkseagreen':         '#8FBC8F',
    'darkslateblue':        '#483D8B',
    'darkslategray':        '#2F4F4F',
    'darkslategrey':        '#2F4F4F',
    'darkturquoise':        '#00CED1',
    'darkviolet':           '#9400D3',
    'deeppink':             '#FF1493',
    'deepskyblue':          '#00BFFF',
    'dimgray':              '#696969',
    'dimgrey':              '#696969',
    'dodgerblue':           '#1E90FF',
    'firebrick':            '#B22222',
    'floralwhite':          '#FFFAF0',
    'forestgreen':          '#228B22',
    'fuchsia':              '#FF00FF',
    'gainsboro':            '#DCDCDC',
    'ghostwhite':           '#F8F8FF',
    'gold':                 '#FFD700',
    'goldenrod':            '#DAA520',
    'gray':                 '#808080',
    'green':                '#008000',
    'greenyellow':          '#ADFF2F',
    'grey':                 '#808080',
    'honeydew':             '#F0FFF0',
    'hotpink':              '#FF69B4',
    'indianred':            '#CD5C5C',
    'indigo':               '#4B0082',
    'ivory':                '#FFFFF0',
    'khaki':                '#F0E68C',
    'lavender':             '#E6E6FA',
    'lavenderblush':        '#FFF0F5',
    'lawngreen':            '#7CFC00',
    'lemonchiffon':         '#FFFACD',
    'lightblue':            '#ADD8E6',
    'lightcoral':           '#F08080',
    'lightcyan':            '#E0FFFF',
    'lightgoldenrodyellow': '#FAFAD2',
    'lightgray':            '#D3D3D3',
    'lightgreen':           '#90EE90',
    'lightgrey':            '#D3D3D3',
    'lightpink':            '#FFB6C1',
    'lightsalmon':          '#FFA07A',
    'lightseagreen':        '#20B2AA',
    'lightskyblue':         '#87CEFA',
    'lightslategray':       '#778899',
    'lightslategrey':       '#778899',
    'lightsteelblue':       '#B0C4DE',
    'lightyellow':          '#FFFFE0',
    'lime':                 '#00FF00',
    'limegreen':            '#32CD32',
    'linen':                '#FAF0E6',
    'magenta':              '#FF00FF',
    'maroon':               '#800000',
    'mediumaquamarine':     '#66CDAA',
    'mediumblue':           '#0000CD',
    'mediumorchid':         '#BA55D3',
    'mediumpurple':         '#9370DB',
    'mediumseagreen':       '#3CB371',
    'mediumslateblue':      '#7B68EE',
    'mediumspringgreen':    '#00FA9A',
    'mediumturquoise':      '#48D1CC',
    'mediumvioletred':      '#C71585',
    'midnightblue':         '#191970',
    'mintcream':            '#F5FFFA',
    'mistyrose':            '#FFE4E1',
    'moccasin':             '#FFE4B5',
    'navajowhite':          '#FFDEAD',
    'navy':                 '#000080',
    'oldlace':              '#FDF5E6',
    'olive':                '#808000',
    'olivedrab':            '#6B8E23',
    'orange':               '#FFA500',
    'orangered':            '#FF4500',
    'orchid':               '#DA70D6',
    'palegoldenrod':        '#EEE8AA',
    'palegreen':            '#98FB98',
    'paleturquoise':        '#AFEEEE',
    'palevioletred':        '#DB7093',
    'papayawhip':           '#FFEFD5',
    'peachpuff':            '#FFDAB9',
    'peru':                 '#CD853F',
    'pink':                 '#FFC0CB',
    'plum':                 '#DDA0DD',
    'powderblue':           '#B0E0E6',
    'purple':               '#800080',
    'rebeccapurple':        '#663399',
    'red':                  '#FF0000',
    'rosybrown':            '#BC8F8F',
    'royalblue':            '#4169E1',
    'saddlebrown':          '#8B4513',
    'salmon':               '#FA8072',
    'sandybrown':           '#F4A460',
    'seagreen':             '#2E8B57',
    'seashell':             '#FFF5EE',
    'sienna':               '#A0522D',
    'silver':               '#C0C0C0',
    'skyblue':              '#87CEEB',
    'slateblue':            '#6A5ACD',
    'slategray':            '#708090',
    'slategrey':            '#708090',
    'snow':                 '#FFFAFA',
    'springgreen':          '#00FF7F',
    'steelblue':            '#4682B4',
    'tan':                  '#D2B48C',
    'teal':                 '#008080',
    'thistle':              '#D8BFD8',
    'tomato':               '#FF6347',
    'turquoise':            '#40E0D0',
    'violet':               '#EE82EE',
    'wheat':                '#F5DEB3',
    'white':                '#FFFFFF',
    'whitesmoke':           '#F5F5F5',
    'yellow':               '#FFFF00',
    'yellowgreen':          '#9ACD32'}


def hex_str_to_int(clr_string: str, fmt: str = 'argb') -> int:
    hex_str = CSS4_COLORS.get(clr_string, clr_string)

    if not hex_str.startswith('#'):
        raise ValueError(f"Некорректный формат цвета: '{clr_string}'")

    code = hex_str[1:]

    if len(code) == 3:  # #RGB -> #RRGGBBFF
        code = ''.join(c * 2 for c in code) + 'ff'
    elif len(code) == 4:  # #RGBA -> #RRGGBBAA
        code = ''.join(c * 2 for c in code)
    elif len(code) == 6:  # #RRGGBB -> #RRGGBBFF
        code += 'ff'
    elif len(code) != 8:
        raise ValueError(f"Неверная длина HEX-кода: '{clr_string}'")

    r, g, b, a = code[0:2], code[2:4], code[4:6], code[6:8]

    if fmt == 'argb':
        final_hex = a + r + g + b
    elif fmt == 'rgba':
        final_hex = r + g + b + a
    elif fmt == 'argb-a':
        final_hex = 'ff' + r + g + b
    else:
        raise ValueError(f"Неподдерживаемый формат: {fmt}")

    return int(final_hex, 16)


def ignore_params(fnc):
    def wrapper(self, *args, **kwargs):
        return fnc(self)
    return wrapper


class RelativePlaceWidget(widget.Widget):
    """Adds relative place interface to a widget"""
    def __init__(self, parent):
        super().__init__(parent)
        self.actual_x = 0
        self.actual_y = 0
        self.actual_width = 0
        self.actual_height = 0

        self.rel_x = 0
        self.rel_y = 0
        self.rel_w = 0
        self.rel_h = 0

        self.x_offset = 0
        self.y_offset = 0
        self.w_offset = 0
        self.h_offset = 0

        self.parent.on_resize(self.replace_relative)

    @ignore_params
    def replace_relative(self):
        if self.rel_x:
            self.actual_x = self.parent.width * self.rel_x
        else:
            self.actual_x = self._x
        if self.rel_y:
            self.actual_y = self.parent.height * self.rel_y
        else:
            self.actual_y = self._y
        if self.rel_w:
            self.actual_width = self.parent.width * self.rel_w
        else:
            self.actual_width = self._width
        if self.rel_h:
            self.actual_height = self.parent.height * self.rel_h
        else:
            self.actual_height = self._height

        self.actual_x += self.x_offset
        self.actual_y += self.y_offset
        self.actual_width += self.w_offset
        self.actual_height += self.h_offset

        self.on_resize.process(self.actual_width, self.actual_height)

        self.invalidate()

    def rel_place(self, rel_x: float = None, rel_y: float = None, rel_width: float = None, rel_height: float = None,
                  x_offset: str = None, y_offset: str = None, width_offset: str = None, height_offset: str = None):
        if rel_x is not None:
            self.rel_x = rel_x
        if rel_y is not None:
            self.rel_y = rel_y
        if rel_width is not None:
            self.rel_w = rel_width
        if rel_height is not None:
            self.rel_h = rel_height

        if x_offset is not None:
            self.x_offset = int(x_offset.format(half=self._width / 2, full=self._width, fourth=self._width / 4))
        if y_offset is not None:
            self.y_offset = int(y_offset.format(half=self._height / 2, full=self._height, fourth=self._height / 4))
        if width_offset is not None:
            self.w_offset = int(width_offset.format(half=self._width / 2, full=self._width, fourth=self._width / 4))
        if height_offset is not None:
            self.h_offset = int(height_offset.format(half=self._height / 2, full=self._height, fourth=self._height / 4))

        self.replace_relative()

    def set_size(self, w=None, h=None, x1=None, y1=None):
        super().set_size(w, h, x1, y1)
        self.replace_relative()

    def set_position(self, x, y):
        super().set_position(x, y)
        self.replace_relative()

    def _get_metrics(self) -> tuple[float, float, float, float]:
        return self.actual_x, self.actual_y, self.actual_width, self.actual_height


def smooth_damp(current, target, vel, smooth_time, dt):
    omega = 2.0 / smooth_time
    x = omega * dt
    e = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    change = current - target
    temp = (vel + omega * change) * dt
    vel = (vel - omega * temp) * e
    out = target + (change + temp) * e
    if (target - current > 0) == (out > target):   # защита от перелёта
        out, vel = target, 0.0
    return out, vel


class ScrollContainerWidget(RelativePlaceWidget):
    SMOOTH_TIME = 0.12   # сек; больше = мягче и медленнее

    def __init__(self, parent):
        super().__init__(parent)
        self.scroll_enabled = True
        self.on_scroll(self._v_scroll)
        self._target_scroll_y = 0.0
        self._vel_y = 0.0
        self._loop_running = False
        self._last_t = 0.0

    def _clamp_y(self, value):
        ch = sum(i.height for i in self.iter_children()) - self.height
        print(0, value, ch)
        return max(0, min(value, ch))   # сюда твои границы

    def _loop(self):
        now = time.perf_counter()
        dt = min(now - self._last_t, 0.05)

        self._last_t = now

        self.scroll_y, self._vel_y = smooth_damp(
            self.scroll_y, self._target_scroll_y, self._vel_y, self.SMOOTH_TIME, dt)

        if abs(self._target_scroll_y - self.scroll_y) < 0.3 and abs(self._vel_y) < 1.0:
            self.scroll_y = self._target_scroll_y
            self._vel_y = 0.0
            self._loop_running = False
        else:
            self.window.call_after(self._loop, 1 / 180)
        self.invalidate()

    def _v_scroll(self, delta, x, y):
        self._target_scroll_y = self._clamp_y(self._target_scroll_y - delta)

        if not self._loop_running:
            self._loop_running = True
            self._last_t = time.perf_counter()
            self.window.call_after(self._loop, 1 / 180)   # первый шаг не синхронно


class ScrollItemWidget(RelativePlaceWidget):
    def _get_metrics(self) -> tuple[float, float, float, float]:
        rx, ry, rw, rh = super()._get_metrics()

        if isinstance(self.parent, ScrollContainerWidget):
            rx -= self.parent.scroll_x
            ry -= self.parent.scroll_y

        return rx, ry, rw, rh


class Container(ScrollContainerWidget):
    def __init__(self, parent, bg: str | None = '#000', counter_color: str | None = '#fff', blur_sigma=None):
        super().__init__(parent)
        if bg:
            self.bg_paint = skia.Paint(hex_str_to_int(bg))
        else:
            self.bg_paint = None
        if counter_color:
            self.counter_paint = skia.Paint(hex_str_to_int(counter_color))
            self.counter_paint.setAntiAlias(True)
            self.counter_paint.setStyle(skia.Paint.kStroke_Style)
            self.counter_paint.setStrokeWidth(1)
            self.counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
            self.counter_paint.setStrokeJoin(skia.Paint.kRound_Join)
        else:
            self.counter_paint = None


        if blur_sigma:
            self.blur_paint = skia.Paint()
            self.blur_paint.setImageFilter(skia.ImageFilters.Blur(blur_sigma, blur_sigma))
        else:
            self.blur_paint = None

    def draw_self(self, ctx: skia.Canvas):
        r = skia.RRect(skia.Rect(0, 0, self.width, self.height), 5, 5)

        if self.blur_paint:
            ctx.save()
            # 1. Жестко клипаем канвас по скругленным углам виджета
            ctx.clipRRect(r, True)

            # 2. Определяем сигму (подставь ту же, что у тебя в blur_paint)
            # Примерный радиус влияния блюра — это sigma * 3
            sigma = 10.0  # Замени на свою сигму, если она другая
            padding = int(sigma * 3)

            # 3. Вырезаем из окна область БОЛЬШЕ размера виджета (с запасом со всех сторон)
            i_rect = skia.IRect.MakeXYWH(
                int(self.global_x) - padding,
                int(self.global_y) - padding,
                int(self.width) + padding * 2,
                int(self.height) + padding * 2
            )
            subset_image = self.window.get_surface().makeImageSnapshot(i_rect)

            # 4. Рисуем картинку со смещением (на этот же padding),
            # чтобы центр совпал с виджетом, а артефакты по краям ушли за пределы клипа
            dst_rect = skia.Rect(-padding, -padding, self.width + padding, self.height + padding)
            ctx.drawImageRect(subset_image, dst_rect, skia.SamplingOptions(), self.blur_paint)

            ctx.restore()
        if self.bg_paint:
            ctx.drawRRect(r, self.bg_paint)
        if self.counter_paint:
            ctx.drawRRect(r, self.counter_paint)