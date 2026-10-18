import time
import queue
import ctypes
import ctypes.util

# Загружаем необходимые фреймворки macOS
libobjc = ctypes.CDLL(ctypes.util.find_library('objc'))
libdispatch = ctypes.CDLL(ctypes.util.find_library('System'))

# Настройка типов для Objective-C runtime
libobjc.objc_getClass.restype = ctypes.c_void_p
libobjc.sel_registerName.restype = ctypes.c_void_p
libobjc.objc_msgSend.restype = ctypes.c_void_p


def sel(name):
    return libobjc.sel_registerName(name.encode('utf-8'))


def objc_msgSend(obj, selector, *args):
    # Универсальный вызов objc_msgSend в зависимости от аргументов
    # Для простоты демонстрации базовых вызовов
    fn = libobjc.objc_msgSend
    return fn(ctypes.c_void_p(obj), ctypes.c_void_p(selector), *args)


# Получаем классы Cocoa
NSApp_cls = libobjc.objc_getClass('NSApplication')
NSApplication_sharedApplication = sel('sharedApplication')
NSRunLoop_cls = libobjc.objc_getClass('NSRunLoop')
currentRunLoop_sel = sel('currentRunLoop')
runMode_beforeDate_sel = sel('runMode:beforeDate:')

CoreFoundation = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

try:
    NSDefaultRunLoopMode = ctypes.c_void_p.in_dll(CoreFoundation, 'kCFRunLoopDefaultMode')
except ValueError:
    # Запасной вариант через создание NSString если символ не поднялся напрямую
    ns_string_cls = libobjc.objc_getClass('NSString')
    utf8_string_sel = sel('stringWithUTF8String:')
    libobjc.objc_msgSend.restype = ctypes.c_void_p
    NSDefaultRunLoopMode = libobjc.objc_msgSend(ns_string_cls, utf8_string_sel, b'kCFRunLoopDefaultMode')
_call_queue = queue.Queue()
_call_at = []


def wakeup_mainloop():
    # Пробуждение NSRunLoop из любого потока с помощью отправки пустого события/асинхронного блока в главную очередь
    def dummy():
        pass

    call_threadsafe(dummy)


def call_at(fnc, time_stmp):
    _call_at.append((fnc, time_stmp))


def call_threadsafe(fnc, *args, **kwargs):
    _call_queue.put((fnc, args, kwargs))

    # Пробуждаем основной ранлуп через GCD (Grand Central Dispatch)
    # dispatch_async_f на главную очередь заставляет runloop проснуться
    @ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    def _dispatch_trampoline(_):
        # Эта функция выполнится в главном потоке внутри runloop
        pass


# Упрощенно через очередь диспетчеризации Main Queue:
libdispatch.dispatch_async_f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.CFUNCTYPE(None, ctypes.c_void_p)]
# Или через более простой механизм вызова главной очереди в Python:
# В macOS проще всего толкнуть runloop через отправку NSEvent или вызов wakeUp
NSApp = libobjc.objc_msgSend(NSApp_cls, NSApplication_sharedApplication)


# Посылаем фиктивное событие в очередь приложения для пробуждения
# (Альтернатива: NSApp postEvent:atStart:)

def mainloop(*windows):
    global _call_at

    for window in windows:
        window.update()

    # Получаем ссылку на sharedApplication и текущий RunLoop
    NSApp = libobjc.objc_msgSend(NSApp_cls, NSApplication_sharedApplication)
    loop = libobjc.objc_msgSend(NSRunLoop_cls, currentRunLoop_sel)

    while windows:
        # 1. Обработка потокобезопасной очереди
        while not _call_queue.empty():
            fnc, args, kwargs = _call_queue.get()
            fnc(*args, **kwargs)

        # 2. Обработка таймеров (call_at)
        now = time.time()
        stay = []
        min_after = 0.1  # Таймаут по умолчанию для итерации ранлупа (в секундах)

        for _call in _call_at:
            fnc, deadline = _call
            if deadline <= now:
                fnc()
            else:
                aft = deadline - now
                if aft < min_after:
                    min_after = aft
                stay.append((fnc, deadline))

        _call_at = stay

        # 3. Опрос окон и рендеринг
        for window in windows:
            window.pool()

            if window.children_rebuild:
                window.build_children()
                window.invalidate()
            if window.dirty:
                window.update()

        # Условие выхода, если все окна закрылись
        windows = [w for w in windows if w.is_running]
        if not windows:
            break

        # 4. Нативный шаг цикла macOS (замена MsgWaitForMultipleObjectsEx)
        # Вызываем runMode:beforeDate: для обработки одного события или истечения таймера min_after
        # NSDate *date = [NSDate dateWithTimeIntervalSinceNow:min_after];
        NSDate_cls = libobjc.objc_getClass('NSDate')
        dateWithTimeInterval_sel = sel('dateWithTimeIntervalSinceNow:')
        libobjc.objc_msgSend.restype = ctypes.c_void_p
        later_date = libobjc.objc_msgSend(NSDate_cls, dateWithTimeInterval_sel, ctypes.c_double(min_after))

        # [loop runMode:NSDefaultRunLoopMode beforeDate:later_date]
        libobjc.objc_msgSend.restype = ctypes.c_bool
        libobjc.objc_msgSend(
            loop,
            runMode_beforeDate_sel,
            NSDefaultRunLoopMode,
            later_date
        )