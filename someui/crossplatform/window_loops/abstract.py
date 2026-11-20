import abc
import sys


class AbstractWindowLoop(abc.ABC):
    def __init__(self):
        self.windows = []

    def run(self):
        self._run()

    @abc.abstractmethod
    def attach_callback(self, win):
        pass

    @abc.abstractmethod
    def deattach_callback(self, win):
        pass

    def attach(self, win):
        self.windows.append(win)
        win.on_ready(lambda: self.attach_callback(win))

    def deattach(self, win):
        self.windows.remove(win)
        self.deattach_callback(win)

    @abc.abstractmethod
    def _run(self):
        pass

    @abc.abstractmethod
    def call_at(self, fnc, ts):
        pass

    @abc.abstractmethod
    def call(self, fnc, *args, **kwargs):
        pass

    @abc.abstractmethod
    def wakeup(self):
        pass


NativeLoop: type[AbstractWindowLoop] | None = None


if sys.platform == 'win32':
    from someui.crossplatform.window_loops.win32 import Loop

    NativeLoop = Loop

elif sys.platform == 'darwin':
    from someui.crossplatform.window_loops.macos import Loop

    NativeLoop = Loop
else:
    raise NotImplementedError(f'No window loop for {sys.platform}')