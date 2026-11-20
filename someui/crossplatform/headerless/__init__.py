import abc
import platform

system = platform.system()


class AbstractProtocol(abc.ABC):
    def __init__(self, window):
        self.window = window

    @property
    @abc.abstractmethod
    def on_header(self) -> bool: ...

    @on_header.setter
    @abc.abstractmethod
    def on_header(self, value) -> bool: ...

    @property
    @abc.abstractmethod
    def on_sysmenu(self) -> bool: ...

    @on_sysmenu.setter
    @abc.abstractmethod
    def on_sysmenu(self, value) -> bool: ...

    @abc.abstractmethod
    def enable(self): ...

    @abc.abstractmethod
    def disable(self): ...

    @abc.abstractmethod
    def debug(self) -> str: ...

    @abc.abstractmethod
    def set_maxi_rect(self, l, t, r, b): ...

def get_win32():
    from . import win32
    return win32.Window


def get() -> type[AbstractProtocol] | None:
    if system == 'Windows':
        return get_win32()
    else:
        return None



