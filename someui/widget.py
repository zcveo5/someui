from __future__ import annotations

import enum
import operator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal
import skia

from someui import defaults
from someui.util import Event, Defaults

if TYPE_CHECKING:
    import abstract as tc_window


_get_z_attr = operator.attrgetter('z')


class Direction(enum.Enum):
    COLUMN = 0
    ROW = 1


class PlacementType(enum.Enum):
    FIXED = 0
    AUTO = 1
    RELATIVE = 2


@dataclass(frozen=True)
class PlacementValue:
    """Порт C# PlacementValue: одно значение размещения с типом"""
    type: PlacementType = PlacementType.AUTO
    value: float = 0.0
    offset: float = 0.0

    @staticmethod
    def fixed(value: float) -> 'PlacementValue':
        return PlacementValue(PlacementType.FIXED, value)

    @staticmethod
    def auto() -> 'PlacementValue':
        return PlacementValue(PlacementType.AUTO)

    @staticmethod
    def relative(value: float) -> 'PlacementValue':
        return PlacementValue(PlacementType.RELATIVE, value)


@dataclass(kw_only=True, frozen=True)
class PlacingConfig:
    """Порт C# PlacementConfig"""
    x: PlacementValue = PlacementValue.fixed(0)
    y: PlacementValue = PlacementValue.fixed(0)
    width: PlacementValue = PlacementValue.auto()
    height: PlacementValue = PlacementValue.auto()
    anchor: Literal['left', 'right'] = 'left'


@dataclass(kw_only=True, frozen=True)
class Margins:
    """Порт C# Margins"""
    left: float = 0.0
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0


@dataclass(kw_only=True)
class ChildrenPlacementConfig:
    """Порт C# ChildrenPlacementConfig: как раскладываются дети виджета"""
    child_direction: Direction = Direction.COLUMN
    gap: float = 0.0
    margins: Margins = field(default_factory=Margins)
    propagate: bool = True


def do_rectangles_overlap(rect1, rect2):
    if (rect1[2] <= rect2[0] or  # rect1 is left of rect2
        rect2[2] <= rect1[0] or  # rect2 is left of rect1
        rect1[3] <= rect2[1] or  # rect1 is below rect2
        rect2[3] <= rect1[1]):   # rect2 is below rect1
        return False
    return True


def _coerce_placement(value, relative: bool = False) -> PlacementValue:
    """Число -> Fixed, 'auto' -> Auto, float с relative=True -> Relative.
    Готовый PlacementValue проходит как есть."""
    if isinstance(value, PlacementValue):
        return value
    if isinstance(value, str) and value.strip().lower() == 'auto':
        return PlacementValue.auto()
    if relative:
        return PlacementValue.relative(value)
    return PlacementValue.fixed(value)


def _coerce_placement_kwargs(kwargs: dict) -> dict:
    """Поддержка старого синтаксиса place(relative_width=..., x=..., y='auto')."""
    out = {}
    for key, value in kwargs.items():
        if key in ('x', 'y', 'width', 'height'):
            out[key] = _coerce_placement(value)
        elif key in ('relative_x', 'relative_y', 'relative_width', 'relative_height'):
            out[key.removeprefix('relative_')] = _coerce_placement(value, relative=True)
        else:
            raise TypeError(f'place(): неожидаемый параметр {key!r}')
    return out


class Widget:
    """Base widget class"""
    widget_type = 'Widget'

    window: tc_window.AbstractWindow
    parent: Widget | None
    children: dict[int, Widget]
    defaults: Defaults

    last_id = 0

    def __init__(self, parent: Widget | None):
        self.debug = False
        self.debug_fp = False
        self._enabled = True
        self.visible = False
        self.hidden = False
        self.placeable = True
        self.clip_self = True

        self.clickable = True
        self.hoverable = True
        self.draggable = True

        if parent is not None:
            parent = parent.real()

        self.id = Widget.last_id
        Widget.last_id += 1
        self.name = f'{self.__class__.__mro__[0].__name__}{'' if parent else ' Window'}'

        self.children = {}

        self.parent = parent

        if parent is not None:
            self.window = parent.window
            self._z = self.parent.z + 1
        else:
            self.window = self
            self._z = 0

        self.defaults = defaults.RootDefaults
        if self.parent is not None:
            self.defaults = self.parent.defaults

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
        self.mcfg = ChildrenPlacementConfig()
        self._required: tuple[float, float] | None = None

        if self.parent:
            self.parent.add_child(self)

        self.on_hold_move = Event()

        self.held = False

    def real(self):
        return self

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
        self.window.invalidate_place()
        self.window.invalidate_children()

    def cord_to_local(self, gx, gy):
        return gx - self.global_x, gy - self.global_y

    def get_size_hint(self):
        return 0, 0

    def required_size(self) -> tuple[float, float]:
        """Порт C# RequiredWidth/RequiredHeight: если виджет сам считает
        свой размер из детей (propagate), значение кладёт Measure,
        иначе берётся get_size_hint() как у листовых виджетов."""
        if not self._enabled:
            return 0, 0
        if self._required is not None:
            return self._required
        return self.get_size_hint()

    def invalidate_place(self):
        self.dirty_placement = True
        self.window.invalidate_place()

    def place(self, config: PlacingConfig | None = None, *,
              x: PlacementValue = PlacementValue.fixed(0),
              y: PlacementValue = PlacementValue.fixed(0),
              width: PlacementValue = PlacementValue.auto(),
              height: PlacementValue = PlacementValue.auto(),
              anchor: Literal['left', 'right'] = 'left'):
        if config is not None:
            self.pcfg = config
        else:
            self.pcfg = PlacingConfig(x=x, y=y, width=width, height=height, anchor=anchor)

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
        if self._width == w and self._height == h:
            return

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
        if self.x == x and self.y == y:
            return

        self._x = x
        self._y = y

        self.on_repos.process(x, y)

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
        self.children.pop(child.id)
        self.window.invalidate_children()

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

    def draw_post(self, ctx: skia.Canvas):
        pass

    def draw(self, ctx: skia.Canvas):
        if not self.enabled:
            return

        l, t, r, b = self.visible_rect()

        if r <= l or b <= t:
            self.visible = False
            return

        if self.parent:
            if not do_rectangles_overlap([self.global_x, self.global_y, self.global_x1, self.global_y1],
                                     [self.parent.global_x, self.parent.global_y, self.parent.global_x1, self.parent.global_y1]):
                self.visible = False
                return

        self.visible = True

        if self.dirty or self._bmp is None:
            self.dirty = False
            ctx.save()

            # 1. Сдвигаем холст в верхний левый угол виджета
            ctx.translate(self.global_x, self.global_y)

            if self.clip_self:
                # l, t, r, b — это глобальные координаты из твоей visible_rect()
                # Переводим их в локальные координаты виджета, вычитая его позицию:
                local_l = l - self.global_x
                local_t = t - self.global_y
                local_r = r - self.global_x
                local_b = b - self.global_y

                # 2. Режем в локальной системе координат.
                # Если родитель меньше виджета, local_r/local_b обрежут его по размеру родителя!
                ctx.clipRect(skia.Rect(local_l, local_t, local_r, local_b), skia.ClipOp.kIntersect, True)

            self.draw_self(ctx)
            ctx.restore()

            self.draw_post(ctx)


    def __repr__(self):
        return f'<{self.widget_type} name="{self.name}" id={self.id} gx={self.global_x} gy={self.global_y} width={self.width} height={self.height}>'

    def destroy_render_resources(self):
        pass

    def destroy(self):
        for child in self.children.values():
            child.destroy()
        if self.parent is not None:
            self.parent.remove_child(self)
        self.destroy_render_resources()