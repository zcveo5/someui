from ctypes import *

from win32more.Windows.Win32.Foundation import POINT
from win32more.Windows.Win32.Graphics.Gdi import ScreenToClient
from win32more.Windows.Win32.UI.Input.KeyboardAndMouse import GetKeyNameTextW


def lparam_to_xy(lP):
    x = c_short(lP & 0xffff).value
    y = c_short((lP >> 16) & 0xffff).value
    return x, y


def decode_cords(fnc):
    def wrapper(lParam, wParam):
        return fnc(*lparam_to_xy(lParam))

    wrapper.__name__ = f'@decode_cords {fnc.__name__}'
    return wrapper


def decode_screen_cords(hwnd):
    def decorator(fnc):
        def wrapper(lParam, wParam):
            point = POINT(*lparam_to_xy(lParam))
            ScreenToClient(hwnd, byref(point))
            return fnc(point.x, point.y, wParam)

        wrapper.__name__ = f'@decode_screen_cords({hwnd}) {fnc.__name__}'
        return wrapper
    return decorator


def key_name(lParam):
    buffer = create_unicode_buffer(32)
    GetKeyNameTextW(lParam, buffer, c_int32(len(buffer)))
    return buffer.value


def decode_keyboard(fnc):
    def wrapper(lParam, wParam):
        return fnc(key_name(lParam))
    wrapper.__name__ = f'@decode_keyboard {fnc.__name__}'
    return wrapper


def drop_param(fnc):
    def wrapper(*_):
        return fnc()
    wrapper.__name__ = f'@drop_param {fnc.__name__}'
    return wrapper


__all__ = ['decode_cords', 'decode_screen_cords', 'decode_keyboard', 'drop_param', 'lparam_to_xy', 'key_name']