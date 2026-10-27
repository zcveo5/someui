from __future__ import annotations

import operator
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import skia

if TYPE_CHECKING:
    import abstract as tc_window


_get_z_attr = operator.attrgetter('z')

DEBUG_FONT = skia.Font(skia.Typeface(), 14)
DEBUG_RED = skia.Paint(0x44ff0000)
DEBUG_BLACK = skia.Paint(skia.ColorBLACK)


class Event:
    def __init__(self):
        self._functions = []
        self._is_processing = False

    def __call__(self, fnc):
        self._functions.append(fnc)
        return fnc

    def process(self, *args):
        if self._is_processing:
            return
        self._is_processing = True
        [i(*args) for i in self._functions]
        self._is_processing = False


@dataclass(kw_only=True, frozen=True)
class PlacingConfig:
    x: float | None | Literal['auto'] = None
    y: float | None | Literal['auto'] = None
    relative_x: float | None = None
    relative_y: float | None = None
    width: int | None = None
    height: int | None = None
    relative_width: float | None = None
    relative_height: float | None = None

@dataclass(kw_only=True)
class MyPlacingHint:
    propagate: bool = False


def do_rectangles_overlap(rect1, rect2):
    if (rect1[2] <= rect2[0] or  # rect1 is left of rect2
        rect2[2] <= rect1[0] or  # rect2 is left of rect1
        rect1[3] <= rect2[1] or  # rect1 is below rect2
        rect2[3] <= rect1[1]):   # rect2 is below rect1
        return False
    return True


class Widget:
    """Base widget class"""
    widget_type = 'Widget'

    window: tc_window.AbstractWindow
    parent: Widget
    children: dict[int, Widget]

    last_id = 0

    def __init__(self, parent: Widget | None):
        self.debug = False
        self.debug_fp = False
        self._enabled = True
        self.visible = False
        self.hidden = False
        self.id = Widget.last_id
        Widget.last_id += 1
        self.name = f'{self.__class__.__mro__[0].__name__}{self.id}'

        self.children = {}

        self.parent = parent

        if parent is not None:
            self.window = parent.window
            self._z = self.parent.z + 1
        else:
            self.window = self
            self._z = 0

        self._x = 0
        self._y = 0
        self._width = 0
        self._height = 0

        self.scroll_x = self.scroll_y = 0

        self.on_mouse_press = Event()
        self.on_mouse_release = Event()
        self.on_hover = Event()
        self.on_hover_enter = Event()
        self.on_hover_exit = Event()
        self.on_scroll = Event()
        self.on_horizontal_scroll = Event()
        self.scroll_enabled = False

        self.on_resize = Event()
        self.on_repos = Event()

        self.on_resize(lambda *_: self.invalidate_place())

        self.hovered = False
        self.dirty = False
        self.dirty_placement = False
        self._bmp = None
        self.caching_bmp_enabled = False

        self.pcfg = PlacingConfig()
        self.mcfg = MyPlacingHint()

        if self.parent:
            self.parent.add_child(self)

        self.on_hold_move = Event()

        self.held = False

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = value
        for c in self.children.values():
            c.z = self.z + 1

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        self.window.invalidate_children()

    def cord_to_local(self, gx, gy):
        return gx - self.global_x, gy - self.global_y

    def get_size_hint(self):
        return 0, 0

    def invalidate_place(self):
        self.dirty_placement = True
        self.window.invalidate_place()

    def place(self, config: PlacingConfig | None = None, **kwargs):
        if config:
            self.pcfg = config
        else:
            self.pcfg = PlacingConfig(**kwargs)

        self.invalidate_place()
        self.invalidate()

    ###

    def _get_metrics(self) -> tuple[float, float, float, float]:
        return self._x, self._y, self._width, self._height

    @property
    def x(self):
        return self._get_metrics()[0]

    @property
    def y(self):
        return self._get_metrics()[1]

    @property
    def width(self):
        return self._get_metrics()[2]

    @property
    def height(self):
        return self._get_metrics()[3]

    ###

    @property
    def x1(self):
        return self.x + self.width

    @property
    def y1(self):
        return self.y + self.height

    @property
    def global_x(self):
        if self.parent is None:
            return self.x
        return self.parent.global_x + self.x

    @property
    def global_y(self):
        if self.parent is None:
            return self.y
        return self.parent.global_y + self.y

    @property
    def global_x1(self):
        return self.global_x + self.width

    @property
    def global_y1(self):
        return self.global_y + self.height

    def set_size(self, w=None, h=None, x1=None, y1=None):
        if w is not None and h is not None:
            self._width = w
            self._height = h
        elif x1 is not None and y1 is not None:
            self._width = x1 - self.x
            self._height = y1 - self.y
        else:
            raise ValueError('w, h, x1 or y1 needs to be specified')

        self.on_resize.process(w, h)

    def set_position(self, x, y):
        self._x = x
        self._y = y

    def iter_children(self):
        for c in self.children.values():
            yield c

    def iter_visible_children(self):
        for c in self.children.values():
            if not c.visible or not c.enabled: continue
            yield c

    def hittest(self, x, y):
        return self.global_x < x < self.global_x1 and self.global_y < y < self.global_y1

    def add_child(self, child):
        self.children[child.id] = child
        self.window.invalidate_children()

    def remove_child(self, child):
        del self.children[child.id]

    def invalidate(self):
        self.dirty = True
        self.window.request_redraw()

    def update(self):
        self.window.update()

    def prepare_render_resources(self, ctx: skia.Canvas):
        pass

    def draw_children(self, ctx: skia.Canvas):
        for c in sorted(self.children.values(), key=_get_z_attr, reverse=True):
            c.draw(ctx)

    def draw_self(self, ctx: skia.Canvas):
        pass

    @property
    def skia_irect(self):
        return skia.IRect.MakeXYWH(
                int(self.global_x),
                int(self.global_y),
                int(self.width),
                int(self.height)
            )

    def visible_rect(self):
        l, t, r, b = self.global_x, self.global_y, self.global_x1, self.global_y1
        if self.parent is not None:
            pl, pt, pr, pb = self.parent.visible_rect()
            l, t, r, b = max(l, pl), max(t, pt), min(r, pr), min(b, pb)
        return l, t, r, b

    def draw(self, ctx: skia.Canvas):
        if not self.enabled:
            return

        l, t, r, b = self.visible_rect()
        if r <= l or b <= t:  # целиком обрезан предком
            return

        if not do_rectangles_overlap([self.global_x, self.global_y, self.global_x1, self.global_y1],
                                 [self.parent.global_x, self.parent.global_y, self.parent.global_x1, self.parent.global_y1]):
            self.visible = False
            return
        self.visible = True

        if self.dirty or self._bmp is None:
            self.dirty = False
            ctx.save()
            ctx.clipRect(skia.Rect(l, t, r, b), skia.ClipOp.kIntersect, True)  # сначала клип в глобальных координатах
            ctx.translate(self.global_x, self.global_y)  # потом сдвиг
            self.draw_self(ctx)
            ctx.restore()

            if self.caching_bmp_enabled:
                self._bmp_pos = (l, t)
                self._bmp = self.window.get_surface().makeImageSnapshot(
                    skia.IRect.MakeLTRB(int(l), int(t), int(r), int(b)))
        else:
            ctx.drawImage(self._bmp, *self._bmp_pos)

    def __repr__(self):
        return f'<{self.widget_type} name={self.name} id={self.id} gx={self.global_x} gy={self.global_y} width={self.width} height={self.height}>'

    def destroy_render_resources(self):
        pass

    def destroy(self):
        for child in self.children.values():
            child.destroy()
        if self.parent is not None:
            self.parent.remove_child(self)
        self.destroy_render_resources()