import platform

from someui import GLFWWindow
from someui.windows.macos_window import MacWindow

WINDOWS = {
    'Windows': GLFWWindow,
    'Darwin': MacWindow,
}
DEFAULT = GLFWWindow

WindowForPlatform = WINDOWS.get(platform.system(), DEFAULT)

if WindowForPlatform is None:
    raise RuntimeError(f'{platform.system()} is not supported')