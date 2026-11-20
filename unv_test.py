import asyncio
import os
import threading
from pathlib import Path

import skia
import time

import someui
from someui import PlacingConfig, PlacementValue, defaults, smooth_damp
from someui.threadsafe import async_ui_thread, widget

IMG_DIR = Path(r'C:\Users\zcveo\Pictures')

async def loop(recall, dec):
    c = 0
    lbl: someui.Label = widget(tick)
    while True:
        c += 1#
        lbl.set_text(f'Second: {c}')
        await asyncio.sleep(1)


def get_skia_image_size(_img: skia.Image) -> str:
    width = _img.width()
    height = _img.height()

    # Определяем сколько байт весит 1 пиксель по цветовому формату (ColorType)
    color_type = _img.colorType()

    # Словарь соответствия форматов Skia и размера в байтах
    # (актуальные константы skia.ColorType)
    bytes_per_pixel = 4  # По умолчанию для N32 / RGBA_8888

    if color_type == skia.ColorType.kRGB_565_ColorType:
        bytes_per_pixel = 2
    elif color_type == skia.ColorType.kAlpha_8_ColorType:
        bytes_per_pixel = 1
    elif color_type in (skia.ColorType.kRGBA_8888_ColorType,
                        skia.ColorType.kBGRA_8888_ColorType):
        bytes_per_pixel = 4
    elif color_type == skia.ColorType.kRGBA_F16_ColorType:
        bytes_per_pixel = 8  # 16-битные флоаты на канал (4 канала * 2 байта)

    # Альтернативный и самый надежный способ через rowBytes() * height:
    # rowBytes() уже учитывает ширину строки с учетом выравнивания (stride/alignment)
    total_bytes = width * height * bytes_per_pixel

    # Красивое форматирование в КБ / МБ / ГБ
    units = ['Б', 'КБ', 'МБ', 'ГБ']
    size = float(total_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


class Image(someui.Label):
    def __init__(self, parent, fp=None):
        self.debug_img = True
        super().__init__(parent)
        if fp:
            self._image: skia.Image | None = skia.Image.open(fp)
            self.set_text(f'Image {self._image.width()}x{self._image.height()} Weight {get_skia_image_size(self._image)}')
        else:
            self.set_text('No image')
            self._image = None
        self.set_align('left', 'bottom')
        self._exc = None
        self._text_paint.setBlendMode(skia.BlendMode.kDifference)

    def set_image(self, fp):
        try:
            self._image = skia.Image.open(f'{fp}')
            self.set_text(f'Image {self._image.width()}x{self._image.height()} Weight {get_skia_image_size(self._image)}')
        except Exception as _ex:
            self.set_text(f'{_ex.__class__.__name__}: {_ex}')
            self._image = None

    def draw_self(self, ctx: skia.Canvas):
        if self._image:
            ctx.drawImageRect(self._image, skia.Rect(0, 0, self.width, self.height))
        if self.debug_img or not self._image:
            super().draw_self(ctx)


class Selector(someui.Label):
    def __init__(self, parent, items, selected_callback, font='Inter', font_size=14):
        super().__init__(parent, font=font, font_size=font_size, background_color='#888')
        self._items = items
        self.selected_callback = selected_callback
        self._items_bmp = None
        self._surface: skia.Surfaces | None = None
        self._items_click_zones = []
        self.on_resize(self._create_surface)
        self.on_mouse_press(self._proc_click)
        self.on_hover(self._proc_hover)
        self.state = ''
        self.on_scroll(self._v_scroll)
        self.scroll_enabled = True
        self.ch = 0
        self.cw = 0
        self._target_scroll_y = 0.0
        self._vel_y = 0.0
        self._loop_running = False
        self._last_t = 0.0
        self.selected = None

        # Переменные для плавной анимации прямоугольника выбора
        self._has_selection = False
        self._target_rect = None
        self._curr_rect = [0.0, 0.0, 0.0, 0.0]
        self._vel_rect = [0.0, 0.0, 0.0, 0.0]

        self._target_alpha = 0.0
        self._curr_alpha = 0.0
        self._vel_alpha = 0.0

        self.selected_paint = skia.Paint(0x550000ff)

    def _clamp_y(self, value):
        return max(0, min(value, self.ch - self.height))

    def _loop(self, dt):
        # Плавная прокрутка
        self.scroll_y, self._vel_y = smooth_damp(
            self.scroll_y, self._target_scroll_y, self._vel_y, 0.12, dt)

        self._proc_hover(self.window.mouse_x, self.window.mouse_y)

        # Плавная анимация прозрачности (время затухания ~0.04-0.06 дает быстрый эффект за ~20-40мс)
        self._curr_alpha, self._vel_alpha = smooth_damp(
            self._curr_alpha, self._target_alpha, self._vel_alpha, 0.05, dt)

        # Плавная анимация прямоугольника выделения
        rect_moving = False
        if self._target_rect:
            for i in range(4):
                self._curr_rect[i], self._vel_rect[i] = smooth_damp(
                    self._curr_rect[i], self._target_rect[i], self._vel_rect[i], 0.08, dt)
                if abs(self._target_rect[i] - self._curr_rect[i]) > 0.1 or abs(self._vel_rect[i]) > 0.1:
                    rect_moving = True

        scroll_moving = (abs(self._target_scroll_y - self.scroll_y) > 0.5 or abs(self._vel_y) > 0.5)
        alpha_moving = (abs(self._target_alpha - self._curr_alpha) > 0.5 or abs(self._vel_alpha) > 0.5)

        # Если всё доехало и альфа полностью упала (затухло) — отключаем анимационный цикл
        if not scroll_moving and not rect_moving and not alpha_moving:
            if self._target_alpha <= 0.1:
                self._has_selection = False
            self.scroll_y = self._target_scroll_y
            self._vel_y = 0.0
            self._loop_running = False
            self.window.on_animation_frame.remove(self._loop)

    def _v_scroll(self, delta, x, y):
        self._target_scroll_y = self._clamp_y(self._target_scroll_y - delta)

        if not self._loop_running:
            self._loop_running = True
            self.window.on_animation_frame(self._loop)

    def _proc_hover(self, x, y):
        x, y = self.cord_to_local(x, y)
        y += self.scroll_y
        found = False
        for rect, item in self._items_click_zones:
            if rect.contains(x, y):
                self.selected = item
                new_target = (rect.left(), rect.top(), rect.right(), rect.bottom())

                # Если до этого ховера не было, мгновенно инициализируем позицию, чтобы рамка не летела из угла (0,0)
                if not self._has_selection:
                    self._curr_rect = list(new_target)
                    self._vel_rect = [0.0, 0.0, 0.0, 0.0]

                self._target_rect = new_target
                self._has_selection = True
                self._target_alpha = 85
                found = True
                break

        if not found:
            self.selected = None
            self._target_alpha = 0

        if not self._loop_running:
            self._loop_running = True
            self.window.on_animation_frame(self._loop)

    def _proc_click(self, button, x, y):
        if self.selected and button == 0:
            if self.selected_callback:
                self.selected_callback(self.selected)

    def _create_surface(self, w, h):
        self._surface = skia.Surface.MakeRaster(
            skia.ImageInfo.MakeN32Premul(int(self.cw if self.cw > 0 else w), int(self.ch if self.ch > 0 else h)))

    @property
    def items(self):
        return self._items

    def set_items(self, items):
        self._items = items
        self._items_bmp = None

    def _ensure_items(self):
        if self._items_bmp is None:
            if self._surface is None:
                return
            canvas: skia.Canvas = self._surface.getCanvas()
            canvas.clear(0x0)
            y = 0
            cw = 0
            for c, item in enumerate(self._items):
                blob = skia.TextBlob(item, self._font)
                bounds = blob.bounds()
                w, h = bounds.width(), bounds.height()
                r = skia.Rect(5, y, 5 + w, y + h)
                canvas.drawRoundRect(r, 5, 5, self._text_paint)
                self._items_click_zones.append([r, item])
                canvas.drawTextBlob(blob, 5, y + h / 2, self._bg_paint)
                y += h + 5
                self.state = f'rendering {c} / {len(self._items)}'
                if w > cw:
                    cw = w
            self.cw = cw
            if self.ch == 0:
                self.ch = y
                return
            self._items_bmp = self._surface.makeImageSnapshot()
            self.ch = y

    def get_size_hint(self):
        return self.cw, self.ch

    def draw_self(self, ctx: skia.Canvas):
        rect = skia.Rect(0, 0, self.width, self.height)
        r = skia.RRect(rect, 5, 5)
        ctx.drawRRect(r, self._bg_paint)
        if self._items_bmp is not None:
            ctx.save()
            ctx.translate(0, -self.scroll_y)
            ctx.drawImage(self._items_bmp, 0, 0)

            if self._has_selection and self._curr_alpha > 0.5:
                anim_rect = skia.Rect(*self._curr_rect)
                # Динамически меняем прозрачность кисти Skia в зависимости от текущей анимации
                self.selected_paint.setAlpha(int(max(0, min(255, self._curr_alpha))))
                ctx.drawRoundRect(anim_rect, 5, 5, self.selected_paint)

            ctx.restore()
        else:
            blob = skia.TextBlob(f'No items_bmp | {self.state} | {self._surface}', defaults.DEBUG_FONT)
            bounds = blob.bounds()
            w, h = bounds.width(), bounds.height()
            ctx.drawTextBlob(blob, self.width / 2 - w / 2, self.height / 2, defaults.DEBUG_BLACK)
            root.call_after(self._ensure_items, 0)



class SelectorViewPort(someui.Label):
    def __init__(self, parent, items, selected_callback, font: str = 'Inter', font_size: float = 14,
                 typeface: skia.Typeface | None = None, text_color: str = 'white',
                 background_color: str = None):
        super().__init__(parent, '', font, font_size, typeface, text_color, background_color)
        self.selected_callback = selected_callback
        self.items = items
        self.stack: list[someui.Button] = []
        self.scroll_enabled = True
        self.ch = 0
        self.mcfg.gap = 5
        self.mcfg.margins = someui.Margins(top=5)
        self.on_resize(self._resize)

    def _select(self, item):
        return lambda: self.selected_callback(item)

    def _clamp_y(self, value):
        return max(0, min(value, self.ch - self.height))

    def _v_scroll(self, delta, x, y):
        self.scroll_y = self._clamp_y(self.scroll_y - delta)

    def _resize(self, w, h):
        [b.destroy() for b in self.stack]
        buttons = h // 40
        for item in range(buttons):
            btn = someui.Button(self, text=f'{item}')
            btn.place(x=5, y='auto', height=35, relative_width=1)

    def draw_self(self, ctx: skia.Canvas):
        ctx.save()
        ctx.translate(0, self.scroll_y)
        ctx.restore()



root = someui.GLFWWindow(width=1000)
#Cursor(root)

right_panel = someui.Container(root, '#888')
right_panel.place(PlacingConfig(x=PlacementValue.relative(0.75), width=PlacementValue.relative(0.25),
                                height=PlacementValue.relative(1)))

main_panel = someui.Container(root)
main_panel.place(PlacingConfig(width=PlacementValue.relative(0.75), height=PlacementValue.relative(1)))

img = Image(main_panel)
img.place(relative_width=1, relative_height=1)

settings_panel = someui.Container(root, '#888c', blur_sigma=None)

def close_settings():
    settings_panel.enabled = False

title = someui.Label(settings_panel, 'Settings', font_size=20)
title.set_align('center', 'center')
title.place(someui.PlacingConfig(width=PlacementValue.relative(1.0)))
close = someui.Button(settings_panel, 'X', close_settings)
close.set_size(*close.get_size_hint())
close.place(relative_x=0.95, relative_y=0, y=0)

settings_panel.z = right_panel.z + 2
settings_panel.enabled = False
settings_panel.place(PlacingConfig(x=PlacementValue.relative(0.20), width=PlacementValue.relative(0.6),
                                   y=PlacementValue.relative(0.05), height=PlacementValue.relative(0.9)))
settings_panel.scroll_enabled = False

tick = someui.Label(settings_panel, 'No text')
tick.place()

def open_settings():
    settings_panel.enabled = True

settings_btn = someui.Button(right_panel, 'Settings', open_settings)
settings_btn.place(PlacingConfig(width=PlacementValue.relative(1)))

def create_select_callback(path):
    if path not in imgs_ignore:
        img.set_image(f'{IMG_DIR}{path}')
    else:
        img.set_image(path)

imgs = ['./numpy_static.png']
imgs_ignore = ['./numpy_static.png']

for root_path, folders, files in IMG_DIR.walk():
    for i in files:
        i = root_path / i
        ext = i.name.split('.')[-1]
        if ext not in ['png', 'jpg', 'jpeg']:
            continue
        imgs.append(f'{i}'.replace(f'{IMG_DIR}', ''))

img_selector = Selector(settings_panel, imgs, lambda item: create_select_callback(f'{item}'))
img_selector.name = 'ImgSelector'
img_selector.mcfg.propagate = True
img_selector.place(relative_y=0.1, relative_width=1, relative_height=0.9)

#dp = async_ui_thread(loop)

root.mainloop()
