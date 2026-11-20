import ctypes
import heapq
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable

from someui.crossplatform.window_loops.abstract import AbstractWindowLoop

_WBEventCallback = ctypes.CFUNCTYPE(None, ctypes.c_void_p)


def _load_bridge(dylib_path: Path | None = None) -> ctypes.CDLL:
    path = dylib_path or Path(__file__).with_name("libwindow_bridge.dylib")
    lib = ctypes.CDLL(str(path))

    lib.wb_loop_create.argtypes = []
    lib.wb_loop_create.restype = ctypes.c_void_p

    lib.wb_loop_step.argtypes = [ctypes.c_void_p, ctypes.c_double]
    lib.wb_loop_step.restype = None

    lib.wb_loop_wakeup.argtypes = [ctypes.c_void_p]
    lib.wb_loop_wakeup.restype = None

    lib.wb_loop_destroy.argtypes = [ctypes.c_void_p]
    lib.wb_loop_destroy.restype = None

    lib.wb_attach_window.argtypes = [
        ctypes.c_void_p,
        _WBEventCallback,
        ctypes.c_void_p,
    ]
    lib.wb_attach_window.restype = ctypes.c_void_p

    lib.wb_detach_window.argtypes = [ctypes.c_void_p]
    lib.wb_detach_window.restype = None

    return lib


class Loop(AbstractWindowLoop):
    def __init__(self, dylib_path: Path | None = None) -> None:
        super().__init__()
        self._lib = _load_bridge(dylib_path)
        self._ctx: int | None = None
        self._calls: queue.SimpleQueue[
            tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]
        ] = queue.SimpleQueue()
        self._timers: list[tuple[float, int, Callable[[], Any]]] = []
        self._seq: int = 0
        self._wake_event = threading.Event()
        self._observers: dict[int, int] = {}
        self._event_cb = _WBEventCallback(self._on_native_event)

    def _on_native_event(self, _user_data: int) -> None:
        self.wakeup()

    def attach_callback(self, win: Any) -> None:
        ptr = getattr(win, "macos_handle", None)
        if not ptr or ptr in self._observers:
            return
        print(ptr)
        obs_ptr = self._lib.wb_attach_window(
            ctypes.c_void_p(ptr),
            self._event_cb,
            None,
        )
        if obs_ptr:
            self._observers[ptr] = obs_ptr

    def deattach_callback(self, win: Any) -> None:
        ptr = getattr(win, "macos_handle", None)
        if not ptr:
            return
        obs_ptr = self._observers.pop(ptr, None)
        if obs_ptr:
            self._lib.wb_detach_window(ctypes.c_void_p(obs_ptr))

    def wakeup(self) -> None:
        self._wake_event.set()
        if self._ctx:
            self._lib.wb_loop_wakeup(ctypes.c_void_p(self._ctx))

    def call(self, fnc: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self._calls.put((fnc, args, kwargs))
        self.wakeup()

    def call_at(self, fnc: Callable[[], Any], ts: float) -> None:
        self._seq += 1
        heapq.heappush(self._timers, (float(ts), self._seq, fnc))
        self.wakeup()

    def _drain_calls(self) -> None:
        self._wake_event.clear()
        while True:
            try:
                fnc, args, kwargs = self._calls.get_nowait()
            except queue.Empty:
                break
            fnc(*args, **kwargs)

    def _drain_timers(self, now: float) -> float:
        default_timeout = 0.016
        while self._timers and self._timers[0][0] <= now:
            _, _, fnc = heapq.heappop(self._timers)
            fnc()

        if not self._timers:
            return default_timeout

        return max(0.0, min(default_timeout, self._timers[0][0] - now))

    def _run(self) -> None:
        if not self.windows:
            return

        ctx = self._lib.wb_loop_create()
        if not ctx:
            return
        self._ctx = ctx

        try:
            for win in list(self.windows):
                self.attach_callback(win)
                win.update()

            while self.windows:
                self._drain_calls()
                timeout = self._drain_timers(time.monotonic())

                for win in list(self.windows):
                    win.pool()

                alive = []
                for win in self.windows:
                    if win.is_running:
                        alive.append(win)
                    else:
                        self.deattach_callback(win)
                self.windows = alive

                if not self.windows:
                    break

                if self._wake_event.is_set():
                    continue

                self._lib.wb_loop_step(
                    ctypes.c_void_p(self._ctx),
                    ctypes.c_double(timeout),
                )
        finally:
            for obs_ptr in self._observers.values():
                self._lib.wb_detach_window(ctypes.c_void_p(obs_ptr))
            self._observers.clear()
            self._lib.wb_loop_destroy(ctypes.c_void_p(self._ctx))
            self._ctx = None