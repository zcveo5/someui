import skia
from someui import widget
from someui.util import hex_str_to_int, smooth_damp


class ScrollContainerWidget(widget.Widget):
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
        return max(0, min(value, ch))   # сюда твои границы

    def _loop(self, dt):
        self.scroll_y, self._vel_y = smooth_damp(
            self.scroll_y, self._target_scroll_y, self._vel_y, self.SMOOTH_TIME, dt)

        if abs(self._target_scroll_y - self.scroll_y) < 0.3 and abs(self._vel_y) < 1.0:
            self.scroll_y = self._target_scroll_y
            self._vel_y = 0.0
            self._loop_running = False
            self.window.on_animation_frame.remove(self._loop)

    def _v_scroll(self, delta, x, y):
        self._target_scroll_y = self._clamp_y(self._target_scroll_y - delta)

        if not self._loop_running:
            self._loop_running = True
            self.window.on_animation_frame(self._loop)   # первый шаг не синхронно


class ScrollItemWidget(widget.Widget):
    def _get_metrics(self) -> tuple[float, float, float, float]:
        rx, ry, rw, rh = super()._get_metrics()

        if isinstance(self.parent, ScrollContainerWidget):
            rx -= self.parent.scroll_x
            ry -= self.parent.scroll_y

        return rx, ry, rw, rh


class Container(ScrollContainerWidget):
    def __init__(self, parent, bg: str | None = None, counter_color: str | None = None, counter=True, is_rounded=True, blur_sigma=None, bg_enabled=True):
        super().__init__(parent)
        self.bg_color = bg if bg else self.defaults.bg
        if bg_enabled:
            self.bg_paint = skia.Paint(hex_str_to_int(self.bg_color))
        else:
            self.bg_paint = None

        self.is_rounded = is_rounded

        self.counter_paint = None
        if counter:
            self.counter_paint = skia.Paint(hex_str_to_int(counter_color if counter_color else self.defaults.fg))
            self.counter_paint.setAntiAlias(True)
            self.counter_paint.setStyle(skia.Paint.kStroke_Style)
            self.counter_paint.setStrokeWidth(1)
            self.counter_paint.setStrokeCap(skia.Paint.kRound_Cap)
            self.counter_paint.setStrokeJoin(skia.Paint.kRound_Join)

        if blur_sigma:
            self.blur_paint = skia.Paint()
            self.blur_paint.setImageFilter(skia.ImageFilters.Blur(blur_sigma, blur_sigma))
        else:
            self.blur_paint = None

    def draw_self(self, ctx: skia.Canvas):
        r = skia.Rect(0, 0, self.width, self.height)
        rr = skia.RRect(r, 5, 5)

        if self.blur_paint:
            ctx.save()
            # 1. Жестко клипаем канвас по скругленным углам виджета
            if self.is_rounded:
                ctx.clipRRect(rr, True)
            else:
                ctx.clipRect(r)

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
            if self.is_rounded:
                ctx.drawRRect(rr, self.bg_paint)
            else:
                ctx.drawRect(r, self.bg_paint)
        if self.counter_paint:
            if self.is_rounded:
                ctx.drawRRect(rr, self.counter_paint)
            else:
                ctx.drawRect(r, self.counter_paint)


__all__ = ['ScrollContainerWidget', 'ScrollItemWidget', 'Container']