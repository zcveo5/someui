import operator
import platform
import threading
import time
import traceback

import glfw
import skia
from someui.abstract import AbstractWindow

_get_z_attr = operator.attrgetter('z')


def _ignore_first(fnc):
    def wrapper(*args):
        return fnc(*args[1::])
    return wrapper


SPECIAL_KEYS = {
    glfw.KEY_SPACE: "SPACE",
    glfw.KEY_ENTER: "ENTER",
    glfw.KEY_ESCAPE: "ESCAPE",
    glfw.KEY_BACKSPACE: "BACKSPACE",
    glfw.KEY_TAB: "TAB",
    glfw.KEY_LEFT_SHIFT: "LSHIFT",
    glfw.KEY_RIGHT_SHIFT: "RSHIFT",
    glfw.KEY_LEFT_CONTROL: "LCTRL",
    glfw.KEY_RIGHT_CONTROL: "RCTRL",
    glfw.KEY_LEFT_ALT: "LALT",
    glfw.KEY_RIGHT_ALT: "RALT",
    glfw.KEY_UP: "UP",
    glfw.KEY_DOWN: "DOWN",
    glfw.KEY_LEFT: "LEFT",
    glfw.KEY_RIGHT: "RIGHT",
    glfw.KEY_DELETE: "DELETE",
    glfw.KEY_INSERT: "INSERT",
    glfw.KEY_HOME: "HOME",
    glfw.KEY_END: "END",
    glfw.KEY_PAGE_UP: "PAGE_UP",
    glfw.KEY_PAGE_DOWN: "PAGE_DOWN",
}

ACTIONS = {
            glfw.PRESS: "press",
            glfw.RELEASE: "release",
            glfw.REPEAT: "repeat"
        }


def resolve_key(key, scancode) -> str:
    if key in SPECIAL_KEYS:
        return SPECIAL_KEYS[key]

    name = glfw.get_key_name(key, scancode)
    if name:
        return name.upper()

    return f"UNKNOWN_{key}"


system = platform.system()


class GLFWWindow(AbstractWindow):
    """Window implementation based on GLFW"""
    _glfws = []

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', headerless=False):
        super().__init__(width, height, title, headerless)

        if not glfw.init():
            raise RuntimeError('GLFW failed to init')

        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        if system == 'Darwin':
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        else:
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_COMPAT_PROFILE)

        glfw.window_hint(glfw.STENCIL_BITS, 8)
        glfw.window_hint(glfw.DEPTH_BITS, 24)

        self._window = window = glfw.create_window(width, height, title, None, None)

        if not self._window:
            glfw.terminate()
            raise RuntimeError()

        self.surface_dirty = True

        self.skia_context: skia.GrBackendRenderTargets | None = None
        self.surface: skia.Surfaces | None = None

        self.surface_props = skia.SurfaceProps(
            skia.SurfaceProps.kUseDeviceIndependentFonts_Flag,
            skia.PixelGeometry.kRGB_H_PixelGeometry
        )

        self._maximized = False
        self.pending_size = None

        glfw.set_window_close_callback(window, self._on_close_callback)
        glfw.set_framebuffer_size_callback(window, self._on_resize)
        glfw.set_mouse_button_callback(window, _ignore_first(self.dispatch_click))
        glfw.set_cursor_pos_callback(window, _ignore_first(self.dispatch_hover))
        glfw.set_scroll_callback(window, _ignore_first(self._wrap_scroll))
        glfw.set_key_callback(window, _ignore_first(self._process_char))
        glfw.set_window_maximize_callback(window, _ignore_first(self._maximized_proc))
        glfw.set_window_content_scale_callback(window, _ignore_first(self._resolve_size))

        self.mcfg.propagate = False

        self.on_resize.process(width, height)
        self._holden_widgets = {}

        self._glfws.append(self)

        def _on_cursor_exit(wnd, entered):
            if not entered:
                self.on_mouse_exit.process(self.mouse_x, self.mouse_y)
            else:
                self.on_mouse_enter.process()

        glfw.set_cursor_enter_callback(self._window, _on_cursor_exit)

        super().__post_init__()

    def _resolve_size(self, x, y):
        self.scale_x = x
        self.scale_y = y
        self.invalidate()

    @property
    def win32_handle(self) -> int:
        return glfw.get_win32_window(self._window)

    @property
    def macos_handle(self):
        return glfw.get_cocoa_window(self._window)

    def _maximized_proc(self, val):
        self._maximized = val == 1
        self.on_maximize.process(self._maximized)

    def _render_thread(self):
        window = self._window
        glfw.make_context_current(window)
        glfw.swap_interval(1)

        self.skia_context = skia.GrDirectContext.MakeGL()

        last_time = time.time()

        try:
            while self.is_running:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                if self.surface_dirty:
                    self._create_surface()
                    self.surface_dirty = False

                self.on_animation_frame.process(dt)

                self.render(self.get_canvas())
                self.surface.flushAndSubmit()
                glfw.swap_buffers(window)
        except Exception as _ex:
            traceback.print_exception(_ex)
            self.destroy()
        finally:
            self.skia_context.abandonContext()
            self.skia_context = None

    def _wrap_scroll(self, dx, dy):
        if system == 'Windows':
            dy *= 120
            dx *= 120

        self.dispatch_scroll(dx, dy)

    def _process_char(self, key, scancode, action, mods):
        key_str = resolve_key(key, scancode)

        if key_str.startswith('UNKNOWN'):
            return

        # Превращаем числовой action в нормальную строчку или оставляем константу
        # glfw.PRESS (1), glfw.RELEASE (0), glfw.REPEAT (2)
        action_str = ACTIONS.get(action, "UNKNOWN")

        shift_state = bool(mods & glfw.MOD_SHIFT)
        ctrl_state = bool(mods & glfw.MOD_CONTROL)
        alt_state = bool(mods & glfw.MOD_ALT)
        # super_state = bool(mods & glfw.MOD_SUPER)

        # Итоговый кортеж со всеми данными
        # event_tuple = (key_str, action_str, shift_state, ctrl_state, alt_state)

        # Дальше отправляй этот эвент в свой диспетчер / фокусный инпут
        if action_str == 'press':
            self.on_keyboard_press.process(key_str, shift_state, ctrl_state, alt_state)
        elif action_str == 'release':
            self.on_keyboard_release.process(key_str, shift_state, ctrl_state, alt_state)
        if action_str == 'press' or action_str == 'repeat':
            self.on_keyboard_write.process(key_str, shift_state, ctrl_state, alt_state)

    @property
    def is_maximized(self) -> bool:
        return self._maximized

    @is_maximized.setter
    def is_maximized(self, value):
        if value:
            glfw.maximize_window(self._window)
        else:
            glfw.restore_window(self._window)

    def show(self):
        glfw.show_window(self._window)

    def hide(self):
        glfw.iconify_window(self._window)

    def _set_size(self, w, h):
        glfw.set_window_size(self._window, int(w), int(h))

    def get_size(self) -> tuple[int, int]:
        return glfw.get_window_size(self._window)

    def set_title(self, title: str):
        glfw.set_window_title(self._window, title)

    def swap_buffers(self):
        self.skia_context.flush()
        glfw.swap_buffers(self._window)

    def get_canvas(self) -> skia.Canvas:
        return self.surface.getCanvas()

    def get_surface(self) -> skia.Surface:
        return self.surface

    def destroy_window(self):
        if self._window:
            glfw.destroy_window(self._window)

        self._glfws.remove(self)
        if not self._glfws:
            glfw.terminate()

    def pool_native(self):
        glfw.poll_events()
        if self.pending_size:
            self.on_resize.process(*self.pending_size)
            self.pending_size = None

    def _on_close_callback(self, window):
        self.is_running = False
        self.destroy()

    def _on_resize(self, win, width, height):
        self._width, self._height = width, height
        self.pending_size = (width, height)
        self._invalidate_surface()
        self.invalidate_place()

    def _invalidate_surface(self):
        self.surface_dirty = True

    def _create_surface(self):
        width, height = glfw.get_framebuffer_size(self._window)
        if width <= 0 or height <= 0:
            return

        fb_info = skia.GrGLFramebufferInfo(0, 0x8058)

        backend_target = skia.GrBackendRenderTarget(
            width,
            height,
            0,
            8,
            fb_info,
        )

        self.surface = skia.Surface.MakeFromBackendRenderTarget(
            self.skia_context,
            backend_target,
            skia.kBottomLeft_GrSurfaceOrigin,
            skia.kRGBA_8888_ColorType,
            skia.ColorSpace.MakeSRGB(),
            self.surface_props
        )

        if self.surface is None:
            raise RuntimeError(f'Surface is None')


class WindowHeaderWidgetMixin:
    window: GLFWWindow

    def __init__(self: 'Self@WindowHeaderWidgetMixin'):
        if not isinstance(self.window, GLFWWindow):
            raise ValueError(self.window)

        self.on_hover_enter(self._set_header)
        self.on_hover_exit(self._reset_header)

    def _set_header(self, *_):
        self.window.on_header = True

    def _reset_header(self, *_):
        self.window.on_header = False