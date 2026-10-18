import abc
import sys


class AbstractWindowLoop(abc.ABC):
    def __init__(self, windows: list):
        self.windows = windows

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def call_at(self, fnc, ts):
        pass

    @abc.abstractmethod
    def wakeup(self):
        pass

NativeLoop: AbstractWindowLoop | None = None


if sys.platform == 'win32':
    from someui.win32loop import mainloop, wakeup_mainloop, call_at

    class _W32Loop(AbstractWindowLoop):
        def run(self):
            mainloop(*self.windows)

        def call_at(self, fnc, ts):
            call_at(fnc, ts)

        def wakeup(self):
            wakeup_mainloop()

    NativeLoop = _W32Loop

elif sys.platform == 'darwin':
    from someui.mac_os_loop import mainloop, wakeup_mainloop, call_at

    class _MacLoop(AbstractWindowLoop):
        def run(self):
            mainloop(*self.windows)

        def call_at(self, fnc, ts):
            call_at(fnc, ts)

        def wakeup(self):
            wakeup_mainloop()

    NativeLoop = _MacLoop
else:
    raise NotImplementedError(f'No window loop for {sys.platform}')