import traceback
from collections import defaultdict
from typing import Literal

from someui.abstract import AbstractWindow
import ctypes
from win32more.Windows.Win32.Foundation import HWND, WPARAM, LPARAM
from win32more.Windows.Win32.UI.WindowsAndMessaging import (
    WNDCLASSEXW, RegisterClassExW, CreateWindowExW, DefWindowProcW,
    GetMessageW, TranslateMessage, DispatchMessageW, ShowWindow,
    WS_OVERLAPPEDWINDOW, CS_OWNDC, MSG, SetWindowPos, SWP_NOMOVE,
    SWP_NOACTIVATE, SWP_FRAMECHANGED, SetWindowTextW, DestroyWindow, PeekMessageW, PM_REMOVE, IsWindow
)
from win32more.Windows.Win32.Graphics.Gdi import (
    GetDC, ReleaseDC
)
from win32more.Windows.Win32.Graphics.OpenGL import (
    PIXELFORMATDESCRIPTOR,
    PFD_DRAW_TO_WINDOW,
    PFD_SUPPORT_OPENGL,
    PFD_DOUBLEBUFFER,
    PFD_TYPE_RGBA,
    ChoosePixelFormat,
    SetPixelFormat,
    SwapBuffers,
    wglCreateContext,
    wglMakeCurrent,
    wglDeleteContext,
)

import skia
from param_decryprers import *


e_expl = {
    0x0001: "WM_CREATE"                ,# Окно создаётся (вызывается до того, как окно станет видимым)
    0x0002: "WM_DESTROY"               ,# Окно уничтожается (сигнал к завершению работы окна)
    0x0003: "WM_MOVE"                  ,# Окно перемещено
    0x0005: "WM_SIZE"                  ,# Изменён размер окна
    0x0006: "WM_ACTIVATE"              ,# Окно активируется или деактивируется (получает/теряет фокус ввода)
    0x0007: "WM_SETFOCUS"              ,# Окно получило фокус клавиатуры
    0x0008: "WM_KILLFOCUS"             ,# Окно потеряло фокус клавиатуры
    0x000A: "WM_ENABLE"                ,# Состояние доступности окна изменено (Enabled / Disabled)
    0x000E: "WM_GETTEXT"               ,# Запрос на получение текста/заголовка окна
    0x000F: "WM_PAINT"                 ,# Запрос на отрисовку клиентской области окна
    0x0010: "WM_CLOSE"                 ,# Сигнал о запросе на закрытие окна (например, нажали «крестик»)
    0x0012: "WM_QUIT"                  ,# Запрос на выгрузку цикла сообщений приложения (PostQuitMessage)
    0x0014: "WM_ERASEBKGND"            ,# Запрос на очистку/стерение фона окна
    0x001C: "WM_ACTIVATEAPP"           ,# Приложение активируется или деактивируется (переход на другое приложение)
    0x0020: "WM_SETCURSOR"             ,# Запрос на установку вида курсора мыши
    0x0046: "WM_WINDOWPOSCHANGING"     ,# Позиция или размер окна собираются измениться
    0x0047: "WM_WINDOWPOSCHANGED"      ,# Позиция или размер окна уже изменились
    0x007F: "WM_GETICON"               ,# Запрос на получение иконки окна
    0x0081: "WM_NCCREATE"              ,# Начало создания не клиентской области (рамки)
    0x0082: "WM_NCDESTROY"             ,# Завершение уничтожения окна
    0x0083: "WM_NCCALCSIZE"            ,# Расчёт размера клиентской области окна
    0x0084: "WM_NCHITTEST"             ,# Проверка, в какой части окна находится мышь
    0x0085: "WM_NCPAINT"               ,# Отрисовка не клиентской области (рамки/заголовка)
    0x0086: "WM_NCACTIVATE"            ,# Изменение визуального состояния заголовка (активный / неактивный)
    0x00A0: "WM_NCMOUSEMOVE"           ,# Движение мыши над рамкой окна
    0x00A1: "WM_NCLBUTTONDOWN"         ,# Нажата левая кнопка мыши над рамкой/заголовком
    0x00A2: "WM_NCLBUTTONUP"           ,# Отпущена левая кнопка мыши над рамкой/заголовком
    0x0100: "WM_KEYDOWN"               ,# Нажата клавиша
    0x0101: "WM_KEYUP"                 ,# Отпущена клавиша
    0x0102: "WM_CHAR"                  ,# Сгенерирован символ (ввод текста после трансляции TranslateMessage)
    0x0104: "WM_SYSKEYDOWN"            ,# Нажата системная клавиша (например, Alt или сочетание Alt + Key)
    0x0105: "WM_SYSKEYUP"              ,# Отпущена системная клавиша
    0x0111: "WM_COMMAND"               ,# Событие от элементов управления (кнопки, меню, акселераторы)
    0x0112: "WM_SYSCOMMAND"            ,# Системное командующее событие (сворачивание, разворачивание, закрытие из меню)
    0x0113: "WM_TIMER"                 ,# Сработал таймер (SetTimer)
    0x0200: "WM_MOUSEMOVE"             ,# Движение мыши внутри окна
    0x0201: "WM_LBUTTONDOWN"           ,# Нажата левая кнопка мыши
    0x0202: "WM_LBUTTONUP"             ,# Отпущена левая кнопка мыши
    0x0203: "WM_LBUTTONDBLCLK"         ,# Двойной клик левой кнопкой мыши
    0x0204: "WM_RBUTTONDOWN"           ,# Нажата правая кнопка мыши
    0x0205: "WM_RBUTTONUP"             ,# Отпущена правая кнопка мыши
    0x0206: "WM_RBUTTONDBLCLK"         ,# Двойной клик правой кнопкой мыши
    0x0207: "WM_MBUTTONDOWN"           ,# Нажата средняя кнопка мыши (колёсико)
    0x0208: "WM_MBUTTONUP"             ,# Отпущена средняя кнопка мыши
    0x020A: "WM_MOUSEWHEEL"            ,# Прокрутка колесика мыши
    0x020E: "WM_MOUSEHWHEEL"           ,# Прокрутка горизонтального колёсика мыши
    0x02A1: "WM_MOUSEHOVER"            ,# Курсор мыши задержался над окном на заданное время
    0x02A3: "WM_MOUSELEAVE"            ,# Курсор мыши покинул пределы клиентской области окна
    0x02E0: "WM_DPICHANGED"            ,# Изменился масштаб экрана (DPI) для окна
    0x031E: "WM_DWMCOMPOSITIONCHANGED" ,# Изменилось состояние режима Desktop Window Manager (Aero / стили оформления)
    0x0400: "WM_USER"                  ,# Базовое смещение для пользовательских (собственных) сообщений программы
}

e_expl_rev = {}
e_expl_rev.update(zip(e_expl.values(), e_expl.keys()))

e_types = Literal['WM_CREATE', 'WM_DESTROY', 'WM_MOVE', 'WM_SIZE', 'WM_ACTIVATE', 'WM_SETFOCUS', 'WM_KILLFOCUS', 'WM_ENABLE', 'WM_GETTEXT', 'WM_PAINT', 'WM_CLOSE', 'WM_QUIT', 'WM_ERASEBKGND', 'WM_ACTIVATEAPP', 'WM_SETCURSOR', 'WM_WINDOWPOSCHANGING', 'WM_WINDOWPOSCHANGED', 'WM_GETICON', 'WM_NCCREATE', 'WM_NCDESTROY', 'WM_NCCALCSIZE', 'WM_NCHITTEST', 'WM_NCPAINT', 'WM_NCACTIVATE', 'WM_NCMOUSEMOVE', 'WM_NCLBUTTONDOWN', 'WM_NCLBUTTONUP', 'WM_KEYDOWN', 'WM_KEYUP', 'WM_CHAR', 'WM_SYSKEYDOWN', 'WM_SYSKEYUP', 'WM_COMMAND', 'WM_SYSCOMMAND', 'WM_TIMER', 'WM_MOUSEMOVE', 'WM_LBUTTONDOWN', 'WM_LBUTTONUP', 'WM_LBUTTONDBLCLK', 'WM_RBUTTONDOWN', 'WM_RBUTTONUP', 'WM_RBUTTONDBLCLK', 'WM_MBUTTONDOWN', 'WM_MBUTTONUP', 'WM_MOUSEWHEEL', 'WM_MOUSEHWHEEL', 'WM_MOUSEHOVER', 'WM_MOUSELEAVE', 'WM_DPICHANGED', 'WM_DWMCOMPOSITIONCHANGED', 'WM_USER']


class EventHandler:
    def __init__(self):
        self.hooks = {}
        self.callbacks = defaultdict(list)

    def result(self, tp: e_types | int, fnc):
        if isinstance(tp, str):
            tp = e_expl_rev[tp]
        self.hooks[tp] = fnc

    def rd(self, tp: e_types | int):
        def decorator(fnc):
            self.result(tp, fnc)
            return fnc
        return decorator

    def hook(self, tp: e_types | int, fnc):
        if isinstance(tp, str):
            tp = e_expl_rev[tp]
        self.callbacks[tp].append(fnc)

    def hd(self, tp: e_types | int):
        def decorator(fnc):
            self.hook(tp, fnc)
            return fnc
        return decorator

    def process(self, ev: int, wp, lp):
        [i(wp, lp) for i in self.callbacks[ev]]
        if ev in self.hooks:
            return self.hooks[ev](wp, lp)
        return None


class Win32Window(AbstractWindow):
    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', frameless=False):
        super().__init__(width, height, title, frameless)
        self.handler = EventHandler()

        wndclass = WNDCLASSEXW()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wndclass.style = CS_OWNDC  # Обязательно CS_OWNDC для OpenGL!
        wndclass.lpfnWndProc = self._wnd_proc
        wndclass.lpszClassName = "Win32MoreSkiaClass"

        RegisterClassExW(ctypes.byref(wndclass))

        self.hwnd = CreateWindowExW(
            0,
            "Win32MoreSkiaClass",
            self._title,
            WS_OVERLAPPEDWINDOW,
            100, 100, self.width, self.height,
            None, None, None, None
        )

        self.hdc = GetDC(self.hwnd)
        self.create_event_handlers()

        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion = 1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER
        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = 32
        pfd.cDepthBits = 24
        pfd.cStencilBits = 8

        pixel_format = ChoosePixelFormat(self.hdc, ctypes.byref(pfd))
        SetPixelFormat(self.hdc, pixel_format, ctypes.byref(pfd))

        self._hglrc = wglCreateContext(self.hdc)
        wglMakeCurrent(self.hdc, self._hglrc)

        self.skia_context = skia.GrDirectContext.MakeGL()
        self._create_surface()

    def show(self):
        ShowWindow(self.hwnd, 5)

    def hide(self):
        ShowWindow(self.hwnd, 0)

    def _set_size(self, w, h):
        SetWindowPos(self.hwnd, 0, 0, 0, w, h, SWP_NOMOVE | SWP_NOACTIVATE | SWP_FRAMECHANGED)

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def set_title(self, title: str):
        SetWindowTextW(self.hwnd, title)

    def get_native_handle(self) -> int | None:
        return self.hwnd

    def swap_buffers(self):
        SwapBuffers(self.hdc)

    def get_canvas(self) -> skia.Canvas:
        return self.surface.getCanvas()

    def _destroy(self):
        DestroyWindow(self.hwnd)

    def pool(self):
        msg = MSG()
        msg_c = 0
        if not IsWindow(self.hwnd):
            raise RuntimeError('Window destroyed')
        while PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            if msg_c > 30:
                break
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))
            msg_c += 1

    def pool_forever(self):
        msg = MSG()
        while GetMessageW(ctypes.byref(msg), None, 0, 0):
            print(e_expl.get(msg.message, f'{msg.message:04x}'))
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))

    def create_event_handlers(self):
        hn = self.handler

        @hn.hd('WM_SIZE')
        @decode_cords
        def _update_size(w, h):
            print(f'size update: {w, h}')

        @hn.hd('WM_DESTROY')
        @drop_param
        def _cleanup():
            wglMakeCurrent(None, None)
            if self._hglrc:
                wglDeleteContext(self._hglrc)
            if self.hdc:
                ReleaseDC(self.hwnd, self.hdc)

    def _create_surface(self):
        width, height = self.get_size()
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

    def _wnd_proc(self, hwnd: HWND, msg: int, wparam: WPARAM, lparam: LPARAM):
        try:
            r = self.handler.process(msg, wparam, lparam)
            if r is not None:
                return r
        except Exception as _ex:
            _ex.add_note(f'Exception ignored while processing {msg:06x} for {hwnd}')
            traceback.print_exception(_ex)
        return DefWindowProcW(hwnd, msg, wparam, lparam)


if __name__ == '__main__':
    w = Win32Window()
    w.show()
    w.pool_forever()