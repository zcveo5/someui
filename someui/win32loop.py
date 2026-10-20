import time

from win32more.Windows.Win32.Media import timeBeginPeriod, timeEndPeriod
from win32more.Windows.Win32.System.Threading import CreateEventW, SetEvent, ResetEvent
from win32more.Windows.Win32.UI.WindowsAndMessaging import MsgWaitForMultipleObjectsEx, QS_ALLINPUT, \
    MWMO_INPUTAVAILABLE, MWMO_ALERTABLE
from win32more.Windows.Win32.Foundation import CloseHandle
import ctypes
import queue

_wake_up_event = ctypes.c_void_p(CreateEventW(None, True, False, 'UiWakeUp'))
_call_queue = queue.Queue()
_call_at = []
_event_state = False

def wakeup_mainloop():
    global _event_state
    if not _event_state:
        SetEvent(_wake_up_event)
        _event_state = True

def _reset_event():
    global _event_state
    if _event_state:
        ResetEvent(_wake_up_event)
        _event_state = False


def call_at(fnc, time_stmp):
    _call_at.append((fnc, time_stmp))


def call_threadsafe(fnc, *args, **kwargs):
    _call_queue.put((fnc, args, kwargs))
    wakeup_mainloop()


def mainloop(windows):
    global _call_at

    for window in windows:
        window.update()

    try:
        timeBeginPeriod(1)

        while windows:

            while not _call_queue.empty():
                fnc, args, kwargs = _call_queue.get()
                fnc(*args, **kwargs)

            now = time.time()
            stay = []
            min_after = 0xffffffff

            for _call in _call_at:
                fnc, deadline = _call
                if deadline <= now:
                    fnc()
                else:
                    aft = deadline - now
                    if aft < min_after:
                        min_after = aft * 1000 # Milliseconds

                    stay.append((fnc, deadline))

            _call_at = stay

            for window in windows:
                window.pool()

                if window.children_rebuild:
                    window.build_children()
                    window.invalidate()
                if window.dirty:
                    window.update()

            if _call_queue.empty() and not any(w.dirty for w in windows):
                _reset_event()

            if min_after > 0 and windows:
                MsgWaitForMultipleObjectsEx(1,
                                            _wake_up_event,
                                            int(min_after),
                                            QS_ALLINPUT,
                                            MWMO_INPUTAVAILABLE | MWMO_ALERTABLE)
    finally:
        timeEndPeriod(1)
        CloseHandle(_wake_up_event)