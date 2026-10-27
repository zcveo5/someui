import operator
import platform

import glfw
import skia
from .abstract import AbstractWindow

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
    # 1. Проверяем, есть ли клавиша в словаре спецклавиш
    if key in SPECIAL_KEYS:
        return SPECIAL_KEYS[key]

    # 2. Пробуем получить имя от GLFW (возвращает символ в текущей раскладке, например 'a', '1', '.')
    name = glfw.get_key_name(key, scancode)
    if name:
        return name.upper()

    return f"UNKNOWN_{key}"


system = platform.system()

print(f'System: {system}')


class GLFWWindow(AbstractWindow):
    """Window implementation based on GLFW"""
    _glfws = []

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', frameless=False):
        super().__init__(width, height, title, frameless)

        if not glfw.init():
            raise RuntimeError('GLFW failed to init')

        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        if frameless:
            glfw.window_hint(glfw.DECORATED, False)

        # Профиль зависит от ОС: на macOS только Core, на Windows/Linux можно Compat
        if system == 'Darwin':
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # Обязательно для Core Profile на Mac
            self.scale_mod = 2.0
        else:
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_COMPAT_PROFILE)

        glfw.window_hint(glfw.STENCIL_BITS, 8)
        glfw.window_hint(glfw.DEPTH_BITS, 24)

        self._window = window = glfw.create_window(width, height, title, None, None)

        if not self._window:
            glfw.terminate()
            raise RuntimeError()

        glfw.make_context_current(window)
        glfw.swap_interval(1)

        self.skia_context: skia.GrBackendRenderTargets = skia.GrDirectContext.MakeGL()
        self._create_surface()

        glfw.set_window_close_callback(window, self._on_close_callback)
        glfw.set_framebuffer_size_callback(window, self._on_resize)
        glfw.set_mouse_button_callback(window, _ignore_first(self.dispatch_click))
        glfw.set_cursor_pos_callback(window, _ignore_first(self.dispatch_hover))
        glfw.set_scroll_callback(window, _ignore_first(self._wrap_scroll))
        glfw.set_key_callback(window, _ignore_first(self._process_char))

        self.mcfg.propagate = False

        self.on_resize.process(width, height)
        self._holden_widgets = {}

        self._glfws.append(self)

        def _on_cursor_exit(wnd, entered):
            if not entered:
                self.on_mouse_exit.process()
            else:
                self.on_mouse_enter.process()

        glfw.set_cursor_enter_callback(self._window, _on_cursor_exit)

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
        event_tuple = (key_str, action_str, shift_state, ctrl_state, alt_state)

        # Дальше отправляй этот эвент в свой диспетчер / фокусный инпут
        if action_str == 'press':
            self.on_keyboard_press.process(key_str, shift_state, ctrl_state, alt_state)
        elif action_str == 'release':
            self.on_keyboard_release.process(key_str, shift_state, ctrl_state, alt_state)
        elif action_str == 'press' or action_str == 'repeat':
            self.on_keyboard_write.process(key_str, shift_state, ctrl_state, alt_state)

    def show(self):
        glfw.show_window(self._window)

    def hide(self):
        glfw.hide_window(self._window)

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

    def _destroy(self):
        if self._window:
            glfw.destroy_window(self._window)

        self._glfws.remove(self)
        if not self._glfws:
            glfw.terminate()

    def pool(self):
        glfw.poll_events()

    def _on_close_callback(self, window):
        self.is_running = False
        self.destroy()

    def _on_resize(self, win, width, height):
        self._width, self._height = width, height
        self._create_surface()
        self.on_resize.process(width, height)
        self.update()
        self.invalidate_place()

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

        surface_props = skia.SurfaceProps(
            skia.SurfaceProps.kUseDeviceIndependentFonts_Flag,
            skia.PixelGeometry.kRGB_H_PixelGeometry
        )

        self.surface = skia.Surface.MakeFromBackendRenderTarget(
            self.skia_context,
            backend_target,
            skia.kBottomLeft_GrSurfaceOrigin,
            skia.kRGBA_8888_ColorType,
            skia.ColorSpace.MakeSRGB(),
            surface_props
        )
