import abc
import sys


class AbstractWindowLoop(abc.ABC):
    def __init__(self, windows: list):
        self.windows = windows

    def run(self):
        self._run()

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