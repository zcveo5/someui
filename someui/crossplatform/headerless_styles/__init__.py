import platform

from someui.windows.platrel_window import WindowForPlatform
from someui.abstract import AbstractWindow
from someui.crossplatform.headerless_styles.win32 import Headered as _Win32Style

system = platform.system()


_windows = {
    'Windows': _Win32Style
}


HeaderlessWindow: type[AbstractWindow] = _windows.get(system, WindowForPlatform)

