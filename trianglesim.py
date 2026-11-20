import skia
import time
import someui
from someui import Widget, PlacingConfig, PlacementType, PlacementValue, defaults
from someui.util import hex_str_to_int
import math

from someui.widgets.animated_button import PrettyButton


class TriangleCalculator:
    @staticmethod
    def get_median(a, b, c):
        """Медиана из вершины a к стороне bc.
        У a, b, c должны быть атрибуты cx и cy."""
        mid_x = (b.cx + c.cx) / 2.0
        mid_y = (b.cy + c.cy) / 2.0
        return (a.cx, a.cy, mid_x, mid_y)

    @staticmethod
    def get_bisector(a, b, c):
        """Биссектриса из вершины a к стороне bc."""
        # Длины сторон AB и AC
        ab = math.hypot(b.cx - a.cx, b.cy - a.cy)
        ac = math.hypot(c.cx - a.cx, c.cy - a.cy)

        if ab + ac < 1e-5:
            return (a.cx, a.cy, a.cx, a.cy) # Защита от вырождения

        # Точка деления стороны BC по теореме о биссектрисе
        lx = (ac * b.cx + ab * c.cx) / (ab + ac)
        ly = (ac * b.cy + ab * c.cy) / (ab + ac)

        return (a.cx, a.cy, lx, ly)

    @staticmethod
    def get_height_with_extension(a, b, c):
        """Возвращает кортеж:
        (hx1, hy1, hx2, hy2) - саму высоту от вершины a до основания H
        (ex1, ey1, ex2, ey2) или None - пунктирный отрезок продления стороны от B/C до H
        """
        vx = c.cx - b.cx
        vy = c.cy - b.cy
        v_len_sq = vx * vx + vy * vy

        if v_len_sq < 1e-5:
            return (a.cx, a.cy, a.cx, a.cy), None

        wx = a.cx - b.cx
        wy = a.cy - b.cy

        t = (wx * vx + wy * vy) / v_len_sq

        # Основание высоты H
        hx = b.cx + t * vx
        hy = b.cy + t * vy

        # Сама высота от A до H
        height_line = (a.cx, a.cy, hx, hy)

        extension_line = None
        # Проверяем, упала ли высота ЗА пределы отрезка BC (t < 0 или t > 1)
        if t < 0.0:
            # Основание за точкой B -> продлеваем от B через H дальше на 20 пикселей
            bh_len = math.hypot(hx - b.cx, hy - b.cy)
            if bh_len > 1e-5:
                ex = hx + (hx - b.cx) / bh_len * 20.0
                ey = hy + (hy - b.cy) / bh_len * 20.0
                extension_line = (b.cx, b.cy, ex, ey)
            else:
                extension_line = (b.cx, b.cy, hx, hy)

        elif t > 1.0:
            # Основание за точкой C -> продлеваем от C через H дальше на 20 пикселей
            ch_len = math.hypot(hx - c.cx, hy - c.cy)
            if ch_len > 1e-5:
                ex = hx + (hx - c.cx) / ch_len * 20.0
                ey = hy + (hy - c.cy) / ch_len * 20.0
                extension_line = (c.cx, c.cy, ex, ey)
            else:
                extension_line = (c.cx, c.cy, hx, hy)

        return height_line, extension_line


class RequiredSize(someui.Widget):
    def __init__(self, parent: Widget | None):
        super().__init__(parent)
        self.req_w = 0
        self.req_h = 0

    def set_req_size(self, w, h):
        self.req_w = w
        self.req_h = h

    def get_size_hint(self):
        return self.req_w, self.req_h




def lerp_color_int(color1: int, color2: int, t: float) -> int:
    """Интерполирует между двумя цветами в формате int (например, 0xFF0000 и 0x0000FF)
    с коэффициентом t от 0.0 до 1.0."""
    t = max(0.0, min(1.0, t))

    # Распаковываем каналы RGB из первого цвета
    r1 = (color1 >> 16) & 0xFF
    g1 = (color1 >> 8) & 0xFF
    b1 = color1 & 0xFF

    # Распаковываем каналы RGB из второго цвета
    r2 = (color2 >> 16) & 0xFF
    g2 = (color2 >> 8) & 0xFF
    b2 = color2 & 0xFF

    # Интерполируем каждый канал
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)

    # Собираем обратно в целое число с помощью побитового сдвига
    return (255 << 24) | (r << 16) | (g << 8) | b


def are_colors_close_rgb(c1: int, c2: int, tolerance: int = 2) -> bool:
    """Проверяет, близки ли два целочисленных цвета в пределах tolerance."""
    r1, g1, b1 = (c1 >> 16) & 0xFF, (c1 >> 8) & 0xFF, c1 & 0xFF
    r2, g2, b2 = (c2 >> 16) & 0xFF, (c2 >> 8) & 0xFF, c2 & 0xFF

    return (
            abs(r1 - r2) <= tolerance and
            abs(g1 - g2) <= tolerance and
            abs(b1 - b2) <= tolerance
    )


class Sized(RequiredSize):
    """Only visual size for a widget"""

    def __init__(self, parent: Widget | None, bg=None, counter_color=None):
        super().__init__(parent)

        self._size = 1.0

        self.bg_paint = skia.Paint(hex_str_to_int(bg if bg else self.defaults.bg))
        self.counter_paint = skia.Paint(hex_str_to_int(counter_color if counter_color else self.defaults.fg))
        self.counter_paint.setAntiAlias(True)
        self.counter_paint.setStyle(skia.Paint.kStroke_Style)
        self.counter_paint.setStrokeWidth(1)
        self.counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
        self.counter_paint.setStrokeJoin(skia.Paint.kRound_Join)

    @property
    def size(self) -> float:
        return self._size

    @size.setter
    def size(self, value: float):
        if self._size != value:
            self._size = value
            self.invalidate()

    @property
    def visual_x(self):
        return -(self.width * (self._size - 1.0) * 0.5)

    @property
    def visual_y(self):
        return -(self.height * (self._size - 1.0) * 0.5)

    @property
    def visual_width(self):
        return self.width + self.width * (self._size - 1.0) * 0.5

    @property
    def visual_height(self):
        return self.height + self.height * (self._size - 1.0) * 0.5

    @property
    def cx(self):
        return self.x + self.width / 2

    @property
    def cy(self):
        return self.y + self.height / 2

    def draw_self(self, ctx: skia.Canvas):
        # Skip drawing if completely shrunk
        if self._size <= 0.001:
            return

        # Divide by 2 so both sides expand/shrink equally from the center
        half_diff_w = self.width * (self._size - 1.0) * 0.5
        half_diff_h = self.height * (self._size - 1.0) * 0.5

        # skia.Rect takes (left, top, right, bottom)
        rect = skia.Rect(
            -half_diff_w,
            -half_diff_h,
            self.width + half_diff_w,
            self.height + half_diff_h
        )

        ctx.drawRect(rect, self.bg_paint)
        ctx.drawRect(rect, self.counter_paint)



def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class TrianglePoint(Sized):
    def __init__(self, parent: Widget | None, bg=None, counter_color=None, idle_size=0.5, active_size=1):
        super().__init__(parent, bg, counter_color)

        self.clip_self = False
        self.placeable = False

        self._size = idle_size
        self._target_size = idle_size
        self._speed = 15.0  # Higher value = faster transition

        self.on_hover_enter(self._set_target_size(active_size))
        self.on_hover_exit(self._set_target_size(idle_size))
        self.window.on_animation_frame(self._frame)

        self._start_x = 0
        self._start_y = 0

        self.on_hold_move(self.on_drag)
        self.on_mouse_press(self.drag_start)

        self._last_click = 0
        self._finish_anim = None

    def dblclick_continue(self):
        if self.hovered:
            self._target_size = 1

    def drag_start(self, btn, x, y):
        x, y = x - self.global_x, y - self.global_y
        self._start_x = x
        self._start_y = y

        now = time.time()

        if now - self._last_click < 0.20:
            self._finish_anim = self.dblclick_continue
            self._target_size = 2

        self._last_click = now

    def on_drag(self, x, y):
        x, y = x - self.parent.global_x, y - self.parent.global_y
        self.set_position(x - self._start_x, y - self._start_y)

    def _frame(self, dt: float):
        if abs(self._target_size - self._size) < 0.01:
            self._size = self._target_size
            if callable(self._finish_anim):
                self._finish_anim()
            self._finish_anim = None
            return

        t = 1.0 - math.exp(-self._speed * dt)
        self._size = lerp(self._size, self._target_size, t)

    def _set_target_size(self, value: float):
        def _wrapper(*args):
            if self.held:
                self._target_size = max(1, value)
            else:
                self._target_size = value
        return _wrapper


class Triangle(someui.Container):
    def __init__(self, parent, bg: str | None = None, counter_color: str | None = None):
        super().__init__(parent, bg, counter_color)
        self.scroll_enabled = False

        self.red =    skia.Paint(Color=skia.ColorRED, AntiAlias=True)
        self.yellow = skia.Paint(Color=skia.ColorYELLOW, AntiAlias=True)
        self.green =  skia.Paint(Color=skia.ColorGREEN, AntiAlias=True)
        self.pointer_paint = skia.Paint(
            Color=skia.ColorWHITE,
            StrokeWidth=2.0,
            Style=skia.Paint.kStroke_Style,
            PathEffect=skia.DashPathEffect.Make([6.0, 4.0], 0.0), AntiAlias=True
        )

        self.paints = [self.red, self.yellow, self.green]

        self.head = TrianglePoint(self, bg='#f00')
        self.left = TrianglePoint(self, bg='#0f0')
        self.right = TrianglePoint(self, bg='#00f')

        self.points = [self.left, self.head, self.right]
        self.points_pairs = [[self.left, self.head, self.right], [self.head, self.right, self.left], [self.right, self.left, self.head]]

        for element, position_offset in zip(self.points, [(0, 1), (0.5, 0), (1, 1)]):
            element.set_size(15, 15)
            xo, yo = position_offset
            element.set_position(100 * xo, 100 * yo)

    def reset(self):
        for element, position_offset in zip(self.points, [(0, 1), (0.5, 0), (1, 1)]):
            element.set_size(15, 15)
            xo, yo = position_offset
            element.set_position(100 * xo, 100 * yo)

    def draw_self(self, ctx: skia.Canvas):
        super().draw_self(ctx)

        for idx in range(0, len(self.points)):
            p = self.points[idx]
            prev_p = self.points[idx - 1]
            ctx.drawLine(prev_p.x + prev_p.width / 2, prev_p.y + prev_p.height / 2,
                         p.x + p.width / 2, p.y + p.height / 2, self.counter_paint)

        if is_medians:
            for (a, b, c), paint in zip(self.points_pairs, self.paints):
                ctx.drawLine(*TriangleCalculator.get_median(a, b, c), paint=paint)
        if is_heights:
            for (a, b, c), paint in zip(self.points_pairs, self.paints):
                main_line, ext_line = TriangleCalculator.get_height_with_extension(a, b, c)
                ctx.drawLine(*main_line, paint=paint)
                if ext_line:
                    ctx.drawLine(*ext_line, paint=self.pointer_paint)
        if is_bisectors:
            for (a, b, c), paint in zip(self.points_pairs, self.paints):
                ctx.drawLine(*TriangleCalculator.get_bisector(a, b, c), paint=paint)


class Checkbox(someui.Button):
    def __init__(self, parent, text = '', on_value_change=None, font: str = 'Inter', font_size: float = 14,
                 typeface: skia.Typeface | None = None, text_color: str = 'white',
                 background_color=None):
        super().__init__(parent, text, self._toggle, font, font_size, typeface, text_color, background_color)
        self._flag = False
        self.on_value_change = on_value_change
        self._flag_color = skia.ColorRED
        self._flag_color_target = skia.ColorRED
        self._running = False
        self.text_pad_x = 14

        self._target_color = hex_str_to_int(self._bg_color)
        self._current_color = hex_str_to_int(self._bg_color)

        self.flag_paint = skia.Paint(skia.ColorRED)
        self._active_paint = skia.Paint(self._bg_paint.getColor())

    def _frame(self, dt):
        new_color = lerp_color_int(self._flag_color, self._flag_color_target, 0.05)
        self._flag_color = new_color
        self.flag_paint.setColor(new_color)

        new_color = lerp_color_int(self._current_color, self._target_color, 0.2)
        self._current_color = new_color
        self._active_paint.setColor(new_color)

        if are_colors_close_rgb(self._flag_color, self._flag_color_target) and are_colors_close_rgb(self._flag_color, self._target_color):
            self._flag_color = self._flag_color_target
            self._current_color = self._target_color
            self.window.on_animation_frame.remove(self._frame)
            self._running = False

    def _run_anim(self, clr=None):
        if clr:
            self._target_color = clr
        if not self._running:
            self._running = True
            self.window.on_animation_frame(self._frame)

    def get_size_hint(self):
        w, h = super().get_size_hint()
        return w, h

    def _rebuild_blob(self):
        super()._rebuild_blob()
        self._text_x_offset += 14

    def _set_color(self):
        if self.held:
            clr = self._click_color
        elif self.hovered:
            clr = self._hover_color
        else:
            clr = self._bg_color

        self._run_anim(hex_str_to_int(clr))

    def _toggle(self):
        self._flag = not self._flag
        if self._flag:
            self._flag_color_target = skia.ColorGREEN
        else:
            self._flag_color_target = skia.ColorRED
        self._run_anim()
        if self.on_value_change is not None:
            self.on_value_change(self._flag)

    def draw_self(self, ctx: skia.Canvas):
        super().draw_self(ctx)
        rect = skia.Rect(6, 6, 10 + self._text_x_offset / 2, self.height - 6)
        ctx.drawRect(rect, self.flag_paint)


is_heights = False
is_bisectors = False
is_medians = False


window = someui.DefaultWindow()
defaults.RootDefaults.config(bg='#111', fg='#fff')

#Cursor(window)

config_window = someui.Container(window)
config_window.mcfg.gap = 4
config_window.mcfg.margins = someui.Margins(left=4, top=4)
config_window.place(PlacingConfig(width=PlacementValue.fixed(150), height=PlacementValue.relative(1.0)))

def _set_heights(val):
    global is_heights
    is_heights = val

height = Checkbox(config_window, 'heights enabled', _set_heights)
height.place(PlacingConfig(y=PlacementValue.auto()))

def _set_bisectors(val):
    global is_bisectors
    is_bisectors = val

bisectors = Checkbox(config_window, 'bisectors enabled', _set_bisectors)
bisectors.place(PlacingConfig(y=PlacementValue.auto()))

def _set_medians(val):
    global is_medians
    is_medians = val

medians = Checkbox(config_window, 'medians enabled', _set_medians)
medians.place(PlacingConfig(y=PlacementValue.auto()))

w_test = Triangle(window)
w_test.place(PlacingConfig(x=PlacementValue.fixed(150), width=PlacementValue(PlacementType.RELATIVE, 1.0, -150), height=PlacementValue(PlacementType.RELATIVE, 1.0)))

PrettyButton(config_window, 'reset', w_test.reset).place(PlacingConfig(y=PlacementValue.auto()))

window.rebuild_scene()

window.mainloop()