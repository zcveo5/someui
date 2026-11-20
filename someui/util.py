from dataclasses import dataclass, field


class Event:
    def __init__(self):
        self._functions = []
        self._is_processing = False

    def __call__(self, fnc):
        self._functions.append(fnc)
        return fnc

    def remove(self, fnc):
        self._functions.remove(fnc)

    def process(self, *args):
        if self._is_processing:
            return
        self._is_processing = True
        [i(*args) for i in self._functions]
        self._is_processing = False


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

    if len(code) == 3:  # #RGB -> #RRGGBBAA
        code = ''.join(c * 2 for c in code) + 'ff'
    elif len(code) == 4:  # #RGBA -> #RRGGBBAA
        code = ''.join(c * 2 for c in code)
    elif len(code) == 6:  # #RRGGBB -> #RRGGBBAA
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


def gamma_to_linear(c: int) -> float:
    norm = c / 255.0
    return norm / 12.92 if norm <= 0.04045 else ((norm + 0.055) / 1.055) ** 2.4

def linear_to_gamma(c: float) -> int:
    val = c * 12.92 if c <= 0.003308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055
    return round(max(0.0, min(1.0, val)) * 255)

def hex_str_to_argb_tuple(clr_string: str) -> tuple[int, int, int, int]:
    """Вспомогательная функция для разбора цвета в (a, r, g, b)"""
    hex_str = CSS4_COLORS.get(clr_string, clr_string) if 'CSS4_COLORS' in globals() else clr_string

    if not hex_str.startswith('#'):
        raise ValueError(f"Некорректный формат цвета: '{clr_string}'")

    code = hex_str[1:]

    if len(code) == 3:  # #RGB -> #RRGGBBFF (alpha по умолчанию ff)
        code = ''.join(c * 2 for c in code) + 'ff'
    elif len(code) == 4:  # #RGBA -> #RRGGBBAA
        code = ''.join(c * 2 for c in code)
    elif len(code) == 6:  # #RRGGBB -> #RRGGBBFF
        code += 'ff'
    elif len(code) != 8:
        raise ValueError(f"Неверная длина HEX-кода: '{clr_string}'")

    r = int(code[0:2], 16)
    g = int(code[2:4], 16)
    b = int(code[4:6], 16)
    a = int(code[6:8], 16)
    return a, r, g, b

def color_mix(color1: str, color2: str, weight1: float = 0.5) -> str:
    """
    Смешивает два цвета (строки #hex или названия из CSS4_COLORS)
    в линейном пространстве и возвращает результат в формате '#aarrggbb'.
    """
    weight1 = max(0.0, min(1.0, weight1))
    weight2 = 1.0 - weight1

    a1, r1, g1, b1 = hex_str_to_argb_tuple(color1)
    a2, r2, g2, b2 = hex_str_to_argb_tuple(color2)

    # Линейная интерполяция для альфы
    a = round(a1 * weight1 + a2 * weight2)

    # Перевод RGB в линейное пространство для честного смешивания
    lr1, lg1, lb1 = gamma_to_linear(r1), gamma_to_linear(g1), gamma_to_linear(b1)
    lr2, lg2, lb2 = gamma_to_linear(r2), gamma_to_linear(g2), gamma_to_linear(b2)

    mixed_r = linear_to_gamma(lr1 * weight1 + lr2 * weight2)
    mixed_g = linear_to_gamma(lg1 * weight1 + lg2 * weight2)
    mixed_b = linear_to_gamma(lb1 * weight1 + lb2 * weight2)

    return f"#{mixed_r:02x}{mixed_g:02x}{mixed_b:02x}{a:02x}"


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


def lerp_color_argb(color1: int, color2: int, t: float) -> int:
    """Интерполирует между двумя цветами в формате 0xAARRGGBB."""
    t = max(0.0, min(1.0, t))

    a1 = (color1 >> 24) & 0xFF
    r1 = (color1 >> 16) & 0xFF
    g1 = (color1 >> 8) & 0xFF
    b1 = color1 & 0xFF

    a2 = (color2 >> 24) & 0xFF
    r2 = (color2 >> 16) & 0xFF
    g2 = (color2 >> 8) & 0xFF
    b2 = color2 & 0xFF

    a = int(a1 + (a2 - a1) * t)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)

    return (a << 24) | (r << 16) | (g << 8) | b


def are_colors_close_argb(c1: int, c2: int, tolerance: int = 2) -> bool:
    """Проверяет, близки ли два цвета 0xAARRGGBB в пределах tolerance."""
    a1, r1, g1, b1 = (c1 >> 24) & 0xFF, (c1 >> 16) & 0xFF, (c1 >> 8) & 0xFF, c1 & 0xFF
    a2, r2, g2, b2 = (c2 >> 24) & 0xFF, (c2 >> 16) & 0xFF, (c2 >> 8) & 0xFF, c2 & 0xFF

    return (
        abs(a1 - a2) <= tolerance and
        abs(r1 - r2) <= tolerance and
        abs(g1 - g2) <= tolerance and
        abs(b1 - b2) <= tolerance
    )


def ignore_params(fnc):
    def wrapper(self, *args, **kwargs):
        return fnc(self)
    return wrapper


_FIELDS = ("bg", "fg", "font", "font_size", "hover_color", "click_color")
_UNSET = object()


@dataclass
class Defaults:
    bg: str
    fg: str
    font: str
    font_size: int
    hover_color: str | None = None
    click_color: str | None = None
    on_change: Event = field(default_factory=Event, init=False)

    def __post_init__(self):
        self._apply_derived_colors()

    def _apply_derived_colors(self, hover_explicit: bool = False, click_explicit: bool = False):
        if not hover_explicit:
            self.hover_color = color_mix(self.bg, "#fff", 0.95)
        if not click_explicit:
            self.click_color = color_mix(self.bg, "#000", 0.85)

    def config(
        self,
        bg=_UNSET,
        fg=_UNSET,
        font=_UNSET,
        font_size=_UNSET,
        hover_color=_UNSET,
        click_color=_UNSET,
    ):
        kwargs = {
            k: v
            for k, v in {
                "bg": bg,
                "fg": fg,
                "font": font,
                "font_size": font_size,
                "hover_color": hover_color,
                "click_color": click_color,
            }.items()
            if v is not _UNSET
        }

        unknown = set(kwargs) - set(_FIELDS)
        if unknown:
            raise TypeError(f"Unknown config keys: {', '.join(sorted(unknown))}")

        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return

        for k, v in updates.items():
            setattr(self, k, v)
        if "bg" in updates:
            self._apply_derived_colors(
                hover_explicit="hover_color" in updates,
                click_explicit="click_color" in updates,
            )

        self.on_change.process()