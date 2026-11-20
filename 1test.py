import ctypes
from ctypes import wintypes
import glfw
import skia
from OpenGL import GL

# Win32 Constants
GWLP_WNDPROC = -4
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOOWNERZORDER = 0x0200
SWP_FRAMECHANGED = 0x0020

SM_CXSIZEFRAME = 32
SM_CYSIZEFRAME = 33
SM_CXPADDEDBORDER = 92

HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

TITLEBAR_HEIGHT = 36


def get_resize_padding(hwnd):
    dpi = user32.GetDpiForWindow(hwnd) or 96
    padded = user32.GetSystemMetricsForDpi(SM_CXPADDEDBORDER, dpi)
    bx = user32.GetSystemMetricsForDpi(SM_CXSIZEFRAME, dpi) + padded
    by = user32.GetSystemMetricsForDpi(SM_CYSIZEFRAME, dpi) + padded
    return bx, by


class NCCALCSIZE_PARAMS(ctypes.Structure):
    _fields_ = [
        ("rgrc", wintypes.RECT * 3),
        ("lppos", ctypes.c_void_p),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

user32 = ctypes.windll.LoadLibrary('user32')
user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, WNDPROC]
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.CallWindowProcW.argtypes = [
    ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
]
user32.CallWindowProcW.restype = ctypes.c_ssize_t
user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT
]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.GetDpiForWindow.argtypes = [wintypes.HWND]
user32.GetSystemMetricsForDpi.argtypes = [ctypes.c_int, wintypes.UINT]

old_wndproc = None


def custom_wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_NCCALCSIZE and wparam == 1:
        params = ctypes.cast(lparam, ctypes.POINTER(NCCALCSIZE_PARAMS)).contents
        bx, by = get_resize_padding(hwnd)
        params.rgrc[0].left += bx
        params.rgrc[0].right -= bx
        params.rgrc[0].bottom -= by
        params.rgrc[0].top += 0
        return 0

    if msg == WM_NCHITTEST:
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        bx, by = get_resize_padding(hwnd)

        if not user32.IsZoomed(hwnd):
            left = rect.left <= x < rect.left + bx
            right = rect.right - bx <= x < rect.right

            top = rect.top <= y < rect.top + by

            if top and left: return HTTOPLEFT
            if top and right: return HTTOPRIGHT
            if left: return HTLEFT
            if right: return HTRIGHT
            if top: return HTTOP

        if rect.top <= y < rect.top + TITLEBAR_HEIGHT:
            return HTCAPTION

        return HTCLIENT

    return user32.CallWindowProcW(old_wndproc, hwnd, msg, wparam, lparam)


wndproc_ref = WNDPROC(custom_wndproc)


def main():
    global old_wndproc

    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(900, 600, "Skia Custom NC Zone", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    hwnd = glfw.get_win32_window(window)

    # Create Skia GPU DirectContext
    gr_context = skia.GrDirectContext.MakeGL()

    # Hook WndProc and trigger WM_NCCALCSIZE
    old_wndproc = user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, wndproc_ref)
    user32.SetWindowPos(
        hwnd, None, 0, 0, 0, 0,
        SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER
    )

    surface = None
    last_size = (0, 0)

    while not glfw.window_should_close(window):
        fb_w, fb_h = glfw.get_framebuffer_size(window)

        if fb_w > 0 and fb_h > 0:
            # Recreate Skia surface only when framebuffer dimensions change
            if (fb_w, fb_h) != last_size or surface is None:
                GL.glViewport(0, 0, fb_w, fb_h)
                surface = create_skia_surface(gr_context, fb_w, fb_h)
                last_size = (fb_w, fb_h)

            with surface as canvas:
                draw_skia_ui(canvas, fb_w, fb_h)
            surface.flushAndSubmit()

        glfw.swap_buffers(window)
        glfw.wait_events()

    surface = None
    gr_context = None
    user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(old_wndproc, WNDPROC))
    glfw.terminate()


if __name__ == "__main__":
    main()
