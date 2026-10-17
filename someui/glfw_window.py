import operator
import glfw
import skia
from .abstract import AbstractWindow

_get_z_attr = operator.attrgetter('z')


def _ignore_first(fnc):
    def wrapper(*args):
        return fnc(*args[1::])
    return wrapper


class GLFWWindow(AbstractWindow):
    _glfws = []

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', frameless=False):
        super().__init__(width, height, title, frameless)

        if not glfw.init():
            raise RuntimeError('GLFW failed to init')

        glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
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
        glfw.set_scroll_callback(window, _ignore_first(self.dispatch_scroll))

        self.on_resize.process(width, height)
        self._holden_widgets = {}

        self._glfws.append(self)

        def _on_cursor_exit(wnd, entered):
            if not entered:
                self.on_mouse_exit.process()

        glfw.set_cursor_enter_callback(self._window, _on_cursor_exit)

    def show(self):
        glfw.show_window(self._window)

    def hide(self):
        glfw.hide_window(self._window)

    def _set_size(self, w, h):
        glfw.set_window_size(self._window, w, h)

    def get_size(self) -> tuple[int, int]:
        return glfw.get_window_size(self._window)

    def set_title(self, title: str):
        glfw.set_window_title(self._window, title)

    def get_native_handle(self) -> int | None:
        return glfw.get_win32_window(self._window)

    def swap_buffers(self):
        self.skia_context.flush()
        glfw.swap_buffers(self._window)

    def get_canvas(self) -> skia.Canvas:
        return self.surface.getCanvas()

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
        self.invalidate()

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
        )
