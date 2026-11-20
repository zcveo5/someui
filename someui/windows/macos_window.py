# someui/macos_window.py
from __future__ import annotations

import ctypes
import time

import objc
import skia
from AppKit import (
    NSApplication, NSApplicationActivationPolicyRegular, NSBackingStoreBuffered,
    NSEventMaskAny, NSEventModifierFlagControl, NSEventModifierFlagOption,
    NSEventModifierFlagShift, NSMakeRect, NSView, NSWindow,
    NSWindowStyleMaskClosable, NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable, NSWindowStyleMaskTitled,
)
from Foundation import NSDate, NSDefaultRunLoopMode, NSObject, NSRunLoop
from Metal import (
    MTLCreateSystemDefaultDevice, MTLPixelFormatBGRA8Unorm, MTLRegionMake2D,
    MTLOriginMake, MTLSizeMake, MTLStorageModeShared, MTLTextureDescriptor,
    MTLTextureUsageShaderRead,
)
from Quartz import CAMetalLayer

from someui.crossplatform.headerless import get as get_headerless
from someui.abstract import AbstractWindow, _loop

_KEY_NAMES = {
    49: "SPACE", 36: "ENTER", 53: "ESCAPE", 51: "BACKSPACE", 48: "TAB",
    123: "LEFT", 124: "RIGHT", 125: "DOWN", 126: "UP",
    117: "DELETE", 115: "HOME", 119: "END", 116: "PAGE_UP", 121: "PAGE_DOWN",
}

_app_ready = False


def _ensure_app():
    global _app_ready
    if not _app_ready:
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        app.finishLaunching()
        _app_ready = True


class _MetalView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(_MetalView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.owner = None
        self.setWantsLayer_(True)
        self.setLayer_(CAMetalLayer.layer())
        return self

    def acceptsFirstResponder(self):
        return True

    def setFrameSize_(self, size):
        objc.super(_MetalView, self).setFrameSize_(size)
        if self.owner is not None:
            self.owner._on_view_resize()

    def viewDidChangeBackingProperties(self):
        if self.owner is not None:
            self.owner._on_view_resize()

    def mouseDown_(self, e):        self.owner._on_mouse(e, e.buttonNumber(), 1)
    def mouseUp_(self, e):          self.owner._on_mouse(e, e.buttonNumber(), 0)
    def rightMouseDown_(self, e):   self.owner._on_mouse(e, e.buttonNumber(), 1)
    def rightMouseUp_(self, e):     self.owner._on_mouse(e, e.buttonNumber(), 0)
    def otherMouseDown_(self, e):   self.owner._on_mouse(e, e.buttonNumber(), 1)
    def otherMouseUp_(self, e):     self.owner._on_mouse(e, e.buttonNumber(), 0)

    def mouseMoved_(self, e):          self.owner._on_hover(e)
    def mouseDragged_(self, e):        self.owner._on_hover(e)
    def rightMouseDragged_(self, e):   self.owner._on_hover(e)
    def otherMouseDragged_(self, e):   self.owner._on_hover(e)

    def scrollWheel_(self, e):
        self.owner._on_scroll(e)

    def keyDown_(self, e):
        self.owner._on_key(e, pressed=True)

    def keyUp_(self, e):
        self.owner._on_key(e, pressed=False)


class _WindowDelegate(NSObject):
    def windowWillClose_(self, notification):
        self.owner.is_running = False


class MacWindow(AbstractWindow):
    """Нативное окно macOS: NSWindow + CAMetalLayer. Skia рисует на CPU,
    результат копируется в Metal-текстуру и выводится через blit.
    Рендер выполняется в главном потоке из pool_native()."""

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui', headerless=False):
        super().__init__(width, height, title, headerless)
        _ensure_app()

        self._layer = None
        self._surface = None
        self._tex = None
        self._tex_size = None
        self._last_frame = time.time()
        self.surface_props = skia.SurfaceProps(
            skia.SurfaceProps.kUseDeviceIndependentFonts_Flag,
            skia.PixelGeometry.kRGB_H_PixelGeometry,
        )

        rect = NSMakeRect(200, 200, width, height)
        style = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
                 | NSWindowStyleMaskResizable | NSWindowStyleMaskMiniaturizable)
        self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False)
        self._window.setTitle_(title)
        self._window.setReleasedWhenClosed_(False)
        self._window.setAcceptsMouseMovedEvents_(True)

        self._view = _MetalView.alloc().initWithFrame_(rect)
        self._view.owner = self
        self._window.setContentView_(self._view)
        self._window.makeFirstResponder_(self._view)

        self._delegate = _WindowDelegate.alloc().init()
        self._delegate.owner = self
        self._window.setDelegate_(self._delegate)

        self._setup_metal()

        self.__post_init__()
        self.show()

    # ---- инициализация -----------------------------------------------------

    def _setup_metal(self):
        self._device = MTLCreateSystemDefaultDevice()
        self._queue = self._device.newCommandQueue()

        self._layer = self._view.layer()
        self._layer.setDevice_(self._device)
        self._layer.setPixelFormat_(MTLPixelFormatBGRA8Unorm)
        self._layer.setFramebufferOnly_(False)     # нужно для blit в drawable
        self._layer.setDisplaySyncEnabled_(True)   # vsync
        self._layer.setMaximumDrawableCount_(2)

        self._update_scale()
        self._on_view_resize()

    def __post_init__(self):
        # AbstractWindow.__post_init__ стартует отдельный поток; на macOS его не нужно
        _inst = get_headerless()
        self.headerless_helper = None
        if _inst is not None:
            self.headerless_helper = _inst(self)
            if self._headerless:
                self.headerless_helper.enable()

        self.on_ready.process()

    def _ensure_texture(self, w, h):
        if self._tex is not None and self._tex_size == (w, h):
            return self._tex
        desc = MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(
            MTLPixelFormatBGRA8Unorm, w, h, False)
        desc.setUsage_(MTLTextureUsageShaderRead)
        desc.setStorageMode_(MTLStorageModeShared)
        self._tex = self._device.newTextureWithDescriptor_(desc)
        self._tex_size = (w, h)
        return self._tex

    # ---- масштаб и размер --------------------------------------------------

    def _update_scale(self):
        s = float(self._window.backingScaleFactor())
        self.scale_x = self.scale_y = s
        self._layer.setContentsScale_(s)

    def _on_view_resize(self):
        if self._layer is None:
            return
        self._update_scale()
        size = self._view.bounds().size
        s = self.scale_x
        self._width, self._height = int(size.width), int(size.height)
        self._layer.setDrawableSize_((size.width * s, size.height * s))
        self.on_resize.process(self._width, self._height)
        self.invalidate_place()
        self._draw()   # рисуем сразу, пока Cocoa в live resize

    # ---- события -----------------------------------------------------------

    def _view_point(self, e):
        p = self._view.convertPoint_fromView_(e.locationInWindow(), None)
        return float(p.x), float(self._view.bounds().size.height - p.y)

    def _on_mouse(self, e, button, action):
        self.mouse_x, self.mouse_y = self._view_point(e)
        self.dispatch_click(button, action, 0)

    def _on_hover(self, e):
        x, y = self._view_point(e)
        self.dispatch_hover(x, y)

    def _on_scroll(self, e):
        self.mouse_x, self.mouse_y = self._view_point(e)
        self.dispatch_scroll(e.scrollingDeltaX(), e.scrollingDeltaY())

    def _on_key(self, e, pressed: bool):
        mods = e.modifierFlags()
        shift = bool(mods & NSEventModifierFlagShift)
        ctrl = bool(mods & NSEventModifierFlagControl)
        alt = bool(mods & NSEventModifierFlagOption)

        code = e.keyCode()
        key = _KEY_NAMES.get(code) or (e.charactersIgnoringModifiers() or '').upper() or f'UNKNOWN_{code}'

        if pressed:
            if not e.isARepeat():
                self.on_keyboard_press.process(key, shift, ctrl, alt)
            self.on_keyboard_write.process(key, shift, ctrl, alt)
        else:
            self.on_keyboard_release.process(key, shift, ctrl, alt)

    # ---- рисование ---------------------------------------------------------

    def _draw(self):
        if self._layer is None:
            return

        drawable = self._layer.nextDrawable()
        if drawable is None:
            return

        size = self._layer.drawableSize()
        w, h = int(size.width), int(size.height)
        if w <= 0 or h <= 0:
            return

        now = time.time()
        dt, self._last_frame = now - self._last_frame, now

        # 1. Skia рисует на CPU
        info = skia.ImageInfo.Make(w, h, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType)
        surface = skia.Surface.MakeRaster(info)
        self._surface = surface
        try:
            self.on_animation_frame.process(dt)
            self.render(surface.getCanvas())
        finally:
            self._surface = None

        # 2. Копируем пиксели в Metal-текстуру
        data = surface.makeImageSnapshot().tobytes()
        stride = w * 4
        tex = self._ensure_texture(w, h)
        tex.replaceRegion_mipmapLevel_withBytes_bytesPerRow_(
            MTLRegionMake2D(0, 0, w, h), 0, data, stride)

        # 3. Blit в drawable и показ
        cmd = self._queue.commandBuffer()
        blit = cmd.blitCommandEncoder()
        blit.copyFromTexture_sourceSlice_sourceLevel_sourceOrigin_sourceSize_toTexture_destinationSlice_destinationLevel_destinationOrigin_(
            tex, 0, 0, MTLOriginMake(0, 0, 0), MTLSizeMake(w, h, 1),
            drawable.texture(), 0, 0, MTLOriginMake(0, 0, 0))
        blit.endEncoding()
        cmd.presentDrawable_(drawable)
        cmd.commit()

    # ---- AbstractWindow ----------------------------------------------------

    @property
    def win32_handle(self) -> int:
        raise NotImplementedError()

    @property
    def macos_handle(self):
        return self._window.pyobjc_id()

    def _render_thread(self):
        pass  # не используется

    @property
    def is_maximized(self) -> bool:
        return bool(self._window.isZoomed())

    @is_maximized.setter
    def is_maximized(self, value):
        if bool(self._window.isZoomed()) != bool(value):
            self._window.zoom_(None)

    def show(self):
        self._window.makeKeyAndOrderFront_(None)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    def hide(self):
        self._window.miniaturize_(None)

    def _set_size(self, w, h):
        self._window.setContentSize_((w, h))

    def get_size(self) -> tuple[int, int]:
        size = self._view.bounds().size
        return int(size.width), int(size.height)

    def set_title(self, title: str):
        self._window.setTitle_(title)

    def swap_buffers(self):
        pass  # presentDrawable уже в _draw()

    def get_canvas(self):
        return self._surface.getCanvas() if self._surface is not None else None

    def get_surface(self):
        return self._surface

    def pool_native(self):
        app = NSApplication.sharedApplication()
        while True:
            ev = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                NSEventMaskAny, NSDate.distantPast(), NSDefaultRunLoopMode, True)
            if ev is None:
                break
            app.sendEvent_(ev)

        NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
        self._draw()

    def destroy_window(self):
        self._window.close()

    def destroy(self):
        self.is_running = False
        self.destroy_window()
        if self in self.windows:
            self.windows.remove(self)
        if self in _loop.windows:
            _loop.deattach(self)
        _loop.wakeup()