import ctypes
import os
from ctypes import wintypes
from pathlib import Path
import glfw
import dotenv
from someui.crossplatform.headerless import AbstractProtocol

env = dotenv.load_dotenv()
dll_path = None # Debug DLL path

if env:
    dll_path = os.environ.get('W32_HEADERLESS_DLL_PATH', None)

fp = Path(__file__)
dll = ctypes.CDLL(fp.parent / 'lib' / 'win32-headerless.dll' if not dll_path else dll_path)


dll.AttachWindow.argtypes = [wintypes.HWND]
dll.AttachWindow.restype = wintypes.BOOL

dll.SetHeader.argtypes = [wintypes.HWND, wintypes.BOOL]
dll.SetHeader.restype = None

dll.SetOnMaximize.argtypes = [wintypes.HWND, wintypes.BOOL]
dll.SetOnMaximize.restype = None

dll.SetEnabled.argtypes = [wintypes.HWND, wintypes.BOOL]
dll.SetEnabled.restype = None

dll.DetachWindow.argtypes = [wintypes.HWND]
dll.DetachWindow.restype = None

dll.GetDebug.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
dll.GetDebug.restype = ctypes.c_int

dll.SetMaxiRect.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
dll.SetMaxiRect.restype = None


class Window(AbstractProtocol):
    def __init__(self, window):
        super().__init__(window)
        self.hwnd = window.win32_handle()
        self._enabled = False
        if not self._enabled:
            if not dll.AttachWindow(self.hwnd):
                raise Exception('Failed to AttachWindow')

    def enable(self):
        dll.SetEnabled(self.hwnd, True)

    def disable(self):
        dll.SetEnabled(self.hwnd, False)

    @property
    def on_header(self):
        return None

    @on_header.setter
    def on_header(self, value):
        dll.SetHeader(self.hwnd, value)

    @property
    def on_sysmenu(self):
        return None

    @on_sysmenu.setter
    def on_sysmenu(self, value):
        dll.SetOnMaximize(self.hwnd, value)

    def set_maxi_rect(self, left, top, right, bottom):
        dll.SetMaxiRect(self.hwnd, left, top, right, bottom)

    def dispose(self):
        dll.DetachWindow(self.hwnd)

    def debug(self) -> str:
        needed_size = dll.GetDebug(self.hwnd, None, 0)
        if needed_size <= 0:
            return ""

        buf = ctypes.create_unicode_buffer(needed_size)
        dll.GetDebug(self.hwnd, buf, needed_size)

        return buf.value