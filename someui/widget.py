from __future__ import annotations

import operator
import traceback
from typing import TYPE_CHECKING

import skia
if TYPE_CHECKING:
    import abstract as tc_window


_get_z_attr = operator.attrgetter('z')


class Event:
    def __init__(self):
        self._functions = []

    def __call__(self, fnc):
        self._functions.append(fnc)
        return fnc

    def process(self, *args):
        [i(*args) for i in self._functions]


class Widget:
    """Base widget class"""
    widget_type = 'Widget'

    window: tc_window.AbstractWindow
    parent: Widget
    children: dict[int, Widget]

    last_id = 0

    def __init__(self, parent: Widget | None):
        self.enabled = True
        self.id = Widget.last_id
        Widget.last_id += 1

        self.children = {}

        self.parent = parent
        if parent is not None:
            self.window = parent.window
            self.z = self.parent.z + 1
        else:
            self.window = self
            self.z = 0

        self._x = 0
        self._y = 0
        self._width = 0
        self._height = 0

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

        self.hovered = False

        self.dirty = False

        if self.parent:
            self.parent.add_child(self)

        self.on_hold_move = Event()

        self.held = False

    @property
    def is_hold(self):
        return self.held

    def cord_to_local(self, gx, gy):
        return gx - self.global_x, gy - self.global_y

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
    def skia_rect(self) -> skia.Rect:
        return skia.Rect(self.global_x, self.global_y, self.global_x1, self.global_y1)

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
        self.on_repos.process(x, y)

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
        for _c in sorted(self.children.values(), key=_get_z_attr, reverse=True):
            _c.draw(ctx)

    def draw_self(self, ctx: skia.Canvas):
        pass

    def draw(self, ctx: skia.Canvas):
        self.draw_self(ctx)
        self.draw_children(ctx)

    def __repr__(self):
        return f'<{self.widget_type} id={self.id}>'

    def destroy_render_resources(self):
        pass

    def destroy(self):
        for child in self.children.values():
            child.destroy()
        if self.parent is not None:
            self.parent.remove_child(self)
        self.destroy_render_resources()