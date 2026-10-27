from __future__ import annotations
import abc
import operator
import skia
from . import widget
import time
from someui.universal_loop import NativeLoop, AbstractWindowLoop

if NativeLoop is None:
    raise ImportError('NativeLoop not found')

_loop: AbstractWindowLoop = NativeLoop([])

_get_z_attr = operator.attrgetter('z')


def get_loop() -> AbstractWindowLoop:
    return _loop


class AbstractWindow(widget.Widget, abc.ABC):
    windows: list[AbstractWindow] = []

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', frameless=False):
        super().__init__(None)
        self._width = width
        self._height = height
        self._title = title

        self.is_running = True
        self.flat_children: list[widget.Widget] = []
        self.children_rebuild = False
        self.scene_rebuild = False

        self.mouse_x, self.mouse_y = 0, 0
        self.window_background = 0x0

        self.scale_mod = 1.0

        self.on_mouse_exit = widget.Event()
        self.on_mouse_enter = widget.Event()
        self.on_keyboard_press = widget.Event() # Press
        self.on_keyboard_release = widget.Event() # Release
        self.on_keyboard_write = widget.Event() # Press & Repeat
        self.on_resize.process(width, height)

        self.windows.append(self)
        _loop.windows.append(self)

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
    def pool(self): ...

    @abc.abstractmethod
    def _destroy(self): ...

    def destroy(self):
        if self in self.windows:
            self.windows.remove(self)
        if self in _loop.windows:
            _loop.windows.remove(self)
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

    def rebuild_scene(self):
        self.scene_rebuild = False

        def build_widget(wdg: widget.Widget):
            base_w, base_h = wdg.width, wdg.height  # размер родителя — база для relative
            auto_y = 0
            max_w = 0
            deferred = []

            for c in wdg.iter_children():
                #if not c.enabled:
                #    continue

                # propagate-виджет: сначала раскладываем его внутренности (снизу вверх),
                # его размер станет известен после этого
                if c.mcfg.propagate:
                    build_widget(c)

                cfg = c.pcfg
                hint_w, hint_h = c.get_size_hint()
                if c.mcfg.propagate:
                    hint_w, hint_h = c.width, c.height

                tx = cfg.x if cfg.x is not None else 0
                if cfg.y == 'auto':
                    ty = auto_y
                else:
                    ty = cfg.y if cfg.y is not None else 0

                if cfg.width is not None:
                    tw = cfg.width
                elif cfg.relative_width is not None:
                    tw = base_w * cfg.relative_width
                else:
                    tw = hint_w

                if cfg.height is not None:
                    th = cfg.height
                elif cfg.relative_height is not None:
                    th = base_h * cfg.relative_height
                else:
                    th = hint_h

                if cfg.relative_x is not None:
                    tx = base_w * cfg.relative_x
                if cfg.relative_y is not None:
                    ty = base_h * cfg.relative_y

                if cfg.y == 'auto':
                    auto_y += th
                max_w = max(max_w, tx + tw)

                c.set_position(tx, ty)
                c.set_size(tw, th)
                deferred.append(c)

            # теперь размер каждого ребёнка известен — идём вглубь
            for c in deferred:
                if not c.mcfg.propagate:  # propagate уже обработан выше
                    build_widget(c)

            if wdg.mcfg.propagate:
                wdg.set_size(max_w, min(auto_y, wdg.parent.height))

        build_widget(self)


    def render(self, ctx):
        ctx.save()
        ctx.scale(self.scale_mod, self.scale_mod)

        for i in self.flat_children:
            i.draw(ctx)

        ctx.restore()

    def update(self):
        canvas = self.get_canvas()
        if canvas is None:
            return
        canvas.clear(self.window_background)
        self.render(canvas)
        self.swap_buffers()
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

        for _child in reversed(self.flat_children):
            if not _child.enabled:
                continue

            if _child.held:
                _child.on_hold_move.process(x, y)

            is_hovered = _child.hittest(x, y)

            if is_hovered:
                if not _child.hovered:
                    _child.hovered = True
                    _child.on_hover_enter.process(x, y)

                _child.on_hover.process(x, y)
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
            if not _child.enabled:
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

    @staticmethod
    def call_after(cb, sec):
        _loop.call_at(cb, time.time() + sec)

    @staticmethod
    def mainloop():
        return _loop.run()