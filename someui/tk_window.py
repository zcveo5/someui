from __future__ import annotations

import sys
import ctypes
import tkinter
import traceback

import skia

from win32more.Windows.Win32.Foundation import HWND, LPARAM, WPARAM, RECT
from win32more.Windows.Win32.UI.WindowsAndMessaging import (
    GetWindowLongPtrW,
    SetWindowLongPtrW,
    CallWindowProcW,
    PeekMessageW,
    TranslateMessage,
    DispatchMessageW,
    GWL_WNDPROC,
    WNDPROC,
    MSG,
    PM_REMOVE,
    WM_SIZE,
    WM_MOUSEMOVE,
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WM_RBUTTONDOWN,
    WM_RBUTTONUP, WM_PAINT, WM_ERASEBKGND,
)
from win32more.Windows.Win32.Graphics.Gdi import (
    SetDIBitsToDevice,
    BITMAPINFOHEADER,
    BI_RGB,
    DIB_RGB_COLORS,
    GetDC, ReleaseDC, BITMAPINFO, ValidateRect
)

from abstract import AbstractWindow
from widget_extensions import RRectWidget

import ctypes
from ctypes import c_ssize_t, c_uint

_CallWindowProcW_proto = ctypes.CFUNCTYPE(c_ssize_t, c_ssize_t, c_ssize_t, c_uint, c_ssize_t, c_ssize_t)
_call_window_proc = _CallWindowProcW_proto(
    ("CallWindowProcW", ctypes.windll.user32)
)


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


class TkinterWindow(AbstractWindow):
    def __init__(self, widget: tkinter.Widget):
        self.widget: tkinter.Widget = widget
        self.hwnd = HWND(widget.winfo_id())

        width = max(widget.winfo_width(), 1)
        height = max(widget.winfo_height(), 1)
        super().__init__(width, height)

        self._surface: skia.Surface | None = None
        self._recreate_surface(width, height)

        # Сохраняем указатель на оригинальный WndProc
        self._old_wndproc_ptr = GetWindowLongPtrW(self.hwnd, GWL_WNDPROC)

        # Создаем WNDPROC колбэк через win32more
        self._new_wndproc = WNDPROC(self._wnd_proc)

        # Кастуем функцию к int/ssize_t для передачи в SetWindowLongPtrW
        new_proc_addr = ctypes.cast(self._new_wndproc, ctypes.c_void_p).value
        SetWindowLongPtrW(self.hwnd, GWL_WNDPROC, new_proc_addr)

    def _recreate_surface(self, w: int, h: int):
        self._surface = skia.Surfaces(w, h)

    def _wnd_proc(self, hwnd: HWND, msg: int, wparam: WPARAM, lparam: LPARAM) -> int:
        try:
            lp_val = lparam if isinstance(lparam, int) else lparam.value
            wp_val = wparam if isinstance(wparam, int) else wparam.value
            h_val = hwnd if isinstance(hwnd, int) else hwnd.value

            #print(f'{e_expl.get(msg, f'{msg:04x}')}')
            if msg == WM_PAINT:
                self.update()
                ValidateRect(self.hwnd, None)
                return 0

            elif msg == WM_ERASEBKGND:
                return 1

            elif msg == WM_SIZE:
                print(lp_val, type(lp_val))

                w = lp_val & 0xFFFF
                h = (lp_val >> 16) & 0xFFFF
                if w > 0 and h > 0:
                    self._recreate_surface(w, h)
                    self.on_window_resize(w, h)

            elif msg == WM_MOUSEMOVE:
                x = lp_val & 0xFFFF
                y = (lp_val >> 16) & 0xFFFF
                self.dispatch_hover(x, y)

            elif msg in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                btn = 0 if msg == WM_LBUTTONDOWN else 1
                self.dispatch_click(btn, action=1, mods=0)

            elif msg in (WM_LBUTTONUP, WM_RBUTTONUP):
                btn = 0 if msg == WM_LBUTTONUP else 1
                self.dispatch_click(btn, action=0, mods=0)

        except Exception as e:
            e.add_note(f'WNDPROC for {self} ({self.widget})')
            traceback.print_exception(e)

        # Передаем целые числа (адрес старой WndProc, hwnd, msg, wparam, lparam)
        return _call_window_proc(self._old_wndproc_ptr, h_val, msg, wp_val, lp_val)

    # --- Реализация абстрактных методов AbstractWindow ---

    def show(self):
        pass

    def hide(self):
        pass

    def _set_size(self, w: int, h: int):
        pass

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def set_title(self, title: str):
        pass

    def get_native_handle(self) -> int | None:
        return self.hwnd.value if self.hwnd else None

    def get_canvas(self) -> skia.Canvas | None:
        return self._surface.getCanvas() if self._surface else None

    def swap_buffers(self):
        if not self._surface:
            return

        image = self._surface.makeImageSnapshot()
        pixel_bytes = image.tobytes()

        hdc = GetDC(self.hwnd)
        if not hdc:
            return

        try:
            # Создаем полную структуру BITMAPINFO
            bmi = BITMAPINFO()
            bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.bmiHeader.biWidth = self._width
            bmi.bmiHeader.biHeight = -self._height  # Y сверху вниз
            bmi.bmiHeader.biPlanes = 1
            bmi.bmiHeader.biBitCount = 32
            bmi.bmiHeader.biCompression = BI_RGB

            SetDIBitsToDevice(
                hdc,
                0, 0,
                self._width, self._height,
                0, 0,
                0, self._height,
                pixel_bytes,
                ctypes.byref(bmi),  # Теперь это корректный LP_BITMAPINFO
                DIB_RGB_COLORS
            )
        finally:
            ReleaseDC(self.hwnd, hdc)

    def pool(self):
        """Пумпим Win32 сообщения для всего потока (включая Tcl/Tk)"""
        msg = MSG()
        count = 0
        while count < 30 and PeekMessageW(ctypes.byref(msg), HWND(0), 0, 0, PM_REMOVE):
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))
            count += 1

    def _destroy(self):
        if self._old_wndproc_ptr:
            SetWindowLongPtrW(self.hwnd, GWL_WNDPROC, self._old_wndproc_ptr)
            self._old_wndproc_ptr = 0


if __name__ == '__main__':
    def inject():
        btn.configure(state='disabled')
        tk_wnd = TkinterWindow(frame)
        rrect = RRectWidget(tk_wnd)
        rrect.paint.color = '#ffffff'
        rrect.rel_place(0.1, 0.1, 0.9, 0.9)
        tk_wnd.update()

    root = tkinter.Tk()

    frame = tkinter.Frame(root)
    frame.place(relwidth=1, relheight=1, height=-20)

    btn = tkinter.Button(root, text='Inject', command=inject)
    btn.place(rely=1.0, y=-20)

    root.mainloop()