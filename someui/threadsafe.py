import asyncio
import inspect
import queue
import threading
import typing

from someui.abstract import get_loop

lp = get_loop()

def recaller(method, *args, **kwargs):
    lp.call(method, *args, **kwargs)


def ui_thread(fnc):
    def wrapper():
        fnc(recaller)

    thread = threading.Thread(target=wrapper)
    return thread


def async_ui_thread(coro):
    wakeup_function = None
    call_queue = queue.Queue()

    def submit(fnc, *args):
        call_queue.put((fnc, args))
        if wakeup_function is not None:
            wakeup_function()

    def submit_wrapper(fnc):
        def wrapper(*args):
            submit(fnc, *args)
        return wrapper

    async def _threadloop():
        nonlocal wakeup_function
        loop = asyncio.get_running_loop()

        # Запускаем основную корутину в цикле
        asyncio.create_task(coro(recaller, submit_wrapper))

        while True:
            wakeup_future = loop.create_future()
            wakeup_function = lambda: loop.call_soon_threadsafe(wakeup_future.set_result, True)

            # Ждем пробуждения из другого потока
            await wakeup_future

            # Обрабатываем все накопленные в очереди задачи
            while not call_queue.empty():
                try:
                    fnc, args = call_queue.get_nowait()
                except queue.Empty:
                    break

                if asyncio.iscoroutine(fnc):
                    asyncio.create_task(fnc)
                elif inspect.iscoroutinefunction(fnc):
                    asyncio.create_task(fnc(*args))
                else:
                    fnc(*args)

    def _run_thread():
        asyncio.run(_threadloop())

    # Создаем и запускаем поток с циклом событий
    thread = threading.Thread(target=_run_thread, daemon=True)
    thread.start()

    # Функция для безопасного вызова из любых других потоков

    return submit


def iter_obj(obj):
    for i in dir(obj):
        attr = getattr(obj, i)
        yield i, attr


def wrap_method(method):
    def wrapper(*args):
        recaller(method, *args)
    return wrapper


class ThreadsafeWidget:
    def __init__(self, obj):
        self._do_not_wrap = []
        self._o = obj
        for attr_name, attr in iter_obj(obj):
            if callable(attr) and not attr_name.startswith('_'):
                setattr(self, attr_name, wrap_method(attr))
            elif not attr_name.startswith('_'):
                self._do_not_wrap.append(attr_name)

    def __getattr__(self, item):
        if item in self._do_not_wrap:
            return getattr(self._o, item)
        else:
            raise AttributeError(f'No {item} in wrapper, available only public methods and fields')


def widget(wdg) -> typing.Any:
    return ThreadsafeWidget(wdg)

