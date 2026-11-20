from __future__ import annotations
import abc
import operator
import threading

import skia
from someui import widget
import time

from someui.crossplatform.headerless import AbstractProtocol, get as get_headerless
from someui.crossplatform.window_loops.abstract import NativeLoop, AbstractWindowLoop

if NativeLoop is None:
    raise ImportError('NativeLoop not found')

_loop: AbstractWindowLoop = NativeLoop()

_get_z_attr = operator.attrgetter('z')


def get_loop() -> AbstractWindowLoop:
    return _loop


class AbstractWindow(widget.Widget, abc.ABC):
    windows: list[AbstractWindow] = []

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', headerless=False):
        super().__init__(None)
        self._width = width
        self._height = height
        self._title = title
        self._headerless = headerless

        self.is_running = True
        self.flat_children: list[widget.Widget] = []
        self.children_rebuild = False
        self.scene_rebuild = False
        self.scene_rebuilding = False

        self.mouse_x, self.mouse_y = 0, 0
        self.window_background = 0x0

        self.scale_x = self.scale_y = 1.0

        self.on_mouse_exit = widget.Event()
        self.on_mouse_enter = widget.Event()
        self.on_keyboard_press = widget.Event() # Press
        self.on_keyboard_release = widget.Event() # Release
        self.on_keyboard_write = widget.Event() # Press & Repeat
        self.on_resize.process(width, height)
        self.on_animation_frame = widget.Event()
        self.on_maximize = widget.Event()
        self.on_ready = widget.Event()
        self.on_scene_rebuild = widget.Event()

        self.windows.append(self)
        _loop.attach(self)

    def __post_init__(self):
        _inst = get_headerless()
        self.headerless_helper: AbstractProtocol | None = None
        if _inst is not None:
            self.headerless_helper = _inst(self)
            if self._headerless:
                self.headerless_helper.enable()

        self.on_ready.process()

        self.render_thread = threading.Thread(target=self._render_thread, name=f'{self.name}-RenderThread')
        self.render_thread.start()

    @property
    def on_header(self):
        if self.headerless_helper:
            return self.headerless_helper.on_header
        return False

    @on_header.setter
    def on_header(self, value):
        if self.headerless_helper:
            self.headerless_helper.on_header = value

    @property
    def headerless(self):
        return self._headerless

    @headerless.setter
    def headerless(self, value):
        self._headerless = value
        if self.headerless_helper is not None:
            if value:
                self.headerless_helper.enable()
            else:
                self.headerless_helper.disable()

    @abc.abstractmethod
    def win32_handle(self) -> int: ...

    @abc.abstractmethod
    def macos_handle(self): ...

    @abc.abstractmethod
    def _render_thread(self): ...

    @property
    @abc.abstractmethod
    def is_maximized(self) -> bool: ...

    @is_maximized.setter
    @abc.abstractmethod
    def is_maximized(self, value): ...

    @abc.abstractmethod
    def show(self): ...

    @abc.abstractmethod
    def hide(self): ...

    @abc.abstractmethod
    def _set_size(self, w, h): ...

    @abc.abstractmethod
    def get_size(self) -> tuple[int, int]: ...

    @abc.abstractmethod
    def set_title(self, title: str): ...

    @abc.abstractmethod
    def swap_buffers(self): ...

    @abc.abstractmethod
    def get_canvas(self) -> skia.Canvas: ...

    @abc.abstractmethod
    def get_surface(self) -> skia.Surfaces: ...

    @abc.abstractmethod
    def pool_native(self): ...

    def pool(self):
        self.pool_native()
        if self.scene_rebuild:
            self.rebuild_scene()
        if self.children_rebuild:
            self.build_children()

    @abc.abstractmethod
    def destroy_window(self): ...

    def get_size_hint(self):
        return self.get_size()

    def destroy(self):
        self.hide()
        self.render_thread.join()
        self.destroy_window()
        if self in self.windows:
            self.windows.remove(self)
        if self in _loop.windows:
            _loop.deattach(self)
        self.is_running = False
        _loop.wakeup()

    def set_size(self, w=None, h=None, x1=None, y1=None):
        super().set_size(w, h, x1, y1)
        self._set_size(self._width, self._height)

    def add_child(self, child):
        super().add_child(child)
        self.invalidate_children()

    def invalidate_place(self):
        self.scene_rebuild = True
        _loop.wakeup()

    def invalidate_children(self):
        self.children_rebuild = True
        _loop.wakeup()

    def build_children(self):
        self.children_rebuild = False
        _flat = []
        stack = list(self.children.values())

        while stack:
            _child = stack.pop()
            if _child.enabled:
                _flat.append(_child)
                if _child.children:
                    stack.extend(reversed([i for i in _child.children.values() if i.enabled]))

        _flat.sort(key=_get_z_attr)
        self.flat_children = _flat

    def render(self, ctx: skia.Canvas):
        ctx.clear(self.window_background)

        ctx.save()
        ctx.scale(self.scale_x, self.scale_y)

        for i in self.flat_children:
            try:
                i.draw(ctx)
            except Exception as _ex:
                _ex.add_note(f'While rendering {i}')
                raise _ex

        ctx.restore()

    def update(self):
        self.dirty = False

    def request_redraw(self):
        if not self.dirty:
            self.dirty = True
            _loop.wakeup()

    def on_window_resize(self, width: int, height: int):
        self._width, self._height = width, height
        self.on_resize.process(width, height)
        self.invalidate()

    def dispatch_hover(self, x: float, y: float):
        self.mouse_x, self.mouse_y = x, y

        self.on_hover.process(x, y)

        given = False

        for _child in reversed(self.flat_children):
            if not _child.enabled or not _child.hoverable:
                continue

            if _child.held:
                _child.on_hold_move.process(x, y)

            is_hovered = _child.hittest(x, y)

            if is_hovered and not given:
                if not _child.hovered:
                    _child.hovered = True
                    _child.on_hover_enter.process(x, y)

                _child.on_hover.process(x, y)

                given = True
            elif _child.hovered:
                _child.hovered = False
                _child.on_hover_exit.process(x, y)

    def dispatch_scroll(self, delta_x: int, delta_y: int):
        x, y = self.mouse_x, self.mouse_y

        for _child in reversed(self.flat_children):
            if not _child.enabled or not _child.scroll_enabled:
                continue
            if _child.hittest(x, y):
                if delta_x:
                    _child.on_horizontal_scroll.process(delta_x, x, y)
                if delta_y:
                    _child.on_scroll.process(delta_y, x, y)

    def dispatch_click(self, button: int, action: int, mods: int):
        x, y = self.mouse_x, self.mouse_y

        if action == 1:
            self.on_mouse_press.process(button, x, y)
        else:
            self.on_mouse_release.process(button, x, y)

        for _child in reversed(self.flat_children):
            if not _child.enabled  or not _child.clickable:
                continue
            if _child.hittest(x, y):
                if action == 1:  # PRESS
                    _child.held = True
                    _child.on_mouse_press.process(button, x, y)
                else:  # RELEASE
                    _child.held = False
                    _child.on_mouse_release.process(button, x, y)
            elif _child.held:
                _child.held = False
                _child.on_mouse_release.process(button, x, y)

    def __repr__(self):
        return f'<Window id={self.id} dirty={self.dirty} d_place={self.scene_rebuild}>'

    @staticmethod
    def call_after(cb, sec):
        _loop.call_at(cb, time.time() + sec)

    @staticmethod
    def mainloop():
        return _loop.run()

    def rebuild_scene(self):
        if self.scene_rebuilding:
            raise RuntimeError('Scene is rebuilding')

        self.scene_rebuilding = True
        self.scene_rebuild = False

        try:
            self._rebuild_scene(self)
        finally:
            self.scene_rebuilding = False

        self.on_scene_rebuild.process()

    def _measure(self, wdg: widget.Widget):
        """Порт SceneWidget.Measure: считает required-размер виджета из детей
        (только если propagate), снизу вверх."""
        ccfg = wdg.mcfg

        if not ccfg.propagate or not wdg.enabled:
            return

        for c in wdg.iter_children():
            self._measure(c)

        total_w = 0.0
        total_h = 0.0

        for c in wdg.iter_children():
            cw, ch = c.required_size()

            if ccfg.child_direction == widget.Direction.COLUMN:
                total_h += ch + ccfg.gap
                total_w = max(total_w, cw)
            else:
                total_w += cw + ccfg.gap
                total_h = max(total_h, ch)

        if wdg.children:
            m = ccfg.margins
            wdg._required = (total_w + m.left + m.right, total_h + m.top + m.bottom)

    def _resolve_place(self, wdg: widget.Widget, child: widget.Widget, auto: float):
        """Порт SceneWidget.ResolvePlace: возвращает (x, y, w, h, auto)."""
        if not wdg.enabled:
            return 0, 0, 0, 0, auto

        ccfg = wdg.mcfg
        m = ccfg.margins

        available_width = wdg.width - m.left - m.right
        available_height = wdg.height - m.top - m.bottom

        p = child.pcfg

        if p.width.type == widget.PlacementType.FIXED:
            w = p.width.value
        elif p.width.type == widget.PlacementType.RELATIVE:
            w = available_width * p.width.value
        else:
            w = child.required_size()[0]

        w += p.width.offset

        if p.height.type == widget.PlacementType.FIXED:
            h = p.height.value
        elif p.height.type == widget.PlacementType.RELATIVE:
            h = available_height * p.height.value
        else:
            h = child.required_size()[1]

        h += p.height.offset

        x = 0.0
        if p.x.type == widget.PlacementType.FIXED:
            x = p.x.value
        elif p.x.type == widget.PlacementType.RELATIVE:
            x = available_width * p.x.value
        elif p.x.type == widget.PlacementType.AUTO and ccfg.child_direction == widget.Direction.ROW:
            x = auto
            auto += w + ccfg.gap

        x += m.left + p.x.offset

        if p.anchor == 'right':
            x -= w

        y = 0.0
        if p.y.type == widget.PlacementType.FIXED:
            y = p.y.value
        elif p.y.type == widget.PlacementType.RELATIVE:
            y = available_height * p.y.value
        elif p.y.type == widget.PlacementType.AUTO and ccfg.child_direction == widget.Direction.COLUMN:
            y = auto
            auto += h + ccfg.gap

        y += m.top + p.y.offset

        return x, y, w, h, auto

    def _rebuild_scene(self, wdg: widget.Widget):
        """Порт SceneWidget.RebuildScene."""
        if wdg.mcfg.propagate:
            self._measure(wdg)

        auto = 0.0

        for child in wdg.iter_children():
            if not child.placeable:
                continue

            if child.enabled:
                x, y, w, h, auto = self._resolve_place(wdg, child, auto)

                child.set_position(x, y)
                child.set_size(w, h)

                self._rebuild_scene(child)