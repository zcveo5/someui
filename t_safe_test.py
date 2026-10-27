import queue
import threading
import time
from typing import Any


class Test:
    def __init__(self):
        self.thread = threading.current_thread()
        self.a = 0
        self.b = 1

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name != 'thread':
            if threading.current_thread() != self.thread:
                raise RuntimeError()
        super().__setattr__(name, value)

a = Test()


def thrd():
    global a
    a.a += 1


def check(f: FunctionType):
    pr


threading.Thread(target=thrd).start()



_wk = threading.Event()
_q = queue.Queue()

while True:
    while not _q.empty():
        fnc, args = _q.get()
        fnc(*args)
    _wk.wait()
